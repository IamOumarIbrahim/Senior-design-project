#!/bin/bash
#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649
# sets up a new raspberry pi 5 with raspberry pi os 64 bit
# NOT TESTED, the pi is not here yet
set -e

sudo apt update
sudo apt install -y python3-venv alsa-utils chromium-browser python3-lgpio g++
# only with the ai hat+ on the board
sudo apt install -y hailo-all

python3 -m venv --system-site-packages /home/pi/dms-venv
/home/pi/dms-venv/bin/pip install -r /home/pi/Repo/requirements.txt

# the blind check is faster in c++, if this fails opencv does the same job
bash /home/pi/Repo/edge/native/build.sh || true

# flash rate and volume are capped, keep the speaker below full so the usb stays under 1.6 A
amixer -q sset PCM 70% || true

sudo cp /home/pi/Repo/deploy/dms.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dms.service

mkdir -p /home/pi/.config/autostart
cp /home/pi/Repo/deploy/kiosk.desktop /home/pi/.config/autostart/

echo "put your key in /home/pi/dms.env then reboot"
