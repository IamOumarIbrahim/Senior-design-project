#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import datetime
import random

import db

LAST_TRIPS = 7
DROWSY = ["yawning", "hand_over_mouth"]


def parse(t):
    return datetime.datetime.fromisoformat(t)


def round_ten(x):
    return int(round(x / 10.0)) * 10


# gets the last trips of a driver with their first time events, newest first
def last_trips(driver_id):
    found = db.rows("SELECT session_id, started_at, monitored_pct FROM session WHERE driver_id=:d ORDER BY started_at DESC LIMIT " + str(LAST_TRIPS),
                    {"d": driver_id})
    trips = []
    for s in found:
        ev = db.rows("SELECT class_name, ts FROM event WHERE session_id=:s AND escalated=0 ORDER BY ts", {"s": s[0]})
        trips.append({"id": s[0], "start": parse(s[1]), "monitored": s[2], "events": ev})
    return trips


def count_class(trip, names):
    n = 0
    for e in trip["events"]:
        if e[0] in names:
            n = n + 1
    return n


# rules over patterns that repeat across trips, so its advice and not a score
def make_tips(driver_id):
    trips = last_trips(driver_id)
    tips = []
    total = len(trips)
    if total == 0:
        return tips

    # Yawning rose after some minutes
    # for each trip take the time of the second drowsy cue
    minuts = []
    for trip in trips:
        seen = 0
        for e in trip["events"]:
            if e[0] in DROWSY:
                seen = seen + 1
                if seen == 2:
                    gap = parse(e[1]) - trip["start"]
                    minuts.append(gap.total_seconds() / 60.0)
    if len(minuts) >= 2:
        s = 0
        for m in minuts:
            s = s + m
        rose = round_ten(s / len(minuts))
        if rose >= 10:
            text = "Yawning rose after " + str(rose) + " minutes on " + str(len(minuts)) + " of " + str(total) + " trips: take a break around " + str(rose + 10) + " minutes."
            tips.append(("yawning_rise", text))

    # Phone use on many trips
    k = 0
    for trip in trips:
        if count_class(trip, ["phone_use"]) > 0:
            k = k + 1
    if k >= 2:
        text = "Phone use happened on " + str(k) + " of " + str(total) + " trips: set navigation before leaving."
        tips.append(("phone_repeat", text))

    # Drinking
    k = 0
    for trip in trips:
        if count_class(trip, ["drinking"]) > 0:
            k = k + 1
    if k >= 3:
        text = "Drinking was seen on " + str(k) + " of " + str(total) + " trips: have your drink before you set off or at a stop."
        tips.append(("drinking_repeat", text))

    # Eyes closed on the last trip
    newest = trips[0]
    if count_class(newest, ["eyes_closed"]) > 0:
        tips.append(("eyes_closed", "Your eyes closed while driving on the last trip: do not start a long drive tired."))

    # Camera blocked
    if newest["monitored"] != None and newest["monitored"] < 90:
        tips.append(("camera_blocked", "The camera could only see you " + str(int(newest["monitored"])) + "% of the last trip: keep the lens clear."))

    if len(tips) == 0:
        tips.append(("clean", "No repeating problems on your last trips. Keep it up."))
    return tips


# saved on the newest session of the driver, old tips of that session are replaced
def update_tips(session_id, driver_id):
    db.run("DELETE FROM tip WHERE session_id=:s", {"s": session_id})
    tips = make_tips(driver_id)
    for t in tips:
        db.run("INSERT INTO tip (tip_id, session_id, rule, text) VALUES (:i, :s, :r, :t)",
               {"i": random.randint(1, 2000000000), "s": session_id, "r": t[0], "t": t[1]})
