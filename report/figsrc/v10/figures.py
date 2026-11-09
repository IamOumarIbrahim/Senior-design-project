"""The v10 overview figures. Each function returns a lib.Fig; render.py prints them."""
import numpy as np
from lib import Fig, CLS, CLS_NAME, ST, INK, MUTED, LINE, CUE_BOX, CUE_IMG, ROI, yolo_frac

# real labels of the yawn sequence (DMD subject_09 video_04, frames 110-120 -> yawn_seq_00..10)
YAWN_LBL = {4: yolo_frac(0.460250, 0.704328, 0.128312, 0.106000), 6: yolo_frac(0.465133, 0.675023, 0.126922, 0.125516)}
ORDER = ["yawn", "hand", "drink", "phone"]
TIER = {"T1": "#e2ae3c", "T2": "#d9822b", "T3": "#c4453c"}


def score_chips(f, x, y, scores, size=17, gap=4):
    for i, (k, s) in enumerate(zip(ORDER, scores)):
        f.rect(x + i * (size + gap), y, size, size, "#e9edf1", radius=3)
        f.rect(x + i * (size + gap), y, size, size, CLS[k], radius=3, opacity=round(0.12 + 0.88 * s, 2))


def dashed_key(f, x, y):
    f.el.append('<div class="chip dash" style="left:%dpx;top:%dpx;width:30px;height:16px;border:1.6px dashed %s;border-radius:4px;"></div>' % (x, y, INK))


def num(f, x, y, s, color):
    """Small numbered/lettered circle like the reference's step markers."""
    f.el.append(f'<div class="pill" style="left:{x - 11}px;top:{y - 11}px;width:22px;height:22px;background:{color};font-size:13px;">{s}</div>')


# ======================================================================================
def r1():
    """Fig 4.2 replacement: the whole system, left to right."""
    f = Fig(1180, 660)
    # ---------------- before deployment band
    f.panel(8, 8, 660, 92, "pre", label="BEFORE DEPLOYMENT")
    f.thumb(22, 30, 62, 62, "dmd_mosaic.jpg", border=ST["pre"][0])
    f.text(92, 38, "Subject-disjoint\nin-cabin clips", size=14.5)
    f.thumb(244, 30, 62, 62, "cue_negative.jpg", border=ST["pre"][0])
    f.thumb(312, 30, 62, 62, "pilot_lesson_c.jpg", border=ST["pre"][0], posy=35)
    f.text(382, 38, "Hard\nnegatives", size=14.5)
    f.box(476, 30, 108, 62, "Fine-tune,\nprune, INT8", "pre", size=14.5)
    f.box(602, 40, 56, 32, "<b>.hef</b>", "det", size=14.5, raw=True)
    f.arrow([(204, 61), (238, 61)]); f.arrow([(452, 61), (472, 61)]); f.arrow([(584, 56), (598, 56)])
    f.arrow([(630, 72), (630, 146)], color=ST["det"][0])

    # ---------------- column headers
    for cx, s in [(88, "Cabin"), (262, "Camera frames"), (526, "Detector"), (729, "Smoothing"),
                  (885, "Decision"), (1080, "Outputs")]:
        f.header(cx, 112, s, 190)

    ys = [172, 284, 396]                      # frame rows (100 px tall)
    cy = [y + 50 for y in ys]
    # ---------------- cabin
    f.thumb(10, 160, 158, 118, "cabin.jpg", posx=60, posy=40)
    f.text(89, 282, "Camera above the\nsteering column", size=13.5, color=MUTED, w=160, align="center")
    f.thumb(42, 330, 94, 126, "pilot_pilot_dash_view.jpg", posy=40)
    f.text(89, 460, "Real dash view\n(pilot session C3)", size=13.5, color=MUTED, w=160, align="center")
    f.arrow([(168, 222), (206, 222)])

    # ---------------- camera frames: one real yawn from DMD
    fr = [(0, "none", "t"), (4, "yawn", "t + 4 s"), (6, "yawn", "t + 6 s")]
    for (i, k, lab), y in zip(fr, ys):
        f.thumb(212, y, 100, 100, f"yawn_seq_{i:02d}.jpg", border=CLS[k], bw=2.6)
        f.tag(216, y + 79, lab, "#27313cb0")
    f.text(262, 502, "1080p at 30 FPS", size=13.5, color=MUTED, w=170, align="center")

    # ---------------- pre-process bar (the reference's shared-encoder bar)
    f.panel(334, 172, 44, 324, "veh", radius=12)
    f.vtext(356, 334, "Crop 400×400 RoI | blind check", size=15, color=ST["veh"][0])
    for c in cy:
        f.arrow([(314, c), (330, c)])

    # ---------------- detector panel: crop -> per-class scores
    f.panel(398, 140, 262, 360, "det", radius=14)
    f.thumb(406, 146, 46, 40, "edge_unit.jpg", border="#ffffff00", bw=0, fit="contain", bg="#00000000")
    f.text(458, 146, "YOLO11n", size=16, bold=True, color=ST["det"][0])
    f.text(458, 166, "on the AI HAT+ NPU, INT8", size=13.5, color=MUTED)
    scores = [[0.05, 0.04, 0.02, 0.03], [0.86, 0.10, 0.03, 0.02], [0.91, 0.12, 0.02, 0.03]]
    for (i, k, _), c, sc in zip(fr, cy, scores):
        y = c - 35
        f.thumb(410, y, 70, 70, f"yawn_seq_{i:02d}.jpg", crop=ROI, border="#cfd3ea")
        if i in YAWN_LBL:
            f.bbox(410, y, 70, 70, YAWN_LBL[i], CLS["yawn"], crop=ROI, bw=2.2)
        f.arrow([(484, c), (500, c)], width=1.6)
        score_chips(f, 506, c - 13, sc)
        best = max(range(4), key=lambda j: sc[j])
        f.text(506, c + 9, f"max {sc[best]:.2f}" + (" yawn" if sc[best] > 0.5 else ""), size=12.5, color=MUTED)
        f.arrow([(378, c), (406, c)], width=1.6)
        f.arrow([(600, c), (676, c)], width=1.6)
    f.text(529, 478, "box + score for 4 classes", size=13, color=MUTED, align="center")

    # ---------------- smoothing: per-class EMA
    f.panel(680, 140, 98, 360, "veh", radius=14)
    f.text(729, 148, "EMA per class", size=14, bold=True, color=ST["veh"][0], align="center")
    taus = {"yawn": 0.6, "hand": 0.6, "drink": 1.0, "phone": 1.0}
    rng = np.random.default_rng(3)
    for j, k in enumerate(ORDER):
        y0 = 174 + j * 80
        f.rect(689, y0, 80, 52, "#ffffff", radius=6, stroke="#cfdbe9", sw=1)
        n = 30
        x = np.clip(0.06 + 0.03 * rng.standard_normal(n), 0, 1)
        if k == "yawn":
            x[12:] = 0.88
        if k in ("hand", "drink"):
            x[5] = 0.8
        a = 1 - np.exp(-(1 / 10) / taus[k] * 3)
        s_ = np.zeros(n); p = 0
        for i in range(n):
            p = a * x[i] + (1 - a) * p; s_[i] = p
        f.poly([(691, y0 + 27), (767, y0 + 27)], "#c4453c", width=1, dashed=True)
        f.poly([(691 + i * 76 / (n - 1), y0 + 48 - 42 * s_[i]) for i in range(n)], CLS[k], width=2.2)
        f.text(729, y0 + 55, f"τ = {taus[k]} s", size=12.5, color=MUTED, align="center")

    # ---------------- decision
    f.panel(798, 196, 174, 228, "dec", radius=14)
    f.text(885, 205, "Decision", size=16, bold=True, color=ST["dec"][0], align="center")
    for j, s_ in enumerate(["above cutoff θ?", "held for confirm time?", "then cool-down 30 s", "escalate while it lasts"]):
        f.text(812, 233 + j * 23, "› " + s_, size=14)
    for j, s_ in enumerate(["T1", "T2", "T3"]):
        f.pill(818 + j * 46, 330, 40, 25, s_, TIER[s_])
    f.text(885, 362, "chime → voice → alarm", size=13, color=MUTED, align="center")
    f.text(885, 382, "eyes closed 1.5 s → T3", size=13, color=CLS["eyes"], align="center")
    f.arrow([(778, 310), (794, 310)])
    f.thumb(830, 444, 110, 64, "ui_tablet_cal.jpg", border=ST["veh"][0], dashed=True)
    f.text(885, 510, "per-driver cutoffs", size=13, color=MUTED, align="center")
    f.arrow([(885, 442), (885, 428)], dashed=True, color=ST["veh"][0])

    # ---------------- outputs
    outs = [("lightbar_rgb.jpg", 160, 76, 40, "Light bar", "colour per\nclass"),
            ("speaker.jpg", 254, 64, 64, "Speaker", "chime, then\nvoice EN / AR"),
            ("ui_tablet_dark.jpg", 340, 52, 84, "Display", "explained\nmessage")]
    for src, y, h, w, a1, a2 in outs:
        f.thumb(994 + (84 - w) / 2, y, w, h, src, border=ST["alert"][0], bw=2)
        f.text(1086, y + 2, a1, size=15, bold=True)
        f.text(1086, y + 22, a2, size=13.5, color=MUTED)
        f.arrow([(972, 310), (984, 310), (984, y + h / 2), (992 + (84 - w) / 2, y + h / 2)], width=1.8, color=ST["alert"][0])
    f.box(994, 416, 176, 46, "Event log (SQLite)\nevents only", "veh", size=14)
    f.arrow([(972, 310), (984, 310), (984, 439), (992, 439)], width=1.8)

    # ---------------- after the trip band
    f.panel(560, 536, 612, 116, "srv", label="AFTER THE TRIP")
    f.arrow([(1110, 462), (1110, 564)], color=ST["srv"][0])
    f.text(1102, 476, "no video,\nno images", size=13, color=ST["srv"][0], w=90, align="right")
    f.box(1004, 566, 158, 48, "TLS 1.3 upload\ndevice key, retry", "srv", size=14)
    f.box(812, 566, 160, 48, "Server\ndedupe by event ID", "srv", size=14)
    f.arrow([(1000, 590), (976, 590)], color=ST["srv"][0])
    f.thumb(620, 560, 140, 84, "ui_dashboard.jpg", border=ST["srv"][0])
    f.arrow([(808, 590), (764, 590)], color=ST["srv"][0])

    # ---------------- legend
    f.text(12, 546, "Class colours (= light-bar colours)", size=14, bold=True)
    for j, k in enumerate(ORDER + ["eyes"]):
        cx_, cy_ = 12 + (j % 3) * 172, 570 + (j // 3) * 22
        f.rect(cx_, cy_ + 2, 14, 14, CLS[k], radius=3)
        f.text(cx_ + 20, cy_, CLS_NAME[k], size=14)
    f.rect(12, 624, 30, 16, "#fff", radius=4, stroke=INK, sw=1.6); f.text(48, 623, "Required", size=14)
    dashed_key(f, 130, 624); f.text(166, 623, "Desired", size=14)
    score_chips(f, 246, 624, [0.15, 0.45, 0.75, 1.0], size=15, gap=3)
    f.text(320, 623, "per-class score 0 → 1", size=14)
    return f


# ======================================================================================
def n1():
    """New Ch 1 figure: the product in one look, for a non-technical reader."""
    f = Fig(1180, 500)
    cols = [(110, "In the car"), (311, "What the\ncamera sees"), (525, "What it\nrecognises"),
            (775, "How it\nresponds"), (967, "What leaves\nthe car"), (1104, "What the\ndriver gets")]
    for cx, s in cols:
        f.text(cx, 6, s, size=18, bold=True, w=180, align="center", cls="hdr")
    T = 64
    # in the car
    f.thumb(10, T, 200, 150, "cabin.jpg", posx=62, posy=42)
    for j, (src, lab, fit) in enumerate([("camera.jpg", "Camera", "cover"), ("edge_unit.jpg", "Pi 5 +\nAI HAT+", "contain"),
                                         ("lightbar.jpg", "Light bar", "contain")]):
        x = 10 + j * 70
        f.thumb(x, T + 162, 60, 60, src, fit=fit, bg="#fff")
        f.text(x + 30, T + 226, lab, size=12.5, color=MUTED, w=70, align="center")
    f.text(110, T + 270, "+ speaker and 7-inch display", size=13, color=MUTED, align="center")
    # camera view
    f.thumb(236, T, 150, 200, "pilot_pilot_dash_view.jpg", posy=45)
    f.text(311, T + 206, "Real dash-mounted view\n(our pilot session C3)", size=13, color=MUTED, w=170, align="center")
    # what it recognises
    pos = {"yawn": (410, T), "hand": (530, T), "drink": (410, T + 120), "phone": (530, T + 120)}
    short = {"yawn": "yawn", "hand": "hand-mouth", "drink": "drink", "phone": "phone"}
    for k, (x, y) in pos.items():
        f.thumb(x, y, 112, 112, CUE_IMG[k], border=CLS[k], bw=2.6)
        f.bbox(x, y, 112, 112, CUE_BOX[k], CLS[k], label=short[k], bw=2.6)
    f.rect(410, T + 246, 16, 16, CLS["eyes"], radius=3)
    f.text(432, T + 244, "Eyes closed (from eye landmarks)", size=13.5)
    f.thumb(410, T + 274, 56, 56, "cue_negative.jpg", border=CLS["none"])
    f.text(474, T + 280, "Normal driving and\nlook-alikes stay silent", size=13.5, color=MUTED)
    # how it responds: three tiers
    rows = [("T1", "lightbar_rgb.jpg", 30, "Chime and a\nshort light pulse"),
            ("T2", "speaker.jpg", 50, "Adds a spoken\nreason"),
            ("T3", "lightbar_rgb.jpg", 30, "Alarm and the\nfull light pattern")]
    for j, (t, src, w, s) in enumerate(rows):
        y = T + j * 72
        f.pill(668, y + 16, 40, 26, t, TIER[t])
        f.thumb(714 + (50 - w) / 2, y, w, 58, src, border=TIER[t], bw=2.2)
        f.text(772, y + 8, s, size=13.5)
        if j < 2:
            f.arrow([(688, y + 44), (688, y + 86)], color=TIER["T" + str(j + 2)], width=1.8)
    f.text(668, T + 214, "if the cue continues", size=12.5, color=MUTED)
    f.thumb(668, T + 236, 206, 120, "ui_tablet_dark.jpg", border=TIER["T2"])
    f.text(771, T + 360, "The display explains the alert", size=13, color=MUTED, align="center")
    # what leaves the car
    f.panel(902, T, 132, 170, "srv", radius=10, fill="#ffffff")
    f.text(912, T + 8, "Event record", size=14, bold=True, color=ST["srv"][0])
    for j, (a, b) in enumerate([("class", "yawning"), ("tier", "2"), ("length", "4.1 s"), ("time", "21:42"), ("driver", "#2")]):
        f.text(912, T + 34 + j * 24, a, size=13.5, color=MUTED, cls="mono")
        f.text(972, T + 34 + j * 24, b, size=13.5, cls="mono")
    f.text(967, T + 176, "example values", size=12.5, color=MUTED, italic=True, align="center")
    f.thumb(906, T + 210, 50, 50, "camera.jpg")
    f.poly([(908, T + 256), (954, T + 212)], "#c4453c", width=3.2)
    f.text(962, T + 214, "No video,\nno images", size=13, bold=True, color="#c4453c")
    f.text(967, T + 282, "sent over TLS after\nthe trip", size=13, color=MUTED, w=140, align="center")
    # what the driver gets
    f.thumb(1046, T, 126, 82, "ui_dashboard.jpg", border=ST["srv"][0])
    f.text(1109, T + 86, "Trends and heatmap", size=13, color=MUTED, align="center")
    f.panel(1046, T + 116, 126, 150, "srv", radius=10, fill="#ffffff")
    f.text(1054, T + 122, "Post-trip tip", size=13.5, bold=True, color=ST["srv"][0])
    f.text(1054, T + 144, "Yawning rose after 90 min on 4 of 7 trips. Take a break around 90 minutes.", size=13, w=114)
    f.text(1109, T + 272, "dashboard sample data", size=12, color=MUTED, italic=True, align="center")
    # arrows between columns
    for x0, x1 in [(212, 232), (388, 406), (646, 664), (880, 898), (1036, 1044)]:
        f.arrow([(x0, T + 100), (x1, T + 100)])
    # bottom group bands, like the reference's group legend
    f.panel(10, 460, 870, 32, "veh", radius=9)
    f.text(445, 466, "In the car, in real time, on the Raspberry Pi", size=15, bold=True, color=ST["veh"][0], align="center")
    f.panel(902, 460, 270, 32, "srv", radius=9)
    f.text(1037, 466, "After the trip, on the server", size=15, bold=True, color=ST["srv"][0], align="center")
    return f


# ======================================================================================
def r2():
    """Fig 4.4 replacement: the per-frame loop, with the worked example under the steps that produce it."""
    f = Fig(1180, 708)
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

    # ---------------- stage cards
    W, G, X0, TY, BY = 128, 16, 12, 44, 140
    st = [("Grab frame", "1080p, Δt", "veh"), ("Blind check", "light, sharpness", "veh"),
          ("Crop", "400×400 RoI", "veh"), ("YOLO11n", "score per class", "det"),
          ("EMA", "τ = 0.6 s", "veh"), ("Above cutoff?", "θ = 0.50", "dec"),
          ("Held 1.0 s?", "confirm time", "dec"), ("Alert + log", "tier, cool-down", "alert")]
    xs = [X0 + i * (W + G) for i in range(8)]
    for i, (a1, a2, sk) in enumerate(st):
        f.box(xs[i], BY, W, 52, f"<div><b>{a1}</b></div><div style='font-size:13px;color:{MUTED}'>{a2}</div>", sk, raw=True, size=15)
        if i < 7:
            f.arrow([(xs[i] + W + 1, BY + 25), (xs[i + 1] - 3, BY + 25)])
    # thumbnails above each card (the "what it looks like" row)
    f.thumb(xs[0], TY, W, 88, "yawn_seq_04.jpg", border=ST["veh"][0])
    f.thumb(xs[1], TY, W, 88, "yawn_seq_04.jpg", border=ST["veh"][0])
    for j, (lab, v) in enumerate([("light", 0.62), ("sharp", 0.78)]):
        f.rect(xs[1] + 8, TY + 52 + j * 16, 56, 10, "#ffffffcc", radius=3)
        f.rect(xs[1] + 8, TY + 52 + j * 16, 56 * v, 10, ST["ok"][0], radius=3)
        f.tag(xs[1] + 70, TY + 49 + j * 16, lab, "#27313cb0")
    f.thumb(xs[2], TY, W, 88, "yawn_seq_04.jpg", border=ST["veh"][0])
    f.bbox(xs[2], TY, W, 88, ROI, "#ffffff", bw=2.2)
    f.thumb(xs[3] + 20, TY, 88, 88, "yawn_seq_04.jpg", crop=ROI, border=ST["det"][0])
    f.bbox(xs[3] + 20, TY, 88, 88, YAWN_LBL[4], CLS["yawn"], crop=ROI)
    f.tag(xs[3] + 24, TY + 5, "yawn 0.86", CLS["yawn"])
    # mini plots for EMA / cutoff / confirm
    def mini(xo, kind):
        f.rect(xo, TY, W, 88, "#ffffff", radius=7, stroke="#cfd6de", sw=1.6)
        px = lambda i: xo + 6 + i * (W - 12) / (N - 1)
        py = lambda v: TY + 80 - 70 * v
        if kind in ("ema",):
            for i in range(N):
                f.rect(px(i) - 1.2, py(x[i]), 2.4, TY + 80 - py(x[i]), CLS["yawn"], radius=0, opacity=0.35)
        if kind in ("cut", "hold"):
            f.poly([(xo + 4, py(theta)), (xo + W - 4, py(theta))], "#c4453c", width=1.2, dashed=True)
        f.poly([(px(i), py(s[i])) for i in range(N)], CLS["yawn"], width=2.4)
        if kind == "cut":
            f.rect(px(cross) - 4, py(s[cross]) - 4, 8, 8, "#c4453c", radius=4)
        if kind == "hold":
            f.rect(px(cross), TY + 82, px(alert) - px(cross), 5, "#e2ae3c", radius=2)
            f.rect(px(alert) - 4, py(s[alert]) - 4, 8, 8, "#c4453c", radius=4)
    mini(xs[4], "ema"); mini(xs[5], "cut"); mini(xs[6], "hold")
    f.thumb(xs[7], TY, 40, 88, "lightbar_rgb.jpg", border=ST["alert"][0])
    f.thumb(xs[7] + 44, TY, 84, 42, "speaker.jpg", border=ST["alert"][0])
    f.thumb(xs[7] + 44, TY + 46, 84, 42, "ui_tablet_dark.jpg", border=ST["alert"][0])
    # loop back + blocked branch
    f.arrow([(xs[7] + W / 2, BY + 52), (xs[7] + W / 2, BY + 66), (xs[0] + W / 2, BY + 66), (xs[0] + W / 2, BY + 54)], color=LINE, width=1.6)
    f.text(590, BY + 68, "next frame (also when a check says no)", size=13, color=MUTED, align="center")
    f.text(xs[1] + W / 2, 8, "view blocked 3 s → voice prompt, pause", size=13, color=ST["alert"][0], align="center")
    f.arrow([(xs[1] + W / 2, TY - 2), (xs[1] + W / 2, 26)], color=ST["alert"][0], width=1.4, dashed=True, head=False)
    # step letters on the stages that produce each row below
    for xi, L in [(4, "A"), (5, "B"), (6, "C"), (7, "D")]:
        num(f, xs[xi] + W - 6, TY + 4, L, "#b98a1e")

    # ---------------- worked example
    PY = 232
    f.panel(8, PY, 1164, 468, "pre", radius=14, fill="#fafbfc")
    f.text(22, PY + 8, "WORKED EXAMPLE: ONE YAWN AT 10 FPS", size=14.5, bold=True, color=ST["pre"][0])
    f.text(1158, PY + 9, "Real DMD frames (subject_09) | illustrative scores", size=13, color=MUTED, align="right")
    CW, LX = 27, 168
    cx = lambda i: LX + i * CW
    FY = PY + 40
    keep = [0, 1, 2, 3, 4, 5, 6, 7]
    for j, k in enumerate(range(0, N - 5, 5)):                       # one thumbnail every 0.5 s, all inside the axis
        seq = j if k < cue0 else 3 + (j - 3)
        f.thumb(cx(k) + 2, FY, 5 * CW - 4, 118, f"yawn_seq_{seq:02d}.jpg", border=CLS["yawn"] if k >= cue0 else "#c9d0d7", bw=2.4)
    f.text(LX - 12, FY + 50, "Frames", size=15, bold=True, align="right")
    rows = {"x": FY + 156, "s": FY + 210, "a": FY + 280}
    RH = 30
    for r, (lab, L) in {"x": ("Raw score xₜ", "A"), "s": ("Smoothed sₜ", "A"), "a": ("sₜ > θ", "C")}.items():
        f.text(LX - 12, rows[r] + 6, lab, size=15, bold=True, align="right")
    num(f, 30, rows["s"] + 15, "A", "#b98a1e"); num(f, 30, rows["a"] + 15, "B", "#b98a1e")
    for i in range(N):
        f.rect(cx(i) + 1, rows["x"], CW - 2, RH, "#eef1f4", radius=3)
        f.rect(cx(i) + 1, rows["x"], CW - 2, RH, CLS["yawn"], radius=3, opacity=round(float(x[i]), 2))
        f.rect(cx(i) + 1, rows["s"], CW - 2, RH, "#eef1f4", radius=3)
        f.rect(cx(i) + 1, rows["s"], CW - 2, RH, CLS["yawn"], radius=3, opacity=round(float(s[i]), 2))
        if above[i]:
            col = "#c4453c" if i == alert else ("#e2ae3c" if i < alert else "#f2d9a0")
        else:
            col = "#eef1f4"
        f.rect(cx(i) + 1, rows["a"], CW - 2, RH, col, radius=3)
    f.text(cx(alert) + CW / 2, rows["a"] + 5, "!", size=16, bold=True, color="#fff", align="center")
    num(f, cx(alert) + CW / 2, rows["a"] - 12, "D", "#b98a1e")
    # spikes note
    f.poly([(cx(4) + CW / 2, rows["x"] - 4), (cx(6) + CW / 2, rows["x"] - 14), (cx(8) + CW / 2, rows["x"] - 4)], MUTED, width=1.2)
    f.text(cx(6) + CW / 2, rows["x"] - 32, "single-frame spikes: ignored", size=13, color=MUTED, align="center")
    # braces as bars
    yb = rows["s"] + RH + 4
    f.poly([(cx(cue0), yb), (cx(cue0), yb + 6), (cx(cross), yb + 6), (cx(cross), yb)], INK, width=1.3)
    f.text((cx(cue0) + cx(cross)) / 2, yb + 7, "rise time", size=12.5, color=MUTED, align="center")
    yb = rows["a"] + RH + 4
    f.poly([(cx(cross), yb), (cx(cross), yb + 6), (cx(alert), yb + 6), (cx(alert), yb)], "#b98a1e", width=1.5)
    f.text((cx(cross) + cx(alert)) / 2, yb + 7, "confirmation time 1.0 s", size=12.5, color="#8a6a17", align="center")
    num(f, (cx(cross) + cx(alert)) / 2 - 92, yb + 16, "C", "#b98a1e")
    # time axis
    ya = rows["a"] + RH + 46
    f.poly([(LX, ya), (cx(N), ya)], LINE, width=1.2)
    for t in range(0, N + 1, 5):
        f.poly([(cx(t), ya), (cx(t), ya + 5)], LINE, width=1.2)
        f.text(cx(t), ya + 7, f"{t / 10:.1f} s", size=12.5, color=MUTED, align="center")
    # key
    kx = LX
    f.text(kx, ya + 30, "Score:", size=13.5, color=MUTED)
    for j, v in enumerate([0.1, 0.4, 0.7, 1.0]):
        f.rect(kx + 50 + j * 20, ya + 32, 16, 16, CLS["yawn"], radius=3, opacity=v)
    f.text(kx + 134, ya + 30, "0 → 1", size=13.5, color=MUTED)
    for j, (c, s_) in enumerate([("#e2ae3c", "above θ, timer running"), ("#c4453c", "alert raised"), ("#f2d9a0", "still above θ, cue continues")]):
        f.rect(kx + 210 + j * 230, ya + 32, 16, 16, c, radius=3)
        f.text(kx + 232 + j * 230, ya + 30, s_, size=13.5, color=MUTED)
    return f


# ======================================================================================
def r3():
    """Fig 4.11 replacement: the alert state machine as a tier ladder."""
    f = Fig(1180, 500)
    CW, CH, Y = 180, 226, 70
    xs = [12, 256, 500, 744, 988]
    heads = [("Idle", "pre", "watching"), ("Candidate", "dec", "above θ, timer running"), ("Tier 1", "T1", "chime + light pulse"),
             ("Tier 2", "T2", "adds explained voice"), ("Tier 3", "T3", "emergency alarm")]
    for x, (h, k, sub) in zip(xs, heads):
        col = TIER.get(k) or ST[k][0]
        fill = {"T1": "#fcf3df", "T2": "#fbeadb", "T3": "#fbe5e2"}.get(k) or ST[k][1]
        f.panel(x, Y, CW, CH, col, radius=14, fill=fill)
        f.el[-1] = f.el[-1].replace("border-color:", "border-width:2px;border-color:")
        f.text(x + CW / 2, Y + 8, h, size=17, bold=True, color=col, align="center")
        f.text(x + CW / 2, Y + 30, sub, size=13.5, color=MUTED, align="center")
    # contents
    f.thumb(xs[0] + 14, Y + 56, 152, 108, "cue_negative.jpg", border=CLS["none"])
    f.text(xs[0] + CW / 2, Y + 172, "every class below\nits cutoff θ", size=13.5, color=MUTED, w=180, align="center")
    f.thumb(xs[1] + 12, Y + 56, 108, 108, "yawn_seq_04.jpg", crop=ROI, border=CLS["yawn"])
    f.bbox(xs[1] + 12, Y + 56, 108, 108, YAWN_LBL[4], CLS["yawn"], crop=ROI)
    f.rect(xs[1] + 126, Y + 60, 42, 100, "#ffffff", radius=6, stroke="#e2d2a8", sw=1)
    f.rect(xs[1] + 137, Y + 100, 20, 56, "#e2ae3c", radius=3)
    f.text(xs[1] + 147, Y + 64, "1.0 s", size=12.5, color="#8a6a17", align="center")
    f.text(xs[1] + CW / 2, Y + 172, "confirm time\nper class", size=13.5, color=MUTED, w=180, align="center")
    f.thumb(xs[2] + 16, Y + 56, 54, 108, "lightbar_rgb.jpg", border=TIER["T1"])
    f.thumb(xs[2] + 78, Y + 76, 86, 70, "speaker.jpg", border=TIER["T1"])
    f.text(xs[2] + CW / 2, Y + 172, "class chime and a\nshort light pulse", size=13.5, color=MUTED, w=180, align="center")
    f.thumb(xs[3] + 8, Y + 58, 164, 96, "ui_tablet_dark.jpg", border=TIER["T2"])
    f.text(xs[3] + CW / 2, Y + 160, "“Yawning detected 3 times\nin 5 minutes. Consider\na short break.”", size=12.5, color=INK, w=176, align="center")
    f.thumb(xs[4] + 16, Y + 56, 54, 108, "lightbar_rgb.jpg", border=TIER["T3"])
    f.thumb(xs[4] + 78, Y + 76, 86, 70, "speaker.jpg", border=TIER["T3"])
    f.text(xs[4] + CW / 2, Y + 172, "alarm sound and the\nfull light pattern", size=13.5, color=MUTED, w=180, align="center")
    # forward transitions
    lab = ["s > θ", "held for\nconfirm\ntime", "5 s after\ncutoff, or\n3rd cue\nin 5 min", "10 s after\nthe cutoff"]
    for i in range(4):
        x0, x1 = xs[i] + CW + 2, xs[i + 1] - 4
        f.arrow([(x0, Y + 70), (x1, Y + 70)], width=2.2, color=INK)
        f.text((x0 + x1) / 2, Y + 78, lab[i], size=12.5, w=62, align="center")
    f.arrow([(xs[1] - 4, Y + 176), (xs[0] + CW + 4, Y + 176)], width=1.6, color=LINE)
    f.text((xs[0] + CW + xs[1]) / 2, Y + 182, "drops\nbelow θ", size=12.5, color=MUTED, w=60, align="center")
    # eyes-closed shortcut over the top
    f.curve(f"M{xs[0] + CW / 2},{Y - 2} C{xs[0] + CW / 2},{Y - 60} {xs[4] + CW / 2},{Y - 60} {xs[4] + CW / 2},{Y - 4}", color=CLS["eyes"], width=2.2)
    f.text(590, 8, "eyes closed 1.5 s (3 s with the head down) → straight to Tier 3", size=14, bold=True, color=CLS["eyes"], align="center")
    # cool-down band
    CY = Y + CH + 40
    f.panel(xs[2], CY, xs[4] + CW - xs[2], 64, "pre", radius=12)
    f.text(xs[2] + 14, CY + 10, "Cool-down 30 s after the cue ends", size=15, bold=True, color=ST["pre"][0])
    f.text(xs[2] + 14, CY + 34, "the class is muted: new cues are logged as tier 0, no sound", size=13.5, color=MUTED)
    for i in (2, 3, 4):
        f.arrow([(xs[i] + CW / 2, Y + CH + 2), (xs[i] + CW / 2, CY - 3)], color=LINE, width=1.6)
    f.text(xs[3] + CW / 2 + 8, Y + CH + 10, "cue ends", size=12.5, color=MUTED)
    f.arrow([(xs[2] - 2, CY + 32), (xs[0] + CW / 2, CY + 32), (xs[0] + CW / 2, Y + CH + 4)], color=LINE, width=1.6)
    f.text(xs[1] + 40, CY + 12, "after 30 s", size=12.5, color=MUTED)
    # camera blocked
    BYY = CY + 84
    f.panel(xs[0], BYY, 700, 52, "alert", radius=12, dashed=False)
    f.rect(xs[0] + 10, BYY + 8, 52, 36, "#1e242b", radius=5)
    f.text(xs[0] + 36, BYY + 15, "✕", size=16, bold=True, color="#fff", align="center")
    f.text(xs[0] + 74, BYY + 7, "From any state: camera view blocked for 3 s", size=14.5, bold=True, color=ST["alert"][0])
    f.text(xs[0] + 74, BYY + 28, "Voice prompt, pause and log. The EMA restarts from zero when the view is back.", size=13.5, color=MUTED)
    return f


# ======================================================================================
def slab(f, x, y, w, layers=5, color="#5a54a6", gap=7, depth=10, alpha=1.0):
    """A stack of thin parallelograms: a tiny 'model' icon."""
    for j in range(layers):
        yy = y + j * gap
        f.poly([(x, yy + depth), (x + depth, yy), (x + depth + w, yy), (x + w, yy + depth), (x, yy + depth)],
               color, width=1.3, fill=color, opacity=0.25 * alpha + 0.05 * j)
        f.poly([(x, yy + depth), (x + depth, yy), (x + depth + w, yy), (x + w, yy + depth), (x, yy + depth)], color, width=1.3, opacity=alpha)


# ======================================================================================
FIGS = {"r1": r1, "n1": n1, "r2": r2, "r3": r3}
import figures_more as _m
FIGS.update({"r4": _m.r4, "n3": _m.n3})
