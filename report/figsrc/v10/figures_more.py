"""R4 and N3 for the v10 figure set."""
import json, pathlib
from lib import Fig, CLS, CLS_NAME, ST, INK, MUTED, LINE, CUE_BOX, CUE_IMG, ROI, yolo_frac
from figures import ORDER, TIER, score_chips, num, slab

ASSETS = pathlib.Path(__file__).resolve().parent / "assets"


def deck(f, x, y, size, key, n=3, off=6, border="#5a54a6"):
    """A small deck of real feature-map tiles (back to front)."""
    for j in reversed(range(n)):
        f.thumb(x + j * off, y - j * off, size, size, f"feat_{key}_{j}.png", border=border, bw=1.4, radius=4, fit="fill")


# ======================================================================================
def r4():
    """Fig 3.2 replacement: YOLO11n with its real activations on the report's phone frame."""
    f = Fig(1180, 384)
    det = json.load(open(ASSETS / "yolo_det.json"))["detections"][0]
    box = tuple(det["box"])
    for cx, s in [(86, "Input"), (421, "Backbone"), (736, "Neck"), (890, "Heads"), (1034, "NMS"), (1134, "Output")]:
        f.header(cx, 8, s, 150)
    # input
    f.thumb(8, 74, 156, 156, "cue_phone.jpg", border=CLS["none"])
    f.text(86, 238, "640×640 RoI crop\nof a DMD frame", size=13.5, color=MUTED, w=160, align="center")
    f.arrow([(166, 152), (184, 152)])
    # backbone: real feature maps, shrinking (2-tile decks)
    f.panel(188, 44, 466, 270, "veh", radius=14)
    stages = [("b320", 84, "320×320", "16 ch"), ("b160", 72, "160×160", "32 ch"), ("b80", 62, "80×80", "128 ch"),
              ("b40", 52, "40×40", "128 ch"), ("b20", 44, "20×20", "256 ch")]
    x, cy = 202, 150
    for j, (k, sz, a1, a2) in enumerate(stages):
        deck(f, x, cy - sz / 2 + 4, sz, k, n=2, off=6, border=ST["veh"][0])
        f.text(x + sz / 2 + 3, 222, a1, size=13.5, bold=True, align="center")
        f.text(x + sz / 2 + 3, 241, a2, size=12.5, color=MUTED, align="center")
        if j < 4:
            f.arrow([(x + sz + 9, cy), (x + sz + 25, cy)], width=1.5)
        x += sz + 32
    f.text(421, 278, "The image gets smaller and the features get richer.", size=13.5, color=ST["veh"][0], align="center")
    f.arrow([(656, 152), (670, 152)])
    # neck: three scales
    f.panel(674, 44, 126, 270, "ok", radius=14)
    f._marker(ST["ok"][0])
    f.svg_raw(f'<path d="M 686 86 L 686 236" stroke="{ST["ok"][0]}" stroke-width="1.6" fill="none" marker-end="url(#m2f8a5b)" marker-start="url(#m2f8a5b)"/>')
    for j, (k, a1) in enumerate([("n80", "80×80"), ("n40", "40×40"), ("n20", "20×20")]):
        y = 62 + j * 74
        deck(f, 698, y + 6, 46, k, n=2, off=5, border=ST["ok"][0])
        f.text(754, y + 16, a1, size=13, bold=True)
        f.arrow([(802, y + 30), (812, y + 30)], width=1.5)
    f.text(737, 268, "Mixes fine and\ncoarse maps.", size=13, color=ST["ok"][0], w=120, align="center")
    # heads: grid cells drawn on the input
    for j, (n, a1, a2) in enumerate([(16, "80×80 grid", "small objects"), (8, "40×40 grid", "medium objects"), (4, "20×20 grid", "large objects")]):
        y = 62 + j * 74
        f.thumb(816, y, 58, 58, "cue_phone.jpg", border=ST["det"][0], bw=2)
        f.grid(816, y, 58, 58, n, color="#ffffffcc", bw=2)
        f.text(880, y + 9, a1, size=13, bold=True)
        f.text(880, y + 28, a2, size=12.5, color=MUTED)
        f.arrow([(976, y + 29), (987, 152)], width=1.3)
    f.text(890, 286, "Every cell guesses a\nbox, a class and a score.", size=13, color=ST["det"][0], w=170, align="center")
    # NMS: overlapping guesses on the frame
    f.thumb(990, 110, 88, 88, "cue_phone.jpg", border=CLS["none"])
    x0, y0, x1, y1 = box
    for dx, dy, dw in [(-0.03, -0.02, 0.05), (0.02, 0.03, -0.03), (0.0, -0.04, 0.02), (0.04, 0.0, 0.04)]:
        f.bbox(990, 110, 88, 88, (max(0, x0 + dx), y0 + dy, x1 + dx + dw, y1 + dy + dw), "#7a4cb099", bw=2)
    f.bbox(990, 110, 88, 88, box, CLS["phone"], bw=2)
    f.text(1034, 206, "Many overlapping\nguesses. Keep\nthe best one.", size=12.5, color=MUTED, w=100, align="center")
    f.arrow([(1080, 154), (1088, 154)])
    # output: the real detection
    f.thumb(1090, 110, 88, 88, "cue_phone.jpg", border=CLS["phone"], bw=2.4)
    f.tag(1094, 114, f"phone {det['score']:.2f}", CLS["phone"])
    f.bbox(1090, 110, 88, 88, box, CLS["phone"], bw=2.4)
    f.text(1134, 206, "One box,\nclass and\nscore.", size=12.5, color=MUTED, w=88, align="center")
    f.text(8, 352, f"Feature maps are real activations of our DMD-trained YOLO11n on this frame (the most active channels per stage). "
                   f"The output box and its score of {det['score']:.2f} are the model's real prediction.", size=13, color=MUTED, italic=True)
    return f


# ======================================================================================
def n3():
    """Fig 5.6 addition: from recording to a subject-disjoint, labelled split."""
    f = Fig(1180, 520)
    f.panel(8, 8, 1164, 262, "pre", label="(a) FROM A RECORDING TO LABELLED FRAMES", fill="#fafbfc")
    heads = [(96, "Record"), (300, "Sample frames"), (520, "Label in CVAT"), (760, "Check agreement"), (1020, "Hard negatives")]
    for cx, s in heads:
        f.header(cx, 36, s, 210)
    T = 72
    for j, g in enumerate([1, 2, 4]):
        f.thumb(20 + j * 22, T + j * 12, 108, 108, f"guide_{g}.jpg", border=ST["pre"][0])
    f.text(96, T + 146, "10-min sessions, 1080p\n30 FPS, guide of Fig 5.2", size=13, color=MUTED, w=190, align="center")
    f.arrow([(176, T + 64), (196, T + 64)])
    for j, src in enumerate(["pilot_grid_3.jpg", "pilot_grid_1.jpg", "pilot_grid_4.jpg", "pilot_grid_2.jpg"]):
        f.thumb(204 + j * 48, T + 6, 44, 116, src, border="#c9d0d7", bw=1.6, radius=5)
    f.text(300, T + 146, "frames at 5 FPS,\nabout 48,000 planned", size=13, color=MUTED, w=190, align="center")
    f.arrow([(400, T + 64), (420, T + 64)])
    for j, k in enumerate(ORDER):
        x, y = 428 + (j % 2) * 92, T + (j // 2) * 66
        f.thumb(x, y, 86, 60, CUE_IMG[k], border=CLS[k], bw=2, posy=55)
    f.text(520, T + 146, "4 classes, box rules,\nvisible ≥ 0.5 s", size=13, color=MUTED, w=190, align="center")
    f.arrow([(616, T + 64), (636, T + 64)])
    f.thumb(644, T, 128, 128, "cue_drink.jpg", border=ST["veh"][0])
    bx = CUE_BOX["drink"]
    f.bbox(644, T, 128, 128, bx, "#3d6fa8", bw=2.4)
    f.bbox(644, T, 128, 128, (bx[0] + 0.03, bx[1] + 0.02, bx[2] + 0.02, bx[3] + 0.04), "#d0661e", bw=2.4)
    f.tag(648, T + 4, "A", "#3d6fa8"); f.tag(668, T + 4, "B", "#d0661e")
    f.text(784, T + 10, "match if\nIoU ≥ 0.5", size=13.5, bold=True)
    f.text(784, T + 58, "then 10 % spot\ncheck; relabel\nif > 5 % differ", size=12.5, color=MUTED)
    f.text(760, T + 146, "two annotators on\nthe first subject", size=13, color=MUTED, w=190, align="center")
    f.arrow([(888, T + 64), (908, T + 64)])
    f.thumb(916, T, 100, 128, "pilot_lesson_c.jpg", border=CLS["none"], posy=30)
    f.tag(920, T + 106, "negative", "#5f6b78")
    f.thumb(1024, T, 128, 128, "cue_negative.jpg", border=CLS["none"])
    f.tag(1028, T + 106, "negative", "#5f6b78")
    f.text(1034, T + 146, "look-alikes labelled negative:\ntalking, chin touch, cup below\nthe chin, phone in a holder", size=13, color=MUTED, w=240, align="center")
    f.panel(8, 284, 1164, 228, "veh", label="(b) SUBJECT-DISJOINT FOLDS", fill="#f6f9fd")
    f.thumb(26, 330, 120, 120, "dmd_mosaic.jpg", border=ST["pre"][0])
    f.text(86, 456, "first: DMD,\n14 drivers", size=13, color=MUTED, w=150, align="center")
    f.arrow([(150, 390), (186, 390)])
    cols = {"Test": ("#c4453c", "#fbe5e2"), "Val": ("#b98a1e", "#fbf3df"), "Train": ("#3d6fa8", "#e8eff8")}
    SX = 290
    for si in range(4):
        cx = SX + si * 150 + 60
        f.el.append(f'<div class="pill" style="left:{cx - 22}px;top:316px;width:44px;height:44px;background:#5f6b78;font-size:14px;">S0{si + 1}</div>')
    for fo in range(4):
        y = 372 + fo * 32
        f.text(SX - 12, y + 4, f"Fold {fo + 1}", size=14, bold=True, align="right")
        for si in range(4):
            lab = "Test" if si == fo else ("Val" if si == (fo + 1) % 4 else "Train")
            sc, fc = cols[lab]
            f.box(SX + si * 150, y, 120, 26, lab, sc, size=13.5, fill=fc, radius=6)
    f.text(912, 330, "Every subject is tested\nonce, by a model that\nnever saw them.", size=15, bold=True, w=250)
    f.text(912, 400, "All of a subject's sessions,\nbaseline and hard-negative\nclips stay with that subject.\nResults: mean and spread\nover the 4 folds.", size=13.5, color=MUTED, w=250)
    return f
