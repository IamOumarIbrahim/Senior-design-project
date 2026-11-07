#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import time

import config


class Calibrator:

    def __init__(self):
        self.rows = []
        self.ears = []
        self.pitches = []

    # one frame of the baseline, x is the score of each class at 0.05 conf
    def add(self, x, ear, pitch=None):
        self.rows.append(x)
        if ear != None:
            self.ears.append(ear)
        if pitch != None:
            self.pitches.append(pitch)

    def percentile(self, values, p):
        values = list(values)
        values.sort()
        pos = (len(values) - 1) * p / 100.0
        low = int(pos)
        high = low + 1
        if high >= len(values):
            return values[low]
        part = pos - low
        return values[low] + (values[high] - values[low]) * part

    # P99 + 0.05, kept between the default and 0.85
    # more than 10% of frames above the default means the driver moved
    # so the defaults stay and the baseline has to be done again
    def finish(self, defaults):
        total = len(self.rows)
        result = {}
        result["ok"] = True
        result["cutoffs"] = {}
        for c in defaults:
            result["cutoffs"][c] = defaults[c]
        result["ear_open"] = None
        result["pitch_rest"] = None

        if total == 0:
            result["ok"] = False
        else:
            for c in defaults:
                above = 0
                for row in self.rows:
                    if row[c] > defaults[c]:
                        above = above + 1
                if above / total > config.CALIB_MANY:
                    result["ok"] = False

        if result["ok"]:
            for c in defaults:
                values = []
                for row in self.rows:
                    values.append(row[c])
                cut = self.percentile(values, 99) + config.CALIB_GAP
                if cut < defaults[c]:
                    cut = defaults[c]
                if cut > config.CUTOFF_TOP:
                    cut = config.CUTOFF_TOP
                result["cutoffs"][c] = cut

        # this one is saved even if the cutoffs were not
        if len(self.ears) > 0:
            result["ear_open"] = self.percentile(self.ears, 50)
        if len(self.pitches) > 0:
            result["pitch_rest"] = self.percentile(self.pitches, 50)
        return result

    # the real 20 s baselin, show() updates the display
    def run(self, grabber, pre, det, eye, show):
        self.rows = []
        self.ears = []
        self.pitches = []
        start = None
        seen = 0
        going = True
        while going:
            item = grabber.read()
            if item == None:
                going = False
            else:
                if start == None:
                    start = item[1]
                img = pre.crop_resize(item[0])
                x = det.scores(img, config.CALIB_CONF)
                ear = None
                pitch = None
                if eye != None:
                    m = eye.measure(img)
                    if m != None:
                        ear = m["ear"]
                        pitch = m["pitch"]
                self.add(x, ear, pitch)
                for c in x:
                    if x[c] > 0:
                        seen = seen + 1
                done_s = item[1] - start
                show(done_s, len(self.rows), seen)
                if done_s >= config.CALIB_S:
                    going = False
        return self.finish(config.CUTOFF)
