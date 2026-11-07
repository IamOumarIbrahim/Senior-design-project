#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import math
import os
import queue
import threading

import cv2

import config

# the 6 points of each eye in the mediapipe face mesh, p1 to p6
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
LEFT_EYE = [362, 385, 387, 263, 373, 380]


def dist(a, b):
    return math.sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]))


# EAR = (|p2-p6| + |p3-p5|) / (2 |p1-p4|)
def ear_of(p):
    top = dist(p[1], p[5]) + dist(p[2], p[4])
    botom = 2 * dist(p[0], p[3])
    if botom == 0:
        return None
    return top / botom


# head pitch in degrees from the face matrix, plus means head down
def pitch_of(m):
    size = math.sqrt(m[0][0] * m[0][0] + m[1][0] * m[1][0] + m[2][0] * m[2][0])
    value = -m[1][2] / size
    if value > 1:
        value = 1
    if value < -1:
        value = -1
    return math.degrees(math.asin(value))


class EyeModule:

    def __init__(self, ear_open, use_model=True, pitch_rest=None):
        self.ear_open = ear_open
        self.pitch_rest = pitch_rest
        self.pitch_seen = []    # first seconds, only used if there is no saved rest pitch
        self.pitch_from = None
        self.head_down = False
        if self.ear_open == None:
            self.ear_open = config.EAR_DEFAULT
        self.closed_s = 0.0
        self.last_t = None
        self.history = []       # time, length, closed
        self.model = None
        self.q = queue.Queue(maxsize=1)
        self.lock = threading.Lock()
        if use_model:
            self.load_model()

    def load_model(self):
        if os.path.exists(config.EYE_MODEL):
            try:
                import mediapipe as mp
                from mediapipe.tasks import python as mp_python
                from mediapipe.tasks.python import vision
                base = mp_python.BaseOptions(model_asset_path=config.EYE_MODEL)
                options = vision.FaceLandmarkerOptions(base_options=base, num_faces=1,
                                                       output_face_blendshapes=True,
                                                       output_facial_transformation_matrixes=True)
                self.model = vision.FaceLandmarker.create_from_options(options)
                self.mp = mp
            except ImportError:
                print("mediapipe is not installed, eye module is off")

    def available(self):
        return self.model != None

    # EAR, blink score and head pitch of the frame, None if no eyes were found
    def measure(self, f):
        if self.model == None:
            return None
        h = f.shape[0]
        w = f.shape[1]
        rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb)
        res = self.model.detect(image)
        if len(res.face_landmarks) == 0:
            return None
        marks = res.face_landmarks[0]
        total = 0
        for eye in [RIGHT_EYE, LEFT_EYE]:
            pts = []
            for i in eye:
                pts.append((marks[i].x * w, marks[i].y * h))
            value = ear_of(pts)
            if value == None:
                return None
            total = total + value

        blink = 0
        for b in res.face_blendshapes[0]:
            if b.category_name == "eyeBlinkLeft" or b.category_name == "eyeBlinkRight":
                blink = blink + b.score
        pitch = pitch_of(res.facial_transformation_matrixes[0])
        return {"ear": total / 2, "blink": blink / 2, "pitch": pitch}

    def ear(self, f):
        m = self.measure(f)
        if m == None:
            return None
        return m["ear"]

    # no saved rest pitch, so use the middle value of the first seconds
    def learn_pitch(self, pitch, t):
        if self.pitch_from == None:
            self.pitch_from = t
        self.pitch_seen.append(pitch)
        if t - self.pitch_from >= config.CALIB_S:
            self.pitch_seen.sort()
            self.pitch_rest = self.pitch_seen[len(self.pitch_seen) // 2]

    def feed(self, m, t):
        if m == None:
            self.update(None, t)
        else:
            self.update(m["ear"], t, m["blink"], m["pitch"])

    # missing eyes are skipped and never counted as open
    # blink and pitch only matter when they come from the model
    def update(self, value, t, blink=1.0, pitch=None):
        dt = 0
        if self.last_t != None:
            dt = t - self.last_t
        self.last_t = t

        self.lock.acquire()
        if value != None:
            closed = value < config.EAR_RATIO * self.ear_open and blink > config.BLINK_MIN
            self.head_down = False
            if pitch != None:
                if self.pitch_rest == None:
                    self.learn_pitch(pitch, t)
                elif pitch - self.pitch_rest > config.HEAD_DOWN_DEG:
                    self.head_down = True
            if closed:
                self.closed_s = self.closed_s + dt
            else:
                self.closed_s = 0.0
            # a look at the lap should not push up the drowsiness number
            if self.head_down == False:
                self.history.append((t, dt, closed))
        while len(self.history) > 0 and t - self.history[0][0] > config.PERCLOS_WINDOW_S:
            self.history.pop(0)
        self.lock.release()

    # part of the last 60 s with the eyes closed
    # None until we have enough of the window to trust it
    def perclos(self, t):
        total = 0
        closed = 0
        for h in self.history:
            total = total + h[1]
            if h[2]:
                closed = closed + h[1]
        if total < config.PERCLOS_WINDOW_S / 2:
            return None
        if len(self.history) == 0 or t - self.history[0][0] < config.PERCLOS_WINDOW_S * 0.9:
            return None
        return closed / total

    def state(self, t):
        self.lock.acquire()
        s = {"closed_s": self.closed_s, "perclos": self.perclos(t), "head_down": self.head_down}
        self.lock.release()
        return s

    def start(self):
        thread = threading.Thread(target=self.loop, daemon=True)
        thread.start()

    # gives the newest crop to the eye thread, old ones are thrown away
    def submit(self, img, t):
        if self.q.full():
            try:
                self.q.get_nowait()
            except queue.Empty:
                pass
        self.q.put((img, t))

    def loop(self):
        while True:
            item = self.q.get()
            self.feed(self.measure(item[0]), item[1])
