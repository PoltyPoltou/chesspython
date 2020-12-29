from typing import Tuple


WHITE = (238/255, 238/255, 210/255)
BLACK = (118/255, 150/255, 86/255)
YELLOW = (1, 1, 0)
BACKGROUND = (81/255, 79/255, 75/255)


def constantToHexStr(color):
    return "#" + ('%02x%02x%02x' % (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)))


def darkerColor(colorTuple: Tuple[int, int, int], scale=0.8) -> Tuple[int, int, int]:
    (r, g, b) = colorTuple
    return ((r*scale), (g*scale), (b*scale))


def brighterColor(colorTuple: Tuple[int, int, int], scale=1/0.8) -> Tuple[int, int, int]:
    return darkerColor(colorTuple, scale)


def middleColor(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> Tuple[int, int, int]:
    return baricenterColor(color1, color2)


def baricenterColor(color1: Tuple[int, int, int], color2: Tuple[int, int, int], x1=0.5, x2=0.5) -> Tuple[int, int, int]:
    return ((x1*color1[0]+x2*color2[0]) / (x1+x2), (x1*color1[1]+x2*color2[1]) / (x1+x2), (x1*color1[2]+x2*color2[2]) / (x1+x2))
