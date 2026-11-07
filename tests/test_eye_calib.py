#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# T-19 T-20 FS-18 FS-19 FS-20
# mediapipe part only runs if mediapipe is installed
import math
import os
import random

import cv2
import numpy as np

from helper import check, done

import config
from calibrator import Calibrator
from crop_tracker import CropTracker
from decision_engine import DecisionEngine
from eye_module import EyeModule, ear_of, pitch_of

ROOT = os.environ.get("DMS_RGB_DIR", r"C:\Dev\repos\Public repos\ieee-aiot\data\processed\RGB")
FACE = os.path.join(ROOT, "images", "subject_05", "video_01", "subject_05_video_01_frame_0100.jpg")


def blank():
    x = {}
    for c in config.CLASSES:
        x[c] = 0.0
    return x


# Calibration formula
cal = Calibrator()
check("percentile matches numpy", abs(cal.percentile(list(range(101)), 99) - 99) < 0.0001)
values = [0.1, 0.7, 0.3, 0.9, 0.2]
check("percentile with gaps matches numpy", abs(cal.percentile(values, 99) - float(np.percentile(values, 99))) < 0.0001)

# Quiet driver, nothing above the default so the default stays
random.seed(3)
cal = Calibrator()
for i in range(600):
    x = blank()
    x["yawning"] = random.uniform(0, 0.2)
    cal.add(x, 0.31)
r = cal.finish(config.CUTOFF)
check("T-19 quiet driver keeps default cutoff", r["ok"] and r["cutoffs"]["yawning"] == 0.50)
check("open eye value saved", abs(r["ear_open"] - 0.31) < 0.001)

# Driver with a noisy class, less than 10% above the default
cal = Calibrator()
for i in range(600):
    x = blank()
    x["hand_over_mouth"] = random.uniform(0, 0.3)
    if i % 20 == 0:
        x["hand_over_mouth"] = 0.65
    cal.add(x, 0.3)
r = cal.finish(config.CUTOFF)
print("noisy class cutoff= " + str(round(r["cutoffs"]["hand_over_mouth"], 3)))
check("T-19 noisy class moves up to p99 + 0.05", abs(r["cutoffs"]["hand_over_mouth"] - 0.70) < 0.001)
check("other classes stay on default", r["cutoffs"]["drinking"] == 0.55)

# Ceiling
cal = Calibrator()
for i in range(600):
    x = blank()
    x["phone_use"] = 0.2
    if i % 15 == 0:
        x["phone_use"] = 0.95
    cal.add(x, None)
r = cal.finish(config.CUTOFF)
check("cutoff never above 0.85", r["cutoffs"]["phone_use"] == 0.85)
check("no eyes seen gives no open eye value", r["ear_open"] == None)
check("no eyes seen gives no rest pitch", r["pitch_rest"] == None)

# Rest pitch is the middle value, a look down in the baseline should not move it
cal = Calibrator()
for i in range(100):
    p = -8.0
    if i % 10 == 0:
        p = 20.0
    cal.add(blank(), 0.3, p)
r = cal.finish(config.CUTOFF)
check("rest pitch saved", r["pitch_rest"] == -8.0)

# Driver moved, more than 10% of frames above the default
cal = Calibrator()
for i in range(600):
    x = blank()
    if i < 100:
        x["yawning"] = 0.8
    cal.add(x, 0.3)
r = cal.finish(config.CUTOFF)
check("too many detections asks to redo", r["ok"] == False)
check("too many detections keeps defaults", r["cutoffs"]["yawning"] == 0.50)

# EAR formula, open eye shape from the paper figure
open_eye = [(0, 0), (2, 1), (4, 1), (6, 0), (4, -1), (2, -1)]
check("EAR formula", abs(ear_of(open_eye) - 2 / 6.0) < 0.0001)
check("flat eye is zero", ear_of([(0, 0), (2, 0), (4, 0), (6, 0), (4, 0), (2, 0)]) == 0)


# T-20, returns when the alert happened or None
# value is the EAR while closed, blink and pitch are what the face model gives
def closure(frames_closed, value_closed=0.08, blink=0.8, pitch=None):
    eye = EyeModule(0.30, False, -5.0)
    eng = DecisionEngine(config.CUTOFF, config.COOLDOWN_S)
    dt = 1 / 30.0
    t = 0.0
    hit = None
    start = None
    empty = blank()
    for i in range(30 + frames_closed + 30):
        value = 0.30
        b = 0.1
        p = -5.0
        if i >= 30 and i < 30 + frames_closed:
            value = value_closed
            b = blink
            if pitch != None:
                p = pitch
            if start == None:
                start = t
        eye.update(value, t, b, p)
        out = eng.step(empty, t, empty, eye.state(t))
        if len(out) > 0 and hit == None:
            hit = t - start + dt
        t = t + dt
    return hit


check("T-20 no alert at 1 s", closure(30) == None)
a = closure(46)
b = closure(60)
print("T-20 alert times " + str(a) + " " + str(b))
check("T-20 alert at 1.5 s", a != None and a <= 1.55)
check("T-20 alert for 2 s closure comes at 1.5 s", b != None and b <= 1.55)

# a blink should do nothing
check("blink of 0.2 s is ignored", closure(6) == None)

# false alarm cases from the replay
check("half open eye does not count as closed", closure(90, 0.20) == None)
check("low EAR with low blink score does not count", closure(90, 0.08, 0.3) == None)
check("looking down for 2 s does not alarm", closure(60, 0.08, 0.8, 10.0) == None)
c = closure(120, 0.08, 0.8, 10.0)
print("head down alert time " + str(c))
check("eyes shut with the head down still alarms at 3 s", c != None and c > 2.9 and c <= 3.05)
check("small head movement keeps 1.5 s", closure(60, 0.08, 0.8, 2.0) <= 1.55)
check("head up keeps 1.5 s", closure(60, 0.08, 0.8, -30.0) <= 1.55)

# Pitch from the face matrix, no turn, then head down by 20 degrees with scale 3
check("level head has zero pitch", abs(pitch_of([[1, 0, 0], [0, 1, 0], [0, 0, 1]])) < 0.0001)
a = math.radians(20)
tilt = [[3, 0, 0], [0, 3 * math.cos(a), -3 * math.sin(a)], [0, 3 * math.sin(a), 3 * math.cos(a)]]
check("head down gives plus 20", abs(pitch_of(tilt) - 20) < 0.0001)

# No saved rest pitch, learn it from the first seconds
eye = EyeModule(0.30, False)
t = 0.0
while t < config.CALIB_S + 1:
    eye.update(0.30, t, 0.1, -6.0)
    t = t + 0.1
check("rest pitch learned", eye.pitch_rest == -6.0)
eye.update(0.30, t, 0.1, 10.0)
check("head down seen after learning", eye.state(t)["head_down"])

# Missing eyes must not count as open and must not add closed time
eye = EyeModule(0.30, False)
t = 0.0
for i in range(30):
    eye.update(0.08, t)
    t = t + 1 / 30.0
held = eye.closed_s
for i in range(30):
    eye.update(None, t)
    t = t + 1 / 30.0
check("missing eyes keep the closed time", eye.closed_s == held)
eye.update(0.08, t)
check("closure continues after missing frames", eye.closed_s > held)

# PERCLOS, closed 20% of the time over 2 minutes
eye = EyeModule(0.30, False)
t = 0.0
check("perclos is none at the start", eye.perclos(0) == None)
for i in range(3600):
    value = 0.30
    if i % 10 < 2:
        value = 0.08
    eye.update(value, t)
    t = t + 1 / 30.0
p = eye.perclos(t)
print("perclos= " + str(round(p, 3)))
check("perclos close to 20%", abs(p - 0.20) < 0.02)
check("perclos keeps only 60 s", t - eye.history[0][0] <= 60.1)

# a long look at the lap is left out of perclos
eye = EyeModule(0.30, False, -5.0)
t = 0.0
for i in range(3600):
    p = -5.0
    value = 0.30
    b = 0.1
    if i % 10 < 3:
        p = 15.0
        value = 0.08
        b = 0.8
    eye.update(value, t, b, p)
    t = t + 1 / 30.0
check("head down time stays out of perclos", eye.perclos(t) == 0)

# only half the window seen must give none, not a good number
eye = EyeModule(0.30, False)
t = 0.0
for i in range(900):
    eye.update(0.30, t)
    t = t + 1 / 30.0
check("half a window gives no perclos", eye.perclos(t) == None)

# Crop tracking on a real face
if os.path.exists(FACE):
    frame = cv2.imread(FACE)
    canvas = np.full((1080, 1920, 3), 60, dtype=np.uint8)
    canvas[300:940, 1200:1840] = frame
    tr = CropTracker(1920, 1080)
    if tr.available():
        rect = tr.rect()
        check("starts on the fixed crop", rect[0] == config.CROP_X and rect[1] == config.CROP_Y)
        t = 0.0
        for i in range(8):
            rect = tr.update(canvas, t)
            t = t + 1.0
        print("tracked crop= " + str(rect))
        check("crop moved over to the face", rect[0] > 1000)
        check("crop stays inside the frame", rect[0] + rect[2] <= 1920 and rect[1] + rect[3] <= 1080)
    else:
        print("yunet model missing, crop test skipped")

    eye = EyeModule(0.30, True)
    if eye.available():
        # one frame can be a blink so look at the middle value of many frames
        folder = os.path.dirname(FACE)
        names = os.listdir(folder)
        names.sort()
        got = []
        for i in range(0, len(names), 20):
            v = eye.ear(cv2.imread(os.path.join(folder, names[i])))
            if v != None:
                got.append(v)
        got.sort()
        mid = got[len(got) // 2]
        print("middle EAR on a real driver= " + str(round(mid, 3)))
        check("real face gives a sensible EAR", mid > 0.2 and mid < 0.4)
        m = eye.measure(cv2.imread(FACE))
        print("real frame " + str(m))
        check("blink score is between 0 and 1", m["blink"] >= 0 and m["blink"] <= 1)
        check("pitch is a sensible angle", abs(m["pitch"]) < 60)
        empty_img = np.zeros((640, 640, 3), dtype=np.uint8)
        check("no face gives none", eye.ear(empty_img) == None)
        eye.model.close()
    else:
        print("mediapipe not available, real EAR test skipped")

done()
