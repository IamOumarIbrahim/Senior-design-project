#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# exports for the cpu fallback, the hailo one is compile_hailo.sh
# python export_models.py weights.pt data.yaml
import sys

from ultralytics import YOLO

if len(sys.argv) < 2:
    print("use: python export_models.py weights.pt [data.yaml]")
else:
    w = sys.argv[1]
    data = None
    if len(sys.argv) > 2:
        data = sys.argv[2]

    print(YOLO(w).export(format="onnx", imgsz=640, opset=12))
    print(YOLO(w).export(format="onnx", imgsz=640, half=True, opset=12, device="cpu"))
    print(YOLO(w).export(format="ncnn", imgsz=640))
    if data != None:
        # int8 needs calibration frames from the train split
        print(YOLO(w).export(format="ncnn", imgsz=640, int8=True, data=data))
