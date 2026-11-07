#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# FS-02 FS-03 FS-17 T-17
# uses the replay video from make_replay.py if its there
import os
import time

import cv2
import numpy as np

from helper import REPO, check, done

import config
import native_blind
from detector import Detector
from frame_grabber import FrameGrabber
from preprocessor import Preprocessor

VIDEO = os.path.join(REPO, "data", "replay_subject_05.mp4")
has_video = os.path.exists(VIDEO)

# Crop
pre = Preprocessor()
big = np.zeros((1080, 1920, 3), dtype=np.uint8)
big[220, 640] = [255, 255, 255]   # mark the corner of the crop
part = pre.crop_resize(big)
check("1080p frame gives 640x640", part.shape[0] == 640 and part.shape[1] == 640)
check("crop starts at the fixed corner", part[0, 0, 0] == 255)
small = pre.crop_resize(np.zeros((480, 640, 3), dtype=np.uint8))
check("small video still gives 640x640", small.shape[0] == 640 and small.shape[1] == 640)

# a normal frame to compare with
if has_video:
    cap = cv2.VideoCapture(VIDEO)
    ok, normal = cap.read()
    cap.release()
else:
    np.random.seed(1)
    normal = np.random.randint(40, 200, (640, 640, 3), dtype=np.uint8)
normal = pre.crop_resize(normal)
check("normal frame is not bad", pre.frame_bad(normal) == False)

dark = np.full((640, 640, 3), 5, dtype=np.uint8)
torch = np.full((640, 640, 3), 250, dtype=np.uint8)
blur = cv2.GaussianBlur(normal, (0, 0), 25)
check("covered lens is bad", pre.frame_bad(dark))
check("torch is bad", pre.frame_bad(torch))
check("very blurred view is bad", pre.frame_bad(blur))


# T-17 feed a bad view for 5 s at 30 fps and find when it says blocked
def time_to_block(bad_frame):
    p = Preprocessor()
    t = 0.0
    for i in range(30):
        p.blind_check(normal, t)
        t = t + 1 / 30.0
    start = t
    found = None
    for i in range(150):
        if p.blind_check(bad_frame, t) and found == None:
            found = t - start
        t = t + 1 / 30.0
    return found


a = time_to_block(dark)
b = time_to_block(torch)
print("T-17 covered " + str(round(a, 2)) + " s, torch " + str(round(b, 2)) + " s")
check("T-17 covered lens in 3 to 3.5 s", a >= 3 and a <= 3.5)
check("T-17 torch in 3 to 3.5 s", b >= 3 and b <= 3.5)

p = Preprocessor()
t = 0.0
hit = False
for i in range(60):
    if p.blind_check(dark, t):
        hit = True
    t = t + 1 / 30.0
for i in range(100):
    if p.blind_check(normal, t):
        hit = True
    t = t + 1 / 30.0
check("2 s of bad view does not trigger", hit == False)

# Real model
det = Detector("pt", config.MODEL_PATH)
x = det.scores(normal, 0.25)
names_ok = True
for c in config.CLASSES:
    if c not in x:
        names_ok = False
check("model gives a score for all four classes", names_ok)
check("model class order matches config", list(det.model.names.values()) == config.CLASSES)

if has_video:
    # Backlog test, a slow reader must always get the newest frame
    g = FrameGrabber(VIDEO, True)
    check("clip opens", g.opened())
    check("clip is 10 fps", abs(g.fps - 10) < 1)
    g.start()
    first = g.read()
    time.sleep(1.0)
    second = g.read()
    g.stop()
    print("slow reader jumped " + str(round(second[1] - first[1], 2)) + " s of video")
    check("slow reader skips old frames", second[1] - first[1] >= 0.8)

    # Replay keeps every frame
    g = FrameGrabber(VIDEO, False)
    g.start()
    n = 0
    last = None
    while n < 60:
        item = g.read()
        last = item
        n = n + 1
    g.stop()
    check("replay keeps every frame", abs(last[1] - 59 / g.fps) < 0.001)

    # Speed of the whole vision part on this pc
    g = FrameGrabber(VIDEO, False)
    g.start()
    start = time.time()
    n = 0
    seen = {}
    while n < 150:
        item = g.read()
        crop = pre.crop_resize(item[0])
        x = det.scores(crop, 0.25)
        for c in x:
            if x[c] > 0:
                seen[c] = True
        n = n + 1
    g.stop()
    speed = n / (time.time() - start)
    print("vision speed on this pc= " + str(round(speed, 1)) + " fps")
    print("classes seen in first 15 s= " + str(list(seen.keys())))
    check("vision loop runs on real video", n == 150)
else:
    print("test video not found so the video checks were skipped")


# The c++ blind check has to give the same numbers as opencv
def same(img):
    a = pre.numbers_cv(img)
    b = native_blind.numbers(img)
    return abs(a[0] - b[0]) < 0.000001 and abs(a[1] - b[1]) < 0.000001


if native_blind.available():
    rng = np.random.default_rng(5)
    noise = rng.integers(0, 256, (640, 640, 3), dtype=np.uint8)
    check("native same on noise", same(noise))
    check("native same on black", same(np.zeros((640, 640, 3), dtype=np.uint8)))
    check("native same on white", same(np.full((640, 640, 3), 255, dtype=np.uint8)))
    check("native same on blur", same(cv2.GaussianBlur(noise, (21, 21), 0)))
    tiny = True
    for size in [(1, 1), (1, 7), (7, 1), (2, 3), (3, 2)]:
        if same(rng.integers(0, 256, (size[0], size[1], 3), dtype=np.uint8)) == False:
            tiny = False
    check("native same on tiny frames", tiny)
    big_noise = rng.integers(0, 256, (1080, 1920, 3), dtype=np.uint8)
    check("native same on a crop of a bigger frame", same(pre.crop_resize(big_noise)))
    if has_video:
        cap = cv2.VideoCapture(VIDEO)
        ok, real = cap.read()
        cap.release()
        check("native same on a real frame", same(real))

    # no library has to give the same answer through opencv
    saved = native_blind.lib
    a = pre.numbers(noise)
    native_blind.lib = None
    b = pre.numbers(noise)
    native_blind.lib = saved
    check("falls back to opencv with no library", abs(a[1] - b[1]) < 0.000001)
else:
    print("blind check library not built so the native checks were skipped")

done()
