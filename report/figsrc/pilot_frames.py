"""Still frames from the four pilot recordings, used as plain visual evidence (no labels, no model runs).

python pilot_frames.py [video folder]      default: D:/Downloads/vid
The source videos are only read. C1 and C4 were filmed upside down and are turned 180 degrees."""
import os, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SRC = sys.argv[1] if len(sys.argv) > 1 else r"D:/Downloads/vid"
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Figures', 'pilot'))
os.makedirs(OUT, exist_ok=True)

CLIPS = {
    'C1': dict(file='IMG_2778.mov', rot=True, cx=0.50),
    'C2': dict(file='WhatsApp Video 2026-11-07 at 7.58.27 PM.mp4', rot=False, cx=0.50),
    'C3': dict(file='WhatsApp Video 2026-11-08 at 1.04.47 PM.mp4', rot=False, cx=0.50),
    'C4': dict(file='WhatsApp Video 2026-11-08 at 9.04.27 PM.mp4', rot=True, cx=0.62),
}
FONT = r"C:/Windows/Fonts/times.ttf"
FONTB = r"C:/Windows/Fonts/timesbd.ttf"
BLUE, ORANGE, GREEN, GREY = (47, 128, 237), (229, 142, 11), (39, 174, 96), (91, 102, 117)


def grab(clip, t):
    c = CLIPS[clip]
    cap = cv2.VideoCapture(os.path.join(SRC, c['file']))
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, f = cap.read(); cap.release()
    assert ok, (clip, t)
    if c['rot']:
        f = cv2.rotate(f, cv2.ROTATE_180)
    return Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))


def crop34(im, cx):
    """3:4 portrait crop. Landscape: full height around cx. Portrait: full width, lower part (the driver)."""
    W, H = im.size
    if W > H:
        w = int(H * 3 / 4); x0 = int(min(max(cx * W - w / 2, 0), W - w))
        return im.crop((x0, 0, x0 + w, H))
    h = int(W * 4 / 3); y0 = H - h
    return im.crop((0, y0, W, H))


def tile(clip, t, w=620):
    im = crop34(grab(clip, t), CLIPS[clip]['cx'])
    return im.resize((w, int(w * 4 / 3)), Image.LANCZOS)


def chip(d, xy, text, color, f):
    x, y = xy
    tw = d.textlength(text, font=f)
    d.rounded_rectangle((x, y, x + tw + 22, y + 40), 10, fill=color)
    d.text((x + 11, y + 5), text, font=f, fill='white')
    return x + tw + 30


def row(tiles, chips, out, gap=18, cap_h=58):
    f = ImageFont.truetype(FONTB, 25)
    w, h = tiles[0].size
    W = len(tiles) * w + (len(tiles) - 1) * gap
    canvas = Image.new('RGB', (W, h + cap_h), 'white'); d = ImageDraw.Draw(canvas)
    for i, (t, cs) in enumerate(zip(tiles, chips)):
        x = i * (w + gap); canvas.paste(t, (x, 0))
        cx = x + 4
        for text, color in cs:
            cx = chip(d, (cx, h + 10), text, color, f)
    canvas.save(os.path.join(OUT, out), quality=92)
    print('wrote', out)


# 1. one frame per pilot session
row([tile('C1', 1.9), tile('C2', 12.0), tile('C3', 21.1), tile('C4', 8.9)],
    [[('C1', BLUE), ('Night', GREY), ('Low dash', ORANGE)],
     [('C2', BLUE), ('Night', GREY), ('Dash', ORANGE)],
     [('C3', BLUE), ('Day', GREY), ('Dash', ORANGE)],
     [('C4', BLUE), ('Night', GREY), ('Below wheel', ORANGE)]],
    'pilot_grid.jpg')

# 2. same driver, same drive, street light changes the face (C4)
row([tile('C4', 3.0), tile('C4', 4.2), tile('C4', 8.9), tile('C4', 24.3)],
    [[('3.0 s', GREY), ('Green cast', GREEN)], [('4.2 s', GREY), ('Red cast', (214, 69, 69))],
     [('8.9 s', GREY), ('Even light', BLUE)], [('24.3 s', GREY), ('Dark', (40, 40, 40))]],
    'pilot_night_strip.jpg')

# 3. lessons, one frame each, letters match the table in Chapter 5
row([tile('C4', 11.3), tile('C1', 51.7), tile('C3', 48.0), tile('C3', 21.1)],
    [[('(a)', BLUE), ('C4, 11.3 s', GREY)], [('(b)', BLUE), ('C1, 51.7 s', GREY)],
     [('(c)', BLUE), ('C3, 48.0 s', GREY)], [('(d)', BLUE), ('C3, 21.1 s', GREY)]],
    'pilot_lessons.jpg')

# 5. single tiles for LaTeX subfigures (captions are set in the report at normal text size)
def save(im, name):
    im.save(os.path.join(OUT, name), quality=92); print('wrote', name)


def mark(im, box, text, color=(214, 69, 69), where='top'):
    """Solid box around the thing the lesson is about, with a short label."""
    d = ImageDraw.Draw(im); f = ImageFont.truetype(FONTB, 44)
    d.rounded_rectangle(box, 14, outline=color, width=7)
    tw = d.textlength(text, font=f)
    x = min(max(box[0], 6), im.width - tw - 26)
    y = box[1] - 66 if where == 'top' else box[3] + 8
    d.rounded_rectangle((x, y, x + tw + 20, y + 58), 10, fill=color)
    d.text((x + 10, y + 5), text, font=f, fill='white')
    return im


for k, (clip, t) in enumerate([('C1', 1.9), ('C2', 12.0), ('C3', 21.1), ('C4', 8.9)]):
    save(tile(clip, t), f'grid_{k + 1}.jpg')
for k, t in enumerate([3.0, 4.2, 8.9, 24.3]):
    save(tile('C4', t), f'night_{k + 1}.jpg')
save(mark(tile('C4', 11.3), (40, 560, 500, 815), 'hand and rim over the face'), 'lesson_a.jpg')
save(mark(tile('C1', 51.7), (120, 150, 600, 700), 'motion blur'), 'lesson_b.jpg')
save(mark(tile('C3', 48.0), (40, 520, 300, 780), 'hand at the chin', where='bottom' if False else 'top'), 'lesson_c.jpg')
im = tile('C3', 21.1)
mark(im, (350, 330, 612, 470), 'bright windows', color=(229, 142, 11))
save(mark(im, (40, 500, 420, 815), 'seatbelt', color=(47, 128, 237), where='top'), 'lesson_d.jpg')

# 4. real view for the Chapter 4 placement figure
tile('C3', 21.1, 700).save(os.path.join(OUT, 'pilot_dash_view.jpg'), quality=92)
print('wrote pilot_dash_view.jpg')
