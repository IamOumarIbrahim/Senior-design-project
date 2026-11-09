"""Parametric models of the SDP hardware (Group 34 purchase list) for gl3d."""
import numpy as np
from PIL import Image
from gl3d import Obj, rbox, cylinder, sphere, torus, tube, quad, T, S, R, chain

BLACK = (0.06, 0.065, 0.07)
DARK = (0.16, 0.17, 0.19)
GUN = (0.30, 0.32, 0.35)
ALU = (0.72, 0.74, 0.77)
WHITE = (0.90, 0.90, 0.88)
GOLD = (0.83, 0.66, 0.25)
PCB = (0.10, 0.42, 0.22)
GLASS = (0.03, 0.04, 0.07)


def wood_texture(path, w=1024, h=1024, seed=3):
    rng = np.random.default_rng(seed)
    x = np.linspace(0, 1, w)[None, :]; y = np.linspace(0, 1, h)[:, None]
    noise = np.zeros((h, w))
    for k, amp in ((4, .6), (16, .25), (64, .1)):
        g = rng.random((k + 1, k + 1))
        gy = np.linspace(0, k, h); gx = np.linspace(0, k, w)
        noise += amp * np.interp(gx, np.arange(k + 1), g[int(k / 2)])[None, :] * np.interp(gy, np.arange(k + 1), g[:, int(k / 3)])[:, None]
    rings = np.sin((x * 150 + noise * 9.0 + 0.8 * np.sin(y * 5)) * np.pi) * 0.5 + 0.5
    rings = 0.45 * rings ** 4
    grain = rng.random((h, w)) * 0.06
    base = np.array([0.66, 0.49, 0.33]); dark = np.array([0.52, 0.36, 0.22])
    img = base * (1 - rings[..., None] * 0.55) + dark * rings[..., None] * 0.55 - grain[..., None]
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(path)
    return path


def table(tex):
    o = [Obj(rbox(140, 4, 90, 0.8), T(0, -2, 0), tex=tex, spec=.12, shin=16)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            o.append(Obj(rbox(5, 70, 5, .5), T(sx * 63, -39, sz * 40), color=DARK))
    o.append(Obj(rbox(92, .35, 52, .17), T(-2, .17, -4), color=(0.20, 0.23, 0.27), spec=.05))  # desk mat
    return o


def pi_case(M):
    """Raspberry Pi 5 + AI HAT+ + active cooler inside the metal case (closed)."""
    o = [Obj(rbox(10.0, 4.0, 7.0, .6), M @ T(0, 2.0, 0), color=GUN, spec=.7, shin=80)]
    o.append(Obj(cylinder(2.0, .06, 48), M @ T(1.2, 4.0, 0), color=BLACK, spec=.1))
    for rr in (0.7, 1.2, 1.7):
        o.append(Obj(torus(rr, .07, 48, 8), M @ T(1.2, 4.05, 0), color=(0.4, 0.42, 0.45), spec=.6))
    for k in range(6):
        o.append(Obj(rbox(.25, .05, 4.8, .1), M @ T(-4.0 + k * .55, 4.01, 0), color=BLACK))
    # ports on the +x short edge: 2x USB stacks + ethernet
    for z, c, w in ((-2.2, (0.15, 0.3, 0.75), 1.5), (-0.2, BLACK, 1.5), (2.1, ALU, 1.7)):
        o.append(Obj(rbox(.6, 1.6, w, .1), M @ T(5.1, 1.4, z), color=c, spec=.5))
    # USB-C / micro HDMI on the +z long edge
    for x in (-3.3, -1.6, -0.3):
        o.append(Obj(rbox(.9, .45, .3, .12), M @ T(x, 1.1, 3.55), color=ALU, spec=.8))
    o.append(Obj(rbox(.9, .14, .3, .05), M @ T(-4.2, .9, 3.55), color=(0.1, 0.1, 0.1)))
    o.append(Obj(sphere(.12, 12, 8), M @ T(-4.5, 1.8, 3.55), color=(0.2, 1, .3), emissive=(0.1, .9, .2)))
    return o


def webcam(M):
    """Logitech C922 on its mini tripod, lens facing +z."""
    o = []
    for a in (90, 210, 330):
        ang = np.radians(a)
        foot = np.array([np.cos(ang) * 4.5, 0.2, np.sin(ang) * 4.5])
        o.append(Obj(tube([foot, [0, 9.5, 0]], .28, 10), M, color=BLACK, spec=.4))
        o.append(Obj(sphere(.45, 16, 10), M @ T(*foot), color=DARK))
    o.append(Obj(cylinder(.5, 2, 16), M @ T(0, 9.5, 0), color=DARK))
    o.append(Obj(sphere(.7, 20, 12), M @ T(0, 11.5, 0), color=DARK, spec=.5))
    body = M @ T(0, 13.3, 0)
    o.append(Obj(rbox(9.6, 2.9, 2.6, 1.25, 7), body, color=BLACK, spec=.55, shin=60))
    o.append(Obj(cylinder(.95, .3, 40), body @ T(0, 0, 1.25) @ R('x', 90), color=ALU, spec=.9, shin=90))
    o.append(Obj(cylinder(.72, .34, 40), body @ T(0, 0, 1.27) @ R('x', 90), color=GLASS, spec=1.4, shin=150))
    for x in (-3.4, 3.4):
        o.append(Obj(cylinder(.32, .25, 20), body @ T(x, 0, 1.28) @ R('x', 90), color=(0.12, 0.12, 0.14), spec=.9))
    o.append(Obj(rbox(1.6, .3, .1, .05), body @ T(-1.9, -.9, 1.32), color=(0.5, 0.5, 0.52)))
    o.append(Obj(sphere(.09, 10, 8), body @ T(2.3, .8, 1.25), color=(1, 1, 1), emissive=(.9, .9, .9)))
    return o


def pebble(M, face_yaw=0):
    """Creative Pebble V3 speaker: sphere with a 45 degree up-firing driver."""
    o = [Obj(sphere(5.6, 64, 40), M @ T(0, 4.9, 0) @ S(1, .93, 1), color=WHITE, spec=.35, shin=40)]
    d = M @ T(0, 4.9, 0) @ R('y', face_yaw)
    o.append(Obj(cylinder(3.3, .4, 64), d @ R('x', 45) @ T(0, 4.95, 0), color=ALU, spec=1.0, shin=100))
    o.append(Obj(cylinder(2.9, .5, 64), d @ R('x', 45) @ T(0, 5.0, 0), color=(0.12, 0.12, 0.13), spec=.3))
    o.append(Obj(sphere(1.1, 32, 20), d @ R('x', 45) @ T(0, 5.2, 0) @ S(1, .35, 1), color=(0.2, 0.2, 0.22), spec=.6))
    o.append(Obj(rbox(4.2, .4, 4.2, .2), M @ T(0, .2, 0), color=(0.75, 0.75, 0.73)))
    return o


def light_bar(M, colors):
    """USB RGB light bar on two feet; colors = list of emissive RGB per segment."""
    o = [Obj(rbox(44, 1.8, 2.0, .5), M @ T(0, 4.0, 0), color=ALU, spec=.8, shin=90)]
    n = len(colors)
    for i, c in enumerate(colors):
        x = -20.5 + 41 * (i + .5) / n
        o.append(Obj(rbox(41 / n - .25, 1.0, .3, .2), M @ T(x, 4.0, 1.05), color=c, emissive=np.array(c) * 1.1, spec=0, shadow=False))
    for x in (-16, 16):
        o.append(Obj(rbox(1.2, 3.2, 3.5, .4), M @ T(x, 1.6, 0), color=DARK))
        o.append(Obj(rbox(4, .4, 4.2, .2), M @ T(x, .2, 0), color=DARK))
    return o


def display_on_holder(M, tex, yaw=-18, tilt=-12):
    """Hosyond 7-inch touch display on the KABCON holder."""
    o = [Obj(rbox(8, 1.4, 8, .5), M @ T(0, .7, 0), color=DARK, spec=.4),
         Obj(cylinder(.55, 14, 24), M @ T(0, 1.4, 0), color=ALU, spec=.9),
         Obj(sphere(1.0, 24, 16), M @ T(0, 15.6, 0), color=DARK, spec=.6)]
    head = M @ T(0, 15.6, 0) @ R('y', yaw) @ R('x', tilt) @ T(0, 0, 1.6)
    o.append(Obj(rbox(7, 7, 1.0, .4), head @ T(0, 0, -.6), color=DARK))
    o.append(Obj(rbox(18.6, 11.6, 1.2, .5), head @ T(0, 0, .4), color=BLACK, spec=.6))
    o.append(Obj(quad(16.4, 9.6), head @ T(0, 0, 1.02), tex=tex, spec=.9, shin=120, shadow=False))
    return o


def steering_wheel(M):
    """PXN racing wheel clamped to the table edge (haptic alert prototype)."""
    o = [Obj(rbox(14, 8, 14, 1.2), M @ T(0, 4, 0), color=(0.12, 0.12, 0.13), spec=.4),
         Obj(rbox(14.1, .5, 14.1, .2), M @ T(0, 6.5, 0), color=(0.75, 0.1, 0.12), emissive=(0.15, 0, 0))]
    o.append(Obj(rbox(6, 7, 1.2, .4), M @ T(0, -1.5, 7.6), color=DARK))  # clamp
    col = M @ T(0, 8.5, 4) @ R('x', -20)
    o.append(Obj(cylinder(2.2, 6, 40, r2=1.8), col @ R('x', 90), color=DARK, spec=.5))
    w = col @ T(0, 0, 7)
    o.append(Obj(torus(13.5, 1.35, 120, 24), w @ R('x', 90), color=BLACK, spec=.25, shin=20))
    o.append(Obj(torus(13.5, 1.38, 40, 24, arc=22), w @ R('x', 90) @ R('y', -101), color=(0.75, 0.1, 0.12), spec=.3))
    o.append(Obj(cylinder(4.2, 1.6, 48), w @ R('x', 90) @ T(0, -.8, 0), color=(0.13, 0.13, 0.15), spec=.6))
    o.append(Obj(cylinder(1.6, .2, 40), w @ R('x', 90) @ T(0, .82, 0), color=ALU, spec=1.0))
    for a in (0, 180, 270):
        o.append(Obj(rbox(10.5, 2.2, 1.0, .4), w @ R('z', a) @ T(8.3, 0, 0), color=(0.13, 0.13, 0.15), spec=.5))
    for x in (-2.4, 2.4):
        o.append(Obj(sphere(.55, 16, 10), w @ T(x, 1.6, .9), color=(0.75, 0.1, 0.12)))
    return o


def usb_hub(M):
    o = [Obj(rbox(10, 1.4, 3.2, .5), M @ T(0, .7, 0), color=(0.55, 0.57, 0.6), spec=.8, shin=80)]
    for k in range(4):
        o.append(Obj(rbox(1.3, .5, .2, .05), M @ T(-3.3 + k * 2.2, .75, 1.6), color=(0.15, 0.3, 0.75)))
    return o


def psu(M):
    o = [Obj(rbox(6.4, 4.2, 4.0, .9), M @ T(0, 2.1, 0), color=WHITE, spec=.4)]
    o.append(Obj(rbox(2, .5, .3, .1), M @ T(0, 3.5, 2.0), color=(0.75, 0.15, 0.25)))
    return o


def breadboard(M):
    o = [Obj(rbox(8.3, .9, 5.5, .2), M @ T(0, .45, 0), color=(0.93, 0.93, 0.9), spec=.2)]
    for r in range(2):
        o.append(Obj(rbox(7.8, .05, .12, .02), M @ T(0, .92, -2.2 + r * .35), color=(0.85, 0.2, 0.2) if r else (0.2, 0.3, 0.85)))
    o.append(Obj(rbox(1.0, 1.4, .45, .05), M @ T(-.5, 2.0, 0), color=BLACK, spec=.5))   # MOSFET body
    o.append(Obj(rbox(1.0, .9, .1, .02), M @ T(-.5, 3.1, -.15), color=ALU, spec=.9))    # tab
    for k in range(3):
        o.append(Obj(cylinder(.05, 1.3, 8), M @ T(-.85 + k * .35, .9, 0), color=ALU))
    o.append(Obj(cylinder(.18, 1.0, 16), M @ T(1.8, 1.2, .3) @ R('z', 90), color=(0.85, 0.75, 0.55)))  # gate resistor
    return o


def laptop(M, tex):
    o = [Obj(rbox(32, 1.4, 22, .7), M @ T(0, .7, 0), color=ALU, spec=.6, shin=60)]
    o.append(Obj(rbox(28, .1, 10, .05), M @ T(0, 1.42, -3), color=(0.25, 0.26, 0.28)))
    o.append(Obj(rbox(10, .05, 6, .05), M @ T(0, 1.42, 6.5), color=(0.62, 0.64, 0.67)))
    sc = M @ T(0, 1.4, -11) @ R('x', -15) @ T(0, 10.5, 0)
    o.append(Obj(rbox(32, 21, .6, .6), sc, color=ALU, spec=.6))
    o.append(Obj(rbox(31, 20, .1, .3), sc @ T(0, 0, .31), color=BLACK))
    o.append(Obj(quad(29.6, 18.5), sc @ T(0, .1, .37), tex=tex, spec=.6, shin=100, shadow=False))
    return o


def cable(points, color=BLACK, r=.22, samples=10):
    return Obj(tube(points, r, 12, samples), np.eye(4), color=color, spec=.35, shin=30)
