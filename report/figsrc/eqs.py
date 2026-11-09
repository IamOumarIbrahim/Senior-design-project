"""Manim stills that map the report's key equations onto visuals (colour-matched terms)."""
from manim import *
import numpy as np

config.background_color = WHITE
config.pixel_width = 2400
config.pixel_height = 1200
INK = '#1b2430'
BLUE_ = '#2f80ed'
ORANGE_ = '#e58e0b'
GREEN_ = '#27ae60'
RED_ = '#d64545'
PURPLE_ = '#7b61ff'
Text.set_default(font='Times New Roman', color=INK)
MathTex.set_default(color=INK)
Tex.set_default(color=INK)


class IoU(Scene):
    def construct(self):
        a = Rectangle(width=3.6, height=2.6, color=BLUE_, stroke_width=6).shift(LEFT * 3.4 + UP * .3)
        b = Rectangle(width=3.6, height=2.6, color=ORANGE_, stroke_width=6).shift(LEFT * 2.0 + DOWN * .6)
        inter = Intersection(a, b, fill_color=GREEN_, fill_opacity=.55, stroke_width=0)
        union = Union(a, b, fill_color=GREY_A, fill_opacity=.35, stroke_width=0)
        la = Text('prediction', font_size=30, color=BLUE_).next_to(a, UP, buff=.15).align_to(a, LEFT)
        lb = Text('ground truth', font_size=30, color=ORANGE_).next_to(b, DOWN, buff=.15).align_to(b, RIGHT)
        eq = MathTex(r'\mathrm{IoU}', '=', r'{\;|A\cap B|\;', r'\over', r'|A\cup B|}', font_size=78).shift(RIGHT * 3.3 + UP * .5)
        eq[2].set_color(GREEN_)
        eq[4].set_color(GREY_D)
        rule = MathTex(r'\mathrm{IoU}\ge 0.5 \;\Rightarrow\; \text{true positive}', font_size=46).next_to(eq, DOWN, buff=.7)
        self.add(union, inter, a, b, la, lb, eq, rule)


class EAR(Scene):
    def construct(self):
        t = np.linspace(0, 2 * np.pi, 200)
        eye = ParametricFunction(lambda u: np.array([2.6 * np.cos(u), 1.15 * np.sin(u) * (1 - .25 * np.cos(u) ** 2), 0]),
                                 t_range=[0, 2 * np.pi], color=GREY_D, stroke_width=5).shift(LEFT * 4.4)
        iris = Circle(radius=.85, color=GREY_B, fill_opacity=.25).move_to(eye.get_center())
        c = eye.get_center()
        P = {1: c + LEFT * 2.6, 4: c + RIGHT * 2.6, 2: c + LEFT * .9 + UP * 1.05, 3: c + RIGHT * .9 + UP * 1.05,
             6: c + LEFT * .9 + DOWN * 1.05, 5: c + RIGHT * .9 + DOWN * 1.05}
        v1 = Line(P[2], P[6], color=BLUE_, stroke_width=7)
        v2 = Line(P[3], P[5], color=BLUE_, stroke_width=7)
        h = DashedLine(P[1], P[4], color=ORANGE_, stroke_width=7)
        dots = VGroup(*[Dot(p, radius=.11, color=INK) for p in P.values()])
        labels = VGroup(*[MathTex(f'p_{k}', font_size=40).next_to(P[k], d, buff=.15)
                          for k, d in ((1, LEFT), (4, RIGHT), (2, UP), (3, UP), (5, DOWN), (6, DOWN))])
        eq = MathTex(r'\mathrm{EAR}', '=', r'{\|p_2-p_6\|+\|p_3-p_5\|', r'\over', r'2\,\|p_1-p_4\|}', font_size=54).shift(RIGHT * 3.3 + UP * .8)
        eq[2].set_color(BLUE_); eq[4].set_color(ORANGE_)
        rule = MathTex(r'\text{closed if } \mathrm{EAR} < 0.75\,\mathrm{EAR}_{\text{open}}', font_size=44).next_to(eq, DOWN, buff=.6)
        self.add(iris, eye, h, v1, v2, dots, labels, eq, rule)


class PR(Scene):
    def construct(self):
        rng = np.random.default_rng(4)
        gt = Circle(radius=1.9, color=ORANGE_, stroke_width=6).shift(LEFT * 4.2)
        pred = Circle(radius=1.9, color=BLUE_, stroke_width=6).shift(LEFT * 2.4)
        tp = Intersection(gt, pred, fill_color=GREEN_, fill_opacity=.5, stroke_width=0)
        lab = VGroup(MathTex('FN', font_size=50, color=ORANGE_).move_to(LEFT * 5.0),
                     MathTex('TP', font_size=50, color=GREEN_).move_to(LEFT * 3.3),
                     MathTex('FP', font_size=50, color=BLUE_).move_to(LEFT * 1.6))
        t1 = Text('true cues', font_size=30, color=ORANGE_).next_to(gt, DOWN, buff=.2)
        t2 = Text('alerts', font_size=30, color=BLUE_).next_to(pred, DOWN, buff=.2)
        eq = VGroup(MathTex(r'P=', r'{TP', r'\over', r'TP', '+', r'FP}', font_size=58),
                    MathTex(r'R=', r'{TP', r'\over', r'TP', '+', r'FN}', font_size=58),
                    MathTex(r'F_1=\frac{2PR}{P+R}', font_size=58)).arrange(DOWN, buff=.45).shift(RIGHT * 3.3)
        for m in eq[:2]:
            m[1].set_color(GREEN_); m[3].set_color(GREEN_)
        eq[0][5].set_color(BLUE_); eq[1][5].set_color(ORANGE_)
        self.add(tp, gt, pred, lab, t1, t2, eq)


class EMA(Scene):
    def construct(self):
        eq = MathTex(r's_t', '=', r'\alpha', r'x_t', '+', r'(1-\alpha)', r's_{t-1}', font_size=62).to_edge(UP, buff=.5)
        eq[2].set_color(BLUE_); eq[5].set_color(ORANGE_)
        eq2 = MathTex(r'\alpha', r'=1-e^{-\Delta t/\tau}', font_size=52).next_to(eq, DOWN, buff=.3)
        eq2[0].set_color(BLUE_)
        self.add(eq, eq2)
        tau = 0.6
        for row, (fps, col) in enumerate(((30, BLUE_), (15, PURPLE_))):
            dt = 1 / fps; a = 1 - np.exp(-dt / tau)
            y0 = -0.6 - row * 2.0
            ax = Line(LEFT * 6 + UP * y0, RIGHT * 2 + UP * y0, color=GREY_C, stroke_width=3)
            self.add(ax)
            for k in range(int(2.0 * fps)):
                w = a * (1 - a) ** k
                x = 2 - 8 * (k * dt) / 2.0
                h = (w / dt) * tau * 1.4
                self.add(Rectangle(width=max(8 / (2.0 * fps) * .7, .04), height=h, fill_color=col, fill_opacity=.85,
                                   stroke_width=0).move_to([x, y0 + h / 2, 0]))
            self.add(MathTex(rf'{fps}\ \mathrm{{FPS}}', font_size=40, color=col).move_to([3.4, y0 + .45, 0]))
            env = ParametricFunction(lambda u: np.array([2 - 4 * u, y0 + np.exp(-u / tau) * 1.4 * (1 - np.exp(-dt / tau)) / (dt / tau), 0]),
                                     t_range=[0, 2], color=GREY_D, stroke_width=2)
            self.add(DashedVMobject(env, num_dashes=40))
        self.add(MathTex(r'\leftarrow\ \text{past 2 s}', font_size=36).move_to([-2, -3.2, 0]))


class Quant(Scene):
    def construct(self):
        eq = MathTex(r'q', '=', r'\operatorname{round}\!\left(\frac{x}{s}\right)', '+', r'z', font_size=58).to_edge(UP, buff=.75)
        eq[0].set_color(ORANGE_); eq[2].set_color(BLUE_)
        self.add(eq)
        fl = NumberLine(x_range=[-2, 2, .5], length=9, color=BLUE_, include_numbers=True, font_size=30,
                        decimal_number_config={'num_decimal_places': 1, 'color': INK}).shift(UP * .5 + RIGHT * 1.2)
        self.add(fl, MathTex(r'x\ (\text{FP32})', font_size=40, color=BLUE_).next_to(fl, LEFT, buff=.3))
        ql = Line(LEFT * 4.5, RIGHT * 4.5, color=ORANGE_).shift(DOWN * 1.5 + RIGHT * 1.2)
        for k in range(-8, 9):
            self.add(Line(UP * .12, DOWN * .12, color=ORANGE_).move_to(ql.point_from_proportion((k + 8) / 16)))
        self.add(ql, MathTex(r'q\ (\text{INT8})', font_size=40, color=ORANGE_).next_to(ql, LEFT, buff=.3))
        for lab, prop in ((r'-128', 0), (r'0', .5), (r'127', 1)):
            self.add(MathTex(lab, font_size=30).next_to(ql.point_from_proportion(prop), DOWN, buff=.2))
        rng = np.random.default_rng(1)
        for x in rng.normal(0, .55, 14).clip(-1.95, 1.95):
            p = fl.n2p(x); qx = np.round(x / (2 / 8)) * (2 / 8)
            p2 = ql.point_from_proportion((qx + 2) / 4)
            self.add(Dot(p, radius=.07, color=BLUE_), Arrow(p, p2, buff=.1, stroke_width=2.5, color=GREY_C,
                                                              max_tip_length_to_length_ratio=.06), Dot(p2, radius=.07, color=ORANGE_))
        self.add(MathTex(r's=\text{scale},\;\; z=\text{zero point}', font_size=36).to_edge(DOWN, buff=.75))
