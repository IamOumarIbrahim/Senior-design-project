#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import os
import queue
import threading
import time

import cv2

import config


class FrameGrabber:

    # source is the camera number or a video file
    # realtime True drops old frames like the real camera does
    # realtime False keeps every frame so a replay gives the same result each time
    def __init__(self, source, realtime):
        self.source = source
        self.realtime = realtime
        self.is_file = isinstance(source, str)
        if self.is_file == False and os.name != "nt":
            self.cap = cv2.VideoCapture(source, cv2.CAP_V4L2)
        else:
            self.cap = cv2.VideoCapture(source)
        if self.is_file == False:
            # mjpg is needed or the c922 wont give 1080p at 30
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc("M", "J", "P", "G"))
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_W)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_H)
            self.cap.set(cv2.CAP_PROP_FPS, config.CAM_FPS)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0:
            self.fps = config.CAM_FPS
        self.q = queue.Queue(maxsize=1)
        self.running = False
        self.thread = None

    def opened(self):
        return self.cap.isOpened()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def loop(self):
        i = 0
        t0 = time.monotonic()
        while self.running:
            ok, frame = self.cap.read()
            if ok == False:
                self.running = False
                break
            wall = time.time()
            if self.is_file:
                t = i / self.fps
                i = i + 1
            else:
                t = time.monotonic() - t0
            item = (frame, t, wall)

            if self.realtime:
                if self.is_file:
                    # dont read the file faster than the camera would
                    wait = t - (time.monotonic() - t0)
                    if wait > 0:
                        time.sleep(wait)
                # keep only the newset frame so nothing builds a backlog
                if self.q.full():
                    try:
                        self.q.get_nowait()
                    except queue.Empty:
                        pass
                self.q.put(item)
            else:
                self.q.put(item)
        self.q.put(None)
        self.cap.release()

    # waits for the next frame, None means the source ended
    def read(self):
        return self.q.get()
