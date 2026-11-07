#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import math
import os

import cv2

import config


class CropTracker:

    def __init__(self, frame_w, frame_h):
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.cx = config.CROP_X + config.CROP_SIZE / 2
        self.cy = config.CROP_Y + config.CROP_SIZE / 2
        self.last_t = None
        self.face = None
        if os.path.exists(config.FACE_MODEL):
            self.face = cv2.FaceDetectorYN.create(config.FACE_MODEL, "", (config.TRACK_W, config.TRACK_H), 0.6, 0.3, 50)

    def available(self):
        return self.face != None

    # runs about once a second on a small copy of the frame
    # returns the crop as x, y, size
    def update(self, f, t):
        if self.face != None:
            if self.last_t == None or t - self.last_t >= config.TRACK_EVERY_S:
                dt = config.TRACK_EVERY_S
                if self.last_t != None:
                    dt = t - self.last_t
                self.last_t = t
                small = cv2.resize(f, (config.TRACK_W, config.TRACK_H))
                res = self.face.detect(small)
                faces = res[1]
                if faces is not None and len(faces) > 0:
                    # bigest face is the driver
                    best = 0
                    for i in range(len(faces)):
                        if faces[i][2] * faces[i][3] > faces[best][2] * faces[best][3]:
                            best = i
                    sx = self.frame_w / config.TRACK_W
                    sy = self.frame_h / config.TRACK_H
                    new_x = (faces[best][0] + faces[best][2] / 2) * sx
                    new_y = (faces[best][1] + faces[best][3] / 2) * sy
                    # the crop follows the face through its own ema
                    alpha = 1 - math.exp(-dt / config.TRACK_TAU)
                    self.cx = alpha * new_x + (1 - alpha) * self.cx
                    self.cy = alpha * new_y + (1 - alpha) * self.cy
        return self.rect()

    def rect(self):
        size = config.CROP_SIZE
        x = int(self.cx - size / 2)
        y = int(self.cy - size / 2)
        # keep it inside the frame
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x + size > self.frame_w:
            x = self.frame_w - size
        if y + size > self.frame_h:
            y = self.frame_h - size
        return [x, y, size, size]
