"""Two explainer plots for Chapter 4 (illustrative signals, not measurements):
calib_strip.pdf  - new-driver calibration, one dot per neutral frame
eye_closure.pdf  - eye-closure rule: a blink is ignored, 1.5 s of closure raises the alarm"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman'], 'mathtext.fontset': 'stix',
                     'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Figures')
BLUE, ORANGE, GREEN, RED, GREY, TEAL = '#1f77b4', '#e58e0b', '#2a9d8f', '#d64545', '#5b6675', '#2a9d8f'
BAND = '#b2dec0'

# ------------------------------------------------------------------ calibration
rng = np.random.default_rng(7)


def scores(a, b, p99):
    s = rng.beta(a, b, 600)
    return np.clip(s * p99 / np.percentile(s, 99), 0, 1)


drivers = [('Driver A', scores(1.3, 9, 0.34), 0.34),
           ('Driver B', scores(2.2, 5, 0.62), 0.62)]
fig, axes = plt.subplots(2, 1, figsize=(6.4, 3.0), sharex=True)
for ax, (name, s, p) in zip(axes, drivers):
    theta = min(max(p + 0.05, 0.50), 0.85)
    ax.axvspan(0.50, 0.85, color=BAND, alpha=0.6, lw=0)
    y = rng.uniform(0.12, 0.88, len(s))
    top = s >= np.percentile(s, 99)
    ax.scatter(s[~top], y[~top], s=6, color=BLUE, alpha=0.35, lw=0)
    ax.scatter(s[top], y[top], s=16, color=RED, lw=0)
    ax.axvline(p, color=GREY, lw=1.4, ls=(0, (4, 2)))
    ax.plot([theta], [0.5], marker='D', ms=9, color=GREEN, mec='white', mew=1.2, zorder=5)
    ax.text(theta, 0.82, f'{theta:.2f}', ha='center', fontsize=10, fontweight='bold', color=GREEN)
    ax.set_ylim(0, 1); ax.set_yticks([]); ax.spines['left'].set_visible(False)
    ax.set_ylabel(name, rotation=0, ha='right', va='center', fontsize=10, fontweight='bold')
axes[1].set_xlim(0, 1)
axes[1].set_xlabel('Detector score during the 20 s baseline')
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
handles = [Line2D([], [], ls='', marker='o', ms=4, color=BLUE, alpha=0.5, label='one frame'),
           Line2D([], [], ls='', marker='o', ms=5, color=RED, label='top 1%'),
           Line2D([], [], color=GREY, lw=1.4, ls=(0, (4, 2)), label='$P_{99}$'),
           Patch(color=BAND, alpha=0.6, label='allowed range'),
           Line2D([], [], ls='', marker='D', ms=7, color=GREEN, label='cutoff $\\theta$')]
fig.legend(handles=handles, loc='upper center', ncol=5, frameon=False, fontsize=9, handletextpad=0.4, columnspacing=1.4)
fig.tight_layout(rect=(0, 0, 1, 0.9), h_pad=1.2)
fig.savefig(os.path.join(OUT, 'calib_strip.pdf')); plt.close(fig)

# ------------------------------------------------------------------ eye closure
t = np.array([0, 1, 1.9, 2.0, 2.15, 2.3, 3.5, 4.4, 4.6, 4.8, 6.4, 6.6, 7.5, 8.6, 10])
e = np.array([0.30, 0.31, 0.30, 0.08, 0.07, 0.30, 0.29, 0.28, 0.10, 0.07, 0.07, 0.27, 0.29, 0.30, 0.30])
TH, C0 = 0.15, 4.6
fig, (ax, st) = plt.subplots(2, 1, figsize=(6.4, 3.4), sharex=True, gridspec_kw={'height_ratios': [3.2, 0.7]})
ax.axvspan(1.95, 2.25, color=GREY, alpha=0.12, lw=0)
ax.axvspan(C0, C0 + 1.5, color=TEAL, alpha=0.16, lw=0)
ax.plot(t, e, color=BLUE, lw=1.8)
ax.axhline(TH, color=RED, ls='--', lw=1.2)
ax.text(9.95, TH + 0.012, 'closed below 50% of the open-eye EAR', ha='right', fontsize=8.5, color=RED)
ax.annotate('blink, 0.15 s:\ntoo short, ignored', xy=(2.1, 0.08), xytext=(2.75, 0.04), fontsize=8.5,
            arrowprops=dict(arrowstyle='->', color=GREY), color=GREY)
ax.annotate('', xy=(C0, 0.37), xytext=(C0 + 1.5, 0.37), arrowprops=dict(arrowstyle='<->', color='#1d6f66'))
ax.text(C0 + 0.75, 0.385, 'closed for 1.5 s', ha='center', fontsize=9, color='#1d6f66')
ax.plot([C0 + 1.5], [0.07], marker='*', ms=13, color=RED, zorder=5)
ax.annotate('Tier 3 alarm', xy=(C0 + 1.5, 0.07), xytext=(7.0, 0.035), fontsize=9.5, color=RED,
            arrowprops=dict(arrowstyle='->', color=RED))
ax.set_ylim(0, 0.44); ax.set_ylabel('EAR')
for a, b, col, lab in [(0, 1.95, GREEN, 'open'), (1.95, 2.25, ORANGE, ''), (2.25, C0, GREEN, 'open'),
                       (C0, C0 + 1.5, ORANGE, 'closed: timer runs'), (C0 + 1.5, 6.5, RED, ''),
                       (6.5, 10, GREEN, 'open')]:
    st.barh(0, b - a, left=a, height=0.8, color=col, alpha=0.85, lw=0)
    if lab:
        st.text((a + b) / 2, 0, lab, ha='center', va='center', fontsize=8.5, color='white', fontweight='bold')
st.text(C0 + 1.7, 0.62, 'alarm', ha='center', va='bottom', fontsize=8.5, color=RED, fontweight='bold')
st.set_ylim(-0.5, 1.15)
st.set_yticks([0]); st.set_yticklabels(['state']); st.spines['left'].set_visible(False)
st.set_xlim(0, 10); st.set_xlabel('Time (s)')
fig.tight_layout(h_pad=0.4)
fig.savefig(os.path.join(OUT, 'eye_closure.pdf')); plt.close(fig)
print('done')
