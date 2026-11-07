#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# makes a replay video from the held out dmd rgb frames
# the frames were taken at 1 fps so each one is repeated 10 times to get a
# 10 fps video with the real timing of the cues
# the video goes in data/ and is not uploaded, dmd has its own licence
# use: python make_replay.py subject_05 video_01 video_02
import os
import sys

import cv2

from helper import REPO

ROOT = os.environ.get("DMS_RGB_DIR", r"C:\Dev\repos\Public repos\ieee-aiot\data\processed\RGB")
REPEAT = 10
NAMES = ["yawning", "hand_over_mouth", "drinking", "phone_use"]

subject = "subject_05"
videos = ["video_01", "video_02"]
if len(sys.argv) > 2:
    subject = sys.argv[1]
    videos = sys.argv[2:]

out_path = os.path.join(REPO, "data", "replay_" + subject + ".mp4")
truth_path = os.path.join(REPO, "data", "replay_" + subject + ".csv")

fourcc = cv2.VideoWriter_fourcc("m", "p", "4", "v")
out = cv2.VideoWriter(out_path, fourcc, REPEAT, (640, 640))
truth = open(truth_path, "w")
truth.write("second,class\n")

sec = 0
for v in videos:
    folder = os.path.join(ROOT, "images", subject, v)
    names = os.listdir(folder)
    names.sort()
    for n in names:
        frame = cv2.imread(os.path.join(folder, n))
        for i in range(REPEAT):
            out.write(frame)

        # what the label says for this second
        label = os.path.join(ROOT, "labels", subject, v, n.replace(".jpg", ".txt"))
        cls = ""
        if os.path.exists(label):
            f = open(label)
            words = f.read().split()
            f.close()
            if len(words) > 0:
                cls = NAMES[int(words[0])]
        truth.write(str(sec) + "," + cls + "\n")
        sec = sec + 1

out.release()
truth.close()
print("wrote " + out_path + " with " + str(sec) + " seconds")
