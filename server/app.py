#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import mimetypes
import os
import secrets
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles

import db
import stats
import tips

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(os.path.dirname(HERE), "dashboard", "dist")

CLASS_NAMES = ["yawning", "hand_over_mouth", "drinking", "phone_use", "eyes_closed", "perclos", "camera_blocked"]
MAX_EVENTS = 1000
TOKEN_HOURS = 12
MAX_TRIES = 5
LOCK_S = 60

app = FastAPI()
db.setup()

tokens = {}     # token: driver and when it ends
tries = {}      # name: wrong tries and last try time


# the key in the header must match the hash we saved for this device
def device_ok(device_id, key):
    found = db.rows("SELECT api_key_hash FROM device WHERE device_id=:d", {"d": device_id})
    if len(found) == 0 or key == None or found[0][0] == None:
        return False
    return secrets.compare_digest(found[0][0], db.hash_key(key))


def good_event(e, session_id):
    names = ["event_id", "session_id", "ts", "class_name", "confidence", "duration_s", "tier", "message"]
    for n in names:
        if n not in e:
            return False
    if e["session_id"] != session_id:
        return False
    if e["class_name"] not in CLASS_NAMES:
        return False
    if e["tier"] < 0 or e["tier"] > 3:
        return False
    return True


@app.post("/api/v1/events")
async def post_events(request: Request):
    key = request.headers.get("X-Device-Key")
    body = await request.json()
    device_id = body.get("device_id")
    if device_ok(device_id, key) == False:
        raise HTTPException(status_code=401, detail="bad device key")

    s = body.get("session")
    events = body.get("events")
    if s == None or events == None or len(events) > MAX_EVENTS:
        raise HTTPException(status_code=400, detail="bad body")

    session_id = s["session_id"]
    driver_id = s["driver_id"]

    # a device cant write into the session of another device
    old = db.rows("SELECT device_id FROM session WHERE session_id=:s", {"s": session_id})
    if len(old) > 0 and old[0][0] != device_id:
        raise HTTPException(status_code=403, detail="not your session")

    db.run("INSERT INTO driver (driver_id) VALUES (:d) ON CONFLICT (driver_id) DO NOTHING", {"d": driver_id})
    db.run("INSERT INTO session (session_id, driver_id, device_id, started_at, ended_at, monitored_pct) VALUES (:s, :d, :v, :a, :b, :m) ON CONFLICT (session_id) DO NOTHING",
           {"s": session_id, "d": driver_id, "v": device_id, "a": s["started_at"], "b": s["ended_at"], "m": s["monitored_pct"]})

    # the id is made on the device so a retry cant make a secound copy
    accepted = []
    for e in events:
        if good_event(e, session_id):
            db.run("INSERT INTO event (event_id, session_id, ts, class_name, confidence, duration_s, tier, message, escalated) VALUES (:i, :s, :t, :c, :f, :d, :n, :m, :x) ON CONFLICT (event_id) DO NOTHING",
                   {"i": e["event_id"], "s": session_id, "t": e["ts"], "c": e["class_name"], "f": e["confidence"],
                    "d": e["duration_s"], "n": e["tier"], "m": e["message"], "x": e.get("escalated", 0)})
            accepted.append(e["event_id"])

    tips.update_tips(session_id, driver_id)
    return {"accepted": accepted}


@app.post("/api/v1/login")
async def login(request: Request):
    body = await request.json()
    name = str(body.get("name"))
    password = str(body.get("password"))

    # small lock so nobody can guess forever
    now = time.time()
    if name in tries and tries[name][0] >= MAX_TRIES and now - tries[name][1] < LOCK_S:
        raise HTTPException(status_code=429, detail="too many tries, wait a minute")

    found = db.rows("SELECT driver_id, pin_hash FROM driver WHERE display_name=:n", {"n": name})
    driver_id = None
    for r in found:
        if db.check_password(password, r[1]):
            driver_id = r[0]

    if driver_id == None:
        count = 0
        if name in tries:
            count = tries[name][0]
        tries[name] = [count + 1, now]
        raise HTTPException(status_code=401, detail="wrong name or password")

    if name in tries:
        del tries[name]
    token = secrets.token_hex(32)
    tokens[token] = {"driver_id": driver_id, "until": now + TOKEN_HOURS * 3600}
    return {"token": token, "name": name}


# every read goes through this so a driver only sees their own account
def who(request):
    head = request.headers.get("Authorization")
    driver_id = None
    if head != None and head.startswith("Bearer "):
        token = head[7:]
        if token in tokens and tokens[token]["until"] > time.time():
            driver_id = tokens[token]["driver_id"]
    if driver_id == None:
        raise HTTPException(status_code=401, detail="please log in")
    return driver_id


@app.get("/api/v1/summary")
def get_summary(request: Request):
    driver_id = who(request)
    week = request.query_params.get("week")
    return stats.summary(driver_id, week)


@app.get("/api/v1/trips")
def get_trips(request: Request):
    return stats.all_trips(who(request))


@app.get("/api/v1/trips/{session_id}")
def get_trip(session_id, request: Request):
    trip = stats.one_trip(who(request), session_id)
    if trip == None:
        raise HTTPException(status_code=404, detail="no such trip")
    return trip


@app.get("/api/v1/tips")
def get_tips(request: Request):
    return stats.all_tips(who(request))


@app.get("/api/v1/health")
def health():
    return {"ok": True}


# windows reads these from the registry and can get them wrong, then the page stays white
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")

# the built react page, has to be after the api routes
if os.path.exists(DIST):
    app.mount("/", StaticFiles(directory=DIST, html=True), name="dashboard")
