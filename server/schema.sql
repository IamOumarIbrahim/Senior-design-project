--   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
--        Oumar Mamoun Ibrahim U22200741
--        Abdullah Jafar Abdelhamid U23101327
--        Faris Munadhil Ahmed Alagha U23104246
--        Mohamed Ahmed Saad Khafagy U20101649

-- same tables as the device, works on postgres and on sqlite
-- times are iso text and sessions end up the same on both

CREATE TABLE IF NOT EXISTS driver (
  driver_id INTEGER PRIMARY KEY,
  pin_hash TEXT,
  display_name TEXT,
  language TEXT
);

CREATE TABLE IF NOT EXISTS device (
  device_id TEXT PRIMARY KEY,
  model_version TEXT,
  api_key_hash TEXT
);

CREATE TABLE IF NOT EXISTS calibration (
  calib_id INTEGER PRIMARY KEY,
  driver_id INTEGER REFERENCES driver(driver_id),
  class_name TEXT,
  cutoff REAL,
  ear_open REAL,
  pitch_rest REAL,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS session (
  session_id TEXT PRIMARY KEY,
  driver_id INTEGER REFERENCES driver(driver_id),
  device_id TEXT REFERENCES device(device_id),
  started_at TEXT,
  ended_at TEXT,
  monitored_pct REAL,
  uploaded INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS event (
  event_id TEXT PRIMARY KEY,
  session_id TEXT REFERENCES session(session_id),
  ts TEXT,
  class_name TEXT,
  confidence REAL,
  duration_s REAL,
  tier INTEGER,
  message TEXT,
  escalated INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tip (
  tip_id INTEGER PRIMARY KEY,
  session_id TEXT REFERENCES session(session_id),
  rule TEXT,
  text TEXT
);
