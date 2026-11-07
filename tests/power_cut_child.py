#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# writes events forever and prints each id after its commit
# test_logger.py kills this process at a random moment
import sys

from helper import REPO

from event_logger import EventLogger

path = sys.argv[1]
log = EventLogger(path)
log.add_device("test", "v1")
log.flush()
sid = log.new_session(None, "test")
i = 0
while True:
    e = {}
    e["event_id"] = sid + "-" + str(i)
    e["class_name"] = "yawning"
    e["confidence"] = 0.9
    e["duration_s"] = 1.0
    e["tier"] = 1
    e["message"] = "test"
    e["escalated"] = 0
    log.write(e, sid, "2026-11-07T10:00:00")
    log.flush()
    print(e["event_id"], flush=True)
    i = i + 1
