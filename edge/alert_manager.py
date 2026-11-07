#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import datetime
import os
import queue
import shutil
import subprocess
import threading
import time

import config


# used on a laptop where there is no gpio
class FakeLed:

    def __init__(self):
        self.value = 0


class LightBar:

    def __init__(self):
        self.fake = False
        try:
            # gpiozero uses lgpio on the pi 5, the old RPi.GPIO does not work on it
            from gpiozero import PWMLED
            self.led = PWMLED(config.LED_PIN)
        except Exception:
            self.fake = True
            self.led = FakeLed()
        self.toggles = []       # time of every switch on, for test T-05
        self.hz = 0
        self.until = 0
        self.last_on = 0
        self.alive = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    # flash at hz for this many seconds, a new call replaces the old pattern
    def flash(self, hz, seconds):
        # software cap, never above 3 flashes each second
        if hz > config.MAX_FLASH_HZ:
            hz = config.MAX_FLASH_HZ
        self.hz = hz
        self.until = time.monotonic() + seconds

    def stop(self):
        self.until = 0

    def bright(self):
        hour = datetime.datetime.now().hour
        if hour >= config.NIGHT_START or hour < config.NIGHT_END:
            return config.LED_NIGHT
        return config.LED_DAY

    def loop(self):
        while self.alive:
            now = time.monotonic()
            if now < self.until and self.hz > 0:
                gap = 1.0 / self.hz
                # also holds when the pattern changes half way
                if now - self.last_on >= gap:
                    self.last_on = now
                    self.toggles.append(now)
                    self.led.value = self.bright()
                    time.sleep(gap / 2)
                    self.led.value = 0
                else:
                    time.sleep(0.005)
            else:
                time.sleep(0.01)


class AlertManager:

    def __init__(self, language, fake_audio=False):
        self.tier = 0
        self.language = language
        self.fake_audio = fake_audio
        self.bar = LightBar()
        self.played = []        # everything that was played, used by the tests
        self.audio_q = queue.Queue()
        self.proc = None
        self.thread = threading.Thread(target=self.audio_loop, daemon=True)
        self.thread.start()

    def audio_loop(self):
        while True:
            path = self.audio_q.get()
            self.played.append(path)
            if self.fake_audio == False:
                self.proc = subprocess.Popen(["aplay", "-q", path])
                self.proc.wait()
            self.audio_q.task_done()

    def add_sound(self, path):
        self.audio_q.put(path)

    # stops what is playing, a higer tier must not wait
    def cut_sound(self):
        while self.audio_q.empty() == False:
            try:
                self.audio_q.get_nowait()
                self.audio_q.task_done()
            except queue.Empty:
                pass
        if self.proc != None and self.proc.poll() == None:
            self.proc.kill()

    def voice_path(self, key):
        return os.path.join(config.VOICE_DIR, self.language, key + ".wav")

    def flash(self, pattern, seconds):
        self.bar.flash(pattern["hz"], seconds)

    def play(self, event):
        c = event["class_name"]
        tier = event["tier"]
        pattern = config.PATTERN[c]

        if tier == 0:
            # muted cue, written to the log and nothing else
            pass
        elif tier == 1:
            # chime and a short pulse
            self.tier = 1
            self.add_sound(config.CLASS_SOUND[c])
            self.flash(pattern, 1.0 / pattern["hz"])
        elif tier == 2:
            self.tier = 2
            self.cut_sound()
            if c in config.CLASS_SOUND:
                self.add_sound(config.CLASS_SOUND[c])
            self.add_sound(self.voice_path(event["voice"]))
            if c == "drinking":
                self.flash(pattern, 1)   # drinking is a single pulse
            else:
                self.flash(pattern, 3)
        elif tier == 3:
            self.tier = 3
            self.cut_sound()
            if event["voice"] != "":
                self.add_sound(self.voice_path(event["voice"]))
            self.add_sound(config.ALARM)
            self.bar.flash(config.MAX_FLASH_HZ, 10)

    def stop_alarm(self):
        if self.tier == 3:
            self.cut_sound()
            self.bar.stop()
        self.tier = 0

    def say(self, key):
        self.add_sound(self.voice_path(key))

    def wait(self):
        self.audio_q.join()

    # checks the speaker side at boot, returns a list of problems
    def self_check(self):
        faults = []
        for path in [config.CHIME, config.BUZZ, config.ALARM]:
            if os.path.exists(path) == False:
                faults.append("missing " + path)
        if self.fake_audio == False and shutil.which("aplay") == None:
            faults.append("aplay not found")
        if self.bar.fake and os.name != "nt":
            faults.append("gpio not available")
        return faults
