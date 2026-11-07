#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# FS-08 and FS-21
# the real test uses a smart relay on the pi power, here we kill the process
# so this proves the database stays clean but not a real power loss
import os
import random
import shutil
import sqlite3
import subprocess
import sys
import tempfile

from helper import HERE, check, done

import config
from event_logger import EventLogger, check_pin, hash_pin

folder = tempfile.mkdtemp()
path = os.path.join(folder, "t.db")
log = EventLogger(path)

# Journal mode and tables
db = sqlite3.connect(path)
mode = db.execute("PRAGMA journal_mode").fetchone()[0]
db.close()
check("database is in wal mode", mode == "wal")

check("right pin works", check_pin("1234", hash_pin("1234")))
check("wrong pin fails", check_pin("1235", hash_pin("1234")) == False)

d1 = log.add_driver("1111", "Driver 1", "en")
d2 = log.add_driver("2222", "Driver 2", "ar")
f = log.find_driver("2222")
check("finds driver from pin", f != None and f["driver_id"] == d2 and f["language"] == "ar")
check("unknown pin is a new driver", log.find_driver("9999") == None)
saved = log.read("SELECT pin_hash FROM driver WHERE driver_id=?", (d2,))[0][0]
check("pin is not saved in plain text", saved != "2222" and len(saved) > 60)

check("new driver has no calibration", log.load_calibration(d1) == None)
log.save_calibration(d1, {"yawning": 0.6}, 0.3)
log.save_calibration(d1, {"yawning": 0.7}, 0.31, -9.5)
c = log.load_calibration(d1)
check("newest calibration is used", c["cutoffs"]["yawning"] == 0.7 and c["ear_open"] == 0.31)
check("rest pitch is saved", c["pitch_rest"] == -9.5)

log.add_device("dev1", "v1")
sid = log.new_session(d1, "dev1")
e = {"event_id": "e1", "class_name": "drinking", "confidence": 0.8, "duration_s": 1.5,
     "tier": 1, "message": "x", "escalated": 0}
log.write(e, sid, "2026-11-07T10:00:00")
log.set_duration("e1", 4.5)
log.flush()
check("session not ready before it ends", len(log.unsent_sessions()) == 0)
log.end_session(sid, 98.5)
check("session ready after it ends", len(log.unsent_sessions()) == 1)
rows = log.unsent_events(sid, 10)
check("event row has final duration", len(rows) == 1 and rows[0]["duration_s"] == 4.5)
log.mark_events(["e1"])
check("marked rows are not sent again", len(log.unsent_events(sid, 10)) == 0)
log.close()

# Bad file gets moved aside
bad = os.path.join(folder, "bad.db")
f2 = open(bad, "wb")
f2.write(b"this is not a database at all" * 100)
f2.close()
log2 = EventLogger(bad)
log2.close()
names = os.listdir(folder)
moved = False
for n in names:
    if n.startswith("bad.db.bad"):
        moved = True
check("bad file moved and new one made", moved)

# Kill test, 50 times like the report
child = os.path.join(HERE, "power_cut_child.py")
lost = 0
broken = 0
print("killing the writer 50 times ...")
for i in range(50):
    p = os.path.join(folder, "kill" + str(i) + ".db")
    run = subprocess.Popen([sys.executable, child, p], stdout=subprocess.PIPE, text=True)
    stop_at = random.randint(1, 40)
    seen = []
    while len(seen) < stop_at:
        line = run.stdout.readline()
        seen.append(line.strip())
    run.kill()
    run.wait()
    run.stdout.close()

    log3 = EventLogger(p)   # this runs the same check as a real boot
    if len(log3.read("SELECT 1")) != 1:
        broken = broken + 1
    db = sqlite3.connect(p)
    if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        broken = broken + 1
    for s in seen:
        got = db.execute("SELECT count(*) FROM event WHERE event_id=?", (s,)).fetchone()[0]
        if got != 1:
            lost = lost + 1
    db.close()
    log3.close()

check("50 kills: database passes integrity check", broken == 0)
check("50 kills: no committed event lost", lost == 0)
print("sync mode used= " + config.DB_SYNC)

shutil.rmtree(folder, ignore_errors=True)
done()
