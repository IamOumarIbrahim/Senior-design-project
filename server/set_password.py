#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# python set_password.py driver_id name
# gives a driver a dashboard account, the id is the one on the pi
import getpass
import sys

import db

if len(sys.argv) < 3:
    print("use: python set_password.py driver_id name")
else:
    db.setup()
    password = getpass.getpass("Password: ")
    db.set_password(int(sys.argv[1]), sys.argv[2], password)
    print("done")
