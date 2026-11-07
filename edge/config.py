#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# same order as the model outputs
CLASSES = ["yawning", "hand_over_mouth", "drinking", "phone_use"]

# these two come from the eye module and not from yolo
EYES = "eyes_closed"
PERCLOS = "perclos"
BLOCKED = "camera_blocked"

# Table 4.15
CUTOFF = {"yawning": 0.50, "hand_over_mouth": 0.50, "drinking": 0.55, "phone_use": 0.55}
TAU = {"yawning": 0.6, "hand_over_mouth": 0.6, "drinking": 1.0, "phone_use": 1.0}
CONFIRM = {"yawning": 1.0, "hand_over_mouth": 1.0, "drinking": 1.5, "phone_use": 2.0}

CUTOFF_TOP = 0.85      # cieling for calibrated cutoff
COOLDOWN_S = 30
TIER2_S = 5
TIER3_S = 10
REPEAT_COUNT = 3       # 3 events in 5 minutes goes to tier 2
REPEAT_WINDOW_S = 300

# Eye module
EAR_RATIO = 0.50       # closed below 50% of open eye value, 75% also caught open eyes
BLINK_MIN = 0.50       # the face model blink score has to agree
EYES_CLOSED_S = 1.5
HEAD_DOWN_DEG = 8      # this far below the rest pitch counts as looking down
EYES_DOWN_S = 3.0      # looking down looks like closed so it has to last longer
EAR_DEFAULT = 0.30     # only used if the driver has no calibration yet
EYE_MODEL = os.path.join(BASE_DIR, "models", "face_landmarker.task")
PERCLOS_WINDOW_S = 60
PERCLOS_LIMIT = 0.15

# Blind check (table in section 4.3.3)
BRIGHT_LOW = 25
BRIGHT_HIGH = 230
SHARP_LOW = 20
BLOCKED_S = 3

# Camera and crop
CAM_INDEX = 0
CAM_W = 1920
CAM_H = 1080
CAM_FPS = 30
CROP_SIZE = 640
CROP_X = 640           # top left of the fixed crop
CROP_Y = 220
CROP_TRACKING = False  # only turned on if it beats the fixed crop (T-18)
TRACK_EVERY_S = 1.0
TRACK_TAU = 1.0
TRACK_W = 480
TRACK_H = 270
FACE_MODEL = os.path.join(BASE_DIR, "models", "face_detection_yunet_2023mar.onnx")

# Detector
# pt and onnx and ncnn all go through ultralytics, hailo goes through hailort
BACKEND = "pt"
MODEL_PATH = os.path.join(BASE_DIR, "models", "yolo11n_dmd.pt")
HEF_PATH = os.path.join(BASE_DIR, "models", "yolo11n_dms.hef")
# the weights remember the gpu they were trained on and the pi has none, so say it here
DEVICE = os.environ.get("DMS_DEVICE", "cpu")
DETECT_CONF = 0.25
CALIB_CONF = 0.05

# Calibration
CALIB_S = 20
CALIB_GAP = 0.05       # added to the 99th percentile
CALIB_MANY = 0.10      # more than 10% of frames above default means redo

# Light bar
LED_PIN = 18
MAX_FLASH_HZ = 3       # wcag limit
LED_DAY = 1.0
LED_NIGHT = 0.3
NIGHT_START = 18
NIGHT_END = 6

# flashes per secnd for each class, colour is only for the display
# (the bar has one mosfet so it cant change colour by itself)
PATTERN = {
    "yawning": {"hz": 1, "colour": "amber"},
    "hand_over_mouth": {"hz": 1, "colour": "amber"},
    "drinking": {"hz": 1, "colour": "teal"},
    "phone_use": {"hz": 2, "colour": "purple"},
    "eyes_closed": {"hz": 3, "colour": "red"},
    "perclos": {"hz": 1, "colour": "amber"},
    "camera_blocked": {"hz": 1, "colour": "grey"},
}

# Sounds
SOUND_DIR = os.path.join(BASE_DIR, "sounds")
VOICE_DIR = os.path.join(BASE_DIR, "voice")
CHIME = os.path.join(SOUND_DIR, "distraction_chime.wav")
BUZZ = os.path.join(SOUND_DIR, "fatigue_buzz.wav")
ALARM = os.path.join(SOUND_DIR, "lockon_alarm_sound.wav")
CLASS_SOUND = {"yawning": BUZZ, "hand_over_mouth": BUZZ, "drinking": CHIME, "phone_use": CHIME}

# Log file
DB_PATH = os.path.join(BASE_DIR, "data", "events.db")
# report uses NORMAL, FULL is safer for a real power cut but slower
DB_SYNC = "NORMAL"

# Upload
DEVICE_ID = "pi5-group34"
DEVICE_KEY = os.environ.get("DMS_DEVICE_KEY", "")
UPLOAD_URL = os.environ.get("DMS_UPLOAD_URL", "https://localhost:8443/api/v1/events")
CA_FILE = os.environ.get("DMS_CA_FILE", "")   # only for our own test certificate
RETRY_S = [30, 60, 120]
UPLOAD_BATCH = 500
MODEL_VERSION = "yolo11n_dmd_seed13"

# Driver display
DISPLAY_HOST = "127.0.0.1"   # change to 0.0.0.0 if a phone has to reach it
DISPLAY_PORT = 8080

# Trip assistant
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
REST_LIST = os.path.join(BASE_DIR, "edge", "rest_stops.json")
REST_RADIUS_M = 5000
REST_TIMEOUT_S = 4     # T-26 gives 5 s, after this we use the saved list
REST_ALERTS = 5        # alerts in the last 30 minutes before we suggest a stop
REST_WINDOW_S = 1800
BREAK_MINUTES = 90
