"""Numbered callouts on the three Blender renders (same badge + key style as the v5 figures)."""
import json, os, sys
import fitz
from PIL import Image, ImageDraw, ImageFilter

V5 = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(V5, 'figsrc'))
from annotate import numbered

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
O = os.path.join(V5, 'Figures')
B, Or, Gr, Gy, Rd = '#2f80ed', '#e58e0b', '#27ae60', '#5b6675', '#d64545'


def load(name, crop=None):
    im = Image.open(os.path.join(R, name + '.png')).convert('RGBA')
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    A = json.load(open(os.path.join(R, name + '.json')))
    if crop:
        bg = bg.crop(crop); A = {k: (x - crop[0], y - crop[1]) for k, (x, y) in A.items()}
    return bg.convert('RGB'), A


def keep(items, size):
    W, H = size
    return [i for i in items if 0 <= i['xy'][0] <= W and 0 <= i['xy'][1] <= H]


# 1. edge unit (exploded)
im, A = load('edge_unit', (430, 200, 1990, 1720))
numbered(im, keep([
    dict(xy=A['lid'], color=Gy, title='Vented lid'),
    dict(xy=A['hat'], color=B, title='AI HAT+'),
    dict(xy=A['hailo'], color=B, title='Hailo-8 NPU (26 TOPS)'),
    dict(xy=A['ribbon'], color=Gy, title='PCIe ribbon to the Pi'),
    dict(xy=A['standoff'], color=Gy, title='Brass standoffs'),
    dict(xy=A['fan'], color=Or, title='Active Cooler fan'),
    dict(xy=A['cool'], color=Or, title='Heatsink over the SoC'),
    dict(xy=A['pi'], color=Gr, title='Raspberry Pi 5 (8 GB)'),
    dict(xy=A['sd'], color=Gr, title='128 GB microSD'),
    dict(xy=A['case'], color=Gy, title='Metal case'),
], im.size), os.path.join(O, 'edge_unit.png'), cols=3)

# 2. wiring with the schematic as an inset
im, A = load('wiring', (330, 170, 2330, 1560))
doc = fitz.open(os.path.join(V5, 'Figures', 'schematic_led.pdf'))
pix = doc[0].get_pixmap(dpi=300); sch = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
w = 620; sch = sch.resize((w, int(sch.height * w / sch.width)), Image.LANCZOS)
x0, y0 = im.width - w - 30, im.height - sch.height - 30
sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle((x0 - 6, y0 - 2, x0 + w + 10, y0 + sch.height + 12), 14, fill=(0, 0, 0, 60))
im = im.convert('RGBA'); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10))); im = im.convert('RGB')
d = ImageDraw.Draw(im)
d.rounded_rectangle((x0 - 14, y0 - 14, x0 + w + 14, y0 + sch.height + 14), 14, fill='white', outline='#c9d2de', width=3)
im.paste(sch, (x0, y0))
numbered(im, keep([
    dict(xy=A['pi'], color=Gr, title='Raspberry Pi 5'),
    dict(xy=A['gpio18'], color=Or, title='GPIO18, pin 12 (signal)'),
    dict(xy=A['v5'], color=Rd, title='5 V, pin 2'),
    dict(xy=A['gnd'], color=Gy, title='GND, pin 6'),
    dict(xy=A['r220'], color=Or, title='220 \u03a9 gate resistor'),
    dict(xy=A['r10k'], color=Or, title='10 k\u03a9 pull-down'),
    dict(xy=A['mos'], color=B, title='IRLZ44N logic-level MOSFET'),
    dict(xy=A['rail'], color=Gy, title='Common ground rail'),
    dict(xy=A['bar'], color=Or, title='Light bar (drain switches its \u2212 lead)'),
], im.size), os.path.join(O, 'wiring_real.png'), cols=3)

# 3. cabin placement
im, A = load('cabin')
numbered(im, keep([
    dict(xy=A['cam'], color=B, title='C922 camera above the column'),
    dict(xy=A['fov'], color=B, title='Camera view: face and hands'),
    dict(xy=A['bar'], color=Or, title='Light bar in peripheral vision'),
    dict(xy=A['disp'], color=Gr, title='7-inch display by the vents', offset=(-60, 150)),
    dict(xy=A['spk'], color=Or, title='Speaker'),
    dict(xy=A['pi'], color=Gy, title='Pi 5 + AI HAT+ on the console'),
], im.size), os.path.join(O, 'cabin_real.png'), cols=2)
print('composed')
