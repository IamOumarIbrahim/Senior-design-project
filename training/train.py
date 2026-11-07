#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# fine tunes yolo11n from the coco weights, settings are Table 4.14
# stage 1 is the 14 dmd drivers, stage 2 is one fold of our own subjects
# python train.py data.yaml run_name [start_weights]
import sys

from ultralytics import YOLO

if len(sys.argv) < 3:
    print("use: python train.py data.yaml run_name [start_weights]")
else:
    start = "yolo11n.pt"
    if len(sys.argv) > 3:
        start = sys.argv[3]

    model = YOLO(start)
    model.train(
        data=sys.argv[1],
        name=sys.argv[2],
        imgsz=640,
        epochs=150,
        patience=30,
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.4,
        degrees=10,
        fliplr=0.5,
        mosaic=1.0,
        project="runs",
    )
