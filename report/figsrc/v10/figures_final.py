"""Final v10 figures: N1 (new, Ch 1), R2 (Fig 4.4), R3 (Fig 4.11), R4 (Fig 3.2), N3 (Fig 5.6).

Rules: short labels, legends instead of repeated words, generous spacing, no middle dots.
Provenance notes (real frames, illustrative scores) live in the LaTeX captions.
"""
import json, pathlib
import numpy as np
from lib import Fig, CLS, CLS_NAME, ST, INK, MUTED, LINE, CUE_BOX, CUE_IMG, ROI, yolo_frac

ASSETS = pathlib.Path(__file__).resolve().parent / "assets"
YAWN_LBL = {4: yolo_frac(0.460250, 0.704328, 0.128312, 0.106000)}
ORDER = ["yawn", "hand", "drink", "phone"]
TIER = {"T1": "#e2ae3c", "T2": "#d9822b", "T3": "#c4453c"}
TIER_FILL = {"T1": "#fcf3df", "T2": "#fbeadb", "T3": "#fbe5e2"}


def class_legend(f, x, y, keys, size=15, gap=30):
    cx = x
    for k in keys:
        f.rect(cx, y + 3, 16, 16, CLS[k], radius=4)
        f.text(cx + 22, y, CLS_NAME[k], size=size)
        cx += 22 + 7.6 * len(CLS_NAME[k]) + gap
    return cx


def swatch(f, x, y, color, label, size=15, opacity=1.0, stroke=None):
    f.rect(x, y + 3, 16, 16, color, radius=4, opacity=opacity, stroke=stroke, sw=1.4)
    f.text(x + 22, y, label, size=size)
    return x + 22 + 7.6 * len(label) + 30


def deck(f, x, y, size, key, n=2, off=6, border="#5a54a6"):
    for j in reversed(range(n)):
        f.thumb(x + j * off, y - j * off, size, size, f"feat_{key}_{j}.png", border=border, bw=1.4, radius=4, fit="fill")


# ======================================================================================
def n1():
    """New Ch 1 figure: the product in one view."""
    f = Fig(1100, 396)
    cols = [(10, 180, "In the car"), (218, 140, "It sees"), (386, 220, "It detects"),
            (634, 160, "It responds"), (822, 120, "It sends"), (970, 120, "You get")]
    for x, w, s in cols:
        f.header(x + w / 2, 6, s, w + 20)
    T = 52
    # in the car
    f.thumb(10, T, 180, 135, "cabin.jpg", posx=62, posy=42)
    for j, (src, lab, fit) in enumerate([("camera.jpg", "Camera", "cover"), ("edge_unit.jpg", "Pi 5", "contain"),
                                         ("lightbar.jpg", "Light bar", "contain")]):
        x = 10 + j * 64
        f.thumb(x, T + 150, 52, 52, src, fit=fit, bg="#fff")
        f.text(x + 26, T + 208, lab, size=14, color=MUTED, align="center")
    # what it sees
    f.thumb(218, T, 140, 187, "pilot_pilot_dash_view.jpg", posy=45)
    # what it detects: four cues, colour = class (legend below)
    for j, k in enumerate(ORDER):
        x, y = 386 + (j % 2) * 115, T + (j // 2) * 115
        f.thumb(x, y, 105, 105, CUE_IMG[k], border=CLS[k], bw=2.8)
        f.bbox(x, y, 105, 105, CUE_BOX[k], CLS[k], bw=2.6)
    # how it responds
    rows = [("T1", "lightbar_rgb.jpg", 30, "Chime +\nlight"), ("T2", "speaker.jpg", 46, "Spoken\nreason"), ("T3", "lightbar_rgb.jpg", 30, "Alarm +\nfull light")]
    for j, (t, src, w, s) in enumerate(rows):
        y = T + j * 78
        f.pill(634, y + 16, 40, 26, t, TIER[t])
        f.thumb(684 + (46 - w) / 2, y, w, 58, src, border=TIER[t], bw=2.2)
        f.text(740, y + 10, s, size=15)
        if j < 2:
            f.arrow([(654, y + 46), (654, y + 90)], color=TIER["T" + str(j + 2)], width=1.8)
    # what it sends
    f.panel(822, T, 120, 140, "srv", radius=10, fill="#ffffff")
    f.text(882, T + 10, "Event", size=15, bold=True, color=ST["srv"][0], align="center")
    for j, a in enumerate(["class", "tier", "duration", "time"]):
        f.text(838, T + 38 + j * 24, a, size=14, color=MUTED, cls="mono")
    f.thumb(822, T + 158, 46, 46, "camera.jpg")
    f.poly([(824, T + 202), (866, T + 160)], "#c4453c", width=3.2)
    f.text(876, T + 170, "No video", size=15, bold=True, color="#c4453c")
    # what you get
    f.thumb(970, T, 120, 78, "ui_dashboard.jpg", border=ST["srv"][0])
    f.text(1030, T + 88, "Trends and\npost-trip tips", size=14, color=MUTED, w=130, align="center")
    # arrows between columns
    for x0, x1 in [(192, 214), (360, 382), (608, 630), (796, 818), (944, 966)]:
        f.arrow([(x0, T + 68), (x1, T + 68)])
    # legend + bands
    f.text(10, 300, "Detects:", size=15, bold=True)
    class_legend(f, 82, 300, ORDER + ["eyes"], size=15, gap=24)
    f.panel(10, 350, 784, 34, "veh", radius=9)
    f.text(402, 357, "In the car, live on the Raspberry Pi", size=15, bold=True, color=ST["veh"][0], align="center")
    f.panel(822, 350, 268, 34, "srv", radius=9)
    f.text(956, 357, "After the trip", size=15, bold=True, color=ST["srv"][0], align="center")
    return f


# ======================================================================================
def r2():
    """Fig 4.4: the per-frame loop, with one yawn worked through underneath."""
    f = Fig(1100, 640)
    fps, tau, theta, confirm = 10, 0.6, 0.5, 1.0                # yawning settings (Table 4.15)
    N, cue0 = 36, 15
    rng = np.random.default_rng(7)                              # same data as v9's frames_grid.py
    x = np.clip(0.06 + 0.03 * rng.standard_normal(N), 0, 1)
    x[4], x[8] = 0.92, 0.88
    x[cue0:] = np.clip(0.86 + 0.04 * rng.standard_normal(N - cue0), 0, 1)
    a = 1 - np.exp(-(1 / fps) / tau)
    s = np.zeros(N); p = 0.0
    for i in range(N):
        p = a * x[i] + (1 - a) * p; s[i] = p
    above = s > theta
    cross = int(np.argmax(above)); alert = cross + int(round(confirm * fps))

    W, G, X0, TY, BY = 118, 12, 36, 8, 96
    st = [("Frame", "1080p", "veh"), ("Blind check", "light, focus", "veh"), ("Crop", "400×400 RoI", "veh"),
          ("YOLO11n", "4 class scores", "det"), ("EMA", "τ = 0.6 s", "veh"), ("Above θ?", "θ = 0.50", "dec"),
          ("Held?", "1.0 s", "dec"), ("Alert", "tier, log", "alert")]
    xs = [X0 + i * (W + G) for i in range(8)]
    for i, (a1, a2, sk) in enumerate(st):
        f.box(xs[i], BY, W, 48, f"<div><b>{a1}</b></div><div style='font-size:13.5px;color:{MUTED}'>{a2}</div>", sk, raw=True, size=15)
        if i < 7:
            f.arrow([(xs[i] + W + 1, BY + 24), (xs[i + 1] - 3, BY + 24)])
    TH = 80
    f.thumb(xs[0], TY, W, TH, "yawn_seq_04.jpg", border=ST["veh"][0])
    f.thumb(xs[1], TY, W, TH, "yawn_seq_04.jpg", border=ST["veh"][0])
    for j, v in enumerate([0.62, 0.78]):
        f.rect(xs[1] + 10, TY + 48 + j * 14, 70, 9, "#ffffffcc", radius=3)
        f.rect(xs[1] + 10, TY + 48 + j * 14, 70 * v, 9, ST["ok"][0], radius=3)
    f.thumb(xs[2], TY, W, TH, "yawn_seq_04.jpg", border=ST["veh"][0])
    f.bbox(xs[2], TY, W, TH, ROI, "#ffffff", bw=2.2)
    f.thumb(xs[3] + (W - TH) / 2, TY, TH, TH, "yawn_seq_04.jpg", crop=ROI, border=ST["det"][0])
    f.bbox(xs[3] + (W - TH) / 2, TY, TH, TH, YAWN_LBL[4], CLS["yawn"], crop=ROI)

    def mini(xo, kind):
        f.rect(xo, TY, W, TH, "#ffffff", radius=7, stroke="#cfd6de", sw=1.6)
        px = lambda i: xo + 7 + i * (W - 14) / (N - 1)
        py = lambda v: TY + TH - 8 - (TH - 18) * v
        if kind == "ema":
            for i in range(N):
                f.rect(px(i) - 1.1, py(x[i]), 2.2, TY + TH - 8 - py(x[i]), CLS["yawn"], radius=0, opacity=0.3)
        if kind in ("cut", "hold"):
            f.poly([(xo + 5, py(theta)), (xo + W - 5, py(theta))], "#c4453c", width=1.2, dashed=True)
        f.poly([(px(i), py(s[i])) for i in range(N)], CLS["yawn"], width=2.4)
        if kind == "cut":
            f.rect(px(cross) - 4, py(s[cross]) - 4, 8, 8, "#c4453c", radius=4)
        if kind == "hold":
            f.rect(px(cross), TY + TH - 5, px(alert) - px(cross), 4, "#e2ae3c", radius=2)
            f.rect(px(alert) - 4, py(s[alert]) - 4, 8, 8, "#c4453c", radius=4)
    mini(xs[4], "ema"); mini(xs[5], "cut"); mini(xs[6], "hold")
    f.thumb(xs[7] + 8, TY, 36, TH, "lightbar_rgb.jpg", border=ST["alert"][0])
    f.thumb(xs[7] + 50, TY + 10, 60, 60, "speaker.jpg", border=ST["alert"][0])
    f.arrow([(xs[7] + W / 2, BY + 50), (xs[7] + W / 2, BY + 64), (xs[0] + W / 2, BY + 64), (xs[0] + W / 2, BY + 52)], color=LINE, width=1.5)
    f.text(550, BY + 68, "next frame", size=14, color=MUTED, align="center")

    # ---------------- worked example
    PY = 192
    f.panel(8, PY, 1084, 438, "pre", radius=14, fill="#fafbfc")
    f.text(24, PY + 10, "WORKED EXAMPLE: ONE YAWN", size=15, bold=True, color=ST["pre"][0])
    CW, LX = 26, 132
    cx = lambda i: LX + i * CW
    FY = PY + 44
    for j, k in enumerate(range(0, N - 5, 5)):
        seq = j if k < cue0 else 3 + (j - 3)
        f.thumb(cx(k) + 2, FY, 5 * CW - 4, 100, f"yawn_seq_{seq:02d}.jpg", border=CLS["yawn"] if k >= cue0 else "#c9d0d7", bw=2.4)
    f.text(LX - 14, FY + 40, "Frames", size=15, bold=True, align="right")
    rows = {"x": FY + 132, "s": FY + 180, "a": FY + 236}
    RH = 28
    for r, lab in {"x": "Raw score", "s": "Smoothed", "a": "Above θ"}.items():
        f.text(LX - 14, rows[r] + 5, lab, size=15, bold=True, align="right")
    for i in range(N):
        f.rect(cx(i) + 1, rows["x"], CW - 2, RH, "#eef1f4", radius=3)
        f.rect(cx(i) + 1, rows["x"], CW - 2, RH, CLS["yawn"], radius=3, opacity=round(float(x[i]), 2))
        f.rect(cx(i) + 1, rows["s"], CW - 2, RH, "#eef1f4", radius=3)
        f.rect(cx(i) + 1, rows["s"], CW - 2, RH, CLS["yawn"], radius=3, opacity=round(float(s[i]), 2))
        col = ("#c4453c" if i == alert else ("#e2ae3c" if i < alert else "#f2d9a0")) if above[i] else "#eef1f4"
        f.rect(cx(i) + 1, rows["a"], CW - 2, RH, col, radius=3)
    f.text(cx(alert) + CW / 2, rows["a"] + 4, "!", size=16, bold=True, color="#fff", align="center")
    f.poly([(cx(4) + CW / 2, rows["x"] - 4), (cx(6) + CW / 2, rows["x"] - 13), (cx(8) + CW / 2, rows["x"] - 4)], MUTED, width=1.2)
    f.text(cx(6) + CW / 2, rows["x"] - 32, "spikes ignored", size=14, color=MUTED, align="center")
    yb = rows["a"] + RH + 5
    f.poly([(cx(cross), yb), (cx(cross), yb + 7), (cx(alert), yb + 7), (cx(alert), yb)], "#b98a1e", width=1.6)
    f.text((cx(cross) + cx(alert)) / 2, yb + 10, "held 1.0 s", size=14, color="#8a6a17", align="center")
    ya = rows["a"] + RH + 52
    f.poly([(LX, ya), (cx(N), ya)], LINE, width=1.2)
    for t in range(0, N + 1, 5):
        f.poly([(cx(t), ya), (cx(t), ya + 5)], LINE, width=1.2)
        f.text(cx(t), ya + 8, f"{t / 10:.1f} s", size=13.5, color=MUTED, align="center")
    ky = ya + 40
    kx = LX
    f.text(kx, ky, "Score", size=15, color=MUTED)
    for j, v in enumerate([0.15, 0.45, 0.75, 1.0]):
        f.rect(kx + 50 + j * 20, ky + 3, 16, 16, CLS["yawn"], radius=4, opacity=v)
    f.text(kx + 134, ky, "0 to 1", size=15, color=MUTED)
    kx += 220
    kx = swatch(f, kx, ky, "#e2ae3c", "timer running")
    kx = swatch(f, kx, ky, "#c4453c", "alert")
    swatch(f, kx, ky, "#f2d9a0", "cue still on, alert already raised")
    return f


# ======================================================================================
def r3():
    """Fig 4.11: the alert state machine as a tier ladder."""
    f = Fig(1100, 466)
    CW, CH, Y = 168, 196, 84
    xs = [14, 240, 466, 692, 918]
    heads = [("Idle", "pre"), ("Candidate", "dec"), ("Tier 1", "T1"), ("Tier 2", "T2"), ("Tier 3", "T3")]
    caps = ["all scores below θ", "timer running", "chime + light pulse", "spoken reason", "alarm + full light"]
    for x, (h, k), c in zip(xs, heads, caps):
        col = TIER.get(k) or ST[k][0]
        fill = TIER_FILL.get(k) or ST[k][1]
        f.panel(x, Y, CW, CH, col, radius=14, fill=fill)
        f.el[-1] = f.el[-1].replace("border-color:", "border-width:2px;border-color:")
        f.text(x + CW / 2, Y + 10, h, size=17, bold=True, color=col, align="center")
        f.text(x + CW / 2, Y + 162, c, size=14.5, color=MUTED, align="center")
    TT = Y + 42
    f.thumb(xs[0] + 14, TT, 140, 108, "cue_negative.jpg", border=CLS["none"])
    f.thumb(xs[1] + 14, TT + 4, 100, 100, "yawn_seq_04.jpg", crop=ROI, border=CLS["yawn"])
    f.bbox(xs[1] + 14, TT + 4, 100, 100, YAWN_LBL[4], CLS["yawn"], crop=ROI)
    f.rect(xs[1] + 124, TT + 4, 30, 100, "#ffffff", radius=6, stroke="#e2d2a8", sw=1)
    f.rect(xs[1] + 131, TT + 44, 16, 56, "#e2ae3c", radius=3)
    for i, t in ((2, "T1"), (4, "T3")):
        f.thumb(xs[i] + 14, TT, 50, 108, "lightbar_rgb.jpg", border=TIER[t])
        f.thumb(xs[i] + 72, TT + 20, 82, 68, "speaker.jpg", border=TIER[t])
    f.thumb(xs[3] + 10, TT + 10, 148, 88, "ui_tablet_dark.jpg", border=TIER["T2"])
    # forward transitions
    lab = ["s > θ", "held for\nconfirm\ntime", "5 s, or\n3 cues\nin 5 min", "10 s"]
    for i in range(4):
        x0, x1 = xs[i] + CW + 3, xs[i + 1] - 5
        f.arrow([(x0, Y + 64), (x1, Y + 64)], width=2.2, color=INK)
        f.text((x0 + x1) / 2, Y + 74, lab[i], size=13.5, w=60, align="center")
    f.arrow([(xs[1] - 5, Y + 160), (xs[0] + CW + 5, Y + 160)], width=1.6, color=LINE)
    f.text((xs[0] + CW + xs[1]) / 2, Y + 166, "below θ", size=13.5, color=MUTED, align="center")
    # eyes-closed shortcut
    f.curve(f"M{xs[0] + CW / 2},{Y - 2} C{xs[0] + CW / 2},{Y - 54} {xs[4] + CW / 2},{Y - 54} {xs[4] + CW / 2},{Y - 4}", color=CLS["eyes"], width=2.2)
    f.text(550, 2, "eyes closed 1.5 s (3 s head down)", size=15, bold=True, color=CLS["eyes"], align="center")
    # cool-down
    CY = Y + CH + 46
    f.panel(xs[2], CY, xs[4] + CW - xs[2], 52, "pre", radius=12)
    f.text(xs[2] + 16, CY + 15, "Cool-down 30 s: new cues are logged, with no sound", size=15, color=INK)
    for i in (2, 3, 4):
        f.arrow([(xs[i] + CW / 2, Y + CH + 3), (xs[i] + CW / 2, CY - 4)], color=LINE, width=1.6)
    f.text(xs[3] + CW / 2 + 10, Y + CH + 13, "cue ends", size=13.5, color=MUTED)
    f.arrow([(xs[2] - 3, CY + 26), (xs[0] + CW / 2, CY + 26), (xs[0] + CW / 2, Y + CH + 5)], color=LINE, width=1.6)
    f.text((xs[0] + CW / 2 + xs[2]) / 2, CY + 32, "after 30 s", size=13.5, color=MUTED, align="center")
    # blocked camera
    BYY = CY + 76
    f.panel(xs[0], BYY, 670, 46, "alert", radius=12)
    f.rect(xs[0] + 10, BYY + 8, 44, 30, "#1e242b", radius=5)
    f.text(xs[0] + 32, BYY + 12, "✕", size=15, bold=True, color="#fff", align="center")
    f.text(xs[0] + 66, BYY + 13, "Camera blocked for 3 s, in any state: voice prompt, pause, EMA reset", size=15, color=ST["alert"][0])
    f.text(1086, BYY + 13, "Times count from the θ crossing.", size=13.5, color=MUTED, italic=True, align="right")
    return f


# ======================================================================================
def r4():
    """Fig 3.2: YOLO11n with its real activations on the report's phone frame."""
    f = Fig(1100, 356)
    det = json.load(open(ASSETS / "yolo_det.json"))["detections"][0]
    box = tuple(det["box"])
    for cx, s in [(71, "Input"), (370, "Backbone"), (659, "Neck"), (808, "Heads"), (944, "NMS"), (1054, "Output")]:
        f.header(cx, 6, s, 140)
    # input
    f.thumb(6, 76, 130, 130, "cue_phone.jpg", border=CLS["none"])
    f.text(71, 214, "640×640", size=14.5, color=MUTED, align="center")
    f.arrow([(138, 141), (160, 141)])
    # backbone
    f.panel(164, 44, 412, 250, "veh", radius=14)
    stages = [("b320", 76, "320"), ("b160", 66, "160"), ("b80", 56, "80"), ("b40", 48, "40"), ("b20", 40, "20")]
    x, cy = 178, 140
    for j, (k, sz, a1) in enumerate(stages):
        deck(f, x, cy - sz / 2 + 4, sz, k, n=2, off=6, border=ST["veh"][0])
        f.text(x + sz / 2 + 3, 206, f"{a1}×{a1}", size=14.5, bold=True, align="center")
        if j < 4:
            f.arrow([(x + sz + 9, cy), (x + sz + 21, cy)], width=1.5)
        x += sz + 24
    f.text(370, 252, "smaller maps, richer features", size=14.5, color=ST["veh"][0], align="center")
    f.arrow([(578, 141), (598, 141)])
    # neck
    f.panel(602, 44, 114, 250, "ok", radius=14)
    f._marker(ST["ok"][0])
    f.svg_raw(f'<path d="M 614 80 L 614 214" stroke="{ST["ok"][0]}" stroke-width="1.6" fill="none" marker-end="url(#m2f8a5b)" marker-start="url(#m2f8a5b)"/>')
    for j, k in enumerate(["n80", "n40", "n20"]):
        y = 64 + j * 66
        deck(f, 628, y + 6, 44, k, n=2, off=5, border=ST["ok"][0])
        f.arrow([(718, y + 26), (738, y + 26)], width=1.5)
    f.text(659, 252, "mixes scales", size=14.5, color=ST["ok"][0], align="center")
    # heads
    for j, (n, a1, a2) in enumerate([(16, "80×80", "small"), (8, "40×40", "medium"), (4, "20×20", "large")]):
        y = 64 + j * 66
        f.thumb(742, y, 52, 52, "cue_phone.jpg", border=ST["det"][0], bw=2)
        f.grid(742, y, 52, 52, n, color="#ffffffcc", bw=2)
        f.text(802, y + 6, a1, size=14, bold=True)
        f.text(802, y + 26, a2, size=13.5, color=MUTED)
        f.arrow([(872, y + 26), (898, 141)], width=1.3)
    f.text(808, 270, "box, class, score\nper cell", size=14.5, color=ST["det"][0], w=150, align="center")
    # NMS
    f.thumb(902, 98, 84, 84, "cue_phone.jpg", border=CLS["none"])
    x0, y0, x1, y1 = box
    for dx, dy, dw in [(-0.03, -0.02, 0.05), (0.02, 0.03, -0.03), (0.0, -0.04, 0.02), (0.04, 0.0, 0.04)]:
        f.bbox(902, 98, 84, 84, (max(0, x0 + dx), y0 + dy, x1 + dx + dw, y1 + dy + dw), "#7a4cb099", bw=2)
    f.bbox(902, 98, 84, 84, box, CLS["phone"], bw=2)
    f.text(944, 192, "keep the best", size=14.5, color=MUTED, align="center")
    f.arrow([(988, 141), (1008, 141)])
    # output
    f.thumb(1012, 98, 84, 84, "cue_phone.jpg", border=CLS["phone"], bw=2.4)
    f.bbox(1012, 98, 84, 84, box, CLS["phone"], bw=2.4)
    f.tag(1016, 102, f"phone {det['score']:.2f}", CLS["phone"])
    f.text(6, 326, "Feature maps and output are real, from our trained YOLO11n on this frame.", size=14, color=MUTED, italic=True)
    return f


# ======================================================================================
def n3():
    """Fig 5.6: from a recording to labelled frames (a) and the subject-disjoint folds (b)."""
    f = Fig(1100, 480)
    f.panel(8, 8, 1084, 222, "pre", label="(a) FROM RECORDING TO LABELS", fill="#fafbfc")
    T = 74
    cols = [(26, 128, "Record", "1080p, 30 FPS"), (206, 176, "Sample", "5 FPS"), (432, 166, "Label", "4 classes"),
            (648, 120, "Check", "2 annotators"), (818, 196, "Hard negatives", "labelled negative")]
    for x, w, h, c in cols:
        f.header(x + w / 2, 38, h, w + 40)
        f.text(x + w / 2, T + 116, c, size=14.5, color=MUTED, align="center")
    for j, g in enumerate([1, 2, 4]):
        f.thumb(26 + j * 18, T + j * 6, 92, 92, f"guide_{g}.jpg", border=ST["pre"][0])
    for j, src in enumerate(["pilot_grid_3.jpg", "pilot_grid_1.jpg", "pilot_grid_4.jpg", "pilot_grid_2.jpg"]):
        f.thumb(206 + j * 45, T, 41, 104, src, border="#c9d0d7", bw=1.6, radius=5)
    for j, k in enumerate(ORDER):
        x, y = 432 + (j % 2) * 86, T + (j // 2) * 54
        f.thumb(x, y, 80, 50, CUE_IMG[k], border=CLS[k], bw=2.2, posy=55)
    f.thumb(658, T, 100, 100, "cue_drink.jpg", border=ST["veh"][0])
    bx = CUE_BOX["drink"]
    f.bbox(658, T, 100, 100, bx, "#3d6fa8", bw=2.4)
    f.bbox(658, T, 100, 100, (bx[0] + 0.03, bx[1] + 0.02, bx[2] + 0.02, bx[3] + 0.04), "#d0661e", bw=2.4)
    f.thumb(818, T, 94, 104, "guide_5.jpg", border=CLS["none"])
    f.thumb(920, T, 94, 104, "cue_negative.jpg", border=CLS["none"])
    for x0, x1 in [(160, 200), (388, 426), (604, 642), (774, 812)]:
        f.arrow([(x0, T + 52), (x1, T + 52)])
    # (b) folds
    PY = 244
    f.panel(8, PY, 1084, 228, "veh", label="(b) SUBJECT-DISJOINT FOLDS", fill="#f6f9fd")
    f.thumb(30, PY + 50, 110, 110, "dmd_mosaic.jpg", border=ST["pre"][0])
    f.text(85, PY + 168, "pre-train: DMD", size=14.5, color=MUTED, align="center")
    f.arrow([(146, PY + 105), (186, PY + 105)])
    cols_ = {"Test": ("#c4453c", "#fbe5e2"), "Val": ("#b98a1e", "#fbf3df"), "Train": ("#3d6fa8", "#e8eff8")}
    SX, P = 290, 124
    for si in range(4):
        f.el.append(f'<div class="pill" style="left:{SX + si * P + 50 - 21}px;top:{PY + 40}px;width:42px;height:30px;background:#5f6b78;font-size:14px;">S0{si + 1}</div>')
    for fo in range(4):
        y = PY + 84 + fo * 34
        f.text(SX - 14, y + 3, f"Fold {fo + 1}", size=15, bold=True, align="right")
        for si in range(4):
            lab = "Test" if si == fo else ("Val" if si == (fo + 1) % 4 else "Train")
            sc, fc = cols_[lab]
            f.rect(SX + si * P, y, 100, 24, fc, radius=6, stroke=sc, sw=1.8)
    lx = 820
    for j, lab in enumerate(["Test", "Val", "Train"]):
        sc, fc = cols_[lab]
        f.rect(lx, PY + 88 + j * 30, 30, 20, fc, radius=5, stroke=sc, sw=1.8)
        f.text(lx + 40, PY + 88 + j * 30, lab, size=15)
    f.text(lx, PY + 184, "Each subject is tested once,\nby a model that never saw them.", size=15, bold=True)
    return f


FIGS = {"n1": n1, "r2": r2, "r3": r3, "r4": r4, "n3": n3}
