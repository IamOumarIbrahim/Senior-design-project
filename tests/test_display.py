#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# FS-24 FS-25 FS-26 and the login and calibration flow, with no camera
import json
import os
import shutil
import tempfile
import threading

from helper import check, done

import config
import main
import trip_assistant
from event_logger import EventLogger
from tablet_ui import TabletUI
from trip_assistant import TripAssistant, closest, pretrip_advice, read_places


class FakeGrabber:

    def __init__(self):
        self.t = 0.0

    def read(self):
        self.t = self.t + 1 / 30.0
        return (None, self.t, 0)


class FakePre:

    def crop_resize(self, f):
        return f


# detector that sees nothing, or sees a yawn all the time
class FakeDet:

    def __init__(self, noisy):
        self.noisy = noisy

    def scores(self, img, conf):
        x = {}
        for c in config.CLASSES:
            x[c] = 0.01
        if self.noisy[0]:
            x["yawning"] = 0.9
        return x


folder = tempfile.mkdtemp()
log = EventLogger(os.path.join(folder, "ui.db"))
helper = TripAssistant()
ui = TabletUI(helper)
web = ui.app.test_client()


def post(body):
    res = web.post("/api/action", data=json.dumps(body), content_type="application/json")
    return res.get_json()


def wait_screen(name):
    for i in range(500):
        if ui.data["screen"] == name:
            return True
        threading.Event().wait(0.01)
    return False


check("page loads", web.get("/").status_code == 200)
check("icons load", web.get("/icons.js").status_code == 200)
check("phone page loads", web.get("/phone").status_code == 200)
check("unknown action is refused", post({"type": "drop_table"})["ok"] == False)
check("state has a screen", web.get("/api/state").get_json()["screen"] == "pin")

# New driver goes through pin, name, pre trip then a noisy baseline then a good one
noisy = [True]
out = {}


def do_login():
    a, b = main.login(log, ui, FakeGrabber(), FakePre(), FakeDet(noisy), None)
    out["driver"] = a
    out["saved"] = b


thread = threading.Thread(target=do_login, daemon=True)
thread.start()

post({"type": "pin", "pin": "4321"})
check("unknown pin asks for a name", wait_screen("new_driver"))
post({"type": "new_driver", "name": "Sara", "language": "ar"})
check("then the pre trip check", wait_screen("pretrip"))
post({"type": "pretrip", "hours": 4, "tired": 2})
check("then calibration", wait_screen("calibrate"))
post({"type": "calibrate"})
for i in range(500):
    if ui.data["error"] != "":
        break
    threading.Event().wait(0.01)
check("noisy baseline asks to redo", "Too many" in ui.data["error"])
check("short sleep gives rest advice", "Rest" in ui.data["advice"])
noisy[0] = False
post({"type": "calibrate"})
thread.join(10)
check("good baseline finishes", "saved" in out)
check("600 frames in 20 s at 30 fps", ui.data["calib"]["frames"] >= 600 and ui.data["calib"]["frames"] <= 602)
check("arabic choice is kept", out["driver"]["language"] == "ar")
check("calibration is in the database", log.load_calibration(out["driver"]["driver_id"]) != None)

# Same pin again is a known driver and needs no calibration
out2 = {}


def do_login2():
    a, b = main.login(log, ui, FakeGrabber(), FakePre(), FakeDet(noisy), None)
    out2["driver"] = a
    out2["saved"] = b


thread = threading.Thread(target=do_login2, daemon=True)
thread.start()
post({"type": "pin", "pin": "4321"})
wait_screen("pretrip")
post({"type": "pretrip", "hours": 8, "tired": 1})
thread.join(5)
check("known driver loads saved cutoffs", "saved" in out2 and out2["driver"]["display_name"] == "Sara")

# Pre trip
check("tired answer gives rest advice", "Rest" in pretrip_advice(7, 5))
check("good answer is fine", "good to go" in pretrip_advice(8, 1))

# Status
ui.show_status("Drowsy", 2, "Yawning detected 3 times in 5 minutes.", "x")
s = web.get("/api/state").get_json()
check("status reaches the page", s["status"] == "Drowsy" and s["tier"] == 2)
for i in range(5):
    ui.add_recent("yawning", "tier 1", "10:0" + str(i))
s = web.get("/api/state").get_json()
check("recent list keeps 3 newest", len(s["recent"]) == 3 and s["recent"][0]["clock"] == "10:04")

# Rest stop logic with no network
data = {"elements": [
    {"type": "node", "lat": 25.30, "lon": 55.48, "tags": {"amenity": "fuel", "name": "Near Fuel"}},
    {"type": "way", "center": {"lat": 25.40, "lon": 55.60}, "tags": {"highway": "rest_area"}},
]}
places = read_places(data)
check("reads nodes and ways", len(places) == 2)
best = closest(places, 25.2854, 55.48)
check("picks the nearest place", best["name"] == "Near Fuel" and best["km"] > 0)
check("empty list gives none", closest([], 25, 55) == None)

h = TripAssistant()
h.set_location(25.3, 55.4)
called = []


def fake_nearest(lat, lon):
    called.append((lat, lon))
    return {"name": "X", "kind": "Fuel station", "km": 1.0}


trip_assistant.nearest_stop = fake_nearest
for i in range(4):
    h.add_alert(i)
h.check(5)
check("4 alerts is below the limit", len(called) == 0)
h.add_alert(6)
h.check(7)
threading.Event().wait(0.2)
check("5 alerts in 30 minutes asks for a stop", len(called) == 1 and h.result["name"] == "X")
check("location is forgotten after one use", h.location == None)

# old alerts fall out of the window
h = TripAssistant()
for i in range(5):
    h.add_alert(i)
check("alerts older than 30 minutes dont count", h.too_many(2000) == False)

log.close()
shutil.rmtree(folder, ignore_errors=True)
done()
