#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# runs the first model at low confidence on train and val subjects
# and collects the frames it wrongly flags, these show what fools it
# the test subject is never used here
# python mine_hard_negatives.py weights.pt list.txt out_folder
# list.txt is the train.txt or val.txt of a fold
import os
import shutil
import sys

from ultralytics import YOLO

LOW_CONF = 0.10
NAMES = ["yawning", "hand_over_mouth", "drinking", "phone_use"]


# labels are next to the image, folders images and labels like yolo wants
def label_of(path):
    return path.replace("images", "labels").replace(".jpg", ".txt")


def is_empty(label):
    if os.path.exists(label) == False:
        return True
    return os.path.getsize(label) == 0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("use: python mine_hard_negatives.py weights.pt list.txt out_folder")
    else:
        model = YOLO(sys.argv[1])
        out = sys.argv[3]
        if os.path.exists(out) == False:
            os.makedirs(out)

        f = open(sys.argv[2])
        images = []
        for line in f:
            if line.strip() != "":
                images.append(line.strip())
        f.close()

        counts = {}
        for n in NAMES:
            counts[n] = 0
        report = open(os.path.join(out, "hard_negatives.csv"), "w")
        report.write("image,class,score\n")

        total = 0
        for path in images:
            # only frames with no cue can be a false alarm
            if is_empty(label_of(path)):
                res = model.predict(path, imgsz=640, conf=LOW_CONF, verbose=False)
                b = res[0].boxes
                if len(b) > 0:
                    best = 0
                    for i in range(len(b)):
                        if float(b.conf[i]) > float(b.conf[best]):
                            best = i
                    name = NAMES[int(b.cls[best])]
                    counts[name] = counts[name] + 1
                    total = total + 1
                    report.write(path + "," + name + "," + str(round(float(b.conf[best]), 3)) + "\n")
                    shutil.copy(path, os.path.join(out, os.path.basename(path)))
        report.close()

        print("----------------------")
        print("Hard negatives= " + str(total))
        for n in NAMES:
            print(n + "= " + str(counts[n]))
        print("----------------------")
