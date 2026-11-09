"""Static 400x400 RoI crop, three steps in one row, cut from the crop column of input_methods.png
(our pruning and input paper, rs3). Native frame -> RoI on the frame -> RoI given to the model."""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'input_methods_src.png')
OUT = os.path.join(HERE, '..', 'Figures', 'crop_roi.png')
FONT = r"C:/Windows/Fonts/times.ttf"

src = Image.open(SRC).convert('RGB')
X0, X1 = 157, 801                                   # crop column (left half of the source figure)
rows = [(126, 766), (889, 1529), (1652, 2292)]      # native, preprocessing, result
panels = [src.crop((X0, a, X1, b)) for a, b in rows]

S = panels[0].width
gap, cap = 120, 90
W = 3 * S + 2 * gap
canvas = Image.new('RGB', (W, S + cap), 'white')
d = ImageDraw.Draw(canvas)
f = ImageFont.truetype(FONT, 40)
labels = ['1. Native 640\u00d7640 frame', '2. Fixed 400\u00d7400 RoI', '3. RoI resized for the model']
for i, (p, lab) in enumerate(zip(panels, labels)):
    x = i * (S + gap)
    canvas.paste(p, (x, 0))
    tw = d.textlength(lab, font=f)
    d.text((x + (S - tw) / 2, S + 22), lab, font=f, fill=(27, 36, 48))
    if i < 2:                                        # arrow between panels
        ax, ay = x + S + 18, S // 2
        d.line((ax, ay, ax + gap - 46, ay), fill=(91, 102, 117), width=8)
        d.polygon([(ax + gap - 36, ay), (ax + gap - 62, ay - 18), (ax + gap - 62, ay + 18)], fill=(91, 102, 117))
canvas.save(OUT)
print('wrote', OUT, canvas.size)
