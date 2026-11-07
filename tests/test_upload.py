#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# FS-22 FS-23 and the security tests in section 5.4.2
# real https on this pc with our own test certificate, sqlite instead of postgres
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

folder = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(folder, "server.db").replace("\\", "/")

from helper import REPO, check, done

import config
import db
import stats
import tips
from event_logger import EventLogger
from uploader import Uploader

PORT = 18443
key_file = os.path.join(folder, "key.pem")
cert_file = os.path.join(folder, "cert.pem")
subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key_file, "-out", cert_file,
                "-days", "1", "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost"],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

db.setup()
device_key = db.add_device("dev1")
other_key = db.add_device("dev2")


def start_server():
    cmd = [sys.executable, "-m", "uvicorn", "app:app", "--port", str(PORT), "--log-level", "error",
           "--ssl-keyfile", key_file, "--ssl-certfile", cert_file]
    proc = subprocess.Popen(cmd, cwd=os.path.join(REPO, "server"))
    for i in range(100):
        s = socket.socket()
        s.settimeout(0.2)
        try:
            s.connect(("127.0.0.1", PORT))
            s.close()
            return proc
        except OSError:
            time.sleep(0.2)
    return proc


def make_trip(log, driver_id, start, n):
    sid = log.new_session(driver_id, "dev1")
    log.set_start(sid, start)
    for i in range(n):
        e = {}
        e["event_id"] = sid + "-" + str(i)
        e["class_name"] = "phone_use"
        e["confidence"] = 0.8
        e["duration_s"] = 3.0
        e["tier"] = 1
        e["message"] = "Phone use detected for 2.0 seconds."
        e["escalated"] = 0
        log.write(e, sid, start[:14] + "1" + str(i) + ":00")
    log.flush()
    log.end_session(sid, 97.5, start[:11] + "11:00:00")
    return sid


config.UPLOAD_URL = "https://localhost:" + str(PORT) + "/api/v1/events"
config.DEVICE_ID = "dev1"
config.DEVICE_KEY = device_key
config.CA_FILE = cert_file
config.RETRY_S = [0.1, 0.1, 0.1]

log = EventLogger(os.path.join(folder, "edge.db"))
log.add_device("dev1", "v1")
driver_a = log.add_driver("1111", "Alia", "en")
sid1 = make_trip(log, driver_a, "2026-11-02T10:00:00", 3)

# Server down, nothing is lost
up = Uploader(log)
sent = up.sync()
check("server down sends nothing", sent == 0)
check("rows wait for the next try", len(log.unsent_events(sid1, 100)) == 3)

server = start_server()

# Plain http is refused by the device
config.UPLOAD_URL = "http://localhost:" + str(PORT) + "/api/v1/events"
check("plain http is refused", Uploader(log).sync() == 0)
config.UPLOAD_URL = "https://localhost:" + str(PORT) + "/api/v1/events"

# Self signed certificate the device doesnt trust
config.CA_FILE = ""
check("self signed certificate is refused", Uploader(log).sync() == 0)
check("no rows marked after refused certificate", len(log.unsent_events(sid1, 100)) == 3)
config.CA_FILE = cert_file

# Wrong key
config.DEVICE_KEY = "wrong"
check("wrong device key is refused", Uploader(log).sync() == 0)
config.DEVICE_KEY = device_key

# Good upload
sent = Uploader(log).sync()
check("all events uploaded", sent == 3)
check("rows marked after the server said ok", len(log.unsent_events(sid1, 100)) == 0)
check("session marked as sent", len(log.unsent_sessions()) == 0)
got = db.rows("SELECT count(*) FROM event")[0][0]
check("server has 3 events", got == 3)

# Retry after the answer was lost, no duplicates
log.run("UPDATE event SET uploaded=0 WHERE session_id=?", (sid1,))
log.run("UPDATE session SET uploaded=0 WHERE session_id=?", (sid1,))
log.flush()
sent = Uploader(log).sync()
check("retry is accepted", sent == 3)
check("retry makes no duplicates", db.rows("SELECT count(*) FROM event")[0][0] == 3)

# Another device cant write into this session
config.DEVICE_ID = "dev2"
config.DEVICE_KEY = other_key
log.run("UPDATE event SET uploaded=0 WHERE session_id=?", (sid1,))
log.run("UPDATE session SET uploaded=0 WHERE session_id=?", (sid1,))
log.flush()
check("other device is refused", Uploader(log).sync() == 0)
config.DEVICE_ID = "dev1"
config.DEVICE_KEY = device_key
Uploader(log).sync()

# Big trip goes in batches
config.UPLOAD_BATCH = 2
sid2 = make_trip(log, driver_a, "2026-11-03T10:00:00", 5)
check("batches send everything", Uploader(log).sync() == 5)
config.UPLOAD_BATCH = 500

# Only allowed fields leave the car
rows = log.unsent_sessions()
sid3 = make_trip(log, driver_a, "2026-11-04T10:00:00", 1)
row = log.unsent_events(sid3, 10)[0]
allowed = ["event_id", "session_id", "ts", "class_name", "confidence", "duration_s", "tier", "message", "escalated"]
only = True
for k in row:
    if k not in allowed:
        only = False
check("event row has only the allowed fields", only)
text = json.dumps(row)
check("nothing big like an image in the row", len(text) < 500)
Uploader(log).sync()

# Tips
tip_rows = db.rows("SELECT rule, text FROM tip WHERE session_id=:s", {"s": sid3})
names = []
for t in tip_rows:
    names.append(t[0])
print("tips= " + str(tip_rows))
check("phone on many trips gives a tip", "phone_repeat" in names)
check("tip says trips out of trips", "3 of 3 trips" in tip_rows[0][1] or "3 of 3 trips" in str(tip_rows))

# Dashboard account, driver b must not see the trips of driver a
import httpx

db.set_password(driver_a, "Alia", "alia-pass")
db.set_password(555, "Bilal", "bilal-pass")
base = "https://localhost:" + str(PORT)
c = httpx.Client(verify=cert_file, base_url=base)

res = c.get("/api/v1/summary")
check("no token is refused", res.status_code == 401)

res = c.post("/api/v1/login", json={"name": "Alia", "password": "wrong"})
check("wrong password is refused", res.status_code == 401)

res = c.post("/api/v1/login", json={"name": "Alia", "password": "alia-pass"})
check("right password logs in", res.status_code == 200)
token_a = res.json()["token"]
head_a = {"Authorization": "Bearer " + token_a}

res = c.post("/api/v1/login", json={"name": "Bilal", "password": "bilal-pass"})
head_b = {"Authorization": "Bearer " + res.json()["token"]}

res = c.get("/api/v1/summary", headers=head_a)
data = res.json()
check("summary has the numbers", data["kpi"]["distraction"] == 9 and data["kpi"]["monitored"] == 97.5)
check("counts per class", data["breakdown"][0]["name"] == "Phone use" and data["breakdown"][0]["count"] == 9)

trips = c.get("/api/v1/trips", headers=head_a).json()
check("three trips listed", len(trips) == 3)
res = c.get("/api/v1/trips/" + sid1, headers=head_a)
check("driver sees their own trip", res.status_code == 200)
res = c.get("/api/v1/trips/" + sid1, headers=head_b)
check("other driver cant see that trip", res.status_code == 404)
check("other driver has no trips", c.get("/api/v1/trips", headers=head_b).json() == [])
check("other driver has empty summary", c.get("/api/v1/summary", headers=head_b).json()["empty"] == True)

locked = False
for i in range(7):
    res = c.post("/api/v1/login", json={"name": "Bilal", "password": "nope"})
    if res.status_code == 429:
        locked = True
check("too many wrong passwords locks for a while", locked)

server.terminate()
server.wait()
log.close()
c.close()
shutil.rmtree(folder, ignore_errors=True)
done()
