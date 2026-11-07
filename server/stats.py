#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import datetime

import db

DISTRACT = ["drinking", "phone_use"]
DROWSY = ["yawning", "hand_over_mouth", "eyes_closed", "perclos"]
NICE = {
    "yawning": "Yawning",
    "hand_over_mouth": "Hand over mouth",
    "drinking": "Drinking",
    "phone_use": "Phone use",
    "eyes_closed": "Eyes closed",
    "perclos": "Tired eyes",
    "camera_blocked": "Camera blocked",
}


def parse(t):
    return datetime.datetime.fromisoformat(t)


def get_sessions(driver_id):
    found = db.rows("SELECT session_id, started_at, ended_at, monitored_pct, device_id FROM session WHERE driver_id=:d ORDER BY started_at",
                    {"d": driver_id})
    result = []
    for r in found:
        if r[1] != None and r[2] != None:
            s = {}
            s["id"] = r[0]
            s["start"] = parse(r[1])
            s["end"] = parse(r[2])
            s["monitored"] = r[3]
            s["device"] = r[4]
            result.append(s)
    return result


# only the first row of each cue, later rows are the same cue getting stonger
def get_events(session_id):
    found = db.rows("SELECT event_id, ts, class_name, confidence, duration_s, tier, message FROM event WHERE session_id=:s AND escalated=0 ORDER BY ts",
                    {"s": session_id})
    result = []
    for r in found:
        e = {}
        e["id"] = r[0]
        e["ts"] = parse(r[1])
        e["class"] = r[2]
        e["confidence"] = r[3]
        e["duration"] = r[4]
        e["tier"] = r[5]
        e["message"] = r[6]
        result.append(e)
    return result


def monday_of(day):
    return datetime.datetime(day.year, day.month, day.day) - datetime.timedelta(days=day.weekday())


def change(now, before):
    if before == 0:
        return None
    return round(100.0 * (now - before) / before)


# drive seconds inside one week
def count_week(sessions, start, end):
    r = {"drive": 0, "distract": 0, "drowsy": 0, "blocked": 0, "mon_s": 0, "mon_w": 0}
    for s in sessions:
        if s["start"] >= start and s["start"] < end:
            secs = (s["end"] - s["start"]).total_seconds()
            r["drive"] = r["drive"] + secs
            if s["monitored"] != None:
                r["mon_s"] = r["mon_s"] + s["monitored"] * secs
                r["mon_w"] = r["mon_w"] + secs
            for e in get_events(s["id"]):
                if e["class"] in DISTRACT:
                    r["distract"] = r["distract"] + 1
                elif e["class"] in DROWSY:
                    r["drowsy"] = r["drowsy"] + 1
                elif e["class"] == "camera_blocked":
                    r["blocked"] = r["blocked"] + e["duration"]
    return r


# hours driven in each weekday and hour box
def driven_hours(sessions, start, end):
    hours = []
    for d in range(7):
        row = []
        for h in range(24):
            row.append(0.0)
        hours.append(row)
    for s in sessions:
        if s["start"] >= start and s["start"] < end:
            cur = s["start"]
            while cur < s["end"]:
                top = datetime.datetime(cur.year, cur.month, cur.day, cur.hour) + datetime.timedelta(hours=1)
                stop = top
                if s["end"] < stop:
                    stop = s["end"]
                hours[cur.weekday()][cur.hour] = hours[cur.weekday()][cur.hour] + (stop - cur).total_seconds() / 3600.0
                cur = top
    return hours


def summary(driver_id, week_text):
    sessions = get_sessions(driver_id)
    answer = {"empty": True}
    if len(sessions) > 0:
        answer["empty"] = False
        if week_text != None:
            start = monday_of(parse(week_text))
        else:
            start = monday_of(sessions[len(sessions) - 1]["start"])
        end = start + datetime.timedelta(days=7)
        before = start - datetime.timedelta(days=7)

        answer["week_start"] = start.date().isoformat()
        answer["week_end"] = (end - datetime.timedelta(days=1)).date().isoformat()
        answer["sample"] = False
        for s in sessions:
            if s["device"] == "demo":
                answer["sample"] = True
        answer["last_upload"] = sessions[len(sessions) - 1]["end"].isoformat()

        # Top numbers
        now = count_week(sessions, start, end)
        old = count_week(sessions, before, start)
        kpi = {}
        kpi["drive_s"] = now["drive"]
        kpi["drive_change"] = change(now["drive"], old["drive"])
        kpi["distraction"] = now["distract"]
        kpi["distraction_change"] = change(now["distract"], old["distract"])
        kpi["drowsiness"] = now["drowsy"]
        kpi["drowsiness_change"] = change(now["drowsy"], old["drowsy"])
        kpi["monitored"] = None
        if now["mon_w"] > 0:
            kpi["monitored"] = round(now["mon_s"] / now["mon_w"], 1)
        kpi["blocked_min"] = round(now["blocked"] / 60.0, 1)
        answer["kpi"] = kpi

        # Trend is 4 points for each day, breakdown and heatmap
        trend_a = []
        trend_b = []
        for i in range(28):
            trend_a.append(0)
            trend_b.append(0)
        counts = {}
        heat_n = []
        for d in range(7):
            row = []
            for h in range(24):
                row.append(0)
            heat_n.append(row)
        week_rows = []

        for s in sessions:
            if s["start"] >= start and s["start"] < end:
                for e in get_events(s["id"]):
                    week_rows.append(e)
                    c = e["class"]
                    if c in counts:
                        counts[c] = counts[c] + 1
                    else:
                        counts[c] = 1
                    slot = e["ts"].weekday() * 4 + e["ts"].hour // 6
                    if c in DISTRACT:
                        trend_a[slot] = trend_a[slot] + 1
                    if c in DROWSY:
                        trend_b[slot] = trend_b[slot] + 1
                    if c != "camera_blocked":
                        heat_n[e["ts"].weekday()][e["ts"].hour] = heat_n[e["ts"].weekday()][e["ts"].hour] + 1

        answer["trend_distraction"] = trend_a
        answer["trend_drowsiness"] = trend_b

        breakdwon = []
        for c in NICE:
            if c in counts:
                breakdwon.append({"key": c, "name": NICE[c], "count": counts[c]})
        answer["breakdown"] = breakdwon

        # alerts for each hour of driving
        hours = driven_hours(sessions, start, end)
        heat = []
        for d in range(7):
            row = []
            for h in range(24):
                if hours[d][h] > 0:
                    row.append(round(heat_n[d][h] / hours[d][h], 2))
                else:
                    row.append(0)
            heat.append(row)
        answer["heat"] = heat

        # Last trip
        last = sessions[len(sessions) - 1]
        answer["last_trip"] = trip_detail(last)

        # Recent
        week_rows.reverse()
        recent = []
        for e in week_rows:
            if len(recent) < 5:
                recent.append(row_of(e))
        answer["recent"] = recent

        tips = db.rows("SELECT text FROM tip WHERE session_id=:s", {"s": last["id"]})
        tip_list = []
        for t in tips:
            tip_list.append(t[0])
        answer["tips"] = tip_list
    return answer


def row_of(e):
    r = {}
    r["class"] = e["class"]
    r["name"] = NICE[e["class"]]
    r["message"] = e["message"]
    r["clock"] = e["ts"].strftime("%H:%M")
    r["day"] = e["ts"].date().isoformat()
    r["duration"] = round(e["duration"], 1)
    r["tier"] = e["tier"]
    return r


def trip_detail(s):
    t = {}
    t["session_id"] = s["id"]
    t["started_at"] = s["start"].isoformat()
    t["minutes"] = round((s["end"] - s["start"]).total_seconds() / 60.0, 1)
    t["monitored"] = s["monitored"]
    marks = []
    rows_list = []
    for e in get_events(s["id"]):
        minute = (e["ts"] - s["start"]).total_seconds() / 60.0
        marks.append({"minute": round(minute, 2), "class": e["class"]})
        rows_list.append(row_of(e))
    t["marks"] = marks
    t["events"] = rows_list
    return t


def all_trips(driver_id):
    sessions = get_sessions(driver_id)
    result = []
    i = len(sessions) - 1
    while i >= 0:
        s = sessions[i]
        n = 0
        for e in get_events(s["id"]):
            if e["class"] != "camera_blocked":
                n = n + 1
        result.append({"session_id": s["id"], "started_at": s["start"].isoformat(),
                       "minutes": round((s["end"] - s["start"]).total_seconds() / 60.0, 1),
                       "monitored": s["monitored"], "events": n})
        i = i - 1
    return result


# None if its not this drivers trip
def one_trip(driver_id, session_id):
    found = None
    for s in get_sessions(driver_id):
        if s["id"] == session_id:
            found = trip_detail(s)
    return found


def all_tips(driver_id):
    found = db.rows("SELECT t.text, s.started_at FROM tip t JOIN session s ON t.session_id = s.session_id WHERE s.driver_id=:d ORDER BY s.started_at DESC LIMIT 30",
                    {"d": driver_id})
    result = []
    seen = []
    for r in found:
        if r[0] not in seen:
            seen.append(r[0])
            result.append({"text": r[0], "day": r[1][:10]})
    return result
