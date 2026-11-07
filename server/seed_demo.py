#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# fills the server with made up trips so the dashboard can be shown in a demo
# these rows use the device name demo and the dashboard marks them SAMPLE DATA
# python seed_demo.py name password
import datetime
import random
import sys
import uuid

import db
import tips

CUES = [
    ("yawning", 0.28, "Yawning detected"),
    ("hand_over_mouth", 0.14, "Hand over mouth detected"),
    ("phone_use", 0.24, "Phone use detected"),
    ("drinking", 0.26, "Drinking detected"),
    ("eyes_closed", 0.04, "Eyes closed"),
    ("camera_blocked", 0.04, "Camera blocked"),
]


def pick_class():
    r = random.random()
    total = 0
    for c in CUES:
        total = total + c[1]
        if r <= total:
            return c
    return CUES[0]


def add_trip(driver_id, start, minutes):
    sid = str(uuid.uuid4())
    end = start + datetime.timedelta(minutes=minutes)
    db.run("INSERT INTO session (session_id, driver_id, device_id, started_at, ended_at, monitored_pct) VALUES (:s, :d, 'demo', :a, :b, :m)",
           {"s": sid, "d": driver_id, "a": start.isoformat(), "b": end.isoformat(), "m": round(random.uniform(94, 100), 1)})
    n = random.randint(1, 5 + minutes // 12)
    for i in range(n):
        c = pick_class()
        at = start + datetime.timedelta(minutes=random.uniform(2, minutes - 1))
        secs = round(random.uniform(1.5, 8), 1)
        tier = random.randint(1, 2)
        if c[0] == "camera_blocked":
            tier = 0
        if c[0] == "eyes_closed":
            tier = 3
        db.run("INSERT INTO event (event_id, session_id, ts, class_name, confidence, duration_s, tier, message, escalated) VALUES (:i, :s, :t, :c, :f, :d, :n, :m, 0)",
               {"i": str(uuid.uuid4()), "s": sid, "t": at.isoformat(timespec="seconds"), "c": c[0],
                "f": round(random.uniform(0.55, 0.95), 2), "d": secs, "n": tier, "m": c[2] + "."})
    tips.update_tips(sid, driver_id)


if len(sys.argv) < 3:
    print("use: python seed_demo.py name password")
else:
    db.setup()
    random.seed(34)
    driver_id = random.randint(1, 2000000000)
    db.set_password(driver_id, sys.argv[1], sys.argv[2])
    db.run("INSERT INTO device (device_id) VALUES ('demo') ON CONFLICT (device_id) DO NOTHING")

    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    monday = today - datetime.timedelta(days=today.weekday())
    for week in [14, 7, 0]:
        for day in range(7):
            when = monday - datetime.timedelta(days=week) + datetime.timedelta(days=day)
            if when <= today:
                add_trip(driver_id, when + datetime.timedelta(hours=7, minutes=random.randint(0, 50)), random.randint(25, 60))
                if random.random() < 0.7:
                    add_trip(driver_id, when + datetime.timedelta(hours=17, minutes=random.randint(0, 50)), random.randint(25, 100))
    print("done, driver id= " + str(driver_id))
