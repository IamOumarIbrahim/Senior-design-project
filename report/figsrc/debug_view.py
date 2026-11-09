"""Pipeline debug frame: camera-view render with detection box, EMA bars and alert tier."""
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']

img = Image.open('out/debug_raw.png')
W, H = img.size
head, phone = np.load('out/debug_boxes.npy')

fig = plt.figure(figsize=(12, 12 * H / W), dpi=200)
ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(img); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis('off')

# 640x640 crop window (centred on the driver)
cw = H * 0.92
ax.add_patch(Rectangle((W / 2 - cw / 2 + 40, H * 0.04), cw, cw, fill=False, ec='white', lw=1.2, ls=(0, (6, 5)), alpha=.7))
ax.text(W / 2 - cw / 2 + 52, H * 0.04 + 34, '640 × 640 crop', color='white', fontsize=10, alpha=.85)

# detection box around hand + phone
x0, y0, x1, y1 = 1125, 255, 1385, 690   # hand + phone region in render pixels
ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec='#7b61ff', lw=2.6))
ax.add_patch(Rectangle((x0 - 1.3, y0 - 46), 262, 46, fc='#7b61ff', ec='none'))
ax.text(x0 + 10, y0 - 23, 'phone_use  0.87', color='white', fontsize=12, va='center', fontweight='bold')

# EMA panel
px, py, pw = W * 0.035, H * 0.62, W * 0.25
ax.add_patch(FancyBboxPatch((px - 20, py - 70), pw + 40, 360, boxstyle='round,pad=0,rounding_size=18',
                            fc=(0.08, 0.09, 0.11, 0.82), ec='none'))
ax.text(px, py - 30, 'EMA score (τ in s)', color='white', fontsize=11)
rows = [('yawning', .04, .50, '#f5a524'), ('hand_over_mouth', .02, .50, '#f5a524'),
        ('drinking', .06, .55, '#22a39a'), ('phone_use', .78, .55, '#7b61ff')]
for k, (n, v, th, c) in enumerate(rows):
    y = py + 18 + k * 62
    ax.text(px, y, n, color='#c9d2dc', fontsize=9.5, va='center')
    bx = px + pw * 0.48; bw = pw * 0.5
    ax.add_patch(Rectangle((bx, y - 10), bw, 20, fc=(1, 1, 1, .12), ec='none'))
    ax.add_patch(Rectangle((bx, y - 10), bw * v, 20, fc=c, ec='none'))
    ax.plot([bx + bw * th] * 2, [y - 16, y + 16], color='white', lw=1.6)

# status pill
ax.add_patch(FancyBboxPatch((W * 0.68, H * 0.06), W * 0.29, 110, boxstyle='round,pad=0,rounding_size=22',
                            fc=(0.48, 0.38, 1.0, 0.92), ec='none'))
ax.text(W * 0.825, H * 0.06 + 38, 'Tier 1  ·  confirmed 2.0 s', color='white', fontsize=12.5, ha='center', va='center', fontweight='bold')
ax.text(W * 0.825, H * 0.06 + 80, '"Phone use detected"', color='white', fontsize=11, ha='center', va='center', style='italic')

ax.text(W * 0.035, H * 0.05, '29.8 FPS  ·  21 ms', color='white', fontsize=11, va='center')
ax.text(W * 0.985, H * 0.975, 'illustrative render', color=(1, 1, 1, .55), fontsize=9, ha='right', va='bottom')
fig.savefig('../Figures/debug_view.png', dpi=200)
print('done')
