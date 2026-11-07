#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import os
import queue
import threading

from flask import Flask, jsonify, request, send_from_directory

import config

WEB_DIR = os.path.join(config.BASE_DIR, "edge", "web")
ACTIONS = ["pin", "new_driver", "pretrip", "calibrate", "skip_calibrate", "end_trip", "dismiss"]


class TabletUI:

    def __init__(self, assistant):
        self.assistant = assistant
        self.lock = threading.Lock()
        self.actions = queue.Queue()
        self.data = {
            "screen": "pin",
            "status": "Attentive",
            "tier": 0,
            "message": "",
            "message_ar": "",
            "driver": "",
            "drive_min": 0,
            "alerts": 0,
            "camera_pct": 100,
            "recent": [],
            "stop": None,
            "error": "",
            "calib": {"seconds": 0, "frames": 0, "seen": 0, "total": config.CALIB_S},
            "advice": "",
            "break_min": config.BREAK_MINUTES,
        }
        self.app = Flask("tablet")
        self.routes()

    def routes(self):
        app = self.app

        def home():
            return send_from_directory(WEB_DIR, "index.html")

        def phone():
            return send_from_directory(WEB_DIR, "phone.html")

        def icons():
            return send_from_directory(WEB_DIR, "icons.js")

        def state():
            self.lock.acquire()
            answer = jsonify(self.data)
            self.lock.release()
            return answer

        def action():
            body = request.get_json()
            ok = False
            if body != None and "type" in body:
                if body["type"] in ACTIONS:
                    self.actions.put(body)
                    ok = True
            return jsonify({"ok": ok})

        def location():
            body = request.get_json()
            self.assistant.set_location(float(body["lat"]), float(body["lon"]))
            return jsonify({"ok": True})

        app.add_url_rule("/", "home", home)
        app.add_url_rule("/phone", "phone", phone)
        app.add_url_rule("/icons.js", "icons", icons)
        app.add_url_rule("/api/state", "state", state)
        app.add_url_rule("/api/action", "action", action, methods=["POST"])
        app.add_url_rule("/api/location", "location", location, methods=["POST"])

    def start(self):
        thread = threading.Thread(target=self.serve, daemon=True)
        thread.start()

    def serve(self):
        self.app.run(host=config.DISPLAY_HOST, port=config.DISPLAY_PORT, threaded=True)

    def set(self, key, value):
        self.lock.acquire()
        self.data[key] = value
        self.lock.release()

    def show(self, screen):
        self.set("screen", screen)

    def pin_login(self):
        self.show("pin")

    # called by the main loop with the newest status
    def show_status(self, word, tier, message, message_ar):
        self.lock.acquire()
        self.data["status"] = word
        self.data["tier"] = tier
        if message != "":
            self.data["message"] = message
            self.data["message_ar"] = message_ar
        self.lock.release()

    def add_recent(self, name, text, clock):
        self.lock.acquire()
        self.data["recent"].insert(0, {"name": name, "text": text, "clock": clock})
        if len(self.data["recent"]) > 3:
            self.data["recent"].pop()
        self.data["alerts"] = self.data["alerts"] + 1
        self.lock.release()

    # waits for the driver to press somthing
    def wait_action(self):
        return self.actions.get()

    def poll_action(self):
        try:
            return self.actions.get_nowait()
        except queue.Empty:
            return None
