#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# takes frames at 5 fps for labelling in cvat
# python extract_frames.py recordings frames
import os
import sys

import cv2

KEEP_FPS = 5

if len(sys.argv) < 3:
    print("use: python extract_frames.py recordings_folder output_folder")
else:
    src = sys.argv[1]
    dst = sys.argv[2]
    for subject in os.listdir(src):
        folder = os.path.join(src, subject)
        if os.path.isdir(folder):
            for name in os.listdir(folder):
                if name.endswith(".mp4"):
                    out = os.path.join(dst, subject, name.replace(".mp4", ""))
                    if os.path.exists(out) == False:
                        os.makedirs(out)
                    cap = cv2.VideoCapture(os.path.join(folder, name))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    step = fps / KEEP_FPS
                    i = 0
                    saved = 0
                    next_frame = 0.0
                    ok, frame = cap.read()
                    while ok:
                        if i >= next_frame:
                            cv2.imwrite(os.path.join(out, "frame_" + str(saved).zfill(6) + ".jpg"), frame)
                            saved = saved + 1
                            next_frame = next_frame + step
                        i = i + 1
                        ok, frame = cap.read()
                    cap.release()
                    print(name + " " + str(saved) + " frames")
