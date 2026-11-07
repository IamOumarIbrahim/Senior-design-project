# DriveSafe - Edge-Cloud Driver Monitoring

Senior Design Project, Group 34, University of Sharjah. Supervisor: Dr. Mohamad Khairi Bin Ishak.

| Student | ID |
| --- | --- |
| Oumar Mamoun Ibrahim | U22200741 |
| Abdullah Jafar Abdelhamid | U23101327 |
| Faris Munadhil Ahmed Alagha | U23104246 |
| Mohamed Ahmed Saad Khafagy | U20101649 |

A camera watches the driver, YOLO11n finds yawning, hand over mouth, drinking and phone use on the Pi, and the system warns the driver only when the cue is real. All video stays in the car, only event records are uploaded after the trip.

## Folders

| Folder | What is in it |
| --- | --- |
| `edge/` | everything that runs on the Pi, start with `main.py` |
| `server/` | upload API, database and post-trip tips (FastAPI) |
| `dashboard/` | web dashboard (React) |
| `dataset/` | recording, frames, folds, label checks, hard negatives |
| `training/` | training, pruning, export, Pi benchmark, Hailo compile |
| `tests/` | one script for each group of tests from Chapter 5 |
| `deploy/` | Pi setup, service and voice file generator |
| `sounds/` `voice/` `models/` | alert sounds, English and Arabic voice, model weights |

## Run it on a laptop

```bash
pip install -r requirements.txt
cd tests
python make_replay.py
cd ../edge
python main.py replay ../data/replay_subject_05.mp4
```

The replay has no sound and no display. Events go in `data/events.db`. `make_replay.py` needs the DMD RGB frames, set `DMS_RGB_DIR` to where they are. DMD has its own licence so the frames are not in this repo.

On a laptop with a GPU set `DMS_DEVICE=0`. Dont do this with mediapipe installed on Windows, the two together crash CUDA.

## Run the server and dashboard

```bash
cd dashboard
npm install
npm run build
cd ../server
pip install -r requirements.txt
python add_device.py pi5-group34
python seed_demo.py demo demo1234
uvicorn app:app --port 8000
```

Open `http://127.0.0.1:8000` and log in with the demo account. Those trips are made up and the page marks them SAMPLE DATA. A real driver gets an account with `python set_password.py driver_id name`.

Without `DATABASE_URL` it uses SQLite. `docker compose up` in `server/` runs it with Postgres.

## Tests

```bash
cd tests
python run_all.py
```

Hardware tests like the 240 fps flash video, the relay power cut and the user trials are done on the bench in SDP 2.

## C++ part

The camera blind check is in C++ because it runs on every frame. It takes 0.32 ms against about 3.0 ms with OpenCV on the PC, and it gave the same brightness, sharpness and decision on all 15,723 DMD frames. The rest stays in Python because the heavy work already runs inside OpenCV, MediaPipe, SQLite or the NPU. EMA and the decision logic take about 2 microseconds a frame.

```bash
bash edge/native/build.sh
```

Build it on the machine that will use it. Without the library `preprocessor.py` uses OpenCV and gives the same answer. The Pi time is not measured yet.

## Features

| Spec | Where | State |
| --- | --- | --- |
| FS-01 Pi 5 deployment | `edge/main.py`, `deploy/` | written, needs the Pi |
| FS-02 camera | `edge/frame_grabber.py` | tested on video files |
| FS-03 detector | `edge/detector.py`, `training/train.py` | runs with the DMD model, needs our data |
| FS-04 EMA | `edge/ema_filter.py` | tested, T-04 |
| FS-05 light and voice | `edge/alert_manager.py` | logic tested, needs the bar and speaker |
| FS-06 cool-down | `edge/decision_engine.py` | tested, T-06 |
| FS-07 mirror checks | by design | needs T-07 with people |
| FS-08 logging | `edge/event_logger.py` | tested |
| FS-09 on-device video | `edge/uploader.py` | tested, only event fields are sent |
| FS-10 dataset | `dataset/` | tools ready, recording not done |
| FS-11 compression | `training/prune.py`, `export_models.py`, `compile_hailo.sh` | pruning, fine tune, ONNX and NCNN ran, Hailo needs the toolchain |
| FS-12 hard negatives | `dataset/mine_hard_negatives.py` | tool ready, needs our data |
| FS-13 baseline clips | `dataset/record_session.py` | written, needs the camera |
| FS-14 class alerts | `edge/alert_manager.py` | tested |
| FS-15 tiers | `edge/decision_engine.py` | tested, T-15 |
| FS-16 explained alerts | `edge/messages.py`, `voice/` | tested, T-16 |
| FS-17 blind check | `edge/preprocessor.py` | tested, T-17, values need tuning on the C922 |
| FS-18 crop tracking | `edge/crop_tracker.py` | tested on a real face, off until it beats the fixed crop |
| FS-19 calibration | `edge/calibrator.py` | tested, T-19 |
| FS-20 eye closure | `edge/eye_module.py` | tested on signals and DMD footage, still above the target, see below |
| FS-21 power-cut logging | `edge/event_logger.py` | passed 50 process kills, needs the relay test |
| FS-22 dashboard and sync | `edge/uploader.py`, `server/`, `dashboard/` | tested over real TLS on SQLite |
| FS-23 tips | `server/tips.py` | tested |
| FS-24 tablet | `edge/tablet_ui.py`, `edge/web/` | screens checked, needs the 7 inch display |
| FS-25 pre-trip check | `edge/tablet_ui.py`, `edge/trip_assistant.py` | tested |
| FS-26 rest stops | `edge/trip_assistant.py` | tested with the saved list |

## Known problem

The eye alarm is better but not finished. The report rule (EAR below 75% of open) fired on half open eyes and on looking down. It now needs EAR below 50% of open and the face model blink score above 0.50, and if the head is more than 8 degrees below the rest pitch it waits 3 s instead of 1.5 s. Head down time is left out of PERCLOS.

Eye alarms per hour on the DMD footage, 14 alert drivers, tuned on subjects 1 to 9 and checked on 10 to 14:

| Rule | Subjects 1-9 | Subjects 10-14 |
|---|---|---|
| Report rule | 97.1 | 120.3 |
| New rule | 22.7 | 20.7 |
| New rule, counting only runs proven over 2 s | 7.4 | 9.7 |

The real number sits between the last two rows because the footage is only 1 fps. Both are above the 3 per hour target. What is left is mostly long looks at the lap and eyes shut during a yawn. A closed eye and a downward look can look the same in one frame, so this needs real closures recorded with the C922 at full frame rate before the thresholds can be trusted. How many true closures the new rule misses is not measured, no labelled closed eye data exists yet.

## Things that differ from the report

- Cool-down starts when the cue ends and not at the first alert, or the tiers could never happen. This follows the state diagram and not Appendix A.
- The event table has one more column, `escalated`. Each tier gets its own row for T-15, and the dashboard only counts the first row of a cue.
- Muted cues in the cool-down are logged with tier 0, this is what T-06 asks for.
- Messages add the count or the length so they pass T-16.
- The tip about phone use at speed needs vehicle data we dont have, so it counts trips instead.
- The dashboard has its own password. The PIN stays in the car.
- The light bar has one MOSFET so it can only flash. The colours in Table 4.15 show on the display only.
- Rest stops use the phone location, and the browser only gives that on HTTPS, so the Pi needs a certificate for it.
# Senior-design-project
