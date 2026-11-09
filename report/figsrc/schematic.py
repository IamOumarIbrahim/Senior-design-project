"""Formal schematic of the LED-bar driver and the 5 V rail (schemdraw)."""
import schemdraw
import schemdraw.elements as elm
import matplotlib
matplotlib.use('Agg')
schemdraw.use('matplotlib')
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']

schemdraw.config(font='Times New Roman', fontsize=13, lw=1.4)
with schemdraw.Drawing(show=False) as d:
    d.config(unit=2.6)
    vin = elm.Vdd().label('5 V (pin 2)')
    elm.Line().down(0.5)
    bar = elm.LED().down().label('RGB bar', loc='bottom', ofst=(0.2, 0))
    elm.Line().down(0.6)
    q = elm.NFet(bulk=False).anchor('drain').theta(0).reverse().label('Q1\nIRLZ44N', loc='right', ofst=(-0.2, 0))
    elm.Ground().at(q.source)
    elm.Line().left(1.4).at(q.gate)
    d.push()
    r1 = elm.Resistor().left().label('R1  220 Ω')
    elm.Dot(open=True).label('GPIO18 (pin 12)', loc='left')
    d.pop()
    elm.Resistor().down().label('R2  10 kΩ', loc='bottom')
    elm.Ground()
d.save('../Figures/schematic_led.pdf')
d.save('out/schematic_led.png', dpi=200)
print('done')
