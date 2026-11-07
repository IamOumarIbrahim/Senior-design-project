#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# per class precision recall f1 and map, and the confusion matrix
# the test split is only used one time at the end
# python evaluate.py weights.pt data.yaml test
import sys

from ultralytics import YOLO

if len(sys.argv) < 4:
    print("use: python evaluate.py weights.pt data.yaml split")
else:
    model = YOLO(sys.argv[1])
    res = model.val(data=sys.argv[2], split=sys.argv[3], imgsz=640, plots=True, verbose=False)

    print("class                P      R      F1     AP50   AP50-95")
    for i in range(len(res.box.ap_class_index)):
        c = int(res.box.ap_class_index[i])
        name = res.names[c]
        p = res.box.p[i]
        r = res.box.r[i]
        f1 = 0
        if p + r > 0:
            f1 = 2 * p * r / (p + r)
        print(name.ljust(20) + str(round(p, 3)).ljust(7) + str(round(r, 3)).ljust(7) + str(round(f1, 3)).ljust(7)
              + str(round(res.box.ap50[i], 3)).ljust(7) + str(round(res.box.ap[i], 3)))
    print("----------------------")
    print("mAP50= " + str(round(res.box.map50, 3)))
    print("mAP50-95= " + str(round(res.box.map, 3)))
    print("----------------------")
