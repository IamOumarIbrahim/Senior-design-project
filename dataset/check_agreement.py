#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# checks labels from two annotators, yolo txt files exported from cvat
# agreement is the share of boxes that match at iou 0.5 or more
# a video is relabelled if more than 5% of checked frames disagree
# python check_agreement.py folder_a folder_b
import os
import sys


def to_corners(row):
    x = row[1]
    y = row[2]
    w = row[3]
    h = row[4]
    return [x - w / 2, y - h / 2, x + w / 2, y + h / 2]


def iou(a, b):
    left = a[0]
    if b[0] > left:
        left = b[0]
    top = a[1]
    if b[1] > top:
        top = b[1]
    right = a[2]
    if b[2] < right:
        right = b[2]
    bottom = a[3]
    if b[3] < bottom:
        bottom = b[3]
    if right <= left or bottom <= top:
        return 0.0
    both = (right - left) * (bottom - top)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return both / (area_a + area_b - both)


def read_boxes(path):
    boxes = []
    if os.path.exists(path):
        f = open(path)
        for line in f:
            w = line.split()
            if len(w) == 5:
                boxes.append([int(w[0]), float(w[1]), float(w[2]), float(w[3]), float(w[4])])
        f.close()
    return boxes


# greedy match inside one frame, same class and iou of 0.5
def count_matches(a, b):
    used = []
    matched = 0
    for x in a:
        for j in range(len(b)):
            if j not in used and b[j][0] == x[0]:
                if iou(to_corners(x), to_corners(b[j])) >= 0.5:
                    used.append(j)
                    matched = matched + 1
                    break
    return matched


def compare(folder_a, folder_b):
    names = []
    for n in os.listdir(folder_a):
        if n.endswith(".txt"):
            names.append(n)
    for n in os.listdir(folder_b):
        if n.endswith(".txt") and n not in names:
            names.append(n)

    total = 0
    same = 0
    bad_frames = 0
    for n in names:
        a = read_boxes(os.path.join(folder_a, n))
        b = read_boxes(os.path.join(folder_b, n))
        m = count_matches(a, b)
        bigger = len(a)
        if len(b) > bigger:
            bigger = len(b)
        total = total + bigger
        same = same + m
        if m != len(a) or m != len(b):
            bad_frames = bad_frames + 1
    agreement = 1.0
    if total > 0:
        agreement = same / total
    bad_part = 0.0
    if len(names) > 0:
        bad_part = bad_frames / len(names)
    return agreement, bad_part


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("use: python check_agreement.py folder_a folder_b")
    else:
        agreement, bad_part = compare(sys.argv[1], sys.argv[2])
        print("----------------------")
        print("Agreement= " + str(round(100 * agreement, 1)) + "%")
        print("Frames that disagree= " + str(round(100 * bad_part, 1)) + "%")
        print("----------------------")
        if bad_part > 0.05:
            print("relabel this video")
