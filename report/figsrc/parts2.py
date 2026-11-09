"""Hardware models matched to the team's reference image (v2)."""
import colorsys
import numpy as np
from PIL import Image
from gl3d import Obj, rbox, cylinder, sphere, torus, tube, quad, T, S, R
from parts import BLACK, DARK, ALU, GOLD, PCB, WHITE, webcam, breadboard, cable

COPPER = (0.78, 0.52, 0.36)
SIL = (0.78, 0.79, 0.81)


def oak_texture(path, w=1024, h=1024, seed=5):
    rng = np.random.default_rng(seed)
    x = np.linspace(0, 1, w)[None, :]; y = np.linspace(0, 1, h)[:, None]
    n = np.cumsum(rng.normal(0, 1, (h, 1)), 0); n = (n - n.min()) / (np.ptp(n) + 1e-9)
    streak = np.sin((x * 220 + n * 6 + 1.2 * np.sin(y * 9)) * np.pi) * 0.5 + 0.5
    fine = (rng.random((h, w)) * 255).astype(np.uint8)
    fine = np.asarray(Image.fromarray(fine).resize((w // 8, h)).resize((w, h)), float) / 255
    base = np.array([0.80, 0.78, 0.74])
    img = base[None, None, :] - 0.07 * streak[..., None] ** 3 - 0.05 * fine[..., None]
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(path)
    return path


def table(tex):
    o = [Obj(rbox(140, 4, 90, 0.8), T(0, -2, 0), tex=tex, spec=.15, shin=20)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            o.append(Obj(rbox(5, 70, 5, .5), T(sx * 63, -39, sz * 40), color=(0.92, 0.92, 0.92)))
    return o


def pi_case_open(M):
    """Black open-top metal case with Pi 5, AI HAT+ and active cooler visible."""
    o = []
    wl, ht, dp, t = 10.4, 3.6, 7.4, .25
    o.append(Obj(rbox(wl, .3, dp, .1), M @ T(0, .15, 0), color=BLACK, spec=.5))
    for sx in (-1, 1):
        o.append(Obj(rbox(t, ht, dp, .08), M @ T(sx * (wl / 2 - t / 2), ht / 2, 0), color=BLACK, spec=.6, shin=60))
    for sz in (-1, 1):
        o.append(Obj(rbox(wl, ht, t, .08), M @ T(0, ht / 2, sz * (dp / 2 - t / 2)), color=BLACK, spec=.6, shin=60))
    for k in range(9):
        o.append(Obj(rbox(.18, 1.6, .05, .05), M @ T(-3.6 + k * .9, 1.6, dp / 2 + .01), color=(0.02, 0.02, 0.02)))
    o.append(Obj(rbox(8.5, .16, 5.6, .05), M @ T(0, 1.0, 0), color=PCB, spec=.3))
    o.append(Obj(rbox(3.2, 1.0, 3.0, .1), M @ T(-.6, 1.65, .2), color=(0.55, 0.57, 0.6), spec=.8))
    o.append(Obj(cylinder(1.25, .12, 40), M @ T(-.6, 2.18, .2), color=BLACK))
    o.append(Obj(rbox(6.5, .16, 5.6, .05), M @ T(-.9, 3.05, 0), color=(0.12, 0.45, 0.25), spec=.3))
    o.append(Obj(rbox(1.4, .3, 1.4, .05), M @ T(.6, 3.25, .9), color=(0.08, 0.08, 0.09), spec=.6))
    o.append(Obj(rbox(.9, .06, .9, .05), M @ T(.6, 3.42, .9), color=ALU, spec=1.0))
    for (x, z) in ((-3.9, -2.4), (2.1, -2.4), (-3.9, 2.4), (2.1, 2.4)):
        o.append(Obj(cylinder(.15, 2.0, 12), M @ T(x, 1.05, z), color=GOLD, spec=.9))
    o.append(Obj(rbox(5.0, .8, .5, .05), M @ T(-.9, 1.5, -2.55), color=BLACK))
    for k in range(20):
        o.append(Obj(rbox(.08, .5, .08, 0), M @ T(-3.2 + k * .24, 2.1, -2.55), color=GOLD, spec=1))
    for z, c in ((-1.9, (0.15, 0.3, 0.75)), (0.0, (0.15, 0.3, 0.75)), (2.0, ALU)):
        o.append(Obj(rbox(1.7, 1.4, 1.5, .1), M @ T(3.6, 1.8, z), color=c, spec=.6))
    o.append(Obj(rbox(1.5, .1, 1.1, .05), M @ T(-4.4, .9, 1.6), color=(0.75, 0.12, 0.15)))
    return o


def pebble_black(M):
    o = [Obj(sphere(5.6, 64, 40), M @ T(0, 5.2, 0), color=(0.07, 0.07, 0.08), spec=.55, shin=60)]
    d = M @ T(0, 5.2, 0) @ R('x', 62)
    o.append(Obj(cylinder(2.3, .35, 64), d @ T(0, 5.25, 0), color=(0.03, 0.03, 0.03), spec=.2))
    o.append(Obj(cylinder(1.9, .45, 64), d @ T(0, 5.3, 0), color=COPPER, spec=1.1, shin=90))
    o.append(Obj(sphere(.85, 32, 20), d @ T(0, 5.6, 0) @ S(1, .45, 1), color=(0.70, 0.48, 0.34), spec=1.2, shin=110))
    o.append(Obj(cylinder(.38, .4, 24), M @ T(0, 5.2, 0) @ R('x', 95) @ T(0, 5.3, 0), color=(0.12, 0.12, 0.13), spec=.9))
    return o


def rgb_tower(M, h=30, phase=0.0):
    o = [Obj(cylinder(4.8, .8, 64), M, color=(0.06, 0.06, 0.07), spec=.6),
         Obj(cylinder(.7, 2.5, 24), M @ T(0, .8, 0), color=(0.08, 0.08, 0.09)),
         Obj(rbox(5.2, h + .6, 2.4, 2.5, 6), M @ T(0, 3.2 + h / 2, -.4), color=(0.05, 0.05, 0.06), spec=.5)]
    n = 26
    for i in range(n):
        t = i / (n - 1)
        c = colorsys.hsv_to_rgb((0.78 - 0.78 * t + phase) % 1.0, 0.9, 1.0)
        yy = 3.4 + h * (i + .5) / n
        o.append(Obj(rbox(4.6, h / n + .05, 1.2, .2), M @ T(0, yy, .55), color=c,
                     emissive=np.array(c) * 1.05, spec=0, shadow=False))
    return o


def tablet_on_stand(M, tex, yaw=-20):
    A = (0.80, 0.81, 0.83)
    st = M @ R('y', yaw)
    o = [Obj(rbox(11, .8, 10, .6), st @ T(0, .4, 0), color=A, spec=.9, shin=90),
         Obj(rbox(9, 9.5, .7, .3), st @ T(0, 4.6, -1.5) @ R('x', 18), color=A, spec=.9, shin=90),
         Obj(rbox(10, .6, 1.6, .25), st @ T(0, 3.3, 2.6), color=A, spec=.9)]
    head = st @ T(0, 9.6, -.4) @ R('x', -16)
    o.append(Obj(rbox(19, 12, 1.0, .6), head, color=BLACK, spec=.7, shin=80))
    o.append(Obj(quad(16.6, 9.8), head @ T(0, 0, .52), tex=tex, spec=1.0, shin=140, shadow=False))
    return o


def hub_black(M):
    o = [Obj(rbox(12, 1.6, 3.6, .7), M @ T(0, .8, 0), color=(0.10, 0.10, 0.11), spec=.6, shin=70)]
    for k in range(4):
        o.append(Obj(rbox(1.4, .55, .1, .05), M @ T(-3.2 + k * 2.2, .85, 1.8), color=(0.15, 0.35, 0.95), emissive=(0.02, 0.06, .2)))
    o.append(Obj(sphere(.1, 10, 8), M @ T(-5.2, .85, 1.8), color=(.3, .5, 1), emissive=(.2, .45, 1.0)))
    return o


def psu_black(M):
    return [Obj(rbox(10, 3.2, 5, .9), M @ T(0, 1.6, 0), color=(0.08, 0.08, 0.09), spec=.5)]


def pxn_wheel(M):
    o = [Obj(rbox(15, 7, 13, 1.6), M @ T(0, 3.5, -2), color=(0.10, 0.10, 0.11), spec=.45),
         Obj(rbox(5, 6, 1.2, .4), M @ T(0, -1.2, 5.2), color=DARK)]
    w = M @ T(0, 11.5, 2.5) @ R('x', -22)
    o.append(Obj(cylinder(2.6, 5, 40), w @ R('x', -90) @ T(0, -5, 0), color=DARK))
    o.append(Obj(torus(13.0, 1.55, 128, 24), w @ R('x', 90), color=(0.06, 0.06, 0.07), spec=.3, shin=20))
    o.append(Obj(rbox(14, 7.5, 2.2, 2.4), w @ T(0, 1.0, 0), color=(0.10, 0.10, 0.11), spec=.5))
    o.append(Obj(cylinder(3.7, .9, 64), w @ R('x', 90) @ T(0, -1.4, 0), color=SIL, spec=1.1, shin=100))
    o.append(Obj(cylinder(2.7, .15, 64), w @ R('x', 90) @ T(0, -1.55, 0), color=(0.75, 0.6, 0.25), spec=1.0))
    for x in (-2.1, 2.1):
        o.append(Obj(rbox(1.3, 9, .9, .4), w @ T(x, -6.8, -.2) @ R('z', -x * 4), color=SIL, spec=1.0, shin=90))
    o.append(Obj(rbox(6.5, 1.6, 1.0, .4), w @ T(0, -11.6, -.2), color=SIL, spec=1.0))
    cols = [(0.8, .2, .2), (.2, .7, .3), (.25, .4, .9), (.85, .7, .2)]
    for k, (x, y) in enumerate(((4.6, 2.3), (5.6, 1.3), (4.6, .3), (3.6, 1.3))):
        o.append(Obj(sphere(.42, 16, 10), w @ T(x, y + .4, 1.1), color=cols[k]))
        o.append(Obj(sphere(.4, 16, 10), w @ T(-x, y + .4, 1.1), color=(0.2, 0.2, 0.22), spec=.8))
    return o
