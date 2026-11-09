"""Raspberry Pi 5 board model (cm, board centre at origin + offset), shared by several scenes."""
import math, random
import bpy
from blib import *

T = 0.16
HOLES = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]


def M():
    return dict(
        pcb=mat('pcb', (0.03, 0.22, 0.09), 0.38, coat=0.6), silk=mat('silk', (0.92, 0.92, 0.88), 0.6),
        gold=mat('gold', (1.0, 0.76, 0.33), 0.22, 1.0), nickel=mat('nickel', (0.80, 0.80, 0.80), 0.25, 1.0),
        alu=mat('alu', (0.86, 0.87, 0.89), 0.3, 1.0), blk=mat('blk', (0.015, 0.015, 0.017), 0.45),
        blk_m=mat('blk_m', (0.03, 0.03, 0.035), 0.7), chip=mat('chip', (0.02, 0.02, 0.022), 0.35, coat=0.3),
        blue=mat('usb_blue', (0.02, 0.18, 0.75), 0.45), white=mat('white', (0.85, 0.85, 0.82), 0.5),
        tan=mat('cap', (0.55, 0.42, 0.25), 0.5), red=mat('red_logo', (0.75, 0.05, 0.15), 0.4))


def build(ox=0.0, oy=0.0, z=0.0, cooler=True, seed=4):
    m = M(); rng = random.Random(seed)
    mm = lambda x, y: ((x - 42.5) / 10 + ox, (y - 28) / 10 + oy)
    b = box('pi5', (8.5, 5.6, T), (ox, oy, z + T / 2), m['pcb'], bevel=0.02)
    for (x, y) in HOLES:
        boolean(b, cyl('h', 0.135, 1, (*mm(x, y), z), None, 32))
        cyl('ring', 0.3, 0.012, (*mm(x, y), z + T + 0.006), m['gold'], 48)
    top = z + T
    box('ram', (1.4, 1.2, 0.1), (*mm(45, 31), top + 0.05), m['chip'], 0.01)
    box('rp1', (0.75, 0.75, 0.09), (*mm(63, 25), top + 0.045), m['chip'], 0.01)
    box('soc', (1.7, 1.7, 0.12), (*mm(29, 31), top + 0.06), m['alu'], 0.03)
    box('wifi', (1.0, 1.25, 0.15), (*mm(8, 40), top + 0.075), m['nickel'], 0.01)
    cx, cy = mm(32.5, 52.5)
    box('hdr', (5.08, 0.5, 0.25), (cx, cy, top + 0.125), m['blk'], 0.01)
    for i in range(20):
        for j in (-1, 1):
            box('pin', (0.064, 0.064, 0.84), (cx - 2.413 + i * 0.254, cy + j * 0.127, top + 0.42), m['gold'])
    ex = mm(85 - 8.5, 0)[0]
    box('rj45', (2.1, 1.6, 1.35), (ex, mm(0, 10.25)[1], top + 0.675), m['nickel'], 0.03)
    box('rj45_mouth', (0.05, 1.15, 0.85), (ex + 1.05, mm(0, 10.25)[1], top + 0.6), m['blk'])
    for yc, col in ((29.0, m['blue']), (47.0, m['blk'])):
        box('usb', (1.75, 1.33, 1.56), (ex + 0.1, mm(0, yc)[1], top + 0.78), m['nickel'], 0.02)
        for k in (0.42, 1.12):
            box('usb_mouth', (0.05, 1.18, 0.52), (ex + 0.98, mm(0, yc)[1], top + k), m['blk'])
            box('usb_tongue', (0.06, 0.95, 0.16), (ex + 0.99, mm(0, yc)[1], top + k - 0.05), col)
    box('usbc', (0.9, 0.75, 0.32), (*mm(11.2, 1.8), top + 0.16), m['nickel'], 0.1)
    for x in (25.8, 39.2):
        box('hdmi', (0.65, 0.75, 0.3), (*mm(x, 1.8), top + 0.15), m['nickel'], 0.03)
    for x in (47.5, 54.5):
        box('mipi', (0.55, 0.35, 0.12), (*mm(x, 3.5), top + 0.06), m['blk'], 0.01)
    box('pcie', (0.35, 1.6, 0.13), (*mm(1.8, 28), top + 0.065), m['blk'], 0.01)
    for _ in range(220):
        x, y = rng.uniform(6, 58), rng.uniform(6, 46)
        sx, sy = (0.2, 0.1) if rng.random() < 0.25 else (0.1, 0.05)
        if rng.random() < 0.5:
            sx, sy = sy, sx
        box('smd', (sx, sy, 0.05), (*mm(x, y), top + 0.025), m['tan'] if rng.random() < 0.55 else m['blk_m'])
    text('Raspberry Pi 5', (*mm(53, 12), top + 0.002), 0.32, m['silk'], extrude=0.0003)
    if cooler:
        kx, ky = mm(40, 28); zk = top + 0.15
        box('ac_plate', (5.6, 4.4, 0.18), (kx, ky, zk + 0.09), m['alu'], 0.02)
        for i in range(13):
            box('fin', (0.07, 2.6, 0.95), (kx - 2.6 + i * 0.2, ky - 0.85, zk + 0.655), m['alu'], 0.008)
        fr = box('fan_frame', (2.8, 2.6, 0.95), (kx + 1.35, ky + 0.85, zk + 0.655), m['blk'], 0.08)
        boolean(fr, cyl('fh', 1.15, 1.2, (kx + 1.35, ky + 0.85, zk + 0.78), None, 64))
        cyl('hub', 0.45, 0.85, (kx + 1.35, ky + 0.85, zk + 0.63), m['blk_m'], 48, bevel=0.02)
        for i in range(11):
            a = i * 2 * math.pi / 11
            box('blade', (0.6, 0.06, 0.75), (kx + 1.35 + 0.78 * math.cos(a), ky + 0.85 + 0.78 * math.sin(a), zk + 0.61),
                m['blk'], rot=(0, 0, a + 0.5))
        cyl('sticker', 0.4, 0.004, (kx + 1.35, ky + 0.85, zk + 1.057), m['white'], 48)
        cyl('logo', 0.17, 0.006, (kx + 1.35, ky + 0.85, zk + 1.06), m['red'], 32)

    def pin(n):
        """World position of the tip of header pin n (1..40)."""
        col = (n - 1) // 2
        y = 53.77 if n % 2 == 0 else 51.27
        return (*mm(7.1 + col * 2.54, y), top + 0.84)
    return pin, top
