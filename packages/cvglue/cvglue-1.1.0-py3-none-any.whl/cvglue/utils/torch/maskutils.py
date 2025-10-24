import torch
import numpy as np

__all__ = ["Colorize", "convert_map2onehot", "label2image", "labelcolormap", "uint82bin"]


def convert_map2onehot(label_map, channels, value=1.0):
    '''Convert single channel label map to multi-channel one-hot map.

    Args:
        label_map(Tensor):     [Nx1xHxW]
        channels(int):         the value range of label_map, typically specify category size
        value(float):          output onehot map value

    Outs:
        onehot(Tensor):        [NxCxHxW]
    '''
    size = label_map.size()
    onehot_size = (size[0], channels, size[2], size[3])
    onehot = torch.cuda.FloatTensor(torch.Size(onehot_size)).zero_()
    onehot = onehot.scatter_(1, label_map.data.long().cuda(), value)
    return onehot



###############################################################################
# Code from
# https://github.com/ycszen/pytorch-seg/blob/master/transform.py
# Modified so it complies with the Citscape label map colors
###############################################################################
def uint82bin(n, count=8):
    """returns the binary of integer n, count refers to amount of bits"""
    return ''.join([str((n >> y) & 1) for y in range(count-1, -1, -1)])

def labelcolormap(N):
    if N == 35: # cityscape
        cmap = np.array([(  0,  0,  0), (  0,  0,  0), (  0,  0,  0), (  0,  0,  0), (  0,  0,  0), (111, 74,  0), ( 81,  0, 81),
                     (128, 64,128), (244, 35,232), (250,170,160), (230,150,140), ( 70, 70, 70), (102,102,156), (190,153,153),
                     (180,165,180), (150,100,100), (150,120, 90), (153,153,153), (153,153,153), (250,170, 30), (220,220,  0),
                     (107,142, 35), (152,251,152), ( 70,130,180), (220, 20, 60), (255,  0,  0), (  0,  0,142), (  0,  0, 70),
                     (  0, 60,100), (  0,  0, 90), (  0,  0,110), (  0, 80,100), (  0,  0,230), (119, 11, 32), (  0,  0,142)],
                     dtype=np.uint8)
    else:
        cmap = np.zeros((N, 3), dtype=np.uint8)
        for i in range(N):
            r, g, b = 0, 0, 0
            id = i
            for j in range(7):
                str_id = uint82bin(id)
                r = r ^ (np.uint8(str_id[-1]) << (7-j))
                g = g ^ (np.uint8(str_id[-2]) << (7-j))
                b = b ^ (np.uint8(str_id[-3]) << (7-j))
                id = id >> 3
            cmap[i, 0] = r
            cmap[i, 1] = g
            cmap[i, 2] = b
    return cmap

class Colorize(object):
    def __init__(self, n=35):
        self.cmap = labelcolormap(n)
        self.cmap = torch.from_numpy(self.cmap[:n])

    def __call__(self, gray_image):
        size = gray_image.size()
        color_image = torch.ByteTensor(3, size[1], size[2]).fill_(0)

        for label in range(0, len(self.cmap)):
            mask = (label == gray_image[0]).cpu()
            color_image[0][mask] = self.cmap[label][0]
            color_image[1][mask] = self.cmap[label][1]
            color_image[2][mask] = self.cmap[label][2]

        return color_image


def label2image(label, channels):
    '''
    input label format:  NxCxHxW, [-1, 1]
    output image format: Nx3xHxW  [-1, 1]
    '''
    color_map = Colorize(channels)
    norm_cmap = color_map.cmap.float().cuda() / 127.5 - 1
    p_label = (label + 1) / 2
    p_label = torch.matmul(p_label.transpose(1,3), norm_cmap)
    p_label = p_label.transpose(1,3).contiguous()
    return p_label