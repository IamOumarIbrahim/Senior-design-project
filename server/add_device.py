#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# python add_device.py pi5-group34
# prints the key one time, put it in DMS_DEVICE_KEY on the pi
import sys

import db

if len(sys.argv) < 2:
    print("use: python add_device.py device_id")
else:
    db.setup()
    key = db.add_device(sys.argv[1])
    print("device key (shown only once)= " + key)
