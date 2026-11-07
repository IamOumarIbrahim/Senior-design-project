#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import cv2
import numpy as np

import config


class Detector:

    def __init__(self, backend, path):
        self.backend = backend
        self.names = config.CLASSES
        if backend == "hailo":
            self.setup_hailo(path)
        else:
            # pt onnx and ncnn all load the same way, this is the cpu fallback
            from ultralytics import YOLO
            self.model = YOLO(path, task="detect")

    # NOT TESTED, we dont have the ai hat yet
    # uses the hailort python api and a hef with nms on the chip
    def setup_hailo(self, path):
        from hailo_platform import FormatType, VDevice
        params = VDevice.create_params()
        self.vdevice = VDevice(params)
        self.hmodel = self.vdevice.create_infer_model(path)
        self.hmodel.input().set_format_type(FormatType.UINT8)
        self.hmodel.output().set_format_type(FormatType.FLOAT32)
        self.hconf = self.hmodel.configure()
        self.bind = self.hconf.create_bindings()
        self.out = np.empty(self.hmodel.output().shape, dtype=np.float32)
        self.bind.output().set_buffer(self.out)

    def infer_hailo(self, img, conf):
        # the model was compiled for rgb and the camera gives bgr
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.bind.input().set_buffer(rgb)
        self.hconf.run([self.bind], 1000)
        result = self.bind.output().get_buffer()
        boxes = []
        # one list for each class, each row is y1 x1 y2 x2 score from 0 to 1
        for c in range(len(result)):
            for row in result[c]:
                score = float(row[4])
                if score >= conf:
                    size = config.CROP_SIZE
                    boxes.append([c, score, row[1] * size, row[0] * size, row[3] * size, row[2] * size])
        return boxes

    # returns rows of class, score, x1, y1, x2, y2
    def infer(self, img, conf):
        if self.backend == "hailo":
            return self.infer_hailo(img, conf)
        res = self.model.predict(img, imgsz=config.CROP_SIZE, conf=conf, device=config.DEVICE, verbose=False)
        boxes = []
        b = res[0].boxes
        for i in range(len(b)):
            c = int(b.cls[i])
            score = float(b.conf[i])
            xy = b.xyxy[i]
            boxes.append([c, score, float(xy[0]), float(xy[1]), float(xy[2]), float(xy[3])])
        return boxes

    # higest score for each class, this is what the filter gets
    def scores(self, img, conf):
        x = {}
        for c in self.names:
            x[c] = 0.0
        boxes = self.infer(img, conf)
        for b in boxes:
            name = self.names[b[0]]
            if b[1] > x[name]:
                x[name] = b[1]
        return x
