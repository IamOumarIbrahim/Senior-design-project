#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# runs every test script and prints one line for each
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = ["test_decision.py", "test_logger.py", "test_vision.py", "test_alerts.py",
         "test_eye_calib.py", "test_display.py", "test_upload.py", "test_tools.py"]

failed = 0
for name in TESTS:
    res = subprocess.run([sys.executable, name], cwd=HERE, capture_output=True, text=True)
    line = ""
    for row in res.stdout.split("\n"):
        if row.startswith("Passed="):
            line = row
    print(name.ljust(22) + line)
    if res.returncode != 0:
        failed = failed + 1
        for row in res.stdout.split("\n"):
            if row.startswith("FAIL"):
                print("    " + row)
print("----------------------")
print("Scripts failed= " + str(failed))
print("----------------------")
