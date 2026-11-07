#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import math


class EMAFilter:

    def __init__(self, tau_s):
        self.tau_s = tau_s
        self.s = {}
        for c in tau_s:
            self.s[c] = 0.0

    # s = alpha x + (1 - alpha) s   and   alpha = 1 - e^(-dt/tau)
    # dt is mesured so it forgets at the same speed at any fps
    def update(self, scores, dt):
        result = {}
        for c in self.tau_s:
            alpha = 1 - math.exp(-dt / self.tau_s[c])
            self.s[c] = alpha * scores[c] + (1 - alpha) * self.s[c]
            result[c] = self.s[c]
        return result

    # start from zero after boot and after camera blocked
    def reset(self):
        for c in self.s:
            self.s[c] = 0.0
