#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# opens the display with no camera so the screens can be looked at
# python show_screens.py drive
import sys
import time

from helper import check

from tablet_ui import TabletUI
from trip_assistant import TripAssistant

screen = "drive"
if len(sys.argv) > 1:
    screen = sys.argv[1]

ui = TabletUI(TripAssistant())
ui.set("driver", "Sara")
ui.set("drive_min", 48)
ui.set("camera_pct", 98.2)
ui.show(screen)
if screen == "drive":
    ui.add_recent("drinking", "tier 1", "14:18")
    ui.add_recent("phone use", "tier 2", "13:57")
    ui.add_recent("yawning", "tier 1", "13:41")
    ui.show_status("Drowsy", 2, "Yawning detected 3 times in 5 minutes. Consider a short break.",
                   "تم رصد التثاؤب ثلاث مرات خلال خمس دقائق. يرجى أخذ استراحة قصيرة.")
    ui.set("stop", {"name": "ENOC", "kind": "Fuel station", "km": 1.4})
if screen == "calibrating":
    ui.set("calib", {"seconds": 12, "frames": 362, "seen": 0, "total": 20})
ui.serve()
