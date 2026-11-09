"""Real YOLO11n activations for the redrawn Fig 3.2.

Runs our DMD-trained YOLO11n (seed 13) on the report's phone frame, hooks the backbone and neck,
and saves a few of the most active channels per stage as small heatmap tiles, plus the real
detection (box, class, score) to assets/yolo_det.json.
"""
import json, os, pathlib
import numpy as np
import torch
from PIL import Image
from ultralytics import YOLO

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "assets"
W = pathlib.Path(r"C:\Dev\repos\Public repos\lightweight-driver-behavior-detection\DMS-Eval\RESULTS_TO_MIGRATE"
                 r"\training_runs\yolo11n_seed13\weights\best.pt")
IMG = HERE.parent.parent / "Figures" / "dmd" / "cue_phone.jpg"

model = YOLO(str(W))
net = model.model
# YOLO11n: 0 conv 320, 1 conv 160, 4 C3k2 80 (P3), 6 C3k2 40 (P4), 10 C2PSA 20 (P5); neck outputs 16 (80), 19 (40), 22 (20)
taps = {0: "b320", 1: "b160", 4: "b80", 6: "b40", 10: "b20", 16: "n80", 19: "n40", 22: "n20"}
feats = {}
hooks = [net.model[i].register_forward_hook(lambda m, inp, out, k=k: feats.__setitem__(k, out.detach().float().cpu()))
         for i, k in taps.items()]
res = model.predict(str(IMG), imgsz=640, conf=0.25, device="cpu", verbose=False)[0]
for h in hooks:
    h.remove()

# palette: white -> lavender -> deep purple, matching the detector colour in the figures
stops = np.array([[255, 255, 255], [206, 200, 238], [122, 104, 196], [52, 34, 110]], float)


def cmap(v):
    v = np.clip(v, 0, 1) * (len(stops) - 1)
    i = np.minimum(v.astype(int), len(stops) - 2)
    t = (v - i)[..., None]
    return (stops[i] * (1 - t) + stops[i + 1] * t).astype(np.uint8)


meta = {}
for k, t in feats.items():
    a = t[0].numpy()                                  # C x H x W
    flat = a.reshape(a.shape[0], -1)
    z = (flat - flat.mean(1, keepdims=True)) / (flat.std(1, keepdims=True) + 1e-6)
    spread = (z > 1.0).mean(1) * flat.std(1)      # strong AND spread over the frame, not a single dot
    top = np.argsort(-spread)[:4]
    meta[k] = {"shape": list(a.shape), "channels": [int(c) for c in top]}
    for j, c in enumerate(top):
        m = a[c]
        lo, hi = np.percentile(m, 2), np.percentile(m, 99.5)
        img = Image.fromarray(cmap((m - lo) / (hi - lo + 1e-6)))
        img.resize((160, 160), Image.NEAREST if m.shape[0] <= 40 else Image.BILINEAR).save(OUT / f"feat_{k}_{j}.png")

det = []
names = res.names
for b, c, s in zip(res.boxes.xyxyn.tolist(), res.boxes.cls.tolist(), res.boxes.conf.tolist()):
    det.append({"box": [round(v, 4) for v in b], "cls": names[int(c)], "score": round(float(s), 3)})
json.dump({"detections": det, "features": meta, "weights": str(W)}, open(OUT / "yolo_det.json", "w"), indent=1)
print(json.dumps(det), {k: v["shape"] for k, v in meta.items()})
