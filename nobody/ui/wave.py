"""The drawing engine: every picture in the game is sine waves.

One function underlies all of it,

    Y(x, t) = A · sin(2π · f · x + ω · t + φ) + K

amplitude, frequency, speed, phase, offset — and three ways of
turning it into marks:

  Ribbon   a solid strip: at each step along an axis a vertex at
           Y + w and one at Y - w (w a half-width, itself a wave), the
           pairs bound into one polygon — hulls, sails, blades, columns;
  Trail    a line: the points (x, Y(x, t)) joined by a stroke — the sea,
           rigging, strings, the meander, lightning;
  Orbit    a Lissajous figure: x and y each a wave of the parameter —
           ellipses, circles, the paths things float along;

and a Motion, the matrix mode: a translation, rotation and scale, each
sine-driven, applied to a whole asset — a ship riding a swell, an
hourglass breathing, an oar rowing.

Any parameter of a wave may itself be a wave, of time or of the same
x: that is how a sail billows in a wind that comes and goes, and how
one axis modulates another. Waves add (`a + b`): Fourier synthesis — a
square wave from its odd harmonics for the Greek key, a triangle wave
for a pediment, a quick low ripple on a long swell for the sea. A
straight line is a sine with no amplitude, and a slanted one is that,
rotated.

Every frame runs the same pipeline:

    Timeline.step(dt)          time accumulates, and loops safely
    Wave(x, t)                 state: every parameter resolved at t
    asset.vectors(t)           the vertex buffer refilled
    asset.render(canvas)       the buffer flushed through the canvas
"""

import math
from dataclasses import dataclass

TAU = 2 * math.pi

#: where the timeline loops: 600 turns. Every speed that is a multiple
#: of 0.01 rad/s completes whole cycles in it, so nothing jumps.
PERIOD = 600 * TAU


class Timeline:
    """The time accumulator: seconds summed from frame deltas, kept
    within PERIOD so the sum stays exact over a long session."""

    def __init__(self, t=0.0):
        self.t = float(t) % PERIOD

    def step(self, dt):
        self.t = (self.t + max(0.0, float(dt))) % PERIOD
        return self.t


# --- the wave ---------------------------------------------------------------

def _value(v, x, t):
    """A parameter's value at (x, t): a number, or a wave of its own."""
    return v(x, t) if callable(v) else v


def _column(v, us, t):
    """A parameter over the samples `us`."""
    if not callable(v):
        return [v] * len(us)
    if hasattr(v, 'sample'):
        return v.sample(us, t)
    return [v(u, t) for u in us]


def _scaled(v, k):
    return v.scaled(k) if hasattr(v, 'scaled') else v * k


@dataclass(frozen=True)
class Wave:
    """Y(x, t) = A · sin(2π · f · x + ω · t + φ) + K. Each field is a
    number, or a wave of (x, t) resolved when the value is taken."""
    amplitude: object = 0.0     # A
    frequency: object = 0.0     # f: cycles per unit of x
    speed: object = 0.0         # ω: radians per second
    phase: object = 0.0         # φ: radians
    offset: object = 0.0        # K

    def __call__(self, x, t=0.0):
        A = _value(self.amplitude, x, t)
        f = _value(self.frequency, x, t)
        w = _value(self.speed, x, t)
        p = _value(self.phase, x, t)
        K = _value(self.offset, x, t)
        return A * math.sin(TAU * f * x + w * t + p) + K

    def sample(self, us, t=0.0):
        """The wave over the samples `us` — the vector-generation loop,
        with every parameter resolved once when it is a number."""
        A, f, w, p, K = (self.amplitude, self.frequency, self.speed,
                         self.phase, self.offset)
        sin = math.sin
        if not (callable(A) or callable(f) or callable(w) or callable(p) or callable(K)):
            c, d = TAU * f, w * t + p
            return [A * sin(c * u + d) + K for u in us]
        cols = [_column(v, us, t) for v in (A, f, w, p, K)]
        return [a * sin(TAU * ff * u + ww * t + pp) + k
                for u, a, ff, ww, pp, k in zip(us, *cols)]

    # -- synthesis --

    def __add__(self, other):
        return Composite(self, other)

    def __radd__(self, other):
        return self if other == 0 else Composite(other, self)

    def scaled(self, k):
        """The wave `k` times as big (amplitude and offset both)."""
        return Wave(_scaled(self.amplitude, k), self.frequency, self.speed,
                    self.phase, _scaled(self.offset, k))

    def fix(self, x):
        """The wave at one x, as a wave of time alone — what a swell
        does under a ship that is not going anywhere."""
        return Wave(self.amplitude, 0.0, self.speed,
                    TAU * _value(self.frequency, x, 0.0) * x + _value(self.phase, x, 0.0),
                    self.offset)

    def slope(self):
        """dY/dx — which is a sine too, a quarter turn ahead: the tilt
        of whatever rides the wave."""
        return Wave(_scaled(self.amplitude, TAU * self.frequency), self.frequency,
                    self.speed, self.phase + math.pi / 2, 0.0)

    # -- shapes over a span, for building things --

    @classmethod
    def flat(cls, K=0.0):
        """A straight line: no amplitude."""
        return cls(offset=K)

    @classmethod
    def bulge(cls, A, span, K=0.0):
        """Half a cycle over `span`: nothing at either end, A in the middle."""
        return cls(A, 1.0 / (2 * span), 0.0, 0.0, K)

    @classmethod
    def rise(cls, A, span, K=0.0):
        """A quarter cycle over `span`: nothing at the start, A at the end."""
        return cls(A, 1.0 / (4 * span), 0.0, 0.0, K)

    @classmethod
    def fall(cls, A, span, K=0.0):
        """A quarter cycle over `span`, the other way: A at the start,
        nothing at the end."""
        return cls(A, 1.0 / (4 * span), 0.0, math.pi / 2, K)

    @classmethod
    def square(cls, A, f, harmonics=6, speed=0.0, phase=0.0, K=0.0):
        """A square wave, as Fourier drew it: the odd harmonics, the
        ringing left in."""
        return Composite(*[cls(4 * A / (math.pi * n), n * f, n * speed, n * phase,
                               K if n == 1 else 0.0)
                           for n in range(1, 2 * harmonics, 2)])

    @classmethod
    def triangle(cls, A, f, harmonics=4, speed=0.0, phase=0.0, K=0.0):
        """A triangle wave from its odd harmonics, alternating in sign."""
        return Composite(*[cls((-1) ** k * 8 * A / (math.pi ** 2 * n ** 2), n * f,
                               n * speed, n * phase, K if n == 1 else 0.0)
                           for k, n in enumerate(range(1, 2 * harmonics, 2))])

    @classmethod
    def sawtooth(cls, A, f, harmonics=6, speed=0.0, phase=0.0, K=0.0):
        """A sawtooth from every harmonic: a slow climb and a drop —
        a thing that falls and is back at the top."""
        return Composite(*[cls((-1) ** (n + 1) * 2 * A / (math.pi * n), n * f,
                               n * speed, n * phase, K if n == 1 else 0.0)
                           for n in range(1, harmonics + 1)])

    @classmethod
    def bounce(cls, A, f, harmonics=4, speed=0.0, phase=0.0, K=0.0):
        """|sin|, as its cosine series: A at the peaks, never below
        K — a ball that bounces, a coin that spins."""
        parts = [cls(0.0, 0.0, 0.0, 0.0, K + 2 * A / math.pi)]
        for k in range(1, harmonics + 1):
            parts.append(cls(-4 * A / (math.pi * (4 * k * k - 1)), 2 * k * f,
                             2 * k * speed, 2 * k * phase + math.pi / 2))
        return Composite(*parts)


class Composite:
    """Waves summed: Fourier synthesis. Behaves as a wave."""

    def __init__(self, *parts):
        flat = []
        for p in parts:
            flat.extend(p.parts if isinstance(p, Composite) else [p])
        self.parts = tuple(flat)

    def __call__(self, x, t=0.0):
        return sum(p(x, t) for p in self.parts)

    def sample(self, us, t=0.0):
        cols = [p.sample(us, t) for p in self.parts]
        return [sum(vs) for vs in zip(*cols)]

    def __add__(self, other):
        return Composite(self, other)

    def __radd__(self, other):
        return self if other == 0 else Composite(other, self)

    def scaled(self, k):
        return Composite(*[p.scaled(k) for p in self.parts])

    def fix(self, x):
        return Composite(*[p.fix(x) for p in self.parts])

    def slope(self):
        return Composite(*[p.slope() for p in self.parts])


# --- the matrix mode ----------------------------------------------------------

class Motion:
    """A translation, a rotation and a scale about a pivot, each a
    number or a wave of time — and a mirror, for a thing that faces
    the other way: the transform an asset goes through rather than a
    shape it is."""

    def __init__(self, dx=0.0, dy=0.0, angle=0.0, scale=1.0, pivot=(0.0, 0.0),
                 mirror=False):
        self.dx, self.dy, self.angle, self.scale = dx, dy, angle, scale
        self.pivot, self.mirror = pivot, mirror

    def matrix(self, t=0.0):
        """(a, b, c, d, e, f): x' = a·x + b·y + e, y' = c·x + d·y + f."""
        dx = _value(self.dx, 0.0, t)
        dy = _value(self.dy, 0.0, t)
        angle = _value(self.angle, 0.0, t)
        scale = _value(self.scale, 0.0, t)
        m = -1.0 if self.mirror else 1.0
        cos, sin = math.cos(angle), math.sin(angle)
        a, b, c, d = scale * m * cos, -scale * sin, scale * m * sin, scale * cos
        px, py = self.pivot
        return a, b, c, d, px + dx - a * px - b * py, py + dy - c * px - d * py

    def apply(self, points, t=0.0):
        a, b, c, d, e, f = self.matrix(t)
        return [(a * x + b * y + e, c * x + d * y + f) for x, y in points]

    def point(self, p, t=0.0):
        return self.apply([p], t)[0]


def chain(*motions):
    """Motions applied in order; None and nested chains allowed."""
    out = []
    for m in motions:
        if m is None:
            continue
        if isinstance(m, Motion):
            out.append(m)
        else:
            out.extend(chain(*m))
    return out


def move(points, motion, t=0.0):
    for m in chain(motion):
        points = m.apply(points, t)
    return points


# --- the assets -------------------------------------------------------------------

def _steps(length, step):
    n = max(1, math.ceil(abs(length) / step))
    return [length * i / n for i in range(n + 1)]


class Trail:
    """A line: the points (u, Y(u, t)) from u = 0 to u = length along
    an axis from `origin`, a stroke wide. Negative length runs the
    other way."""

    def __init__(self, wave, length, axis='x', origin=(0.0, 0.0), step=2.0, closed=False):
        self.wave, self.length, self.axis = wave, length, axis
        self.origin, self.step, self.closed = origin, step, closed
        self.buffer = []

    def vectors(self, t=0.0, motion=None):
        us = _steps(self.length, self.step)
        vs = self.wave.sample(us, t)
        ox, oy = self.origin
        if self.axis == 'x':
            pts = [(ox + u, oy + v) for u, v in zip(us, vs)]
        else:
            pts = [(ox + v, oy + u) for u, v in zip(us, vs)]
        self.buffer = move(pts, motion, t)
        return self.buffer

    def render(self, canvas, color, t=0.0, width=1, motion=None):
        pts = self.vectors(t, motion)
        if len(pts) > 1:
            canvas.lines(color, self.closed, pts, width)


class Ribbon:
    """A solid strip along an axis: a centre wave and a half-width
    wave of the distance u along it, the two edges bound into one
    polygon. Filled, or outlined when rendered with a width."""

    def __init__(self, centre, half, length, axis='x', origin=(0.0, 0.0), step=2.0):
        self.centre, self.half, self.length, self.axis = centre, half, length, axis
        self.origin, self.step = origin, step
        self.buffer = []

    def vectors(self, t=0.0, motion=None):
        us = _steps(self.length, self.step)
        cs = self.centre.sample(us, t)
        ws = _column(self.half, us, t)
        ox, oy = self.origin
        if self.axis == 'x':
            upper = [(ox + u, oy + c - w) for u, c, w in zip(us, cs, ws)]
            lower = [(ox + u, oy + c + w) for u, c, w in zip(us, cs, ws)]
        else:
            upper = [(ox + c - w, oy + u) for u, c, w in zip(us, cs, ws)]
            lower = [(ox + c + w, oy + u) for u, c, w in zip(us, cs, ws)]
        self.buffer = move(upper + lower[::-1], motion, t)
        return self.buffer

    def render(self, canvas, color, t=0.0, width=0, motion=None):
        pts = self.vectors(t, motion)
        if len(pts) > 2:
            canvas.polygon(color, pts, width)


class Orbit:
    """A Lissajous figure about a centre: x and y each a wave of the
    parameter s, which runs once round [0, 1). With speeds, `at(0, t)`
    is a point going round it."""

    def __init__(self, x, y, centre=(0.0, 0.0), samples=48):
        self.x, self.y, self.centre, self.samples = x, y, centre, samples
        self.buffer = []

    @classmethod
    def ellipse(cls, centre, rx, ry, samples=None):
        n = samples or max(12, min(96, int(4 * (rx + ry))))
        return cls(Wave(rx, 1.0, 0.0, math.pi / 2), Wave(ry, 1.0), centre, n)

    def at(self, s, t=0.0):
        cx, cy = self.centre
        return cx + self.x(s, t), cy + self.y(s, t)

    def vectors(self, t=0.0, motion=None):
        ss = [i / self.samples for i in range(self.samples)]
        xs, ys = self.x.sample(ss, t), self.y.sample(ss, t)
        cx, cy = self.centre
        self.buffer = move([(cx + x, cy + y) for x, y in zip(xs, ys)], motion, t)
        return self.buffer

    def render(self, canvas, color, t=0.0, width=0, motion=None, closed=True):
        pts = self.vectors(t, motion)
        if len(pts) > 2 and closed:
            canvas.polygon(color, pts, width)
        elif len(pts) > 1:
            canvas.lines(color, False, pts, max(1, width))


# --- lines between points: the matrix mode at work ---------------------------------

def _turn(p, q):
    (x0, y0), (x1, y1) = p, q
    return math.hypot(x1 - x0, y1 - y0), Motion(angle=math.atan2(y1 - y0, x1 - x0), pivot=p)


def stroke(canvas, p, q, color, width=1, bend=None, t=0.0, motion=None, step=None):
    """A line from p to q: a sine with no amplitude, rotated into
    place — or bent, when `bend` is an amplitude (a bow across the
    whole length) or a function of the length giving a wave."""
    length, turn = _turn(p, q)
    if length == 0:
        return
    if bend is None:
        wave, step = Wave(), length
    elif callable(bend):
        wave = bend(length)
    else:
        wave = Wave.bulge(bend, length)
    trail = Trail(wave, length, 'x', p, step or max(1.0, length / 12))
    trail.render(canvas, color, t, width, chain(turn, motion))


def band(canvas, p, q, half, color, width=0, t=0.0, motion=None, step=None, centre=None):
    """A solid strip from p to q: `half` a number, or a function of
    the length giving the half-width wave along it (a blade, a post);
    `centre` likewise, to bend the strip."""
    length, turn = _turn(p, q)
    if length == 0:
        return
    half = half(length) if callable(half) else half
    centre = centre(length) if callable(centre) else (centre or Wave())
    ribbon = Ribbon(centre, half, length, 'x', p, step or max(1.0, length / 12))
    ribbon.render(canvas, color, t, width, chain(turn, motion))
