#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "edge"))
sys.path.insert(0, os.path.join(REPO, "server"))

bad = 0
good = 0


def check(name, ok):
    global bad, good
    if ok:
        good = good + 1
        print("PASS  " + name)
    else:
        bad = bad + 1
        print("FAIL  " + name)


def done():
    print("----------------------")
    print("Passed= " + str(good) + "  Failed= " + str(bad))
    print("----------------------")
    if bad > 0:
        sys.exit(1)
