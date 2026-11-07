#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import datetime
import hashlib
import os
import queue
import random
import sqlite3
import threading
import time
import uuid

import config

TABLES = """
CREATE TABLE IF NOT EXISTS driver (
  driver_id INTEGER PRIMARY KEY,
  pin_hash TEXT,
  display_name TEXT,
  language TEXT
);
CREATE TABLE IF NOT EXISTS device (
  device_id TEXT PRIMARY KEY,
  model_version TEXT,
  api_key_hash TEXT
);
CREATE TABLE IF NOT EXISTS calibration (
  calib_id INTEGER PRIMARY KEY,
  driver_id INTEGER REFERENCES driver(driver_id),
  class_name TEXT,
  cutoff REAL,
  ear_open REAL,
  pitch_rest REAL,
  created_at TEXT
);
CREATE TABLE IF NOT EXISTS session (
  session_id TEXT PRIMARY KEY,
  driver_id INTEGER REFERENCES driver(driver_id),
  device_id TEXT REFERENCES device(device_id),
  started_at TEXT,
  ended_at TEXT,
  monitored_pct REAL,
  uploaded INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS event (
  event_id TEXT PRIMARY KEY,
  session_id TEXT REFERENCES session(session_id),
  ts TEXT,
  class_name TEXT,
  confidence REAL,
  duration_s REAL,
  tier INTEGER,
  message TEXT,
  escalated INTEGER DEFAULT 0,
  uploaded INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS tip (
  tip_id INTEGER PRIMARY KEY,
  session_id TEXT REFERENCES session(session_id),
  rule TEXT,
  text TEXT
);
"""


def now_text():
    return datetime.datetime.now().isoformat(timespec="seconds")


def hash_pin(pin, salt=None):
    if salt == None:
        salt = os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), 100000)
    return salt + "$" + h.hex()


def check_pin(pin, saved):
    parts = saved.split("$")
    return hash_pin(pin, parts[0]) == saved


class EventLogger:

    def __init__(self, path):
        self.path = path
        folder = os.path.dirname(path)
        if folder != "" and os.path.exists(folder) == False:
            os.makedirs(folder)
        self.check_file()
        self.q = queue.Queue()
        self.thread = threading.Thread(target=self.writer, daemon=True)
        self.thread.start()

    # on every boot before a new session
    # if the file is bad move it aside and start a new one
    def check_file(self):
        ok = True
        if os.path.exists(self.path):
            db = sqlite3.connect(self.path)
            try:
                rows = db.execute("PRAGMA integrity_check").fetchall()
                if rows[0][0] != "ok":
                    ok = False
            except sqlite3.DatabaseError:
                ok = False
            db.close()
        if ok == False:
            new_name = self.path + ".bad" + str(int(time.time()))
            print("log file failed the check, moved to " + new_name)
            os.rename(self.path, new_name)
            for extra in ["-wal", "-shm"]:
                if os.path.exists(self.path + extra):
                    os.remove(self.path + extra)
        db = sqlite3.connect(self.path)
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript(TABLES)
        db.commit()
        db.close()

    # only this thread writes, one small transction per item
    def writer(self):
        db = sqlite3.connect(self.path)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=" + config.DB_SYNC)
        while True:
            item = self.q.get()
            if item == None:
                self.q.task_done()
                break
            db.execute(item[0], item[1])
            db.commit()
            self.q.task_done()
        db.close()

    def run(self, sql, values):
        self.q.put((sql, values))

    # wait until everything in the queue is on disk
    def flush(self):
        self.q.join()

    def read(self, sql, values=()):
        db = sqlite3.connect(self.path)
        rows = db.execute(sql, values).fetchall()
        db.close()
        return rows

    def close(self):
        self.q.put(None)
        self.thread.join()

    def write(self, event, session_id, ts):
        sql = "INSERT INTO event (event_id, session_id, ts, class_name, confidence, duration_s, tier, message, escalated) VALUES (?,?,?,?,?,?,?,?,?)"
        values = (event["event_id"], session_id, ts, event["class_name"], event["confidence"],
                  event["duration_s"], event["tier"], event["message"], event["escalated"])
        self.run(sql, values)

    # the first row of a cue gets the full length when the cue ends
    def set_duration(self, event_id, duration):
        self.run("UPDATE event SET duration_s=? WHERE event_id=?", (duration, event_id))

    def add_device(self, device_id, version):
        self.run("INSERT OR IGNORE INTO device (device_id, model_version) VALUES (?,?)", (device_id, version))
        self.run("UPDATE device SET model_version=? WHERE device_id=?", (version, device_id))

    # random id so two devices dont give two drivers the same number
    def add_driver(self, pin, name, language):
        driver_id = random.randint(1, 2000000000)
        self.run("INSERT INTO driver (driver_id, pin_hash, display_name, language) VALUES (?,?,?,?)",
                 (driver_id, hash_pin(pin), name, language))
        self.flush()
        return driver_id

    def find_driver(self, pin):
        rows = self.read("SELECT driver_id, pin_hash, display_name, language FROM driver")
        found = None
        for r in rows:
            if check_pin(pin, r[1]):
                found = {"driver_id": r[0], "display_name": r[2], "language": r[3]}
        return found

    def save_calibration(self, driver_id, cutoffs, ear_open, pitch_rest=None):
        when = now_text()
        for c in cutoffs:
            self.run("INSERT INTO calibration (driver_id, class_name, cutoff, ear_open, pitch_rest, created_at) VALUES (?,?,?,?,?,?)",
                     (driver_id, c, cutoffs[c], ear_open, pitch_rest, when))
        self.flush()

    # newest row for each class, returns None for a new driver
    def load_calibration(self, driver_id):
        rows = self.read("SELECT class_name, cutoff, ear_open, pitch_rest FROM calibration WHERE driver_id=? ORDER BY calib_id",
                         (driver_id,))
        if len(rows) == 0:
            return None
        cutoffs = {}
        ear = None
        pitch = None
        for r in rows:
            cutoffs[r[0]] = r[1]
            ear = r[2]
            pitch = r[3]
        return {"cutoffs": cutoffs, "ear_open": ear, "pitch_rest": pitch}

    def new_session(self, driver_id, device_id):
        session_id = str(uuid.uuid4())
        self.run("INSERT INTO session (session_id, driver_id, device_id, started_at) VALUES (?,?,?,?)",
                 (session_id, driver_id, device_id, now_text()))
        self.flush()
        return session_id

    def set_start(self, session_id, started_at):
        self.run("UPDATE session SET started_at=? WHERE session_id=?", (started_at, session_id))

    def end_session(self, session_id, monitored_pct, ended_at=None):
        if ended_at == None:
            ended_at = now_text()
        self.run("UPDATE session SET ended_at=?, monitored_pct=? WHERE session_id=?",
                 (ended_at, monitored_pct, session_id))
        self.flush()

    # power is cut at ignition off so the last session may have no end time
    # use the last event as the end, or it would never be uploaded
    # monitored stays empty because we dont know it
    def close_old_sessions(self):
        rows = self.read("SELECT session_id, started_at FROM session WHERE ended_at IS NULL")
        for r in rows:
            last = self.read("SELECT MAX(ts) FROM event WHERE session_id=?", (r[0],))
            end = last[0][0]
            if end == None:
                end = r[1]
            self.run("UPDATE session SET ended_at=? WHERE session_id=?", (end, r[0]))
        self.flush()
        return len(rows)

    def unsent_sessions(self):
        rows = self.read("SELECT session_id, driver_id, device_id, started_at, ended_at, monitored_pct FROM session WHERE uploaded=0 AND ended_at IS NOT NULL")
        result = []
        for r in rows:
            s = {}
            s["session_id"] = r[0]
            s["driver_id"] = r[1]
            s["device_id"] = r[2]
            s["started_at"] = r[3]
            s["ended_at"] = r[4]
            s["monitored_pct"] = r[5]
            result.append(s)
        return result

    def unsent_events(self, session_id, limit):
        rows = self.read("SELECT event_id, session_id, ts, class_name, confidence, duration_s, tier, message, escalated FROM event WHERE session_id=? AND uploaded=0 LIMIT ?",
                         (session_id, limit))
        result = []
        for r in rows:
            e = {}
            e["event_id"] = r[0]
            e["session_id"] = r[1]
            e["ts"] = r[2]
            e["class_name"] = r[3]
            e["confidence"] = r[4]
            e["duration_s"] = r[5]
            e["tier"] = r[6]
            e["message"] = r[7]
            e["escalated"] = r[8]
            result.append(e)
        return result

    def mark_events(self, ids):
        for i in ids:
            self.run("UPDATE event SET uploaded=1 WHERE event_id=?", (i,))
        self.flush()

    def mark_session(self, session_id):
        self.run("UPDATE session SET uploaded=1 WHERE session_id=?", (session_id,))
        self.flush()
