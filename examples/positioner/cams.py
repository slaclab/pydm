import numpy as np

# Cam Geometry
R = 31
L = 1.5875
S1 = 34.925
S2 = 290.5
c = 282.0416
b = c + S1 - np.sqrt(2) * R
a = 139.6238
dx = 74.55
dy = 245.47

# Silence invalid arcsin arguments, we deal with that ourselves.
np.seterr(invalid="ignore")


def real2cams(coords):
    (x, y, theta) = coords
    theta = theta * 1.0e-3  # Convert to rad from mrad

    x1 = x + (a * np.cos(theta)) + (b * np.sin(theta)) - a
    y1 = y - (b * np.cos(theta)) + (a * np.sin(theta)) + c
    bp = (np.cos(theta) + np.sin(theta)) / np.sqrt(2.0)
    bm = (np.cos(theta) - np.sin(theta)) / np.sqrt(2.0)

    p1 = theta - np.arcsin((1 / L) * (((x1 + S2) * np.sin(theta)) - (y1 * np.cos(theta)) + (c - b)))
    p2 = theta - np.arcsin((1 / L) * (((x1 + S1) * bm) + (y1 * bp) - R))
    p3 = theta - np.arcsin((1 / L) * (((x1 - S1) * bp) - (y1 * bm) + R))

    valid = False
    if np.all(np.isreal([p1, p2, p3])) and not np.any(np.isnan([p1, p2, p3])):
        valid = True

    return (p1 * 180.0 / np.pi, p2 * 180.0 / np.pi, p3 * 180.0 / np.pi, valid)
