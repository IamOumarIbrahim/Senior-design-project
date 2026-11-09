"""3D render of the SDP2 hardware bench (all purchased parts on one table)."""
import numpy as np
from gl3d import Renderer, Obj, T, R, chain, backdrop, rbox
import parts as P
from annotate import callouts

OUT = '../Figures/'
wood = P.wood_texture('out/wood.png')

objs = []
objs += P.table(wood)
y0 = 0.35
pi_M = T(-6, y0, -8); objs += P.pi_case(pi_M)
objs += P.webcam(T(-20, y0, -5) @ R('y', 12))
objs += P.pebble(T(-31, y0, -30) @ R('y', 20))
objs += P.pebble(T(31, y0, -30) @ R('y', -20))
amber = [(1.0, 0.62 + 0.1 * np.sin(k), 0.12) for k in range(12)]
objs += P.light_bar(T(0, y0, -34), amber)
objs += P.display_on_holder(T(26, y0, -4), 'out/ui_tablet_dark.png', yaw=-22, tilt=-10)
objs += P.steering_wheel(T(-46, y0, 16) @ R('y', 28))
objs += P.usb_hub(T(10, y0, 6))
objs += P.psu(T(-46, y0, -12) @ R('y', 25))
objs += P.breadboard(T(14, y0, -20))
objs += P.laptop(T(46, y0, -18) @ R('y', -32), 'out/ui_dashboard.png')
objs.append(Obj(rbox(2.4, .12, 1.6, .1), T(2, y0 + .06, 14) @ R('y', 20), color=(0.75, 0.12, 0.15), spec=.6))  # microSD
objs.append(Obj(rbox(1.2, .13, 1.6, .1), T(1.0, y0 + .07, 14.4) @ R('y', 20), color=(0.2, 0.2, 0.22), spec=.6))

c = P.cable; yc = y0 + .25
objs += [
    c([(-42, 2.5, -10), (-36, yc, -4), (-22, yc, 4), (-12, yc, 2), (-9.3, 1.4, -4.0)], P.WHITE),         # PSU -> USB-C
    c([(-7.6, 1.4, -4.0), (-6, yc, 3), (8, yc, 0), (20, yc, -1), (25, 1.5, -4.5), (25.6, 10, -5.2), (24, 15, -5.5)], P.BLACK, .25),  # micro-HDMI
    c([(-0.6, 1.6, -9.6), (2.5, yc, -7), (4, yc, 1), (4.6, .9, 6)], P.BLACK),                          # Pi USB -> hub
    c([(6.7, .9, 7.7), (5, yc, 12), (-8, yc, 12), (-16, yc, 4), (-19, yc, -1), (-20, 3, -4.6), (-20, 9, -5)], P.BLACK, .2),  # hub -> webcam
    c([(8.9, .9, 7.7), (8, yc, 18), (-10, yc, 26), (-30, yc, 20), (-40, 3, 16)], P.BLACK, .24),       # hub -> wheel
    c([(11.1, .9, 7.7), (16, yc, 13), (37, yc, 6), (40, yc, -16), (33, 1, -26)], (0.15, 0.15, 0.17)),  # hub -> speakers
    c([(-27, 1, -27), (-14, yc, -40), (14, yc, -40), (27, 1, -27)], (0.15, 0.15, 0.17), .18),          # speaker link
    c([(13.3, .9, 7.7), (17, yc, 6), (22, yc, 1), (25.4, 1.4, -2.6), (25.6, 9, -3)], P.BLACK, .17),    # touch micro-USB
]
for k, col in enumerate([(0.85, 0.15, 0.15), (0.1, 0.1, 0.1), (0.95, 0.8, 0.1)]):              # GPIO jumpers
    dz = k * .5
    objs.append(c([(-8 + k * .6, 3.2, -11.4), (-6 + k * .6, yc, -15 - dz), (6, yc, -19 - dz), (11.5 + k * .9, 1.4, -20 + dz * .2)], col, .12, 8))
for k, col in enumerate([(0.85, 0.15, 0.15), (0.1, 0.1, 0.1)]):                                  # MOSFET -> bar
    objs.append(c([(16.5 + k * .6, 1.2, -21.5), (17 + k * .6, yc, -27), (15 + k * .6, 2.6, -33)], col, .12, 8))

r = Renderer(2600, 1600)
eye, tgt = (50, 60, 86), (-3, 2, -6)
img = r.render(objs, eye, tgt, fov=40, light_dir=(-0.5, -1.0, -0.45), light_span=100, bloom=1.0)
bg = backdrop(img)
bg.save('out/bench_raw.png')

anch = {
    'pi': (-6, 4.3, -8), 'ai': (-4.8, 4.0, -8), 'cam': (-20, 13.3, -4), 'spk': (-31, 10, -30), 'bar': (-6, 5, -33),
    'disp': (26, 17, -2.5), 'wheel': (-50, 24, 27), 'hub': (10, 1.4, 6), 'psu': (-46, 4, -12),
    'bb': (14, 2.6, -20), 'lap': (46, 14, -28), 'sd': (2, .5, 14), 'holder': (26, 5, -4), 'case': (-1.5, 2.5, -4.5),
}
pp = {k: r.project([v])[0] for k, v in anch.items()}
B, O, Pp, Rd, G, Tl = '#2f80ed', '#f5a524', '#7b61ff', '#eb5757', '#27ae60', '#22a39a'
items = [
    dict(xy=pp['pi'], side='auto', num=1, color=B, title='Raspberry Pi 5 (8 GB)', text='Quad Cortex-A76 @ 2.4 GHz, runs the whole\npipeline: capture, filter, alerts, logging'),
    dict(xy=pp['case'], side='auto', num=2, color=B, title='AI HAT+ (Hailo NPU) inside', text='PCIe accelerator: YOLO11n inference,\nINT8 compiled model (.hef)'),
    dict(xy=pp['cam'], side='auto', num=3, color=B, title='Logitech C922 webcam', text='UVC, 1080p at 30 FPS, aimed at\nthe driver\'s face; 640x640 crop'),
    dict(xy=pp['psu'], side='auto', num=4, color='#6b7686', title='27 W USB-C PD supply', text='5.1 V / 5 A for the Pi 5; unlocks\n1.6 A on the USB ports'),
    dict(xy=pp['spk'], side='auto', num=5, color=O, title='Creative Pebble V3', text='USB speakers: chimes, buzz and\nEnglish/Arabic voice messages'),
    dict(xy=pp['wheel'], side='auto', num=6, color=Rd, title='PXN wheel (haptic prototype)', text='Vibration motors used to prototype\nthe steering-wheel alert (Future)'),
    dict(xy=pp['sd'], side='auto', num=7, color='#6b7686', title='SanDisk Extreme Pro 128 GB', text='OS, model files and the\nSQLite (WAL) event log'),
    dict(xy=pp['bar'], side='auto', num=8, color=O, title='RGB light bar', text='Peripheral visual alert, switched by\nGPIO18 PWM via a logic-level MOSFET'),
    dict(xy=pp['bb'], side='auto', num=9, color=O, title='MOSFET driver (breadboard)', text='Gate resistor + pull-down; flash rate\ncapped at 3 Hz in software'),
    dict(xy=pp['disp'], side='auto', num=10, color=G, title='Hosyond 7" touch display', text='Driver-facing "tablet": status,\ncalibration and settings (HDMI + USB)'),
    dict(xy=pp['holder'], side='auto', num=11, color=G, title='KABCON holder', text='Keeps the display in a glanceable\nposition outside the line of sight'),
    dict(xy=pp['hub'], side='auto', num=12, color='#6b7686', title='UGREEN USB 3.0 hub', text='Fans out camera, speakers, touch\nand wheel; micro-USB lead for touch'),
    dict(xy=pp['lap'], side='auto', num=13, color=Tl, title='Web dashboard (laptop)', text='Post-trip analytics from uploaded\nevent records; no video leaves the car'),
]
callouts(bg, items, OUT + 'bench_3d.png', left_frac=.34, right_frac=.34,
         title='SDP2 hardware bench', subtitle='All 14 items from the Group 34 purchase request, wired as planned for SDP2 (rendered with OpenGL)')
print('done')
