#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# saves fuel stations and rest areas from openstreetmap for the sharjah and dubai roads
# the car uses this list if the map service cant be reached
import json
import os
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "edge"))

import config
import trip_assistant

BOX = "(24.85,54.95,25.45,55.75)"
q = '[out:json][timeout:25];('
q = q + 'node["amenity"="fuel"]' + BOX + ';way["amenity"="fuel"]' + BOX + ';'
q = q + 'node["highway"~"rest_area|services"]' + BOX + ';way["highway"~"rest_area|services"]' + BOX + ';'
q = q + ');out center 400;'

body = urllib.parse.urlencode({"data": q}).encode()
req = urllib.request.Request(config.OVERPASS_URL, data=body, headers={"User-Agent": "drivesafe-sdp"})
res = urllib.request.urlopen(req, timeout=40)
places = trip_assistant.read_places(json.loads(res.read().decode()))

f = open(config.REST_LIST, "w", encoding="utf8")
json.dump(places, f, ensure_ascii=False, indent=0)
f.close()
print("saved " + str(len(places)) + " places")
