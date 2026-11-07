#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import cv2

import config
import native_blind


class Preprocessor:

    def __init__(self):
        self.crop = [config.CROP_X, config.CROP_Y, config.CROP_SIZE, config.CROP_SIZE]
        self.bad_since = None

    # cuts the fixed window out of the frame and makes it 640x640
    def crop_resize(self, f):
        h = f.shape[0]
        w = f.shape[1]
        x = self.crop[0]
        y = self.crop[1]
        size = self.crop[2]

        # smaller video like a replay, then use the midle
        if size > w or size > h:
            size = w
            if h < w:
                size = h
            x = (w - size) // 2
            y = (h - size) // 2
        if x + size > w:
            x = w - size
        if y + size > h:
            y = h - size

        part = f[y:y + size, x:x + size]
        if size != config.CROP_SIZE:
            part = cv2.resize(part, (config.CROP_SIZE, config.CROP_SIZE))
        return part

    def numbers_cv(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return gray.mean(), cv2.Laplacian(gray, cv2.CV_64F).var()

    # brightness and sharpness, the c++ one gives the same numbers about 9 times faster
    # if it was not built then opencv does it
    def numbers(self, img):
        result = None
        if native_blind.available():
            result = native_blind.numbers(img)
        if result == None:
            result = self.numbers_cv(img)
        return result

    # is this one frame too dark too bright or too blurry
    def frame_bad(self, img):
        bright, sharp = self.numbers(img)
        bad = False
        if bright < config.BRIGHT_LOW:
            bad = True
        if bright > config.BRIGHT_HIGH:
            bad = True
        if sharp < config.SHARP_LOW:
            bad = True
        return bad

    # True when the view has been unclear for 3 s
    def blind_check(self, img, t):
        blocked = False
        if self.frame_bad(img):
            if self.bad_since == None:
                self.bad_since = t
            if t - self.bad_since >= config.BLOCKED_S:
                blocked = True
        else:
            self.bad_since = None
        return blocked
