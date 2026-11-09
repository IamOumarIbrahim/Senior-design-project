"""Build the thumbnails and cut-out icons used by the v10 overview figures.

Run from anywhere: python prep_assets.py
Reads the report's own images, the Blender renders and the DMD frames; writes figsrc/v10/assets/.
"""
import os, random
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))          # latex_v10
FIG = os.path.join(ROOT, "Figures")
SRC = os.path.join(ROOT, "figsrc")
DMD = os.path.normpath(os.path.join(ROOT, "..", "..", "ieee-aiot", "data", "processed", "RGB"))
OUT = os.path.join(HERE, "assets")
os.makedirs(OUT, exist_ok=True)


def flat(im, bg="white"):
    im = im.convert("RGBA")
    base = Image.new("RGBA", im.size, bg)
    base.alpha_composite(im)
    return base.convert("RGB")


def save_jpg(im, name, size):
    im = im.copy()
    im.thumbnail((size, size), Image.LANCZOS)
    im.save(os.path.join(OUT, name), quality=90)


def save_png(im, name, size):
    im = im.copy()
    im.thumbnail((size, size), Image.LANCZOS)
    im.save(os.path.join(OUT, name))


def trim_white(im, thr=245, pad=10):
    """Crop away the near-white border of a render on white."""
    g = im.convert("L").point(lambda v: 255 if v < thr else 0)
    box = g.getbbox()
    if not box:
        return im
    x0, y0, x1, y1 = box
    return im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))


# --- DMD cue frames (already 640x640 in the report)
for k in ["yawn", "hand_mouth", "drink", "phone", "negative"]:
    save_jpg(Image.open(os.path.join(FIG, "dmd", f"cue_{k}.jpg")), f"cue_{k}.jpg", 420)

# --- one real yawn over time: DMD subject_09 video_04, 1 frame per second, yawn labelled on frames 113-119
for i, f in enumerate([110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120]):
    p = os.path.join(DMD, "images", "subject_09", "video_04", f"subject_09_video_04_frame_{f:04d}.jpg")
    save_jpg(Image.open(p), f"yawn_seq_{i:02d}.jpg", 300)

# --- dataset mosaic: one labelled frame from each of 9 DMD subjects
random.seed(4)
subs = sorted(d for d in os.listdir(os.path.join(DMD, "labels")) if d.startswith("subject_"))[:9]
tiles = []
for s in subs:
    cands = []
    for v in sorted(os.listdir(os.path.join(DMD, "labels", s))):
        vd = os.path.join(DMD, "labels", s, v)
        if not os.path.isdir(vd):
            continue
        for f in os.listdir(vd):
            if f.endswith(".txt") and os.path.getsize(os.path.join(vd, f)) > 0:
                cands.append((v, f[:-4]))
    v, stem = random.choice(cands)
    tiles.append(Image.open(os.path.join(DMD, "images", s, v, stem + ".jpg")).resize((200, 200), Image.LANCZOS))
mosaic = Image.new("RGB", (600, 600), "white")
for i, t in enumerate(tiles):
    mosaic.paste(t, ((i % 3) * 200, (i // 3) * 200))
save_jpg(mosaic, "dmd_mosaic.jpg", 420)

# --- Blender renders
save_jpg(flat(Image.open(os.path.join(SRC, "blender", "out", "cabin.png"))), "cabin.jpg", 900)
save_jpg(trim_white(flat(Image.open(os.path.join(SRC, "blender", "out", "edge_unit.png")))), "edge_unit.jpg", 600)
w = flat(Image.open(os.path.join(SRC, "blender", "out", "wiring.png")))
save_jpg(trim_white(w.crop((860, 280, 1960, 600))), "lightbar.jpg", 600)
save_jpg(trim_white(w.crop((360, 900, 1440, 1560))), "pi5.jpg", 500)
b = Image.open(os.path.join(SRC, "out", "bench_raw.png")).convert("RGB")
for name, box in {
    "camera": (880, 440, 1120, 750),
    "speaker": (1160, 430, 1380, 660),
    "lightbar_rgb": (610, 140, 890, 730),
    "display": (1680, 410, 2090, 740),
    "edgebox": (1160, 810, 1400, 1000),
    "stack": (200, 860, 930, 1600),
    "bench": (200, 100, 2500, 1600),
}.items():
    save_jpg(b.crop(box), f"{name}.jpg", 700 if name == "bench" else 420)

# --- UI screens and pilot frames
for k in ["ui_tablet_light", "ui_tablet_dark", "ui_tablet_cal", "ui_dashboard"]:
    save_jpg(Image.open(os.path.join(FIG, k + ".png")), k + ".jpg", 900)
for k in ["grid_1", "grid_2", "grid_3", "grid_4", "pilot_dash_view", "lesson_a", "lesson_b", "lesson_c", "lesson_d"]:
    save_jpg(Image.open(os.path.join(FIG, "pilot", k + ".jpg")), f"pilot_{k}.jpg", 420)
for i in range(6):
    save_jpg(Image.open(os.path.join(FIG, f"guide_{i}.png")), f"guide_{i}.jpg", 300)
save_jpg(Image.open(os.path.join(FIG, "crop_roi.png")), "crop_roi.jpg", 1200)
print("assets:", len(os.listdir(OUT)))

# --- held-out replay driver subject_05: one frame each of no cue, drinking, phone use
lab = os.path.join(DMD, "labels", "subject_05")
picked = {}
for v in sorted(os.listdir(lab)):
    vd = os.path.join(lab, v)
    if not os.path.isdir(vd):
        continue
    for f in sorted(os.listdir(vd)):
        if not f.endswith(".txt"):
            continue
        t = open(os.path.join(vd, f)).read().split()
        c = t[0] if t else "-"
        if c in ("-", "2", "3") and c not in picked and int(f[-8:-4]) > 30:
            picked[c] = (v, f[:-4])
for c, name in {"-": "s05_none", "2": "s05_drink", "3": "s05_phone"}.items():
    v, stem = picked[c]
    save_jpg(Image.open(os.path.join(DMD, "images", "subject_05", v, stem + ".jpg")), name + ".jpg", 300)
print("subject_05 frames:", picked)
