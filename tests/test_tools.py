#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# FS-10 FS-12 tools with made up folders
import os
import shutil
import sys
import tempfile

from helper import REPO, check, done

sys.path.insert(0, os.path.join(REPO, "dataset"))

import check_agreement
import make_folds

folder = tempfile.mkdtemp()

# Make fake frames for 4 subjects
root = os.path.join(folder, "frames")
for s in make_folds.SUBJECTS:
    p = os.path.join(root, s, "s1_afternoon")
    os.makedirs(p)
    for i in range(3):
        f = open(os.path.join(p, s + "_" + str(i) + ".jpg"), "w")
        f.close()

out = os.path.join(folder, "folds")
tests = []
for i in range(4):
    info = make_folds.make_fold(root, out, i)
    tests.append(info["test"])

    # read the lists back and check no subject is in two splits
    seen = {}
    for split in ["train", "val", "test"]:
        path = os.path.join(out, "fold" + str(i + 1), split + ".txt")
        f = open(path)
        for line in f:
            for s in make_folds.SUBJECTS:
                if os.sep + s + os.sep in line:
                    if s not in seen:
                        seen[s] = []
                    if split not in seen[s]:
                        seen[s].append(split)
        f.close()
    clean = True
    for s in seen:
        if len(seen[s]) != 1:
            clean = False
    check("fold " + str(i + 1) + " has no subject in two splits", clean and len(seen) == 4)
    check("fold " + str(i + 1) + " trains on two subjects", len(info["train"]) == 2)

tests.sort()
check("every subject is tested exactly once", tests == make_folds.SUBJECTS)

# Annotator agreement
a = os.path.join(folder, "a")
b = os.path.join(folder, "b")
os.makedirs(a)
os.makedirs(b)


def save(path, text):
    f = open(path, "w")
    f.write(text)
    f.close()


save(os.path.join(a, "1.txt"), "0 0.5 0.5 0.2 0.2\n")
save(os.path.join(b, "1.txt"), "0 0.51 0.5 0.2 0.2\n")     # nearly the same box
save(os.path.join(a, "2.txt"), "1 0.5 0.5 0.2 0.2\n")
save(os.path.join(b, "2.txt"), "2 0.5 0.5 0.2 0.2\n")      # other class
agreement, bad = check_agreement.compare(a, b)
check("agreement is 50% here", agreement == 0.5)
check("half of the frames disagree", bad == 0.5)

check("same box has iou 1", check_agreement.iou([0, 0, 1, 1], [0, 0, 1, 1]) == 1)
check("far boxes have iou 0", check_agreement.iou([0, 0, 1, 1], [2, 2, 3, 3]) == 0)

shutil.rmtree(folder, ignore_errors=True)
done()
