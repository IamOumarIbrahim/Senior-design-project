#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# leave one subject out, figure 5.4
# every fold has one test subjcet, one val subject and trains on the other two
# everything of a subject stays together, baseline and hard negatives too
# python make_folds.py frames_folder output_folder
import os
import sys

SUBJECTS = ["S01", "S02", "S03", "S04"]
FOLDS = [["S01", "S02"], ["S02", "S03"], ["S03", "S04"], ["S04", "S01"]]   # test, val
NAMES = ["yawning", "hand_over_mouth", "drinking", "phone_use"]


def list_images(root, subject):
    found = []
    top = os.path.join(root, subject)
    if os.path.exists(top):
        for folder, dirs, files in os.walk(top):
            for f in files:
                if f.endswith(".jpg"):
                    found.append(os.path.abspath(os.path.join(folder, f)))
    found.sort()
    return found


def write_list(path, lines):
    f = open(path, "w")
    for line in lines:
        f.write(line + "\n")
    f.close()


def make_fold(root, out, number):
    test_s = FOLDS[number][0]
    val_s = FOLDS[number][1]
    train_s = []
    for s in SUBJECTS:
        if s != test_s and s != val_s:
            train_s.append(s)

    train = []
    for s in train_s:
        train = train + list_images(root, s)
    val = list_images(root, val_s)
    test = list_images(root, test_s)

    folder = os.path.join(out, "fold" + str(number + 1))
    if os.path.exists(folder) == False:
        os.makedirs(folder)
    write_list(os.path.join(folder, "train.txt"), train)
    write_list(os.path.join(folder, "val.txt"), val)
    write_list(os.path.join(folder, "test.txt"), test)

    f = open(os.path.join(folder, "data.yaml"), "w")
    f.write("path: " + os.path.abspath(folder).replace("\\", "/") + "\n")
    f.write("train: train.txt\nval: val.txt\ntest: test.txt\nnames:\n")
    for i in range(len(NAMES)):
        f.write("  " + str(i) + ": " + NAMES[i] + "\n")
    f.close()
    return {"train": train_s, "val": val_s, "test": test_s}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("use: python make_folds.py frames_folder output_folder")
    else:
        for i in range(4):
            print(make_fold(sys.argv[1], sys.argv[2], i))
