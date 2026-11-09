"""Photoreal light-bar driver: Pi 5 GPIO -> 220R -> IRLZ44N gate (10k pull-down), drain -> bar (-), 5 V -> bar (+)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
from blib import *
import pi5

OUT = sys.argv[sys.argv.index('--') + 1]
FAST = '--fast' in sys.argv
reset(2400, 1600, 48 if FAST else 220)
world_hdri('studio_small_08_2k.hdr', 1.0, rot=120)

pin_of, ptop = pi5.build(0, 0, 0, cooler=True)
m = pi5.M()
bb_m = mat('bb', (0.93, 0.93, 0.90), 0.55)
hole_m = mat('bbhole', (0.05, 0.05, 0.05), 0.8)
redl = mat('railred', (0.8, 0.1, 0.1), 0.5)
bluel = mat('railblue', (0.1, 0.25, 0.8), 0.5)
lead = mat('lead', (0.78, 0.78, 0.8), 0.25, 1.0)
epoxy = mat('epoxy', (0.02, 0.02, 0.02), 0.35)
tab = mat('tab', (0.82, 0.82, 0.84), 0.2, 1.0)
beige = mat('rbody', (0.80, 0.68, 0.48), 0.45, coat=0.4)
mfilm = mat('rbody2', (0.25, 0.50, 0.85), 0.4, coat=0.4)
band = {c: mat('band_' + c, rgb, 0.4, metal) for c, rgb, metal in [
    ('red', (0.7, 0.05, 0.03), 0), ('brown', (0.25, 0.1, 0.03), 0), ('black', (0.02, 0.02, 0.02), 0),
    ('orange', (0.9, 0.35, 0.02), 0), ('gold', (0.9, 0.7, 0.3), 1)]}
ins = {c: mat('ins_' + c, rgb, 0.45, coat=0.3) for c, rgb in [
    ('yellow', (0.95, 0.75, 0.05)), ('black', (0.03, 0.03, 0.03)), ('red', (0.75, 0.05, 0.04)),
    ('white', (0.9, 0.9, 0.88)), ('blackg', (0.03, 0.03, 0.03))]}


def many(name, items, mt):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    for (c, s) in items:
        r = bmesh.ops.create_cube(bm, size=1)
        for v in r['verts']:
            v.co = Vector((c[0] + v.co.x * s[0], c[1] + v.co.y * s[1], c[2] + v.co.z * s[2]))
    bm.to_mesh(me); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mt); return o


# ---------------- breadboard
bx, by, BH = 0.6, 8.6, 0.85
board = box('breadboard', (8.2, 5.5, BH), (bx, by, BH / 2), bb_m, bevel=0.04)
box('gap', (8.2, 0.3, 0.02), (bx, by, BH - 0.005), hole_m)
X = lambda i: bx + (i - 14.5) * 0.254
ROW = {k: by - 0.381 - (4 - n) * 0.254 for n, k in enumerate('abcde')}
ROW.update({k: by + 0.381 + n * 0.254 for n, k in enumerate('fghij')})
GND, VCC = by - 2.0, by - 2.25
GND2, VCC2 = by + 2.0, by + 2.25
holes = [((X(i), ROW[r], BH), (0.1, 0.1, 0.02)) for i in range(30) for r in ROW]
for y in (GND, VCC, GND2, VCC2):
    holes += [((X(i), y, BH), (0.1, 0.1, 0.02)) for i in range(1, 29) if i % 6]
many('holes', holes, hole_m)
for y, mt in ((GND + 0.17, bluel), (VCC - 0.17, redl), (GND2 - 0.17, bluel), (VCC2 + 0.17, redl)):
    box('stripe', (7.6, 0.04, 0.004), (bx, y, BH + 0.001), mt)
for i in range(0, 30, 5):
    text(str(i + 1), (X(i), ROW['a'] - 0.22, BH + 0.001), 0.12, mat('bbtxt', (0.3, 0.3, 0.3), 0.6), extrude=0.0002)
zt = BH


def leg(p0, p1, r=0.025):
    """Straight lead between two points."""
    v = Vector(p1) - Vector(p0); c = (Vector(p0) + Vector(p1)) / 2
    o = cyl('lead', r, v.length, c, lead, 12)
    o.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
    return o


# ---------------- IRLZ44N (TO-220) at cols 10/11/12 row c: G D S
yM = ROW['c']; zb = zt + 0.45
for i in (10, 11, 12):
    leg((X(i), yM, zt - 0.3), (X(i), yM, zb))
box('to220', (1.0, 0.45, 0.88), (X(11), yM, zb + 0.44), epoxy, 0.02)
t = box('to220_tab', (1.0, 0.13, 1.35), (X(11), yM + 0.29, zb + 0.67), tab, 0.01)
boolean(t, cyl('tabhole', 0.18, 1, (X(11), yM + 0.29, zb + 1.08), None, 32, rot=(math.pi / 2, 0, 0)))
text('IRLZ44N', (X(11), yM - 0.226, zb + 0.6), 0.14, mat('mark', (0.75, 0.75, 0.75), 0.6), rot=(math.pi / 2, 0, 0),
     extrude=0.0003)


def resistor(p0, p1, body_m, bands, lift=0.25):
    p0, p1 = Vector(p0), Vector(p1)
    a = p0 + Vector((0, 0, lift)); b = p1 + Vector((0, 0, lift))
    leg(p0 - Vector((0, 0, 0.3)), a); leg(p1 - Vector((0, 0, 0.3)), b); leg(a, b, 0.022)
    c = (a + b) / 2; d = (b - a).normalized()
    body = cyl('rbody', 0.12, 0.62, c, body_m, 32, bevel=0.03)
    body.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    for k, (col, off) in enumerate(zip(bands, (-0.2, -0.1, 0.0, 0.2))):
        bd = cyl('band', 0.123, 0.05, c + d * off, band[col], 32)
        bd.rotation_euler = body.rotation_euler
    return c


r220 = resistor((X(6), ROW['b'], zt), (X(10), ROW['b'], zt), beige, ('red', 'red', 'brown', 'gold'))
r10k = resistor((X(10), ROW['a'], zt), (X(13), GND, zt), mfilm, ('brown', 'black', 'orange', 'gold'), lift=0.18)


def wire(pts, col, r=0.065):
    cu = bpy.data.curves.new('w', 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = r; cu.bevel_resolution = 6; cu.resolution_u = 24
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    o = bpy.data.objects.new('wire', cu); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(ins[col]); return o


def dupont_f(p, col):
    """Female housing on a header pin, wire leaves from the top."""
    box('dupont', (0.25, 0.25, 1.4), (p[0], p[1], p[2] + 0.2), m['blk'], 0.02)
    return (p[0], p[1], p[2] + 0.92)


def dupont_m(x, y):
    leg((x, y, zt - 0.3), (x, y, zt + 0.15), 0.03)
    box('dupont_m', (0.24, 0.24, 0.6), (x, y, zt + 0.45), m['blk'], 0.02)
    return (x, y, zt + 0.75)


def route(a, b, h):
    a, b = Vector(a), Vector(b)
    return [a, a + Vector((0, 0, h * 0.6)), (a + b) / 2 + Vector((0, 0, h)), b + Vector((0, 0, h * 0.6)), b]


# GPIO18 (pin 12) -> 220R, GND (pin 6) -> rail, 5 V (pin 2) -> bar (+)
g18 = dupont_f(pin_of(12), 'yellow')
wire(route(g18, dupont_m(X(6), ROW['a']), 1.6), 'yellow')
gp = dupont_f(pin_of(6), 'black')
wire(route(gp, dupont_m(X(3), GND), 1.3), 'black')
v5 = dupont_f(pin_of(2), 'red')
# source -> GND rail (short pre-bent jumper)
s0, s1 = Vector((X(12), ROW['a'], zt)), Vector((X(12), GND, zt))
leg(s0 - Vector((0, 0, 0.3)), s0 + Vector((0, 0, 0.12))); leg(s1 - Vector((0, 0, 0.3)), s1 + Vector((0, 0, 0.12)))
wire([s0 + Vector((0, 0, 0.12)), s0 + Vector((0, -0.2, 0.25)), s1 + Vector((0, 0.2, 0.25)), s1 + Vector((0, 0, 0.12))],
     'blackg', 0.05)

# ---------------- light bar (on, amber)
LY, LX = 15.0, 1.0
box('bar', (14.0, 1.1, 0.75), (LX, LY, 0.375 + 0.25), mat('barhous', (0.04, 0.04, 0.045), 0.35, 0.8), 0.06)
for fx in (-6, 6):
    box('foot', (0.8, 1.0, 0.25), (LX + fx, LY, 0.125), m['blk_m'], 0.04)
box('diff', (13.4, 0.75, 0.05), (LX, LY, 1.0), mat('diffuser', (1, 0.75, 0.35), 0.3, emit=(1.0, 0.22, 0.0),
                                                     emit_str=2.2))
l = bpy.data.lights.new('barlight', 'AREA'); l.size = 14; l.size_y = 1; l.shape = 'RECTANGLE'
l.energy = 120; l.color = (1.0, 0.6, 0.2)
lo = bpy.data.objects.new('barlight', l); bpy.context.scene.collection.objects.link(lo); lo.location = (LX, LY, 1.2)
box('barcap', (0.5, 1.1, 0.75), (LX - 7.2, LY, 0.625), m['blk'], 0.05)
pplus, pminus = (LX - 7.45, LY - 0.2, 0.6), (LX - 7.45, LY + 0.2, 0.6)
wire([Vector(v5), Vector(v5) + Vector((0, 0.3, 1.2)), Vector((LX - 8.6, LY - 4.0, 1.6)), Vector(pplus) + Vector((-0.9, -0.1, 0.1)), Vector(pplus)], 'red')
d0 = Vector((X(11), ROW['e'], zt))
leg(d0 - Vector((0, 0, 0.3)), d0 + Vector((0, 0, 0.15)), 0.03)
box('dupont_m', (0.24, 0.24, 0.6), d0 + Vector((0, 0, 0.45)), m['blk'], 0.02)
wire([d0 + Vector((0, 0, 0.75)), d0 + Vector((0, 0.3, 1.8)), Vector((LX - 5, LY - 2.5, 2.0)),
      Vector(pminus) + Vector((-1.4, 0.4, 0.3)), Vector(pminus) + Vector((-0.6, 0, 0)), Vector(pminus)], 'white')

shadow_catcher(300, 0)
area_light((-20, -25, 35), (0, 6, 0), 30, 9000, (1.0, 0.97, 0.93))
area_light((25, -5, 20), (0, 6, 0), 20, 2200, (0.9, 0.95, 1.0))
camera((9.0, -19.0, 21.0), (0.8, 6.8, 0.3), lens=45)

anchors({'pi': (2.5, -1.0, ptop), 'gpio18': g18, 'gnd': gp, 'v5': v5, 'r220': tuple(r220), 'r10k': tuple(r10k),
         'mos': (X(11), yM, zb + 0.6), 'rail': (X(20), GND, zt), 'bar': (LX + 4, LY, 1.0),
         'breadboard': (X(25), ROW['h'], zt)}, OUT.replace('.png', '.json'))
render(OUT)
