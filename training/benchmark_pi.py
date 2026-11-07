#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# run this ON THE PI, 30 minutes on a recorded clip like section 5.4.2 says
# logs fps latency temperature and throttle flags
# NOT TESTED on a pi yet, the fps and latency part runs on a pc too
# python benchmark_pi.py clip.mp4 backend model minutes
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "edge"))

import config
from detector import Detector
from frame_grabber import FrameGrabber
from preprocessor import Preprocessor


def read_cmd(words):
    res = subprocess.run(words, capture_output=True, text=True)
    return res.stdout.strip()


def pi_status():
    temp = ""
    throttled = ""
    if shutil.which("vcgencmd") != None:
        temp = read_cmd(["vcgencmd", "measure_temp"]).replace("temp=", "").replace("'C", "")
        throttled = read_cmd(["vcgencmd", "get_throttled"]).replace("throttled=", "")
    return temp, throttled


if len(sys.argv) < 5:
    print("use: python benchmark_pi.py clip.mp4 backend model minutes")
else:
    clip = sys.argv[1]
    backend = sys.argv[2]
    model = sys.argv[3]
    minutes = float(sys.argv[4])

    det = Detector(backend, model)
    pre = Preprocessor()
    out = open("benchmark_" + backend + ".csv", "w")
    out.write("seconds,fps,temp,throttled\n")

    times = []
    start = time.time()
    last_print = start
    n = 0
    window = 0

    while time.time() - start < minutes * 60:
        # loop the clip until the time is over
        g = FrameGrabber(clip, False)
        g.start()
        item = g.read()
        while item != None and time.time() - start < minutes * 60:
            t0 = time.time()
            img = pre.crop_resize(item[0])
            pre.blind_check(img, item[1])
            det.scores(img, config.DETECT_CONF)
            times.append((time.time() - t0) * 1000)
            n = n + 1
            window = window + 1
            now = time.time()
            if now - last_print >= 10:
                temp, flags = pi_status()
                fps = window / (now - last_print)
                out.write(str(round(now - start)) + "," + str(round(fps, 1)) + "," + temp + "," + flags + "\n")
                out.flush()
                print(str(round(now - start)) + " s  " + str(round(fps, 1)) + " fps  " + temp + " C  " + flags)
                window = 0
                last_print = now
            item = g.read()
        g.stop()

    out.close()
    times.sort()
    total = 0
    for v in times:
        total = total + v
    print("----------------------")
    print("Frames= " + str(n))
    print("Average fps= " + str(round(n / (time.time() - start), 1)))
    print("Latency mean= " + str(round(total / len(times), 1)) + " ms")
    print("Latency p95= " + str(round(times[int(len(times) * 0.95)], 1)) + " ms")
    print("----------------------")
