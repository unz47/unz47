"""Gear geometry: toothed outlines as SVG path data, and trains of meshing gears.

Angles are radians, measured clockwise from +x (SVG's y axis points down).
"""

import math
from dataclasses import dataclass

TAU = math.tau


def polar(cx, cy, r, a) -> str:
    return f"{cx + r * math.cos(a):.2f} {cy + r * math.sin(a):.2f}"


def circle(cx, cy, r) -> str:
    return f"M{cx + r:.2f} {cy:.2f}A{r} {r} 0 1 1 {cx - r:.2f} {cy:.2f}A{r} {r} 0 1 1 {cx + r:.2f} {cy:.2f}Z"


def teeth(cx, cy, z, m, rot=0.0) -> str:
    """Closed outline of z trapezoid teeth with module m; tooth i is centred on rot + i * TAU / z."""
    r = m * z / 2
    tip, root, p = r + m, r - 1.25 * m, TAU / z
    d = []
    for i in range(z):
        a = rot + i * p
        d.append(("M" if i == 0 else "L") + polar(cx, cy, root, a - .30 * p))
        d.append("L" + polar(cx, cy, tip, a - .16 * p))
        d.append(f"A{tip:.2f} {tip:.2f} 0 0 1 " + polar(cx, cy, tip, a + .16 * p))
        d.append("L" + polar(cx, cy, root, a + .30 * p))
        d.append(f"A{root:.2f} {root:.2f} 0 0 1 " + polar(cx, cy, root, a + .70 * p))
    return "".join(d) + "Z"


def window(cx, cy, ri, ro, a1, a2, half) -> str:
    """Annular cut-out between two spokes of constant half-width `half`."""
    o1, o2 = a1 + math.asin(half / ro), a2 - math.asin(half / ro)
    i1, i2 = a1 + math.asin(half / ri), a2 - math.asin(half / ri)
    big = 1 if o2 - o1 > math.pi else 0
    return (f"M{polar(cx, cy, ro, o1)}A{ro:.2f} {ro:.2f} 0 {big} 1 {polar(cx, cy, ro, o2)}"
            f"L{polar(cx, cy, ri, i2)}A{ri:.2f} {ri:.2f} 0 0 0 {polar(cx, cy, ri, i1)}Z")


def gear(cx, cy, z, m, rot=0.0, hub=0.0, windows=0, bore=0.0) -> str:
    """Path data for a gear (use fill-rule evenodd).

    hub: radius of the axle hole. windows: number of cut-outs between spokes.
    bore: radius of one big central opening instead of spokes (a wheel).
    """
    d = teeth(cx, cy, z, m, rot)
    if bore:
        return d + circle(cx, cy, bore)
    if hub:
        d += circle(cx, cy, hub)
    if windows:
        ro = m * z / 2 - 2.65 * m
        ri = max(hub * 1.9, ro * .38)
        for k in range(windows):
            a = rot + k * TAU / windows
            d += window(cx, cy, ri, ro, a, a + TAU / windows, max(2.5, ro * .09))
    return d


@dataclass
class Gear:
    x: float
    y: float
    z: int
    rot: float    # initial rotation that makes the teeth interlock
    speed: float  # turns per second; negative is counter-clockwise


def train(origin, z0, m, speed0, spec) -> list[Gear]:
    """Lay out meshing gears.

    spec rows are (parent index, z, direction in degrees) to mesh with the parent,
    or (parent index, z, "axle") for a gear fixed to the parent's shaft.
    """
    gears = [Gear(origin[0], origin[1], z0, 0.0, speed0)]
    for parent, z, how in spec:
        p = gears[parent]
        if how == "axle":
            gears.append(Gear(p.x, p.y, z, p.rot, p.speed))
            continue
        th = math.radians(how)
        dist = m * (p.z + z) / 2
        phase = (th - p.rot) * p.z / TAU  # parent's tooth phase facing the new gear
        rot = th + math.pi - (.5 - phase) * TAU / z
        gears.append(Gear(p.x + dist * math.cos(th), p.y + dist * math.sin(th), z, rot,
                          -p.speed * p.z / z))
    return gears
