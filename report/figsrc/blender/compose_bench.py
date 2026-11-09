"""Blender bench render + magnifier + numbered key, same layout and anchors as latex_v3/figsrc/bench.py."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

FIG = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../latex_v3/figsrc'))
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../out'))
sys.path.insert(0, FIG)
from annotate import numbered


def norm(v):
    v = np.asarray(v, float); return v / np.linalg.norm(v)


def projector(eye, tgt, fov, W, H):
    """Same pinhole as gl3d.look_at/perspective, without needing a GL context."""
    f = norm(np.subtract(tgt, eye)); s = norm(np.cross(f, (0, 1, 0))); u = np.cross(s, f)
    V = np.eye(4); V[0, :3], V[1, :3], V[2, :3] = s, u, -f; V[:3, 3] = -V[:3, :3] @ eye
    t = 1 / np.tan(np.radians(fov) / 2)
    def proj(p):
        c = V @ np.r_[p, 1.0]
        return np.array([(t * H / W * c[0] / -c[2] + 1) / 2 * W, (1 - t * c[1] / -c[2]) / 2 * H])
    return proj


def on_white(path):
    im = Image.open(path).convert('RGBA')
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    return bg


bg = on_white(os.path.join(OUT, 'bench_blender_raw.png'))
W, H = bg.size
pj = projector((-12, 92, 112), (-2, 0, -4), 36, W, H)
anch = {'case': (-4, 3.8, 6), 'cam': (-18, 13.3, -19), 'spk': (-42, 9, -2), 'tower': (-34, 26, -22),
        'disp': (34, 15, -14), 'stand': (34, 2, -9), 'wheel': (26, 22, 30), 'hub': (18, 1.6, 4),
        'psu': (-20, 3.2, -4), 'bb': (-12, 2.4, 20)}
pp = {k: pj(v) for k, v in anch.items()}

ins = on_white(os.path.join(OUT, 'bench_internals_raw.png'))
pi = projector((16, 20, 26), (0, 7.2, 0), 40, *ins.size)
ia = {'pi': (3.2, 4.4, 2.8), 'sd': (-4.6, 4.1, 1.6), 'cool': (-.6, 8.6, .2), 'hat': (.5, 11.4, .9), 'lid': (4.2, 14.6, 2)}
ipp = {k: pi(v) for k, v in ia.items()}

# magnifier (same geometry as the OpenGL figure)
D, cx, cy = 720, 560, 1230
disc = ins.resize((D, D), Image.LANCZOS)
mask = Image.new('L', (D, D), 0); ImageDraw.Draw(mask).ellipse((0, 0, D - 1, D - 1), fill=255)
sh = Image.new('RGBA', bg.size, (0, 0, 0, 0))
ImageDraw.Draw(sh).ellipse((cx - D / 2 + 8, cy - D / 2 + 14, cx + D / 2 + 8, cy + D / 2 + 14), fill=(0, 0, 0, 70))
bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
d = ImageDraw.Draw(bg)
case_xy = pp['case']; BLUE = (20, 60, 200, 255)
ang = np.arctan2(case_xy[1] - cy, case_xy[0] - cx)
for s in (-1, 1):
    a = ang + s * np.radians(80)
    d.line([(cx + D / 2 * np.cos(a), cy + D / 2 * np.sin(a)), tuple(case_xy)], fill=BLUE, width=4)
d.ellipse((case_xy[0] - 46, case_xy[1] - 46, case_xy[0] + 46, case_xy[1] + 46), outline=BLUE, width=6)
bg.paste(disc, (int(cx - D / 2), int(cy - D / 2)), mask)
d.ellipse((cx - D / 2, cy - D / 2, cx + D / 2, cy + D / 2), outline=BLUE, width=9)
bg = bg.convert('RGB')
sc = D / ins.size[0]
inset = lambda k: (cx - D / 2 + ipp[k][0] * sc, cy - D / 2 + ipp[k][1] * sc)

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
numbered(bg, items, os.path.join(OUT, 'bench_blender.png'), cols=3)
print('done')
