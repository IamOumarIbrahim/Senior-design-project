#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# T-04 T-06 T-15 T-16 and the numbers worked out in section 4.3.6
import math

from helper import check, done

import config
import messages
from decision_engine import DecisionEngine
from ema_filter import EMAFilter


def zero_scores():
    x = {}
    for c in config.CLASSES:
        x[c] = 0.0
    return x


# plays a list of (start, end, class, score) cues and returns all events
def play(cues, seconds, fps):
    ema = EMAFilter(config.TAU)
    eng = DecisionEngine(config.CUTOFF, config.COOLDOWN_S)
    dt = 1.0 / fps
    events = []
    frames = int(seconds * fps)
    for i in range(frames):
        t = i * dt
        x = zero_scores()
        for cue in cues:
            if t >= cue[0] and t < cue[1]:
                x[cue[2]] = cue[3]
        s = ema.update(x, dt)
        out = eng.step(s, t, x)
        for e in out:
            events.append(e)
    return events


def alerts_only(events):
    keep = []
    for e in events:
        if e["kind"] == "alert":
            keep.append(e)
    return keep


# Numbers from the report
a30 = 1 - math.exp(-(1 / 30.0) / 0.6)
a15 = 1 - math.exp(-(1 / 15.0) / 0.6)
check("alpha at 30 fps is 0.054", abs(a30 - 0.054) < 0.0005)
check("alpha at 15 fps is 0.105", abs(a15 - 0.105) < 0.0005)

ema = EMAFilter(config.TAU)
x = zero_scores()
x["yawning"] = 1.0
s = ema.update(x, 1 / 30.0)
check("single spike only reaches 0.054", abs(s["yawning"] - 0.054) < 0.0005)

ema = EMAFilter(config.TAU)
k = 0
while s["yawning"] < 0.5 or k == 0:
    s = ema.update(x, 1 / 30.0)
    k = k + 1
check("13 frames to reach 0.5", k == 13)
check("delay is 0.42 s for yawning", abs(-0.6 * math.log(0.5) - 0.42) < 0.005)
check("delay is 0.80 s for phone", abs(-1.0 * math.log(1 - 0.55) - 0.80) < 0.005)

# one odd frame must not alert
ev = play([[5.0, 5.04, "phone_use", 1.0]], 10, 30)
check("single frame spike gives no alert", len(alerts_only(ev)) == 0)

# T-04 same cue at 10 15 and 30 fps
times = []
for fps in [10, 15, 30]:
    ev = alerts_only(play([[3.0, 9.0, "yawning", 0.95]], 12, fps))
    times.append(ev[0]["t"])
print("T-04 confirm times " + str(times))
check("T-04 confirm times agree within one frame", max(times) - min(times) <= 1 / 10.0)

# T-06 two cues 10 s apart
ev = alerts_only(play([[2, 6, "drinking", 0.95], [12, 16, "drinking", 0.95]], 25, 30))
check("T-06 both cues are logged", len(ev) == 2)
check("T-06 first one alerts", ev[0]["tier"] == 1)
check("T-06 second is muted", ev[1]["tier"] == 0)

# after the cooldown the third one is a new alert and it counts as 3 in 5 min
ev = alerts_only(play([[2, 6, "drinking", 0.95], [12, 16, "drinking", 0.95],
                       [60, 64, "drinking", 0.95]], 70, 30))
check("cooldown ends and third cue alerts", len(ev) == 3)
check("3 events in 5 minutes goes to tier 2", ev[2]["tier"] == 2)
check("tier 2 has a voice file name", ev[2]["voice"] == "drinking_n3")

# T-15 hold the cue for 15 s
ev = alerts_only(play([[1, 16, "yawning", 0.95]], 20, 30))
tiers = []
for e in ev:
    tiers.append(e["tier"])
check("T-15 tiers go 1 2 3", tiers == [1, 2, 3])
check("T-15 tier 2 at 5 s", abs(ev[1]["duration_s"] - 5) <= 0.2)
check("T-15 tier 3 at 10 s", abs(ev[2]["duration_s"] - 10) <= 0.2)
check("T-15 only first row counts as new", ev[0]["escalated"] == 0 and ev[1]["escalated"] == 1)

# T-16 message says what and how long or how often
for c in config.CLASSES:
    ev = alerts_only(play([[1, 8, c, 0.95]], 12, 30))
    good_msg = True
    for e in ev:
        if messages.NAME_EN[c] not in e["message"]:
            good_msg = False
        has_digit = False
        for ch in e["message"]:
            if ch.isdigit():
                has_digit = True
        if has_digit == False:
            good_msg = False
    check("T-16 message for " + c, good_msg)

# camera blocked pauses alerts
ema = EMAFilter(config.TAU)
eng = DecisionEngine(config.CUTOFF, config.COOLDOWN_S)
eng.set_blocked(True, 0)
x = zero_scores()
x["phone_use"] = 0.95
count = 0
for i in range(300):
    s = ema.update(x, 1 / 30.0)
    count = count + len(eng.step(s, i / 30.0, x))
check("no alerts while camera is blocked", count == 0)

# eyes closed goes straight to tier 3 from idle
eng = DecisionEngine(config.CUTOFF, config.COOLDOWN_S)
s = zero_scores()
out = eng.step(s, 0.5, s, {"closed_s": 2.0, "perclos": None, "head_down": True})
check("head down waits longer than 1.5 s", len(out) == 0)
out = eng.step(s, 1.0, s, {"closed_s": 1.5, "perclos": None})
check("eyes closed is tier 3", len(out) == 1 and out[0]["tier"] == 3)
check("eyes closed row keeps the length", out[0]["duration_s"] == 1.5 and out[0]["confidence"] == 1.0)
out = eng.step(s, 1.1, s, {"closed_s": 1.6, "perclos": None})
check("eyes closed fires once", len(out) == 0)

# perclos is a gentle tier 2 and fires once while it stays high
out = eng.step(s, 2.0, s, {"closed_s": 0, "perclos": 0.2})
check("perclos prompt is tier 2", len(out) == 1 and out[0]["tier"] == 2)
out = eng.step(s, 40.0, s, {"closed_s": 0, "perclos": 0.2})
check("perclos does not repeat", len(out) == 0)

done()
