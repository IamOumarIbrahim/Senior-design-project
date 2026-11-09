"""Worked example under the detection-and-alert loop: one yawn, frame by frame.

Yawning settings from the per-class table: tau = 0.6 s, cutoff 0.5, confirmation 1.0 s, drawn at 10 FPS.
Writes ../Figures/tikz/frames_grid.tex, a fragment placed inside flow_alert.tex. Letters match the flowchart."""
import numpy as np

fps, tau, theta, confirm = 10, 0.6, 0.5, 1.0
N, cue0 = 36, 15
rng = np.random.default_rng(7)
x = np.clip(0.06 + 0.03 * rng.standard_normal(N), 0, 1)
x[4], x[8] = 0.92, 0.88                                   # single-frame look-alikes
x[cue0:] = np.clip(0.86 + 0.04 * rng.standard_normal(N - cue0), 0, 1)
a = 1 - np.exp(-(1 / fps) / tau)
s = np.zeros(N); prev = 0.0
for i in range(N):
    prev = a * x[i] + (1 - a) * prev; s[i] = prev
above = s > theta
cross = int(np.argmax(above))
alert = cross + int(round(confirm * fps))
print('alpha', round(a, 3), 'spike peaks', round(s[4], 3), round(s[8], 3), 'cross', cross, 'alert', alert)

w, h = 0.40, 0.42                                         # cell size (cm)
rows = {'x': 0.0, 's': -0.72, 'a': -1.44}
L = []
P = L.append
top = 0.95
for k in range(0, N, 5):                                  # one thumbnail per half second, same person throughout
    img = 'Figures/guide_2.png' if k >= cue0 else 'Figures/guide_0.png'
    P(r"\node[inner sep=0, anchor=south west] at (%.3f,%.3f) {\includegraphics[width=%.3fcm,height=%.3fcm]{%s}};"
      % (k * w + 0.03, top, 5 * w - 0.06, 5 * w - 0.06, img))
P(r"\node[anchor=east] at (-0.15,%.3f) {Frames};" % (top + 5 * w / 2))
for r, t in (('x', r'Raw score $x_t$'), ('s', r'Smoothed $s_t$'), ('a', r'$s_t > \theta$')):
    P(r"\node[anchor=east] at (-0.15,%.3f) {%s};" % (rows[r] + h / 2, t))
for i in range(N):
    X = i * w
    P(r"\filldraw[draw=white, line width=0.6pt, fill=sbblue!%d!white] (%.3f,%.3f) rectangle ++(%.3f,%.3f);"
      % (int(round(100 * x[i])), X, rows['x'], w, h))
    P(r"\filldraw[draw=white, line width=0.6pt, fill=sbblue!%d!white] (%.3f,%.3f) rectangle ++(%.3f,%.3f);"
      % (int(round(100 * s[i])), X, rows['s'], w, h))
    fill = ('sbred' if i == alert else 'sbgold!85') if above[i] and i <= alert else ('sbgold!35' if above[i] else 'gray!12')
    P(r"\filldraw[draw=white, line width=0.6pt, fill=%s] (%.3f,%.3f) rectangle ++(%.3f,%.3f);" % (fill, X, rows['a'], w, h))
for r, y in rows.items():
    P(r"\draw[gray!45, line width=0.4pt] (0,%.3f) rectangle (%.3f,%.3f);" % (y, N * w, y + h))
ya = rows['a'] - 0.72                                     # time axis
P(r"\draw[gray!70, line width=0.5pt] (0,%.3f) -- (%.3f,%.3f);" % (ya, N * w, ya))
for t in range(0, N + 1, 10):
    P(r"\draw[gray!70] (%.3f,%.3f) -- ++(0,-0.08) node[below, font=\footnotesize, text=gray] {%d\,s};" % (t * w, ya, t // 10))
P(r"\draw[gray!70, line width=0.5pt] (%.3f,%.3f) -- (%.3f,%.3f) -- (%.3f,%.3f);" % (4.5 * w, h + 0.05, 6.5 * w, h + 0.26, 8.5 * w, h + 0.05))
P(r"\node[font=\footnotesize, text=gray, fill=white, inner sep=1pt] at (%.3f,%.3f) {single-frame spikes};" % (6.5 * w, h + 0.34))
P(r"\draw[decorate, decoration={brace, amplitude=3pt, mirror}] (%.3f,%.3f) -- (%.3f,%.3f) node[midway, below=2pt, font=\footnotesize] {$t_\theta$};"
  % (cue0 * w, rows['s'] - 0.03, cross * w, rows['s'] - 0.03))
P(r"\draw[decorate, decoration={brace, amplitude=3pt, mirror}, sbgold!70!black] (%.3f,%.3f) -- (%.3f,%.3f) node[midway, below=2pt, font=\footnotesize] {confirmation time};"
  % (cross * w, rows['a'] - 0.05, alert * w, rows['a'] - 0.05))
P(r"\node[text=white, font=\scriptsize] at (%.3f,%.3f) {\faBell};" % ((alert + 0.5) * w, rows['a'] + h / 2))
# letters tie each row to its step in the flowchart
P(r"\linknum{%.3f}{%.3f}{A}" % (-3.05, rows['s'] + h / 2))
P(r"\linknum{%.3f}{%.3f}{B}" % (-3.05, rows['a'] + h / 2))
P(r"\linknum{%.3f}{%.3f}{C}" % ((cross + alert) / 2 * w + 1.55, rows['a'] - 0.36))
P(r"\linknum{%.3f}{%.3f}{D}" % ((alert + 0.5) * w, rows['a'] + h + 0.13))
kx = N * w + 0.4                                          # colour key
P(r"\shade[left color=white, right color=sbblue] (%.3f,%.3f) rectangle ++(1.0,0.18);" % (kx, rows['s'] + 0.12))
P(r"\node[font=\footnotesize, text=gray, anchor=north] at (%.3f,%.3f) {0};" % (kx, rows['s'] + 0.1))
P(r"\node[font=\footnotesize, text=gray, anchor=north] at (%.3f,%.3f) {1};" % (kx + 1.0, rows['s'] + 0.1))
P(r"\node[font=\footnotesize, text=gray, anchor=south] at (%.3f,%.3f) {score};" % (kx + 0.5, rows['s'] + 0.3))
P(r"\coordinate (exnw) at (-3.3,%.3f); \coordinate (exse) at (%.3f,%.3f);" % (top + 5 * w, kx + 1.15, ya - 0.5))
open('../Figures/tikz/frames_grid.tex', 'w', encoding='utf8').write('\n'.join(L) + '\n')
