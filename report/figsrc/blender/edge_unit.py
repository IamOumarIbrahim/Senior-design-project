"""Exploded view of the edge unit: case base, Pi 5, Active Cooler, standoffs, AI HAT+, lid."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from blib import *

OUT = sys.argv[sys.argv.index('--') + 1]
FAST = '--fast' in sys.argv
reset(2400, 1900, 48 if FAST else 200)
world_hdri('studio_small_08_2k.hdr', 1.1, rot=40)
random.seed(4)

pcb = mat('pcb', (0.03, 0.22, 0.09), 0.38, coat=0.6)
pcb_hat = mat('pcb_hat', (0.03, 0.20, 0.08), 0.38, coat=0.6)
silk = mat('silk', (0.92, 0.92, 0.88), 0.6)
gold = mat('gold', (1.0, 0.76, 0.33), 0.22, 1.0)
nickel = mat('nickel', (0.80, 0.80, 0.80), 0.25, 1.0)
alu = mat('alu', (0.86, 0.87, 0.89), 0.3, 1.0)
blk = mat('blk', (0.015, 0.015, 0.017), 0.45)
blk_m = mat('blk_m', (0.03, 0.03, 0.035), 0.7)
chip = mat('chip', (0.02, 0.02, 0.022), 0.35, coat=0.3)
blue = mat('usb_blue', (0.02, 0.18, 0.75), 0.45)
white = mat('white', (0.85, 0.85, 0.82), 0.5)
tan = mat('cap', (0.55, 0.42, 0.25), 0.5)
anod = mat('anod', (0.05, 0.055, 0.065), 0.35, 0.9)
ribbon = mat('ribbon', (0.85, 0.45, 0.10), 0.5)
brass = mat('brass', (0.83, 0.64, 0.30), 0.3, 1.0)
red = mat('red_logo', (0.75, 0.05, 0.15), 0.4)

T = 0.16                                    # PCB thickness (cm)
mm = lambda x, y: ((x - 42.5) / 10, (y - 28) / 10)
HOLES = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]


def board(name, w, h, z, m, holes):
    b = box(name, (w / 10, h / 10, T), ((w / 2 - 42.5) / 10, 0 + (h / 2 - 28) / 10, z + T / 2), m, bevel=0.02)
    for i, (x, y) in enumerate(holes):
        c = cyl('h', 0.135, 1, (*mm(x, y), z), None, 32)
        boolean(b, c)
        ring = cyl('ring', 0.3, 0.012, (*mm(x, y), z + T + 0.006), gold, 48)
        hole = cyl('hole', 0.14, 0.03, (*mm(x, y), z + T + 0.01), blk, 32)
    return b


def smd(z, region, n, rng=random):
    x0, y0, x1, y1 = region
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        big = rng.random() < 0.25
        sx, sy = (0.2, 0.1) if big else (0.1, 0.05)
        if rng.random() < 0.5:
            sx, sy = sy, sx
        m = tan if rng.random() < 0.55 else blk_m
        box('smd', (sx, sy, 0.05), (*mm(x, y), z + T + 0.025), m)
        for s in (-1, 1):                    # solder caps
            off = (s * sx / 2, 0) if sx > sy else (0, s * sy / 2)
            box('cap', (0.02 if sx > sy else sx, sy if sx > sy else 0.02, 0.052),
                (mm(x, y)[0] + off[0], mm(x, y)[1] + off[1], z + T + 0.026), nickel)


def header(z, female=False):
    cx, cy = mm(32.5, 52.5)
    if female:
        box('sock', (5.08, 0.5, 0.85), (cx, cy, z + 0.425), blk, 0.02)
        for i in range(20):
            for j in (-1, 1):
                box('pinhole', (0.1, 0.1, 0.02), (cx - 2.413 + i * 0.254, cy + j * 0.127, z + 0.851), gold)
        return
    box('hdr', (5.08, 0.5, 0.25), (cx, cy, z + T + 0.125), blk, 0.01)
    for i in range(20):
        for j in (-1, 1):
            box('pin', (0.064, 0.064, 0.84), (cx - 2.413 + i * 0.254, cy + j * 0.127, z + T + 0.42), gold)


# ---------------- case base
ZC = 0.0
base = box('case', (9.4, 6.6, 1.25), (0.25, 0, ZC + 0.625), anod, bevel=0.12)
cut = box('cut', (9.0, 6.2, 1.3), (0.25, 0, ZC + 0.82), None)
boolean(base, cut)
for i in range(9):
    box('vent', (0.12, 2.6, 0.02), (-2.8 + i * 0.5, 0, ZC + 0.161), blk)
for (x, y) in HOLES:
    cyl('boss', 0.28, 0.35, (*mm(x, y), ZC + 0.3), anod, 32)

# ---------------- Raspberry Pi 5
ZP = 2.4
board('pi5', 85, 56, ZP, pcb, HOLES)
top = ZP + T
soc = box('soc', (1.7, 1.7, 0.12), (*mm(29, 31), top + 0.06), alu, 0.03)
text('BCM2712', (*mm(29, 31), top + 0.121), 0.22, blk, extrude=0.0005)
box('ram', (1.4, 1.2, 0.1), (*mm(45, 31), top + 0.05), chip, 0.01)
text('LPDDR4X', (*mm(45, 31), top + 0.101), 0.17, silk, extrude=0.0005)
box('rp1', (0.75, 0.75, 0.09), (*mm(63, 25), top + 0.045), chip, 0.01)
text('RP1', (*mm(63, 25), top + 0.091), 0.17, silk, extrude=0.0005)
box('pmic', (0.5, 0.5, 0.08), (*mm(17, 14), top + 0.04), chip, 0.01)
box('wifi', (1.0, 1.25, 0.15), (*mm(8, 40), top + 0.075), nickel, 0.01)
header(ZP)
# Ethernet + USB stacks on the right edge
ex = mm(85 - 10.5 + 2, 0)[0]
box('rj45', (2.1, 1.6, 1.35), (ex, mm(0, 10.25)[1], top + 0.675), nickel, 0.03)
box('rj45_mouth', (0.05, 1.15, 0.85), (ex + 1.05, mm(0, 10.25)[1], top + 0.6), blk)
for yc, col in ((29.0, blue), (47.0, blk)):
    box('usb', (1.75, 1.33, 1.56), (ex + 0.1, mm(0, yc)[1], top + 0.78), nickel, 0.02)
    for k in (0.42, 1.12):
        box('usb_mouth', (0.05, 1.18, 0.52), (ex + 0.98, mm(0, yc)[1], top + k), blk)
        box('usb_tongue', (0.06, 0.95, 0.16), (ex + 0.99, mm(0, yc)[1], top + k - 0.05), col)
# bottom edge: USB-C, 2x micro-HDMI, 2x MIPI
box('usbc', (0.9, 0.75, 0.32), (*mm(11.2, 1.8), top + 0.16), nickel, 0.1)
for x in (25.8, 39.2):
    box('hdmi', (0.65, 0.75, 0.3), (*mm(x, 1.8), top + 0.15), nickel, 0.03)
for x in (47.5, 54.5):
    box('mipi', (0.55, 0.35, 0.12), (*mm(x, 3.5), top + 0.06), blk, 0.01)
box('pcie', (0.35, 1.6, 0.13), (*mm(1.8, 28), top + 0.065), blk, 0.01)
box('pcie_latch', (0.12, 1.6, 0.05), (*mm(2.6, 28), top + 0.15), mat('latch', (0.45, 0.35, 0.2), 0.5))
box('btn', (0.3, 0.3, 0.12), (*mm(1.5, 8), top + 0.06), blk_m, 0.03)
box('fanjst', (0.45, 0.3, 0.3), (*mm(70, 51), top + 0.15), white, 0.01)
box('sdcard', (1.5, 1.1, 0.08), (*mm(-3, 28), ZP - 0.05), mat('sdblk', (0.06, 0.06, 0.07), 0.4), 0.02)
box('sdlabel', (0.8, 1.0, 0.002), (*mm(-6, 28), ZP - 0.009), mat('sdred', (0.75, 0.08, 0.08), 0.4))
smd(ZP, (6, 6, 58, 47), 260)
text('Raspberry Pi 5', (*mm(53, 12), top + 0.002), 0.32, silk, extrude=0.0003)
for (x, y) in [(20, 47), (48, 9), (10, 22)]:
    text(random.choice(['C14', 'R22', 'U7', 'L3', 'C88']), (*mm(x, y), top + 0.002), 0.14, silk, extrude=0.0002)

# ---------------- Active Cooler
ZK = 4.3
cx, cy = mm(40, 28)
box('ac_plate', (5.6, 4.4, 0.18), (cx, cy, ZK + 0.09), alu, 0.02)
for i in range(13):
    box('fin', (0.07, 2.6, 0.95), (cx - 2.6 + i * 0.2, cy - 0.85, ZK + 0.18 + 0.475), alu, 0.008)
fz = ZK + 0.18
box('fan_frame', (2.8, 2.6, 0.95), (cx + 1.35, cy + 0.85, fz + 0.475), blk, 0.08)
ring = cyl('fan_hole', 1.15, 1.2, (cx + 1.35, cy + 0.85, fz + 0.6), None, 64)
fr = bpy.data.objects['fan_frame']; boolean(fr, ring)
hub = cyl('hub', 0.45, 0.85, (cx + 1.35, cy + 0.85, fz + 0.45), blk_m, 48, bevel=0.02)
for i in range(11):
    a = i * 2 * math.pi / 11
    bl = box('blade', (0.6, 0.06, 0.75), (cx + 1.35 + 0.78 * math.cos(a), cy + 0.85 + 0.78 * math.sin(a), fz + 0.43),
             blk, rot=(0, 0, a + 0.5))
cyl('sticker', 0.4, 0.004, (cx + 1.35, cy + 0.85, fz + 0.877), white, 48)
red_logo = cyl('logo', 0.17, 0.006, (cx + 1.35, cy + 0.85, fz + 0.88), red, 32)
for (x, y) in [(19, 9), (62, 47)]:
    box('pushpin', (0.25, 0.25, 0.6), (*mm(x, y), ZK - 0.2), white, 0.06)

# ---------------- standoffs (exploded, between Pi and HAT)
ZS = 6.0
for (x, y) in HOLES:
    cyl('standoff', 0.27, 1.6, (*mm(x, y), ZS + 0.8), brass, 6, bevel=0.01)

# ---------------- AI HAT+
ZH = 8.6
board('hat', 65, 56.5, ZH, pcb_hat, HOLES)
htop = ZH + T
box('hailo', (1.6, 1.6, 0.11), (*mm(31, 26), htop + 0.055), chip, 0.015)
text('HAILO-8', (*mm(31, 26.8), htop + 0.111), 0.22, silk, extrude=0.0005)
text('26 TOPS', (*mm(31, 24.6), htop + 0.111), 0.16, silk, extrude=0.0005)
box('pmic2', (0.5, 0.4, 0.07), (*mm(48, 14), htop + 0.035), chip)
box('inductor', (0.5, 0.5, 0.3), (*mm(48, 22), htop + 0.15), blk_m, 0.04)
box('inductor2', (0.5, 0.5, 0.3), (*mm(54, 22), htop + 0.15), blk_m, 0.04)
header(ZH - 0.85, female=True)
box('hat_fpc', (0.35, 1.6, 0.12), (*mm(4, 28), htop + 0.06), blk, 0.01)
smd(ZH, (8, 8, 58, 46), 140)
text('Raspberry Pi AI HAT+', (*mm(32, 10), htop + 0.002), 0.28, silk, extrude=0.0003)

# ribbon from HAT FPC down to the Pi PCIe connector (flat flex, bent)
import bmesh
me = bpy.data.meshes.new('rib'); bm = bmesh.new()
pts = []
x0, z0 = mm(4, 0)[0] - 0.1, htop + 0.08
x1, z1 = mm(1.8, 0)[0] - 0.1, top + 0.1
for i in range(41):
    t = i / 40
    x = (1 - t) * x0 + t * x1 - 1.3 * math.sin(math.pi * t)
    z = (1 - t) * z0 + t * z1
    pts.append((x, z))
yh = 0.75
rows = []
for x, z in pts:
    rows.append((bm.verts.new((x, -yh + cy * 0 + mm(0, 28)[1], z)), bm.verts.new((x, yh + mm(0, 28)[1], z))))
for a, b in zip(rows, rows[1:]):
    bm.faces.new((a[0], a[1], b[1], b[0]))
bm.to_mesh(me); rib = bpy.data.objects.new('ribbon', me); bpy.context.scene.collection.objects.link(rib)
rib.data.materials.append(ribbon)
sol = rib.modifiers.new('s', 'SOLIDIFY'); sol.thickness = 0.02
for p in rib.data.polygons:
    p.use_smooth = True

# ---------------- lid
ZL = 11.4
lid = box('lid', (9.4, 6.6, 0.25), (0.25, 0, ZL), anod, bevel=0.08)
for i in range(7):
    s = box('slot', (0.22, 3.4, 1), (-1.0 + i * 0.5, 0.2, ZL), None, bevel=0.0)
    boolean(lid, s)

# dashed assembly guides through two diagonal holes
guide = mat('guide', (0.35, 0.45, 0.85), 0.5, emit=(0.35, 0.45, 0.85), emit_str=0.6)
for (x, y) in (HOLES[0], HOLES[3]):
    z = 0.4
    while z < ZL - 0.2:
        cyl('dash', 0.012, 0.18, (*mm(x, y), z), guide, 8)
        z += 0.36

shadow_catcher(200, 0)
area_light((-25, -30, 40), (0, 0, 5), 25, 9000, (1.0, 0.97, 0.93))
area_light((30, 10, 25), (0, 0, 5), 20, 2500, (0.9, 0.95, 1.0))
camera((24, -30, 23), (0.4, 0.3, 5.4), lens=58)

anchors({'case': (4.6, -3.2, 0.8), 'pi': mm(70, 5) + (top,), 'sd': mm(-8, 28) + (ZP - 0.05,),
         'cool': (cx - 1.6, cy - 1.8, ZK + 0.9), 'fan': (cx + 2.4, cy + 1.8, fz + 0.9),
         'standoff': mm(61.5, 3.5) + (ZS + 0.8,), 'hat': mm(55, 4) + (htop,), 'hailo': mm(31, 26) + (htop + 0.1,),
         'ribbon': (x0 - 1.3, mm(0, 28)[1] - 0.7, (z0 + z1) / 2), 'lid': (4.5, 2.5, ZL + 0.12),
         'gpio': mm(10, 52.5) + (top + 0.8,)}, OUT.replace('.png', '.json'))
render(OUT)
