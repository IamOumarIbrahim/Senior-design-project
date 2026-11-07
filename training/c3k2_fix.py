#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# the normal C3k2 block splits with chunk() and the pruner cant follow that
# so it is swapped for a block with two separate input convs, same numbers come out
# comes from our pruning study (pruning-missed-detections)
import torch
import torch.nn as nn
import ultralytics.nn.modules as um
import ultralytics.nn.modules.block as ub
from ultralytics.nn.modules.block import C3k2, Conv


class C3k2_v2(nn.Module):

    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):
        nn.Module.__init__(self)
        self.c = int(c2 * e)
        self.cv0 = Conv(c1, self.c, 1, 1)
        self.cv1 = Conv(c1, self.c, 1, 1)
        self.cv2 = Conv((2 + n) * self.c, c2, 1)

    def forward(self, x):
        y = [self.cv0(x), self.cv1(x)]
        for m in self.m:
            y.append(m(y[len(y) - 1]))
        return self.cv2(torch.cat(y, 1))


# torch.load has to be able to find the class
C3k2_v2.__module__ = "ultralytics.nn.modules.block"
ub.C3k2_v2 = C3k2_v2
um.C3k2_v2 = C3k2_v2


def move_weights(old, new):
    new.cv2 = old.cv2
    new.m = old.m

    half = old.cv1.conv.weight.data.shape[0] // 2
    new.cv0.conv.weight.data.copy_(old.cv1.conv.weight.data[:half])
    new.cv1.conv.weight.data.copy_(old.cv1.conv.weight.data[half:])
    new.cv0.bn.weight.data.copy_(old.cv1.bn.weight.data[:half])
    new.cv1.bn.weight.data.copy_(old.cv1.bn.weight.data[half:])
    new.cv0.bn.bias.data.copy_(old.cv1.bn.bias.data[:half])
    new.cv1.bn.bias.data.copy_(old.cv1.bn.bias.data[half:])
    new.cv0.bn.running_mean.data.copy_(old.cv1.bn.running_mean.data[:half])
    new.cv1.bn.running_mean.data.copy_(old.cv1.bn.running_mean.data[half:])
    new.cv0.bn.running_var.data.copy_(old.cv1.bn.running_var.data[:half])
    new.cv1.bn.running_var.data.copy_(old.cv1.bn.running_var.data[half:])

    for name in ["i", "f", "type", "np"]:
        if hasattr(old, name):
            setattr(new, name, getattr(old, name))


def swap_blocks(module):
    for name, child in module.named_children():
        if isinstance(child, C3k2):
            new = C3k2_v2(child.cv1.conv.in_channels, child.cv2.conv.out_channels, len(child.m),
                          True, 1, child.c / child.cv2.conv.out_channels)
            move_weights(child, new)
            setattr(module, name, new)
        else:
            swap_blocks(child)
