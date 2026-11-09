"""Tiny layout kit for the v10 overview figures.

Each figure is an absolutely positioned HTML page (px units) with an SVG layer for arrows.
render.py prints it to a vector PDF with headless Chrome; LaTeX includes the PDF.
Style: flat pastel rounded boxes, real photo thumbnails, column headers, DejaVu Sans
(in the manner of ML-paper architecture overview figures).
"""
import html as _html

# ---- palette -------------------------------------------------------------
INK, MUTED, LINE = "#27313c", "#66727f", "#7d8995"
CLS = {  # class colours = the light-bar colours of Table 4.15
    "yawn": "#d99a12", "hand": "#d0661e", "drink": "#16918a", "phone": "#7a4cb0", "eyes": "#cf3a36", "none": "#9aa4ae"}
CLS_NAME = {"yawn": "Yawning", "hand": "Hand-over-mouth", "drink": "Drinking", "phone": "Phone use", "eyes": "Eyes closed"}
ST = {  # stage colours: (stroke, fill)
    "pre": ("#7f8a96", "#eef1f4"), "veh": ("#3d6fa8", "#e8eff8"), "det": ("#5a54a6", "#eeedf8"),
    "dec": ("#b98a1e", "#fbf3df"), "alert": ("#c4453c", "#fbe8e5"), "srv": ("#2f8a5b", "#e5f3ea"),
    "pc": ("#5f6b78", "#f1f3f5"), "ok": ("#2f8a5b", "#e5f3ea")}

CSS = """
@font-face { font-family: DV; src: url('fonts/DejaVuSans.ttf'); }
@font-face { font-family: DV; font-weight: bold; src: url('fonts/DejaVuSans-Bold.ttf'); }
@font-face { font-family: DVC; src: url('fonts/DejaVuSansCondensed.ttf'); }
@font-face { font-family: DVC; font-weight: bold; src: url('fonts/DejaVuSansCondensed-Bold.ttf'); }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: #fff; }
body { font-family: DVC, DV, sans-serif; color: %(ink)s; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.cv { position: relative; overflow: hidden; background: #fff; }
.a { position: absolute; }
.t { position: absolute; line-height: 1.18; }
.c { text-align: center; }
.r { text-align: right; }
.hdr { font-family: DV; font-weight: bold; font-size: 19px; color: %(ink)s; }
.cap { font-size: 14.5px; color: %(muted)s; }
.box { position: absolute; border-radius: 11px; border: 1.8px solid; display: flex; flex-direction: column;
       align-items: center; justify-content: center; text-align: center; font-size: 15.5px; line-height: 1.18; padding: 4px 6px; }
.panel { position: absolute; border-radius: 14px; border: 1.5px solid; }
.th { position: absolute; overflow: hidden; border-radius: 7px; border: 2.2px solid #c9d0d7; background: #f4f6f8; }
.th img { position: absolute; display: block; }
.tag { position: absolute; font-family: DVC; font-weight: bold; font-size: 12.5px; color: #fff; padding: 1px 4px 1px 4px; border-radius: 3px; line-height: 1.15; white-space: nowrap; }
.bb { position: absolute; border: 2.4px solid; border-radius: 2px; }
.chip { position: absolute; border-radius: 3px; }
.pill { position: absolute; border-radius: 999px; font-size: 14px; font-weight: bold; color: #fff; display: flex; align-items: center; justify-content: center; }
.mono { font-family: DVC; }
.dash { border-style: dashed !important; }
""" % {"ink": INK, "muted": MUTED}


class Fig:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.el, self.svg, self.defs = [], [], set()

    # ---- text ------------------------------------------------------------
    def text(self, x, y, s, size=15.5, bold=False, color=INK, w=None, align="left", cls="", italic=False, raw=False):
        st = f"left:{x}px;top:{y}px;font-size:{size}px;color:{color};"
        if bold: st += "font-weight:bold;"
        if italic: st += "font-style:italic;"
        if w is not None:
            if align == "center":
                st = st.replace(f"left:{x}px;", f"left:{x - w / 2}px;")
            if align == "right":
                st = st.replace(f"left:{x}px;", f"left:{x - w}px;")
            st += f"width:{w}px;"
            if align == "center": st += "text-align:center;"
            if align == "right": st += "text-align:right;"
        else:
            st += "white-space:nowrap;"
            if align == "center": st += "transform:translateX(-50%);text-align:center;"
            if align == "right": st += "transform:translateX(-100%);text-align:right;"
        self.el.append(f'<div class="t {cls}" style="{st}">{s if raw else _html.escape(s).replace(chr(10), "<br>")}</div>')

    def header(self, cx, y, s, w=200):
        self.text(cx, y, s, size=19, bold=True, w=w, align="center", cls="hdr")

    def vtext(self, cx, cy, s, size=15, color=INK, bold=False):
        b = "font-weight:bold;" if bold else ""
        self.el.append(f'<div class="t" style="left:{cx}px;top:{cy}px;font-size:{size}px;color:{color};{b}white-space:nowrap;'
                       f'transform:translate(-50%,-50%) rotate(-90deg);">{_html.escape(s)}</div>')

    # ---- shapes ----------------------------------------------------------
    def box(self, x, y, w, h, s, st="veh", size=15.5, bold=False, dashed=False, radius=11, raw=False, color=None, fill=None, extra=""):
        sc, fc = ST[st] if st in ST else (st, "#fff")
        if fill: fc = fill
        txt = s if raw else _html.escape(s).replace("\n", "<br>")
        if bold: txt = f"<b>{txt}</b>"
        self.el.append(f'<div class="box{" dash" if dashed else ""}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
                       f'border-color:{sc};background:{fc};font-size:{size}px;border-radius:{radius}px;color:{color or INK};{extra}">{txt}</div>')

    def panel(self, x, y, w, h, st="veh", dashed=False, radius=14, label=None, lsize=14.5, fill=None):
        sc, fc = ST[st] if st in ST else (st, "#fff")
        self.el.append(f'<div class="panel{" dash" if dashed else ""}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
                       f'border-color:{sc};background:{fill or fc};border-radius:{radius}px;"></div>')
        if label:
            self.text(x + 12, y + 7, label, size=lsize, bold=True, color=sc)

    def rect(self, x, y, w, h, fill, radius=3, opacity=1.0, stroke=None, sw=1.2):
        b = f"border:{sw}px solid {stroke};" if stroke else ""
        self.el.append(f'<div class="chip" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{fill};opacity:{opacity};border-radius:{radius}px;{b}"></div>')

    def pill(self, x, y, w, h, s, color, size=14):
        self.el.append(f'<div class="pill" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{color};font-size:{size}px;">{_html.escape(s)}</div>')

    def tag(self, x, y, s, color):
        self.el.append(f'<div class="tag" style="left:{x}px;top:{y}px;background:{color};">{_html.escape(s)}</div>')

    # ---- thumbnails ------------------------------------------------------
    def thumb(self, x, y, w, h, src, border="#c9d0d7", bw=2.2, crop=None, radius=7, dashed=False, fit="cover", posx=50, posy=50, bg=None):
        """crop=(cx0, cy0, cx1, cy1) in source fractions shows only that window, scaled to fill."""
        if crop:
            cx0, cy0, cx1, cy1 = crop
            iw, ih = (w - 2 * bw) / (cx1 - cx0), (h - 2 * bw) / (cy1 - cy0)
            img = f'<img src="assets/{src}" style="width:{iw:.1f}px;height:{ih:.1f}px;left:{-cx0 * iw:.1f}px;top:{-cy0 * ih:.1f}px;">'
        else:
            img = (f'<img src="assets/{src}" style="width:100%;height:100%;left:0;top:0;object-fit:{fit};'
                   f'object-position:{posx}% {posy}%;">')
        self.el.append(f'<div class="th{" dash" if dashed else ""}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
                       f'border-color:{border};border-width:{bw}px;border-radius:{radius}px;{"background:" + bg + ";" if bg else ""}">{img}</div>')

    def grid(self, x, y, w, h, n, color="#ffffffb0", bw=2.2):
        """Overlay an n x n grid on a thumb (the YOLO head's cells)."""
        iw, ih = w - 2 * bw, h - 2 * bw
        self.el.append(f'<div class="a" style="left:{x + bw}px;top:{y + bw}px;width:{iw}px;height:{ih}px;border-radius:5px;'
                       f'background-image:linear-gradient(to right,{color} 1px,transparent 1px),linear-gradient(to bottom,{color} 1px,transparent 1px);'
                       f'background-size:{iw / n:.3f}px {ih / n:.3f}px;"></div>')

    def bbox(self, x, y, w, h, frac, color, label=None, crop=None, bw=2.2):
        """Draw a detection box given in source fractions (x0, y0, x1, y1) on a thumb at (x, y, w, h)."""
        fx0, fy0, fx1, fy1 = frac
        if crop:
            cx0, cy0, cx1, cy1 = crop
            fx0, fx1 = (fx0 - cx0) / (cx1 - cx0), (fx1 - cx0) / (cx1 - cx0)
            fy0, fy1 = (fy0 - cy0) / (cy1 - cy0), (fy1 - cy0) / (cy1 - cy0)
        iw, ih = w - 2 * bw, h - 2 * bw
        bx, by = x + bw + fx0 * iw, y + bw + fy0 * ih
        self.el.append(f'<div class="bb" style="left:{bx:.1f}px;top:{by:.1f}px;width:{(fx1 - fx0) * iw:.1f}px;height:{(fy1 - fy0) * ih:.1f}px;border-color:{color};"></div>')
        if label:
            self.tag(bx - 1, by - 17, label, color)

    # ---- arrows (SVG) ----------------------------------------------------
    def _marker(self, color):
        mid = "m" + color.strip("#")
        if mid not in self.defs:
            self.defs.add(mid)
            self.svg.insert(0, f'<defs><marker id="{mid}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7.5" markerHeight="7.5" '
                               f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker></defs>')
        return mid

    def arrow(self, pts, color=LINE, width=2.0, dashed=False, head=True, both=False, rounded=True):
        mid = self._marker(color)
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        da = ' stroke-dasharray="6 5"' if dashed else ""
        mk = (f' marker-end="url(#{mid})"' if head else "") + (f' marker-start="url(#{mid})"' if both else "")
        lj = ' stroke-linejoin="round"' if rounded else ""
        self.svg.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{da}{mk}{lj}/>')

    def curve(self, d, color=LINE, width=2.0, dashed=False, head=True):
        mid = self._marker(color)
        da = ' stroke-dasharray="6 5"' if dashed else ""
        self.svg.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{da}{" marker-end=" + chr(34) + "url(#" + mid + ")" + chr(34) if head else ""}/>')

    def poly(self, pts, color, width=2.0, fill="none", dashed=False, opacity=1.0):
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        da = ' stroke-dasharray="5 4"' if dashed else ""
        self.svg.append(f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{width}"{da} opacity="{opacity}" stroke-linejoin="round"/>')

    def svg_raw(self, s):
        self.svg.append(s)

    # ---- output ----------------------------------------------------------
    def html(self, title):
        return (f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title><style>{CSS}"
                f"@page {{ size: {self.w}px {self.h}px; margin: 0; }}</style></head><body>"
                f"<div class='cv' style='width:{self.w}px;height:{self.h}px;'>"
                + "".join(self.el)
                + f"<svg class='a' style='left:0;top:0;pointer-events:none' width='{self.w}' height='{self.h}' viewBox='0 0 {self.w} {self.h}'>"
                + "".join(self.svg) + "</svg></div></body></html>")


def yolo_frac(cx, cy, w, h):
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


# boxes on the report's DMD cue frames (from Figures/tikz/dmd_cues.tex), as (x0, y0, x1, y1) from the top-left
CUE_BOX = {"yawn": (0.46, 0.54, 0.67, 0.68), "hand": (0.38, 0.42, 0.70, 0.95),
           "drink": (0.14, 0.44, 0.49, 0.78), "phone": (0.03, 0.37, 0.28, 0.78)}
CUE_IMG = {"yawn": "cue_yawn.jpg", "hand": "cue_hand_mouth.jpg", "drink": "cue_drink.jpg", "phone": "cue_phone.jpg"}
ROI = (140 / 640, 120 / 640, 540 / 640, 520 / 640)   # fixed 400x400 crop inside the 640x640 square
