#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import datetime
import os
import queue
import signal
import sys
import threading
import time

import config
import messages
from alert_manager import AlertManager
from calibrator import Calibrator
from crop_tracker import CropTracker
from decision_engine import DecisionEngine
from detector import Detector
from ema_filter import EMAFilter
from event_logger import EventLogger
from eye_module import EyeModule
from frame_grabber import FrameGrabber
from preprocessor import Preprocessor
from trip_assistant import TripAssistant, pretrip_advice
from uploader import Uploader

stop_now = False


# systemd sends this at shutdown
def on_stop(sig, frame):
    global stop_now
    stop_now = True


def clock_text(when):
    return datetime.datetime.fromtimestamp(when).isoformat(timespec="seconds")


# Boot and self check, camera speaker and light bar
def self_check(grabber, alerts):
    faults = alerts.self_check()
    if grabber.opened() == False:
        faults.append("camera not found")
    return faults


# capture to detector stage, runs in its own thread
def vision_loop(grabber, pre, det, tracker, eye, results, realtime):
    going = True
    while going:
        item = grabber.read()
        if item == None:
            results.put(None)
            going = False
        else:
            # if this thread dies the main loop would wait forever and nobody
            # is watching the driver, so tell it and let it warn the driver
            try:
                frame = item[0]
                t = item[1]
                if tracker != None:
                    pre.crop = tracker.update(frame, t)
                img = pre.crop_resize(frame)
                blocked = pre.blind_check(img, t)
                x = det.scores(img, config.DETECT_CONF)
                if eye != None:
                    if realtime:
                        eye.submit(img, t)
                    else:
                        # replay does it here so each run gives the same answer
                        eye.feed(eye.measure(img), t)
                results.put((t, item[2], x, blocked))
            except Exception as e:
                print("vision stopped: " + str(e))
                results.put("failed")
                going = False


def show_percent(values, p):
    values.sort()
    return values[int(len(values) * p / 100)]


# the detection and alert loop, figure 4.12
def run_session(grabber, pre, det, tracker, eye, log, alerts, ui, helper, driver, cutoffs, realtime):
    results = queue.Queue()
    thread = threading.Thread(target=vision_loop, args=(grabber, pre, det, tracker, eye, results, realtime), daemon=True)
    thread.start()

    session_id = log.new_session(driver["driver_id"], config.DEVICE_ID)
    ema = EMAFilter(config.TAU)
    eng = DecisionEngine(cutoffs, config.COOLDOWN_S)

    start_t = None
    wall0 = None
    prev_t = None
    last_t = 0
    blocked_now = False
    blocked_from = 0
    blocked_totl = 0
    blocked_id = None
    latency = []
    frames = 0
    rows = 0
    going = True
    failed = False

    while going and stop_now == False:
        r = results.get()
        if r == None:
            going = False
        elif r == "failed":
            going = False
            failed = True
            alerts.say("device_fault")
            if ui != None:
                ui.show_status("Attentive", 0, messages.FAULT_EN, messages.FAULT_AR)
        else:
            t = r[0]
            wall = r[1]
            x = r[2]
            blocked = r[3]
            if start_t == None:
                start_t = t
                wall0 = wall
                prev_t = t
                log.set_start(session_id, clock_text(wall0))
            dt = t - prev_t
            prev_t = t
            last_t = t
            frames = frames + 1
            now_ts = clock_text(wall0 + (t - start_t))

            # Camera blind check
            if blocked and blocked_now == False:
                blocked_now = True
                blocked_from = t - config.BLOCKED_S
                ema.reset()
                eng.set_blocked(True, t)
                alerts.stop_alarm()
                alerts.say(config.BLOCKED)
                event = eng.make_fixed(config.BLOCKED, 0, 0, t)
                event["message"] = messages.BLOCKED_EN
                blocked_id = event["event_id"]
                log.write(event, session_id, now_ts)
                rows = rows + 1
                if ui != None:
                    ui.show_status("Attentive", 0, messages.BLOCKED_EN, messages.BLOCKED_AR)
            elif blocked == False and blocked_now:
                blocked_now = False
                blocked_totl = blocked_totl + (t - blocked_from)
                log.set_duration(blocked_id, t - blocked_from)
                ema.reset()
                eng.set_blocked(False, t)

            if blocked_now == False:
                s = ema.update(x, dt)
                eye_state = None
                if eye != None:
                    eye_state = eye.state(t)
                out = eng.step(s, t, x, eye_state)

                for event in out:
                    if event["kind"] == "end":
                        log.set_duration(event["event_id"], event["duration_s"])
                        alerts.stop_alarm()
                    else:
                        alerts.play(event)
                        # frame capture to alert command, this is what the 100 ms target is about
                        latency.append((time.time() - wall) * 1000)
                        log.write(event, session_id, now_ts)
                        rows = rows + 1
                        print(now_ts + "  tier " + str(event["tier"]) + "  " + event["message"])
                        if event["tier"] > 0:
                            helper.add_alert(t)
                        if ui != None:
                            name = event["class_name"].replace("_", " ")
                            ui.add_recent(name, "tier " + str(event["tier"]), now_ts[11:16])
                            ui.show_status("", 0, event["message"], event["message_ar"])

                helper.check(t)

            if ui != None:
                word, tier = eng.status()
                ui.show_status(word, tier, "", "")
                ui.set("drive_min", int((t - start_t) / 60))
                seen = t - start_t
                if seen > 0:
                    gone = blocked_totl
                    if blocked_now:
                        gone = gone + (t - blocked_from)
                    ui.set("camera_pct", round(100 * (1 - gone / seen), 1))
                if helper.result != None:
                    ui.set("stop", helper.result)
                    helper.result = None
                action = ui.poll_action()
                if action != None and action["type"] == "end_trip":
                    going = False

    grabber.stop()

    # finish the trip
    if blocked_now:
        blocked_totl = blocked_totl + (last_t - blocked_from)
    pct = 100.0
    if start_t != None and last_t > start_t:
        pct = 100 * (1 - blocked_totl / (last_t - start_t))
    end_ts = None
    if start_t != None:
        end_ts = clock_text(wall0 + (last_t - start_t))
    log.end_session(session_id, round(pct, 1), end_ts)

    print("----------------------")
    if failed:
        print("session stopped because of a fault")
    print("Frames= " + str(frames))
    print("Rows written= " + str(rows))
    print("Monitored= " + str(round(pct, 1)) + "%")
    if len(latency) > 0:
        total = 0
        for v in latency:
            total = total + v
        print("Latency mean= " + str(round(total / len(latency), 1)) + " ms")
        print("Latency p95= " + str(round(show_percent(latency, 95), 1)) + " ms")
    print("----------------------")
    return session_id


# PIN and new driver screens, returns the driver and the saved cutoffs
def login(log, ui, grabber, pre, det, eye):
    driver = None
    pin = ""
    while driver == None:
        ui.set("error", "")
        ui.pin_login()
        a = ui.wait_action()
        if a["type"] == "pin":
            pin = str(a["pin"])
            driver = log.find_driver(pin)
            if driver == None:
                ui.show("new_driver")
                b = ui.wait_action()
                if b["type"] == "new_driver":
                    name = b["name"]
                    if name == "":
                        name = "Driver"
                    new_id = log.add_driver(pin, name, b["language"])
                    driver = {"driver_id": new_id, "display_name": name, "language": b["language"]}

    ui.set("driver", driver["display_name"])
    ui.show("pretrip")
    a = ui.wait_action()
    if a["type"] == "pretrip":
        ui.set("advice", pretrip_advice(float(a["hours"]), int(a["tired"])))

    saved = log.load_calibration(driver["driver_id"])
    if saved == None:
        saved = calibrate_driver(log, ui, grabber, pre, det, eye, driver)
    return driver, saved


def calibrate_driver(log, ui, grabber, pre, det, eye, driver):
    result = None
    going = True
    while going:
        ui.show("calibrate")
        a = ui.wait_action()
        if a["type"] == "skip_calibrate":
            going = False
        elif a["type"] == "calibrate":
            def show(seconds, count, seen):
                ui.set("calib", {"seconds": int(seconds), "frames": count, "seen": seen, "total": config.CALIB_S})

            ui.show("calibrating")
            cal = Calibrator()
            result = cal.run(grabber, pre, det, eye, show)
            if result["ok"]:
                log.save_calibration(driver["driver_id"], result["cutoffs"], result["ear_open"], result["pitch_rest"])
                going = False
            else:
                # noisy baseline, keep the defaults and ask again
                ui.set("error", "Too many detections. Please sit normally and try again.")
    if result == None:
        return {"cutoffs": dict(config.CUTOFF), "ear_open": None, "pitch_rest": None}
    return {"cutoffs": result["cutoffs"], "ear_open": result["ear_open"], "pitch_rest": result["pitch_rest"]}


def upload_all(log):
    up = Uploader(log)
    sent = up.sync()
    print("Events uploaded= " + str(sent))


# python main.py                         real camera and the driver display
# python main.py replay clip.mp4         plays a video with no display and no sound
def main():
    signal.signal(signal.SIGTERM, on_stop)
    replay = len(sys.argv) >= 3 and sys.argv[1] == "replay"

    log = EventLogger(config.DB_PATH)
    closed = log.close_old_sessions()
    if closed > 0:
        print("closed " + str(closed) + " session from the last power cut")
    log.add_device(config.DEVICE_ID, config.MODEL_VERSION)
    log.flush()

    path = config.MODEL_PATH
    if config.BACKEND == "hailo":
        path = config.HEF_PATH
    det = Detector(config.BACKEND, path)
    pre = Preprocessor()
    helper = TripAssistant()

    if replay:
        grabber = FrameGrabber(sys.argv[2], False)
        alerts = AlertManager("en", True)
        driver = log.find_driver("0000")
        if driver == None:
            new_id = log.add_driver("0000", "Replay", "en")
            driver = {"driver_id": new_id, "display_name": "Replay", "language": "en"}
        eye = EyeModule(None, True)
        if eye.available() == False:
            eye = None
        grabber.start()
        run_session(grabber, pre, det, None, eye, log, alerts, None, helper, driver, dict(config.CUTOFF), False)
        log.close()
    else:
        from tablet_ui import TabletUI
        ui = TabletUI(helper)
        ui.start()
        grabber = FrameGrabber(config.CAM_INDEX, True)
        alerts = AlertManager("en")

        # keep trying until the hardware is there
        faults = self_check(grabber, alerts)
        while len(faults) > 0:
            print("self check failed " + str(faults))
            ui.set("error", "Device fault: " + ", ".join(faults))
            alerts.say("device_fault")
            time.sleep(5)
            faults = self_check(grabber, alerts)
        ui.set("error", "")

        grabber.start()
        eye = EyeModule(None, True)
        if eye.available() == False:
            eye = None

        driver, saved = login(log, ui, grabber, pre, det, eye)
        alerts.language = driver["language"]

        if eye != None:
            if saved["ear_open"] != None:
                eye.ear_open = saved["ear_open"]
            if saved["pitch_rest"] != None:
                eye.pitch_rest = saved["pitch_rest"]
            eye.start()

        tracker = None
        if config.CROP_TRACKING:
            tracker = CropTracker(config.CAM_W, config.CAM_H)
            if tracker.available() == False:
                tracker = None

        ui.show("drive")
        run_session(grabber, pre, det, tracker, eye, log, alerts, ui, helper, driver, saved["cutoffs"], True)
        ui.show("ended")
        upload_all(log)
        log.close()


if __name__ == "__main__":
    main()
