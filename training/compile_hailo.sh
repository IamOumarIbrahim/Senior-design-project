#!/bin/bash
#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649
# compiles the model for the ai hat+
# NOT TESTED, needs the hailo dataflow compiler on x86 linux and a hailo account
# hailo8l is the 13 tops hat and hailo8 is the 26 tops one, change it to match ours
# use: ./compile_hailo.sh weights.onnx calib_folder
set -e

ONNX=$1
CALIB=$2
HW=hailo8l

hailomz compile yolov11n \
  --ckpt "$ONNX" \
  --hw-arch "$HW" \
  --calib-path "$CALIB" \
  --classes 4 \
  --performance

echo "copy yolov11n.hef to models/yolo11n_dms.hef and set BACKEND to hailo in edge/config.py"
