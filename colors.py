WHITE = (238/255, 238/255, 210/255)
BLACK = (118/255, 150/255, 86/255)
BACKGROUND = (81/255, 79/255, 75/255)


def constantToHexStr(color):
    return "#" + ('%02x%02x%02x' % (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)))
