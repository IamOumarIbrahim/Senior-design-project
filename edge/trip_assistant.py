#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import json
import math
import os
import threading
import time
import urllib.parse
import urllib.request

import config


def km_between(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) * math.sin(dp / 2) + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) * math.sin(dl / 2)
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_query(lat, lon, radius):
    around = "(around:" + str(radius) + "," + str(lat) + "," + str(lon) + ")"
    q = "[out:json][timeout:10];("
    q = q + 'node["amenity"~"fuel|cafe"]' + around + ";"
    q = q + 'way["amenity"~"fuel|cafe"]' + around + ";"
    q = q + 'node["highway"~"rest_area|services"]' + around + ";"
    q = q + 'way["highway"~"rest_area|services"]' + around + ";"
    q = q + ");out center 40;"
    return q


# turns the overpass answer into a simple list of places
def read_places(data):
    places = []
    for e in data["elements"]:
        lat = None
        lon = None
        if "lat" in e:
            lat = e["lat"]
            lon = e["lon"]
        elif "center" in e:
            lat = e["center"]["lat"]
            lon = e["center"]["lon"]
        tags = {}
        if "tags" in e:
            tags = e["tags"]
        kind = "Rest stop"
        if "amenity" in tags:
            if tags["amenity"] == "fuel":
                kind = "Fuel station"
            else:
                kind = "Cafe"
        name = kind
        if "name:en" in tags:
            name = tags["name:en"]
        elif "name" in tags:
            name = tags["name"]
        if lat != None:
            places.append({"name": name, "kind": kind, "lat": lat, "lon": lon})
    return places


def ask_overpass(lat, lon):
    query = build_query(lat, lon, config.REST_RADIUS_M)
    body = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(config.OVERPASS_URL, data=body, headers={"User-Agent": "drivesafe-sdp"})
    res = urllib.request.urlopen(req, timeout=config.REST_TIMEOUT_S)
    data = json.loads(res.read().decode())
    return read_places(data)


def load_saved_list():
    if os.path.exists(config.REST_LIST):
        f = open(config.REST_LIST, encoding="utf8")
        places = json.load(f)
        f.close()
        return places
    return []


def closest(places, lat, lon):
    best = None
    best_km = 0
    for p in places:
        d = km_between(lat, lon, p["lat"], p["lon"])
        if best == None or d < best_km:
            best = p
            best_km = d
    if best == None:
        return None
    return {"name": best["name"], "kind": best["kind"], "km": round(best_km, 1)}


# neerest place, if the map service is down use the saved list
def nearest_stop(lat, lon):
    places = []
    try:
        places = ask_overpass(lat, lon)
    except Exception as e:
        print("overpass failed, using the saved list " + str(e))
    if len(places) == 0:
        places = load_saved_list()
    return closest(places, lat, lon)


# two question pre trip check
def pretrip_advice(hours, tired):
    if hours < 5 or tired >= 4:
        return "You seem tired. Rest before you drive, or take a break soon."
    return "You are good to go. Drive safe."


class TripAssistant:

    def __init__(self):
        self.times = []         # time of each alert
        self.location = None
        self.last_offer = -1000000
        self.result = None

    # location comes from the phone and is used once then forgotten
    def set_location(self, lat, lon):
        self.location = (lat, lon)

    def add_alert(self, t):
        self.times.append(t)

    def too_many(self, t):
        keep = []
        for old in self.times:
            if t - old <= config.REST_WINDOW_S:
                keep.append(old)
        self.times = keep
        return len(keep) >= config.REST_ALERTS

    def check(self, t):
        if self.too_many(t) and t - self.last_offer >= config.REST_WINDOW_S:
            if self.location != None:
                lat = self.location[0]
                lon = self.location[1]
                self.location = None
                self.last_offer = t
                thread = threading.Thread(target=self.fetch, args=(lat, lon), daemon=True)
                thread.start()

    def fetch(self, lat, lon):
        start = time.time()
        self.result = nearest_stop(lat, lon)
        print("rest stop answer took " + str(round(time.time() - start, 2)) + " s")
