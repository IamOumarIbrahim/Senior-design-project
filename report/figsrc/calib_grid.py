"""Per-driver calibration, cell-grid style after PetarV-/TikZ: read left to right in three steps.

Two illustrative drivers, 600 baseline frames each (20 s at 30 FPS), yawning class, default cutoff 0.50:
theta = min(max(P99 + 0.05, default), 0.85). Writes ../Figures/tikz/calib_grid.tex."""
import numpy as np

rng = np.random.default_rng(11)
default, ceil = 0.50, 0.85
drivers = {
    'A': ('Driver A', 'calm baseline', 'stays at the default', np.clip(rng.beta(1.6, 14, 600), 0, 1)),
    'B': ('Driver B', 'hand often near the face', 'raised above the default',
          np.clip(np.r_[rng.beta(2.2, 9, 560), rng.uniform(0.45, 0.66, 40)], 0, 1)),
}
cs, cols = 0.13, 30                                      # cell size (cm), frames per row (1 s)
dy, lx, lw, nx = 3.75, 7.3, 7.6, 5.55                    # row pitch, number line start and length, P99 box x
green = 'sbgreen!55!black'
L = []
P = L.append
P(r"\begin{tikzpicture}[font=\small, >={Stealth[length=2.2mm]}]")


def step(x, n, text, anchor='west'):
    P(r"\node[circle, fill=sbgray, text=white, font=\scriptsize\bfseries, inner sep=1.2pt, minimum size=4.2mm] (s%d) at (%.3f,1.05) {%d};" % (n, x, n))
    P(r"\node[anchor=west, font=\small\bfseries] at (s%d.east) {%s};" % (n, text))


step(0.2, 1, r'600 neutral frames')
step(4.75, 2, r'Find $P_{99}$')
step(lx + 0.1, 3, r'Add 0.05, keep within the allowed range')
for r, (name, sub, verdict, v) in enumerate(drivers.values()):
    rng.shuffle(v)
    oy = -r * dy
    grid = v.reshape(20, cols)
    p99 = float(np.percentile(v, 99))
    cand = p99 + 0.05
    th = min(max(cand, default), ceil)
    top = np.argsort(v)[-6:]                             # top 1 % of 600 frames
    print(name, 'P99', round(p99, 3), 'cand', round(cand, 3), 'theta', round(th, 3))
    for i in range(20):
        for j in range(cols):
            P(r"\fill[sbblue!%d!white] (%.3f,%.3f) rectangle ++(%.3f,%.3f);" % (int(round(100 * grid[i, j])), j * cs, oy - i * cs, cs, -cs))
    P(r"\draw[gray!50, line width=0.4pt] (0,%.3f) rectangle (%.3f,%.3f);" % (oy, cols * cs, oy - 20 * cs))
    P(r"\node[anchor=south west, inner sep=1pt] at (0,%.3f) {\textbf{%s}\enspace{\footnotesize\color{gray}%s}};" % (oy + 0.04, name, sub))
    ny = oy - 10 * cs
    P(r"\node[draw=sbred, line width=0.8pt, rounded corners=2pt, fill=white, inner sep=3pt] (p%d) at (%.3f,%.3f) {$P_{99}=%.2f$};" % (r, nx, ny, p99))
    for k in top:
        i, j = divmod(int(k), cols)
        P(r"\draw[sbred, line width=0.7pt] (%.3f,%.3f) rectangle ++(%.3f,%.3f);" % (j * cs, oy - i * cs, cs, -cs))
        P(r"\draw[densely dotted, sbred!80, line width=0.6pt] (%.3f,%.3f) -- (p%d.west);" % ((j + 1) * cs, oy - (i + 0.5) * cs, r))
    X = lambda t: lx + t * lw
    P(r"\fill[sbgreen!18] (%.3f,%.3f) rectangle (%.3f,%.3f);" % (X(default), ny - 0.2, X(ceil), ny + 0.2))
    P(r"\draw[gray!70, line width=0.6pt] (%.3f,%.3f) -- (%.3f,%.3f);" % (X(0), ny, X(1), ny))
    for t, lab in ((0, '0'), (default, '0.50 default'), (ceil, '0.85 limit'), (1, '1')):
        P(r"\draw[gray!70] (%.3f,%.3f) -- ++(0,-0.1) node[below, font=\footnotesize, text=gray] {%s};" % (X(t), ny - 0.2 if 0 < t < 1 else ny, lab))
    P(r"\draw[->, gray!70, line width=0.6pt] (p%d.east) -- (%.3f,%.3f);" % (r, X(p99) - 0.07, ny))
    P(r"\fill[sbred] (%.3f,%.3f) rectangle ++(0.11,0.11);" % (X(p99) - 0.055, ny - 0.055))
    P(r"\draw[->, black, line width=0.7pt] (%.3f,%.3f) to[bend left=70] node[above=-1pt, font=\footnotesize] {$+0.05$} (%.3f,%.3f);" % (X(p99), ny + 0.08, X(cand), ny + 0.08))
    if th - cand > 1e-6:
        P(r"\draw[gray!80, line width=0.7pt, fill=white] (%.3f,%.3f) circle (0.08);" % (X(cand), ny))
        P(r"\draw[->, %s, line width=0.8pt] (%.3f,%.3f) -- (%.3f,%.3f);" % (green, X(cand) + 0.1, ny, X(th) - 0.12, ny))
    P(r"\fill[%s] (%.3f,%.3f) circle (0.1);" % (green, X(th), ny))
    P(r"\node[anchor=south west, font=\normalsize, text=%s, inner sep=1pt] at (%.3f,%.3f) {$\theta=%.2f$};" % (green, X(th) + 0.33, ny + 0.24, th))
    P(r"\node[anchor=north, font=\footnotesize\itshape, text=%s] at (%.3f,%.3f) {%s};" % (green, X((default + ceil) / 2), ny - 0.72, verdict))
# key under the grids
ky = -dy - 20 * cs - 0.2
P(r"\shade[left color=white, right color=sbblue] (0,%.3f) rectangle ++(1.1,0.16);" % (ky - 0.16))
P(r"\node[font=\footnotesize, text=gray, anchor=east] at (0,%.3f) {0};" % (ky - 0.08))
P(r"\node[font=\footnotesize, text=gray, anchor=west] at (1.1,%.3f) {1};" % (ky - 0.08))
P(r"\draw[sbred, line width=0.7pt] (2.05,%.3f) rectangle ++(0.14,0.14);" % (ky - 0.15))
P(r"\node[font=\footnotesize, text=gray, anchor=west] at (2.2,%.3f) {top 1\%%};" % (ky - 0.08))
P(r"\end{tikzpicture}")
open('../Figures/tikz/calib_grid.tex', 'w', encoding='utf8').write('\n'.join(L) + '\n')
