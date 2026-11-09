"""SDP2 hardware bench render (OpenGL) with a magnified exploded view of the Pi enclosure."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from gl3d import Renderer, Obj, T, R, S, rbox, cylinder, torus, backdrop
import parts2 as P
from parts import webcam, breadboard, cable, BLACK, ALU, GOLD, PCB
from annotate import callouts, numbered

CASE = (0.07, 0.07, 0.08)


def case_closed(M):
    o = [Obj(rbox(10.4, 3.8, 7.4, .5), M @ T(0, 1.9, 0), color=CASE, spec=.65, shin=70)]
    o.append(Obj(cylinder(1.9, .05, 48), M @ T(1.6, 3.8, .2), color=(0.02, 0.02, 0.02)))
    for rr in (0.6, 1.1, 1.6):
        o.append(Obj(torus(rr, .07, 48, 8), M @ T(1.6, 3.83, .2), color=(0.25, 0.25, 0.27), spec=.6))
    for k in range(7):
        o.append(Obj(rbox(.22, .04, 4.6, .1), M @ T(-4.2 + k * .55, 3.81, 0), color=(0.02, 0.02, 0.02)))
    for k in range(9):
        o.append(Obj(rbox(.18, 1.6, .05, .05), M @ T(-3.6 + k * .9, 1.7, 3.71), color=(0.01, 0.01, 0.01)))
    for z, c in ((-2.2, (0.15, 0.3, 0.75)), (-.2, (0.15, 0.3, 0.75)), (2.1, ALU)):
        o.append(Obj(rbox(.3, 1.4, 1.5, .08), M @ T(5.25, 1.7, z), color=c, spec=.6))
    return o


def internals_exploded():
    """Exploded stack: base, Pi 5 + microSD, active cooler, AI HAT+, lid."""
    o = []
    o.append(Obj(rbox(10.4, .35, 7.4, .15), T(0, 0, 0), color=CASE, spec=.6))                       # base
    for sx in (-1, 1):
        o.append(Obj(rbox(.25, 3.0, 7.4, .08), T(sx * 5.07, 1.6, 0), color=CASE, spec=.6))
    o.append(Obj(rbox(10.4, 3.0, .25, .08), T(0, 1.6, -3.57), color=CASE, spec=.6))
    y = 4.2                                                                                          # Pi 5
    o.append(Obj(rbox(8.5, .16, 5.6, .05), T(0, y, 0), color=PCB, spec=.3))
    o.append(Obj(rbox(1.5, .25, 1.5, .05), T(-.6, y + .2, .2), color=ALU, spec=.9))
    o.append(Obj(rbox(1.3, .2, 1.0, .05), T(-2.6, y + .18, .4), color=(0.08, 0.08, 0.09)))
    for z, c in ((-1.9, (0.15, 0.3, 0.75)), (0.0, (0.15, 0.3, 0.75)), (2.0, ALU)):
        o.append(Obj(rbox(1.7, 1.4, 1.5, .1), T(3.6, y + .78, z), color=c, spec=.6))
    o.append(Obj(rbox(5.0, .8, .5, .05), T(-.9, y + .5, -2.55), color=BLACK))
    for k in range(20):
        o.append(Obj(rbox(.08, .6, .08, 0), T(-3.2 + k * .24, y + 1.1, -2.55), color=GOLD, spec=1))
    o.append(Obj(rbox(1.5, .1, 1.1, .05), T(-4.6, y - .12, 1.6), color=(0.75, 0.12, 0.15)))         # microSD
    y = 7.6                                                                                          # cooler
    o.append(Obj(rbox(3.4, .2, 3.2, .05), T(-.6, y, .2), color=(0.6, 0.62, 0.66), spec=.9))
    for k in range(9):
        o.append(Obj(rbox(.12, .9, 3.2, 0), T(-2.1 + k * .37, y + .55, .2), color=(0.6, 0.62, 0.66), spec=.9))
    o.append(Obj(cylinder(1.3, .3, 40), T(-.6, y + 1.0, .2), color=(0.08, 0.08, 0.09)))
    o.append(Obj(cylinder(.45, .35, 24), T(-.6, y + 1.05, .2), color=(0.2, 0.2, 0.22)))
    y = 11.0                                                                                         # AI HAT+
    o.append(Obj(rbox(6.5, .16, 5.6, .05), T(-.9, y, 0), color=(0.12, 0.45, 0.25), spec=.3))
    o.append(Obj(rbox(1.5, .32, 1.5, .05), T(.5, y + .24, .9), color=(0.08, 0.08, 0.09), spec=.6))
    o.append(Obj(rbox(1.0, .06, 1.0, .05), T(.5, y + .42, .9), color=ALU, spec=1.0))
    o.append(Obj(rbox(4.6, .4, .5, .05), T(-.9, y - .25, -2.55), color=BLACK))
    o.append(Obj(rbox(2.6, .1, .8, 0), T(-1.6, y - .1, 2.3), color=(0.85, 0.65, 0.2)))           # PCIe FPC
    y = 14.4                                                                                         # lid
    o.append(Obj(rbox(10.4, .3, 7.4, .15), T(0, y, 0), color=CASE, spec=.6))
    o.append(Obj(cylinder(1.9, .05, 48), T(1.6, y + .15, .2), color=(0.02, 0.02, 0.02)))
    for (x, z) in ((-3.9, -2.4), (2.1, -2.4), (-3.9, 2.4), (2.1, 2.4)):                             # guides
        o.append(Obj(cylinder(.05, 14, 8), T(x, .2, z), color=(0.55, 0.6, 0.7), alpha=.45, shadow=False))
    return o


# ------------------------------------------------------------------ bench scene
objs = P.table(None)
objs[0].color = np.array((0.58, 0.54, 0.48)); objs[0].tex = None
pi_pos = (-4, 0, 6)
objs += case_closed(T(*pi_pos) @ R('y', -8))
objs += webcam(T(-18, 0, -20) @ R('y', 8))
objs += P.pebble_black(T(-42, 0, -2) @ R('y', 30))
objs += P.pebble_black(T(-2, 0, -26) @ R('y', 0))
objs += P.rgb_tower(T(-34, 0, -22))
objs += P.rgb_tower(T(14, 0, -26))
objs += P.tablet_on_stand(T(34, 0, -14), 'out/ui_tablet_dark.png', yaw=-26)
objs += P.pxn_wheel(T(26, 0, 22) @ R('y', -14))
objs += P.hub_black(T(18, 0, 4) @ R('y', -10))
objs += P.psu_black(T(-20, 0, -4) @ R('y', 12))
objs += breadboard(T(-12, 0, 20) @ R('y', 10))
for o in objs:
    if o.emissive.max() > .5 and not o.cast:
        o.emissive = o.emissive * .8

yc, G = .3, (0.1, 0.1, 0.11)
objs += [
    cable([(-15.3, 1.6, -3.4), (-11, yc, 0), (-9, yc, 6), (-9.3, 1.2, 8.8)], BLACK, .3),
    cable([(1.2, 1.6, 4), (6, yc, 6), (12.2, .9, 5)], BLACK, .24),
    cable([(19, .9, 5.9), (26, yc, 2), (32, yc, -8), (33, 6, -12)], BLACK, .2),
    cable([(-1, 1.4, 9.6), (8, yc, 12), (24, yc, 6), (30, yc, -6), (31.4, 7, -12.5)], BLACK, .26),
    cable([(21, .9, 6), (24, yc, 12), (25, 3, 18)], BLACK, .24),
    cable([(15, .9, 6), (10, yc, -4), (-8, yc, -12), (-16, yc, -16), (-17.5, 4, -19), (-17.8, 9, -20)], BLACK, .2),
    cable([(23, .9, 5.4), (24, yc, -10), (17, yc, -22), (14, 1.0, -25)], G, .2),
    cable([(-38, 2, -6), (-36, yc, -14), (-34, 1.0, -21)], G, .18),
    cable([(-38, 3.5, 1.5), (-24, yc, 4), (-12, yc, 5), (-9.4, 2.6, 6)], G, .2),
    cable([(-2, 1, -21), (-6, yc, -6), (-8, 1.6, 3)], G, .18),
]
for k, col in enumerate([(0.85, 0.15, 0.15), (0.1, 0.1, 0.1), (0.95, 0.8, 0.1)]):
    objs.append(cable([(-8.6 + k * .4, 2.6, 2.4), (-10, yc, 10 + k * .4), (-12, yc, 15 + k * .4), (-11.5 + k * .9, 1.4, 20)], col, .12, 8))
for k, col in enumerate([(0.85, 0.15, 0.15), (0.1, 0.1, 0.1)]):
    objs.append(cable([(-13.5 + k * .6, 1.2, 18.5), (-26 + k * .6, yc, 8), (-34 + k * .6, yc, -6), (-34 + k * .6, .9, -18)], col, .12, 8))

r = Renderer(2600, 1650)
img = r.render(objs, (-12, 92, 112), (-2, 0, -4), fov=36, light_dir=(-0.4, -1.0, -0.55),
               light_span=90, bloom=0.45, sky=(0.68, 0.70, 0.74))
bg = backdrop(img)
anch = {'case': (-4, 3.8, 6), 'cam': (-18, 13.3, -19), 'spk': (-42, 9, -2), 'tower': (-34, 26, -22),
        'disp': (34, 15, -14), 'stand': (34, 2, -9), 'wheel': (26, 22, 30), 'hub': (18, 1.6, 4),
        'psu': (-20, 3.2, -4), 'bb': (-12, 2.4, 20)}
pp = {k: r.project([v])[0] for k, v in anch.items()}

# ------------------------------------------------------------------ magnifier inset
r2 = Renderer(1400, 1400)
inner = internals_exploded()
ins = r2.render(inner, (16, 20, 26), (0, 7.2, 0), fov=40, light_dir=(-0.4, -1.0, -0.5), light_span=20,
                light_center=(0, 7, 0), sky=(0.70, 0.72, 0.76))
ia = {'pi': (3.2, 4.4, 2.8), 'sd': (-4.6, 4.1, 1.6), 'cool': (-.6, 8.6, .2), 'hat': (.5, 11.4, .9), 'lid': (4.2, 14.6, 2)}
ipp = {k: r2.project([v])[0] for k, v in ia.items()}
D = 720
cx, cy = 560, 1230
disc = Image.new('RGBA', (1400, 1400), (246, 248, 251, 255)); disc.alpha_composite(ins)
disc = disc.resize((D, D), Image.LANCZOS)
mask = Image.new('L', (D, D), 0); ImageDraw.Draw(mask).ellipse((0, 0, D - 1, D - 1), fill=255)
sh = Image.new('RGBA', bg.size, (0, 0, 0, 0))
ImageDraw.Draw(sh).ellipse((cx - D / 2 + 8, cy - D / 2 + 14, cx + D / 2 + 8, cy + D / 2 + 14), fill=(0, 0, 0, 90))
bg = bg.convert('RGBA'); bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
d = ImageDraw.Draw(bg)
case_xy = pp['case']
# connector cone from the case to the lens
ang = np.arctan2(case_xy[1] - cy, case_xy[0] - cx)
for s in (-1, 1):
    a = ang + s * np.radians(80)
    d.line([(cx + D / 2 * np.cos(a), cy + D / 2 * np.sin(a)), tuple(case_xy)], fill=(47, 128, 237, 255), width=4)
d.ellipse((case_xy[0] - 46, case_xy[1] - 46, case_xy[0] + 46, case_xy[1] + 46), outline=(47, 128, 237, 255), width=6)
bg.paste(disc, (int(cx - D / 2), int(cy - D / 2)), mask)
d.ellipse((cx - D / 2, cy - D / 2, cx + D / 2, cy + D / 2), outline=(47, 128, 237, 255), width=9)
bg = bg.convert('RGB')
bg.save('out/bench_raw.png')

sc = D / 1400
def inset(k):
    return (cx - D / 2 + ipp[k][0] * sc, cy - D / 2 + ipp[k][1] * sc)

B, O, Rd, Gr, Gy = '#2f80ed', '#e58e0b', '#d64545', '#27ae60', '#5b6675'
items = [
    dict(xy=inset('pi'), color=B, title='Raspberry Pi 5 (8 GB)'),
    dict(xy=inset('hat'), color=B, title='AI HAT+ (Hailo NPU)'),
    dict(xy=inset('cool'), color=B, title='Active Cooler'),
    dict(xy=inset('lid'), color=B, title='Metal case'),
    dict(xy=inset('sd'), color=Gy, title='128 GB microSD'),
    dict(xy=pp['psu'], color=Gy, title='27 W USB-C supply'),
    dict(xy=pp['cam'], color=B, title='Logitech C922 webcam'),
    dict(xy=pp['tower'], color=O, title='RGB light bars'),
    dict(xy=pp['bb'], color=O, title='MOSFET driver'),
    dict(xy=pp['spk'], color=O, title='Creative Pebble V3 speakers'),
    dict(xy=pp['hub'], color=Gy, title='UGREEN USB 3.0 hub'),
    dict(xy=pp['disp'], color=Gr, title='7-inch touch display'),
    dict(xy=pp['stand'], color=Gr, title='KABCON stand'),
    dict(xy=pp['wheel'], color=Rd, title='PXN wheel (haptic prototype)'),
]
numbered(bg, items, '../Figures/bench_3d.png', cols=3)
print('done')
