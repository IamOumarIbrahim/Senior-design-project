#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# records one session in the parked car, a 20 s neutral baseline then 10 minutes
# file names only have the subject id, never a real name
# python record_session.py S01 1 afternoon
import os
import sys
import time

import cv2

CAM = 0
W = 1920
H = 1080
FPS = 30
BASELINE_S = 20
SESSION_S = 600
OUT_DIR = "recordings"


def record(cap, path, seconds):
    fourcc = cv2.VideoWriter_fourcc("m", "p", "4", "v")
    out = cv2.VideoWriter(path, fourcc, FPS, (W, H))
    start = time.time()
    n = 0
    while time.time() - start < seconds:
        ok, frame = cap.read()
        if ok:
            out.write(frame)
            n = n + 1
    out.release()
    print("saved " + path + " with " + str(n) + " frames")


if len(sys.argv) < 4:
    print("use: python record_session.py S01 1 afternoon")
else:
    subject = sys.argv[1]
    number = sys.argv[2]
    light = sys.argv[3]

    folder = os.path.join(OUT_DIR, subject)
    if os.path.exists(folder) == False:
        os.makedirs(folder)

    cap = cv2.VideoCapture(CAM)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc("M", "J", "P", "G"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    if cap.isOpened():
        name = subject + "_s" + number + "_" + light
        input("Baseline: sit normally for 20 s. Press enter to start ")
        record(cap, os.path.join(folder, name + "_baseline.mp4"), BASELINE_S)
        input("Session: follow the guideline for 10 minutes. Press enter to start ")
        record(cap, os.path.join(folder, name + ".mp4"), SESSION_S)
    else:
        print("camera not found")
    cap.release()
