"""Minimal callout annotation of rendered images (serif, short labels in side columns)."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['mathtext.fontset'] = 'stix'


def callouts(img, items, out, left_frac=0.2, right_frac=0.2, dpi=220, fontsize=11, accent='#2f80ed'):
    """items: dict(xy=(px,py), side='l'|'r'|'auto', title=str, color=hex, num=int)."""
    W, H = img.size
    tw = W * (1 + left_frac + right_frac)
    figw = 12.0; figh = figw * H / tw
    fig = plt.figure(figsize=(figw, figh), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, tw); ax.set_ylim(H, 0); ax.axis('off')
    ox = W * left_frac
    ax.imshow(img, extent=(ox, ox + W, H, 0), zorder=1)
    for i in items:
        if i.get('side') in (None, 'auto'):
            i['side'] = 'l' if i['xy'][0] < W * 0.5 else 'r'
    for side in ('l', 'r'):
        its = sorted([i for i in items if i['side'] == side], key=lambda i: i['xy'][1])
        if not its:
            continue
        ys = np.linspace(H * 0.12, H * 0.9, len(its)) if len(its) > 1 else [H / 2]
        for i, y in zip(its, ys):
            c = i.get('color', accent)
            if side == 'l':
                tx, ha, ex = ox - W * 0.015, 'right', ox - W * 0.008
            else:
                tx, ha, ex = ox + W + W * 0.015, 'left', ox + W + W * 0.008
            px, py = ox + i['xy'][0], i['xy'][1]
            ax.plot([ex, px], [y, py], color=c, lw=0.8, zorder=3)
            ax.plot([px], [py], 'o', ms=5, mfc='white', mec=c, mew=1.4, zorder=5)
            label = (f"{i['num']}  " if 'num' in i and side == 'r' else '') + i['title'] + \
                    (f"  {i['num']}" if 'num' in i and side == 'l' else '')
            ax.text(tx, y, label, fontsize=fontsize, color=c, ha=ha, va='center', zorder=4)
    fig.savefig(out, dpi=dpi, facecolor='white', bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)


def numbered(img, items, out, cols=3, dpi=220, fontsize=11.5, header=None):
    """Numbered badges on the image plus a numbered key underneath.

    items: dict(xy=(px,py), title=str, color=hex, offset=(dx,dy) optional) in key order."""
    W, H = img.size
    rows = int(np.ceil(len(items) / cols))
    row_h = H * 0.052
    key_h = row_h * (rows + (0.9 if header else 0.4))
    figw = 12.0
    fig = plt.figure(figsize=(figw, figw * (H + key_h) / W), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H + key_h, 0); ax.axis('off')
    ax.imshow(img, extent=(0, W, H, 0), zorder=1)
    r = W * 0.0135
    for n, it in enumerate(items, 1):
        c = it.get('color', '#2f80ed')
        x, y = it['xy']
        dx, dy = it.get('offset', (0, 0))
        bx, by = x + dx, y + dy
        if dx or dy:
            ax.plot([x, bx], [y, by], color=c, lw=1.4, zorder=3)
            ax.plot([x], [y], 'o', ms=3.5, color=c, zorder=3)
        ax.add_patch(plt.Circle((bx, by), r, color=c, ec='white', lw=1.8, zorder=4))
        ax.text(bx, by, str(n), color='white', fontsize=fontsize - 1, fontweight='bold', ha='center', va='center', zorder=5)
    y0 = H + row_h * (0.75 if header else 0.45)
    if header:
        ax.text(W * 0.02, H + row_h * 0.35, header, fontsize=fontsize, color='#5b6675', va='center', style='italic')
    colw = W / cols
    for n, it in enumerate(items, 1):
        k = n - 1
        cx = W * 0.02 + (k // rows) * colw
        cy = y0 + (k % rows) * row_h
        c = it.get('color', '#2f80ed')
        ax.add_patch(plt.Circle((cx + r, cy), r * 0.85, color=c, zorder=4))
        ax.text(cx + r, cy, str(n), color='white', fontsize=fontsize - 2, fontweight='bold', ha='center', va='center', zorder=5)
        ax.text(cx + r * 2.6, cy, it['title'], fontsize=fontsize, color='#1b2430', va='center')
    fig.savefig(out, dpi=dpi, facecolor='white', bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
