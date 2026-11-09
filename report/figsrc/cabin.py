"""In-cabin scenes: SDP2 prototype placement, production mapping, and camera-view debug frame."""
import sys
import numpy as np
from PIL import Image
from gl3d import Renderer, Obj, T, R, S, rbox, cylinder, sphere, torus, quad, frustum, norm, backdrop
import parts2 as P
from annotate import callouts, numbered

CLAY = (0.86, 0.84, 0.82)
SEAT = (0.20, 0.21, 0.24)
TRIM = (0.30, 0.31, 0.34)
DASH = (0.17, 0.18, 0.20)


def align_y(d):
    """Rotation matrix taking +Y onto direction d."""
    d = norm(d); y = np.array([0, 1.0, 0])
    v = np.cross(y, d); c = np.dot(y, d)
    if np.linalg.norm(v) < 1e-8:
        return np.eye(4) if c > 0 else R('x', 180)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    m = np.eye(4); m[:3, :3] = np.eye(3) + vx + vx @ vx / (1 + c)
    return m


def limb(p0, p1, r0, r1=None, color=CLAY):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    r1 = r0 if r1 is None else r1
    L = np.linalg.norm(p1 - p0)
    return [Obj(cylinder(r0, L, 40, caps=False, r2=r1), T(*p0) @ align_y(p1 - p0), color=color, spec=.25, shin=20),
            Obj(sphere(r0, 32, 20), T(*p0), color=color, spec=.25, shin=20),
            Obj(sphere(r1, 32, 20), T(*p1), color=color, spec=.25, shin=20)]


def driver(pose='drive'):
    o = []
    o += limb((0, 60, -12), (0, 98, -20), 15, 16)                 # torso
    o.append(Obj(sphere(17, 40, 24), T(0, 100, -20) @ S(1.25, .62, .8), color=CLAY, spec=.2))  # shoulders
    o += limb((0, 108, -19), (0, 118, -16), 5.2)                  # neck
    o.append(Obj(sphere(11, 48, 32), T(0, 128, -13) @ S(.92, 1.08, 1), color=CLAY, spec=.3, shin=30))
    for s in (-1, 1):
        o.append(Obj(sphere(1.3, 16, 12), T(s * 3.8, 130.5, -3.6) @ S(1.2, .8, .6), color=(0.1, 0.1, 0.12)))
        o.append(Obj(rbox(4.0, .7, .8, .3), T(s * 3.9, 133.8, -3.6) @ R('z', -s * 6), color=(0.35, 0.3, 0.28)))
        o.append(Obj(sphere(2.2, 16, 12), T(s * 10.2, 128, -13) @ S(.5, 1, .8), color=CLAY))
    o.append(Obj(sphere(1.6, 16, 12), T(0, 127.3, -2.4) @ S(.8, 1.1, .9), color=CLAY))
    o.append(Obj(sphere(1.4, 16, 12), T(0, 122.6, -3.6) @ S(2.0, .7, .6), color=(0.45, 0.2, 0.2)))
    o.append(Obj(sphere(11.4, 48, 32), T(0, 132.5, -17.2) @ S(.97, .92, .97), color=(0.18, 0.14, 0.12), spec=.2))
    for s in (-1, 1):                                             # legs
        o += limb((s * 10, 56, -6), (s * 12, 62, 36), 8.5, 7)
        o += limb((s * 12, 62, 36), (s * 12, 18, 52), 6.5, 5)
        o.append(Obj(rbox(8, 6, 22, 3), T(s * 12, 14, 58), color=(0.25, 0.25, 0.28)))
    hands = {}
    for s in (-1, 1):
        sh = (s * 19, 99, -18)
        if pose == 'phone' and s == 1:
            el, ha = (s * 26, 92, 4), (s * 13, 124, -5)
        else:
            el, ha = (s * 24, 82, 16), (s * 16, 98, 40)
        o += limb(sh, el, 5.5, 4.6)
        o += limb(el, ha, 4.6, 4.0)
        o.append(Obj(sphere(4.6, 24, 16), T(*ha), color=CLAY))
        hands[s] = ha
    if pose == 'phone':
        h = hands[1]
        o.append(Obj(rbox(7.5, 15, 1.0, 1.0), T(h[0] - 2, h[1] + 3, h[2] - 3) @ R('y', 70) @ R('z', -10),
                     color=(0.08, 0.08, 0.09), spec=.9, shin=80, name='phone'))
    return o


def seat():
    return [Obj(rbox(52, 12, 52, 5), T(0, 46, -6), color=SEAT, spec=.2),
            Obj(rbox(52, 68, 12, 5), T(0, 88, -34) @ R('x', 14), color=SEAT, spec=.2),
            Obj(rbox(28, 16, 10, 4), T(0, 134, -30) @ R('x', 10), color=SEAT, spec=.2),
            Obj(rbox(40, 30, 40, 4), T(0, 25, -6), color=(0.12, 0.12, 0.13))]


def cabin_shell(steer_color=(0.07, 0.07, 0.08), glass=True):
    o = [Obj(rbox(260, 4, 220, 1), T(30, 8, 20), color=(0.14, 0.14, 0.15), spec=.05)]        # floor
    o.append(Obj(rbox(170, 34, 50, 10), T(30, 92, 82), color=DASH, spec=.25))                  # dashboard
    o.append(Obj(rbox(150, 10, 30, 5), T(30, 110, 74), color=TRIM, spec=.3))                   # dash top
    o.append(Obj(rbox(36, 70, 70, 6), T(48, 45, 40), color=DASH, spec=.2))                     # console
    o.append(Obj(rbox(8, 80, 160, 4), T(-48, 70, 10), color=TRIM, spec=.2))                    # door
    if glass:
        o.append(Obj(rbox(6, 100, 8, 3), T(-46, 150, 84) @ R('x', -35), color=TRIM))           # A-pillar
    if glass: o.append(Obj(quad(180, 95), T(30, 152, 98) @ R('x', -55) @ R('y', 180), color=(0.55, 0.7, 0.85), alpha=.12, shadow=False, spec=1.5, shin=200))
    col = T(0, 92, 58) @ R('x', -65)
    o.append(Obj(cylinder(4, 22, 32), col @ R('x', 180), color=DASH))
    w = T(0, 98, 44) @ R('x', -65)
    o.append(Obj(torus(19, 1.8, 120, 24), w, color=steer_color, spec=.3))
    o.append(Obj(cylinder(6, 3, 40), w @ T(0, -1.5, 0), color=(0.12, 0.12, 0.13), spec=.5))
    for a in (90, 210, 330):
        o.append(Obj(rbox(14, 1.6, 3.5, .8), w @ R('y', a) @ T(10, 0, 0), color=(0.12, 0.12, 0.13)))
    return o


def head_fov(apex, head=(0, 126, -13), half=(26, 24)):
    apex = np.array(apex, float); h = np.array(head, float)
    d = norm(h - apex); right = norm(np.cross(d, [0, 1, 0])); up = np.cross(right, d)
    base = [h + right * sx * half[0] + up * sy * half[1] for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    return Obj(frustum(apex, base), np.eye(4), color=(0.18, 0.5, 0.95), emissive=(0.04, 0.12, 0.3),
               alpha=.22, shadow=False, spec=0)


def scene(kind):
    o = seat() + cabin_shell(glass=False)
    o += driver('phone' if kind == 'debug' else 'drive')
    anchors = {}
    if kind in ('proto', 'debug'):
        cam = (-4, 124, 64)
        o += P.webcam(T(cam[0], cam[1] - 13.3, cam[2]) @ R('y', 180))[3:]                       # body on a dash mount
        o.append(Obj(cylinder(.8, 8, 16), T(cam[0], 115, cam[2] + 1), color=(0.08, 0.08, 0.09)))
        o.append(Obj(rbox(6, 1.2, 6, .5), T(cam[0], 115.4, cam[2] + 1), color=(0.08, 0.08, 0.09)))
        bar = P.rgb_tower(T(-28, 112, 66) @ R('z', 90) @ R('y', 180), 22)
        o += bar[2:]
        o += P.tablet_on_stand(T(44, 112, 64) @ R('y', 180) @ S(.95), 'out/ui_tablet_light.png', yaw=12)[3:]
        o += P.pebble_black(T(70, 115, 70) @ R('y', 200) @ S(.85))
        case = [x for x in __import__('bench_parts').case_closed(T(48, 80, 26) @ R('y', 90) @ S(1.4))]
        o += case
        if kind == 'proto':
            o.append(head_fov((cam[0], cam[1], cam[2] - 2)))
        anchors = dict(cam=(cam[0], cam[1], cam[2]), bar=(-28, 112, 66), tab=(44, 124, 64), spk=(70, 120, 70),
                       pi=(48, 85, 26), head=(0, 132, -13), fov=(-2, 122, 30))
    else:  # production
        o.append(Obj(rbox(10, 4, 5, 1.5), T(0, 96, 60) @ R('x', 20), color=(0.08, 0.08, 0.09), spec=.8))  # NIR cam on column
        for x in (-3.5, 3.5):
            o.append(Obj(sphere(.8, 12, 8), T(x, 96.5, 57.4), color=(0.6, 0.05, 0.05), emissive=(0.5, 0.02, 0.02)))
        o.append(Obj(cylinder(1.4, .5, 24), T(0, 96.5, 57.6) @ R('x', -70), color=(0.02, 0.02, 0.04), spec=1.2))
        o.append(Obj(quad(34, 13), T(0, 104, 56.4) @ R('x', 8) @ R('y', 180), tex='out/ui_tablet_dark.png', shadow=False))   # cluster
        o.append(Obj(quad(30, 18), T(44, 102, 56.4) @ R('x', 8) @ R('y', 180), tex='out/ui_tablet_light.png', shadow=False))  # infotainment
        for k in range(28):                                                                                # ambient strip
            o.append(Obj(rbox(4.2, .8, .8, .3), T(-50 + k * 4.4, 115.6, 62), color=(1, .6, .15), emissive=(.9, .5, .1), shadow=False))
        o.append(Obj(torus(19, 1.85, 40, 24, arc=60), T(0, 98, 44) @ R('x', -65) @ R('y', 60), color=(0.85, .15, .15), emissive=(.4, .03, .03)))
        o.append(Obj(cylinder(6, .8, 40), T(66, 115.2, 72), color=(0.10, 0.10, 0.11), spec=.4))          # dash speaker
        for rr in (2, 3.5, 5):
            o.append(Obj(torus(rr, .25, 40, 8), T(66, 116.1, 72), color=(0.35, 0.36, 0.38), spec=.8))
        o.append(Obj(rbox(16, 5, 12, 1.5), T(48, 83, 30), color=(0.35, 0.37, 0.4), spec=.6))              # ECU
        o.append(Obj(quad(30, 11), T(0, 131, 66) @ R('x', -25) @ R('y', 180), color=(0.3, .9, .6), emissive=(.2, .6, .35), alpha=.6, shadow=False))  # HUD
        anchors = dict(cam=(0, 96, 60), clu=(-10, 108, 56), info=(44, 102, 56), amb=(-30, 116, 62),
                       wheel=(-14, 100, 34), spk=(66, 116.5, 72), ecu=(48, 85.5, 30), hud=(0, 131, 66))
    return o, anchors


if __name__ == '__main__':
    # tiny module so cabin can reuse the closed case from bench without re-running it
    import types, importlib
    src = open('bench.py', encoding='utf8').read()
    mod = types.ModuleType('bench_parts')
    exec(src[:src.index('# ------------------------------------------------------------------ bench scene')], mod.__dict__)
    sys.modules['bench_parts'] = mod

    which = sys.argv[1:] or ['proto', 'prod', 'debug']
    B, O, Gr, Gy, Rd, Tl = '#2f80ed', '#e58e0b', '#27ae60', '#5b6675', '#d64545', '#22a39a'
    if 'proto' in which:
        objs, a = scene('proto')
        r = Renderer(2400, 1600)
        img = backdrop(r.render(objs, (150, 205, -95), (10, 95, 30), fov=38, light_dir=(-0.3, -1, 0.35),
                                light_span=170, light_center=(20, 70, 20), bloom=.5))
        p = {k: r.project([v])[0] for k, v in a.items()}
        numbered(img, [dict(xy=p['cam'], color=B, title='C922 camera on a dash mount'), dict(xy=p['fov'], color=B, title='Camera field of view'),
                       dict(xy=p['bar'], color=O, title='Light bar in peripheral vision'), dict(xy=p['spk'], color=O, title='Speaker'),
                       dict(xy=p['tab'], color=Gr, title='7-inch display'), dict(xy=p['pi'], color=Gy, title='Pi 5 + AI HAT+ on the console')],
                 '../Figures/cabin_proto.png', cols=3)
    if 'prod' in which:
        objs, a = scene('prod')
        r = Renderer(2400, 1600)
        img = backdrop(r.render(objs, (150, 205, -95), (10, 95, 30), fov=38, light_dir=(-0.3, -1, 0.35),
                                light_span=170, light_center=(20, 70, 20), bloom=.6))
        p = {k: r.project([v])[0] for k, v in a.items()}
        numbered(img, [dict(xy=p['cam'], color=B, title='NIR camera (replaces the C922)'),
                       dict(xy=p['hud'], color=Gr, title='HUD warning icon (replaces the display)'),
                       dict(xy=p['clu'], color=Gr, title='Instrument cluster (replaces the display)'),
                       dict(xy=p['info'], color=Tl, title='Infotainment screen (replaces the dashboard)'),
                       dict(xy=p['amb'], color=O, title='Ambient LED strip (replaces the RGB bars)'),
                       dict(xy=(1046, 778), color=Rd, title='Haptic steering wheel (replaces the PXN)'),
                       dict(xy=p['spk'], color=O, title='Cabin speaker (replaces the Pebble V3)'),
                       dict(xy=p['ecu'], color=Gy, title='ADAS ECU with NPU (replaces the Pi 5 + HAT)')],
                 '../Figures/cabin_production.png', cols=2)
    if 'debug' in which:
        objs, a = scene('debug')
        objs = [o for o in objs if o.alpha > .5]
        r = Renderer(1920, 1080)
        cam = np.array((-4, 124, 61.5))
        img = r.render(objs, tuple(cam), (2, 124, -13), fov=36, light_dir=(-0.3, -1, -0.5), light_span=120,
                       light_center=(0, 100, 0), sky=(0.55, 0.57, 0.62), ground=(0.22, 0.22, 0.24))
        bg = backdrop(img, (40, 44, 52), (25, 27, 32))
        bg.save('out/debug_raw.png')
        pts = {'head': r.project([(-11, 141, -13), (11, 114, -13)]),
               'phone': r.project([(4, 136, -12), (16, 110, -2)])}
        np.save('out/debug_boxes.npy', np.array([pts['head'], pts['phone']]))
    print('done')
