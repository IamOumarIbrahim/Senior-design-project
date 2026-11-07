#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# structured pruning of yolo11n by channel l1 norm
# order is fine tune, prune, fine tune again, quantize, then test on the pi
# python prune.py weights.pt 0.2 output.pt
# python prune.py weights.pt 0.2 output.pt data.yaml epochs     fine tunes after
import copy
import sys

import torch
import torch.nn as nn
import torch_pruning as tp
from ultralytics import YOLO
from ultralytics.models.yolo.detect import DetectionTrainer

import c3k2_fix


# stops ultralytics from building the big model again from the yaml
class PrunedTrainer(DetectionTrainer):

    def get_model(self, cfg=None, weights=None, verbose=True):
        if isinstance(weights, nn.Module):
            return weights
        return DetectionTrainer.get_model(self, cfg, weights, verbose)


def count_params(net):
    total = 0
    for p in net.parameters():
        total = total + p.numel()
    return total


def prune_model(path, ratio, out):
    y = YOLO(path)
    net = copy.deepcopy(y.model)
    before = count_params(net)

    c3k2_fix.swap_blocks(net)
    for p in net.parameters():
        p.requires_grad = True

    # the head and the attention block stay as they are
    keep = []
    for m in net.modules():
        name = m.__class__.__name__
        if name == "Detect" or name == "C2PSA" or name == "PSABlock" or name == "Attention":
            keep.append(m)
        elif isinstance(m, nn.Conv2d) and m.out_channels < 8:
            keep.append(m)

    example = torch.randn(1, 3, 640, 640, requires_grad=True)
    pruner = tp.pruner.GroupNormPruner(model=net, example_inputs=example,
                                       importance=tp.importance.GroupMagnitudeImportance(p=1),
                                       iterative_steps=1, pruning_ratio=ratio, ignored_layers=keep)
    pruner.step()

    net.eval()
    for p in net.parameters():
        p.requires_grad = False
    with torch.no_grad():
        net(torch.zeros(1, 3, 640, 640))

    after = count_params(net)
    print("----------------------")
    print("Params before= " + str(before))
    print("Params after= " + str(after))
    print("Removed= " + str(round(100 * (before - after) / before, 1)) + "%")
    print("----------------------")

    ckpt = {"model": net, "optimizer": None, "train_args": y.overrides, "epoch": -1}
    torch.save(ckpt, out)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("use: python prune.py weights.pt ratio output.pt [data.yaml epochs]")
    else:
        prune_model(sys.argv[1], float(sys.argv[2]), sys.argv[3])
        if len(sys.argv) > 5:
            m = YOLO(sys.argv[3])
            m.train(trainer=PrunedTrainer, data=sys.argv[4], epochs=int(sys.argv[5]), imgsz=640, patience=30, project="runs", name="pruned")
