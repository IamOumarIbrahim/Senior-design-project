"""EMA at two frame rates after Rougier: no legend, labels sit on the curves,
the raw signal is context (light grey), and the one finding (fixed alpha is late) is annotated.
Illustrative signal. Writes ../Figures/tikz/ema_fps.tex."""
import numpy as np

rng = np.random.default_rng(3)
tau, T, theta = 0.6, 7.0, 0.5
t30 = np.arange(0, T, 1 / 30)


def raw(t):
    x = 0.05 + 0.03 * rng.standard_normal(len(t))
    x = np.clip(x, 0, 1)
    for ts in (0.8, 1.6):
        x[np.argmin(abs(t - ts))] = 0.9
    held = (t >= 3.0) & (t < 5.2)
    x[held] = np.clip(0.85 + 0.05 * rng.standard_normal(held.sum()), 0, 1)
    return x


def ema(t, x, alpha=None):
    s, out, prev = 0.0, [], t[0]
    for ti, xi in zip(t, x):
        a = alpha if alpha is not None else 1 - np.exp(-(ti - prev) / tau)
        s = a * xi + (1 - a) * s
        out.append(s); prev = ti
    return np.array(out)


x30 = raw(t30)
t15, x15 = t30[::2], x30[::2]
e30, e15 = ema(t30, x30), ema(t15, x15)
e15f = ema(t15, x15, alpha=1 - np.exp(-(1 / 30) / tau))
c30, cfix = t30[np.argmax(e30 > theta)], t15[np.argmax(e15f > theta)]
print('cross 30', round(c30, 3), 'fixed', round(cfix, 3))
C = lambda t, y: ' '.join(f'({a:.3f},{b:.3f})' for a, b in zip(t, y))
tex = r"""\begin{tikzpicture}
\begin{axis}[width=15cm, height=6cm, xmin=0, xmax=7, ymin=0, ymax=1.0, xlabel={Time (s)},
  ytick={0,0.5,1}, axis lines=left, axis line style={gray!60}, tick style={gray!60},
  tick label style={font=\small, text=gray}, label style={font=\small, text=gray}, clip=false]
  \addplot[gray!30, line width=0.5pt] coordinates {%s};
  \addplot[sbblue!45, line width=1.2pt, densely dashed] coordinates {%s};
  \addplot[sbblue, line width=1.6pt] coordinates {%s};
  \addplot[sbgold!90!black, line width=1.6pt] coordinates {%s};
  \draw[sbred, line width=0.6pt] (axis cs:0,%.2f) -- (axis cs:7,%.2f);
  %% direct labels instead of a legend
  \node[anchor=west, font=\small, text=sbred] at (axis cs:7,%.2f) {cutoff};
  \node[anchor=south, font=\small, text=gray] at (axis cs:1.2,0.92) {single-frame spikes};
  \node[anchor=west, font=\small, text=sbblue, align=left] at (axis cs:7,0.06) {$\alpha$ from $\Delta t$\\[-2pt]30 and 15 FPS};
  \node[anchor=west, font=\small, text=sbgold!80!black] at (axis cs:7,0.22) {fixed $\alpha$, 15 FPS};
  %% the finding
  \draw[{Stealth[length=2mm]}-{Stealth[length=2mm]}, black, line width=0.7pt] (axis cs:%.3f,0.36) -- (axis cs:%.3f,0.36);
  \node[anchor=north, font=\small] at (axis cs:%.3f,0.34) {%.2f\,s late};
  \draw[gray!60, densely dotted] (axis cs:%.3f,0.36) -- (axis cs:%.3f,%.2f);
  \draw[gray!60, densely dotted] (axis cs:%.3f,0.36) -- (axis cs:%.3f,%.2f);
\end{axis}
\end{tikzpicture}
""" % (C(t30, x30), C(t15, e15), C(t30, e30), C(t15, e15f), theta, theta, theta,
       c30, cfix, (c30 + cfix) / 2, cfix - c30, c30, c30, theta, cfix, cfix, theta)
open('../Figures/tikz/ema_fps.tex', 'w', encoding='utf8').write(tex)
