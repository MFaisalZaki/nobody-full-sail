"""The bestiary: everything that can stand on the stage, drawn
black-figure from the engine's parts and nothing else — people, the
one-eyed giant, the witch and the nymph, sirens, the rock and the
whirlpool, cattle and swine, the dead, the horse, walls, a cave, a
tree, houses, smoke, sun, cloud, lightning and rain.

Every sprite is a function `(canvas, x, y, h, t, ...)`: (x, y) is where
it touches the ground, `h` how tall it is, `t` the time; `facing` is 1
for right and -1 for left, `phase` staggers copies of a thing so they
do not move in step, `motion` carries it through whatever the stage is
doing. Nothing is a bitmap; everything breathes.
"""

import math

from . import draw as D
from . import theme as T
from . import wave as W
from .wave import Wave

TAU = W.TAU


def at(x, y, facing=1, motion=None, *before):
    """The placement: local (0, 0) lands on (x, y), mirrored to face
    left; `before` motions act first (a breath, a sway)."""
    return W.chain(*before, W.Motion(dx=x, dy=y, mirror=facing < 0), motion)


# --- people --------------------------------------------------------------------

#: the skeleton, in units of height — feet at (0, 0), up negative: where
#: the hips, the waist, the shoulders and the middle of the head are
HIP, WAIST, SHOULDER, HEAD = -0.46, -0.58, -0.75, -0.905
#: a bone of the arm, upper or lower, in units of height
ARM = 0.19

#: where the hands reach for, as (near hand, far hand) in units of height
ARMS = {
    'down':   ((0.17, -0.38), (-0.15, -0.38)),
    'raised': ((0.30, -1.02), (-0.15, -0.38)),
    'out':    ((0.42, -0.66), (-0.15, -0.38)),
    'up':     ((0.30, -1.08), (-0.30, -1.08)),
    'cup':    ((0.26, -0.84), (-0.15, -0.38)),
    'throw':  ((-0.32, -1.05), (0.17, -0.38)),
}


def _joint(root, mark, bone):
    """Two bones of length `bone` from `root` toward `mark`: where the
    joint between them goes — bent the way an elbow hangs, downward,
    and backward when it is a toss-up — and where the end of the second
    bone lands (short of the mark, when the mark is out of reach)."""
    (rx, ry), (mx, my) = root, mark
    dx, dy = mx - rx, my - ry
    d = math.hypot(dx, dy)
    if d == 0:
        return (rx, ry + bone), (rx, ry + 2 * bone)
    if d >= 2 * bone:
        k = 2 * bone / d
        mx, my = rx + dx * k, ry + dy * k
        return ((rx + mx) / 2, (ry + my) / 2), (mx, my)
    r = math.sqrt(bone * bone - (d / 2) ** 2)
    cx, cy = rx + dx / 2, ry + dy / 2
    px, py = -dy / d * r, dx / d * r
    a, b = (cx + px, cy + py), (cx - px, cy - py)
    return (a if (a[1], -a[0]) > (b[1], -b[0]) else b), (mx, my)


def _arm(c, h, shoulder, mark, color, t, m):
    """An arm from `shoulder` reaching for `mark`: an upper arm that
    swells, a forearm that tapers to the wrist, a hand. Returns where
    the hand is."""
    elbow, hand = _joint(shoulder, mark, ARM * h)
    W.band(c, shoulder, elbow, lambda L: Wave.bulge(0.012 * h, L, 0.028 * h), color, t=t, motion=m)
    W.Orbit.ellipse(elbow, 0.026 * h, 0.026 * h).render(c, color, t, 0, m)
    W.band(c, elbow, hand, lambda L: Wave.fall(0.012 * h, L, 0.016 * h), color, t=t, motion=m)
    W.Orbit.ellipse(hand, 0.026 * h, 0.021 * h).render(c, color, t, 0, m)
    return hand


def _leg(c, h, hip, knee, ankle, heel, toe, color, t, m):
    """A leg: a thigh tapering to the knee, a calf that swells, a foot
    from the heel to a pointed toe."""
    W.band(c, hip, knee, lambda L: Wave.fall(0.022 * h, L, 0.032 * h), color, t=t, motion=m)
    W.Orbit.ellipse(knee, 0.03 * h, 0.03 * h).render(c, color, t, 0, m)
    W.band(c, knee, ankle, lambda L: Wave.bulge(0.014 * h, L, 0.02 * h), color, t=t, motion=m)
    W.band(c, heel, toe, lambda L: Wave.fall(0.012 * h, L, 0.005 * h), color, t=t, motion=m)


def _head(c, h, crown, t, color, eye=T.PAPYRUS, beard=False, hair=False, crest=False,
          fair=False, m=None):
    """A head in profile facing +x, its middle at `crown`, `h` the
    height of whoever it belongs to: a skull, a nose that juts, an
    eye; a pointed beard, long hair down the back, a helmet with a
    plume when asked. `fair` paints the face in the eye's colour and
    lines it in ink — the vases' way of drawing a woman."""
    cx, cy = crown
    face, line = (eye, color) if fair and eye else (color, None)
    nose = lambda L: Wave.fall(0.028 * h, L, 0.004 * h)
    bridge, tip = (cx + 0.05 * h, cy - 0.006 * h), (cx + 0.115 * h, cy + 0.012 * h)
    if hair:                    # long, bound at the nape, down the back
        W.band(c, (cx - 0.03 * h, cy - 0.04 * h), (cx - 0.09 * h, cy + 0.26 * h),
               lambda L: Wave.fall(0.02 * h, L, 0.025 * h), color, t=t, motion=m)
    skull = W.Orbit.ellipse((cx, cy), 0.072 * h, 0.078 * h)
    skull.render(c, face, t, 0, m)
    W.band(c, bridge, tip, nose, face, t=t, motion=m)
    if line:
        skull.render(c, line, t, 1, m)
        W.band(c, bridge, tip, nose, line, width=1, t=t, motion=m)
        # the hair over the crown, framing the face
        W.band(c, (cx - 0.078 * h, cy + 0.03 * h), (cx + 0.062 * h, cy - 0.062 * h),
               lambda L: Wave.bulge(0.03 * h, L, 0.012 * h), color, t=t, motion=m,
               centre=lambda L: Wave.bulge(-0.035 * h, L))
    if beard:
        W.band(c, (cx + 0.035 * h, cy + 0.05 * h), (cx + 0.075 * h, cy + 0.15 * h),
               lambda L: Wave.fall(0.03 * h, L, 0.006 * h), color, t=t, motion=m)
    if crest:                   # a Corinthian helmet: the dome, the nose guard, the plume
        W.Orbit.ellipse((cx - 0.006 * h, cy - 0.014 * h), 0.084 * h, 0.088 * h).render(
            c, color, t, 0, m)
        W.band(c, (cx + 0.06 * h, cy - 0.04 * h), (cx + 0.078 * h, cy + 0.055 * h), 0.017 * h,
               color, t=t, motion=m)
        W.band(c, (cx - 0.19 * h, cy), (cx + 0.1 * h, cy - 0.135 * h),
               lambda L: Wave.bulge(0.042 * h, L, 0.005 * h), color, t=t, motion=m,
               centre=lambda L: Wave.bulge(-0.05 * h, L))
    if eye:
        W.Orbit.ellipse((cx + 0.036 * h, cy - 0.012 * h), 0.022 * h, 0.014 * h).render(
            c, color if fair else eye, t, 0, m)


def figure(c, x, y, h, t, color=T.INK, facing=1, phase=0.0, pose='stand', arms='down',
           crest=False, prop=None, walk=0.0, gown=False, lean=0.0, motion=None,
           eye=T.PAPYRUS, beard=None, fair=False):
    """A person as the vases draw one, feet at (x, y), `h` tall: a
    profile head on a frontal chest, broad at the shoulders and narrow
    at the waist, legs with thighs and calves, arms with elbows, a
    belted tunic to the thigh (or a gown to the ground) with its folds
    scratched in, and what the near hand holds. Men are bearded unless
    told otherwise; `fair` gives the face the vases' white. Poses:
    stand, sit (on a stool), lie. The body breathes; a walk swings the
    legs; `lean` bends the back. Returns the placement, for whatever
    else belongs to the figure."""
    breathe = W.Motion(scale=Wave(0.012, 0.0, 1.3, phase, 1.0))
    lie = W.Motion(angle=math.pi / 2 - 0.25) if pose == 'lie' else None
    m = at(x, y, facing, motion, breathe, lie)
    sit = pose == 'sit'
    drop = 0.04 * h if sit else 0.0                 # the hips sink on a stool
    hip_y, waist_y, shoulder_y, head_y = (v * h + drop for v in (HIP, WAIST, SHOULDER, HEAD))
    if beard is None:
        beard = not gown and not fair
    hem_y = -0.005 * h if gown and not sit else -0.30 * h
    # the legs (and the stool)
    if sit:
        W.band(c, (-0.13 * h, hip_y + 0.03 * h), (0.09 * h, hip_y + 0.03 * h), 0.018 * h,
               color, t=t, motion=m)
        for sx in (-0.1 * h, 0.06 * h):
            W.band(c, (sx, hip_y + 0.04 * h), (sx - 0.01 * h, 0.0), 0.013 * h, color, t=t, motion=m)
        legs = (((0.0, hip_y), (0.25 * h, hip_y + 0.02 * h), (0.22 * h, -0.035 * h),
                 (0.17 * h, -0.015 * h), (0.34 * h, -0.003 * h)),
                ((0.0, hip_y), (0.21 * h, hip_y + 0.035 * h), (0.17 * h, -0.035 * h),
                 (0.12 * h, -0.015 * h), (0.29 * h, -0.003 * h)))
    else:
        legs = (((0.02 * h, hip_y), (0.07 * h, -0.25 * h), (0.05 * h, -0.035 * h),
                 (0.0, -0.015 * h), (0.16 * h, -0.003 * h)),
                ((-0.02 * h, hip_y), (-0.05 * h, -0.25 * h), (-0.08 * h, -0.035 * h),
                 (-0.13 * h, -0.015 * h), (0.03 * h, -0.003 * h)))
    for k, (hip, knee, ankle, heel, toe) in enumerate(legs):
        step = (W.Motion(angle=Wave(0.4 * walk, 0.0, 6.0, k * math.pi + phase), pivot=hip)
                if walk and not sit else None)
        _leg(c, h, hip, knee, ankle, heel, toe, color, t, W.chain(step, m))
    if sit and gown:            # the gown over the lap, and down from the knee
        W.band(c, (0.0, hip_y), (0.24 * h, hip_y + 0.02 * h), 0.065 * h, color, t=t, motion=m)
        W.Ribbon(Wave.flat(0.0), Wave.rise(0.05 * h, 0.3 * h, 0.05 * h), -hip_y - 0.02 * h - 0.005 * h,
                 'y', (0.22 * h, hip_y + 0.02 * h), step=h / 10).render(c, color, t, 0, m)
    # the body: chest, waist, skirt, neck — bent at the hips when leaning
    upper = W.chain(W.Motion(angle=lean, pivot=(0.0, hip_y)), m) if lean else m
    chest = waist_y - shoulder_y
    # broad at the shoulders, narrowing to the waist: an eighth of a
    # cycle, near enough a straight taper, with the shoulders rounded off
    W.Ribbon(Wave.flat(0.0), Wave.flat(0.112 * h) + Wave.rise(-0.06 * h, 2 * chest),
             chest, 'y', (0.0, shoulder_y), step=h / 10).render(c, color, t, 0, upper)
    for sx in (-0.085 * h, 0.085 * h):
        W.Orbit.ellipse((sx, shoulder_y + 0.022 * h), 0.034 * h, 0.03 * h).render(
            c, color, t, 0, upper)
    skirt = 0.13 * h if gown and not sit else 0.04 * h
    W.Ribbon(Wave.flat(0.0), Wave.rise(skirt, hem_y - waist_y, 0.07 * h), hem_y - waist_y,
             'y', (0.0, waist_y), step=h / 10).render(c, color, t, 0, upper)
    W.band(c, (0.0, shoulder_y + 0.01 * h), (0.012 * h, head_y + 0.04 * h), 0.028 * h,
           color, t=t, motion=upper)
    if eye:                     # the belt and the folds, scratched through the black
        W.stroke(c, (-0.07 * h, waist_y), (0.07 * h, waist_y), eye, 1, t=t, motion=upper)
        for k in ((-1, 0, 1) if gown else (-1, 1)):
            W.stroke(c, (k * 0.03 * h, waist_y + 0.03 * h), (k * (0.14 if gown else 0.075) * h, hem_y - 0.03 * h),
                     eye, 1, bend=k * 0.012 * h, t=t, motion=upper)
    # the arms: the far one behind, the near one in front (and swinging,
    # when it gestures)
    near, far = ARMS.get(arms, ARMS['down'])
    swing = (W.Motion(angle=Wave(0.22, 0.0, 2.6, phase), pivot=(0.09 * h, shoulder_y + 0.015 * h))
             if arms in ('raised', 'cup', 'throw', 'out') else None)
    _arm(c, h, (-0.09 * h, shoulder_y + 0.015 * h), (far[0] * h, far[1] * h + drop), color, t, upper)
    _head(c, h, (0.0, head_y), t, color, eye, beard, gown or fair, crest, fair, upper)
    reach = W.chain(swing, upper)
    hand = _arm(c, h, (0.09 * h, shoulder_y + 0.015 * h), (near[0] * h, near[1] * h + drop),
                color, t, reach)
    if prop:
        held(c, prop, hand, h, t, color, reach)
    return m


def held(c, prop, hand, h, t, color, m):
    """What a hand holds, in the figure's own coordinates."""
    hx, hy = hand
    if prop == 'spear':
        W.stroke(c, (hx, 0.03 * h), (hx, -1.25 * h), color, 0.035 * h, t=t, motion=m)
        W.band(c, (hx, -1.22 * h), (hx, -1.42 * h), lambda L: Wave.bulge(0.035 * h, L),
               color, t=t, motion=m)
    elif prop == 'staff':
        W.stroke(c, (hx + 0.04 * h, 0.03 * h), (hx + 0.04 * h, -1.15 * h), color,
                 0.035 * h, t=t, motion=m)
    elif prop == 'stick':
        W.stroke(c, (hx + 0.1 * h, -0.03 * h), (hx - 0.02 * h, hy - 0.06 * h), color,
                 0.03 * h, t=t, motion=m)
    elif prop == 'cup':
        W.Orbit.ellipse((hx + 0.02 * h, hy - 0.04 * h), 0.06 * h, 0.04 * h).render(
            c, color, t, 0, m)
    elif prop == 'bow':
        a, b = (hx + 0.06 * h, hy - 0.36 * h), (hx + 0.06 * h, hy + 0.36 * h)
        W.stroke(c, a, b, color, 0.035 * h, bend=0.16 * h, t=t, motion=m)
        W.stroke(c, a, b, color, 1, t=t, motion=m)
    elif prop == 'wand':
        W.stroke(c, (hx, hy), (hx + 0.26 * h, hy - 0.22 * h), color, 0.025 * h,
                 t=t, motion=m)
    elif prop == 'flower':
        W.stroke(c, (hx, hy), (hx + 0.08 * h, hy - 0.2 * h), color, 0.02 * h,
                 bend=0.02 * h, t=t, motion=m)
        W.Orbit.ellipse((hx + 0.09 * h, hy - 0.24 * h), 0.06 * h, 0.045 * h).render(
            c, T.TERRACOTTA, t, 0, m)
    elif prop == 'club':
        W.band(c, (hx, hy), (hx + 0.18 * h, hy - 0.62 * h),
               lambda L: Wave.rise(0.06 * h, L, 0.03 * h), color, t=t, motion=m)
    elif prop == 'bag':
        W.Orbit.ellipse((hx + 0.04 * h, hy + 0.16 * h), 0.13 * h, 0.17 * h).render(
            c, color, t, 0, m)
        W.stroke(c, (hx - 0.04 * h, hy), (hx + 0.12 * h, hy), T.PAPYRUS, 0.02 * h,
                 t=t, motion=m)
    elif prop == 'oar':
        W.stroke(c, (hx - 0.12 * h, 0.06 * h), (hx + 0.22 * h, -1.15 * h), color,
                 0.035 * h, t=t, motion=m)


def shade(c, x, y, h, t, phase=0.0, facing=1, prop=None, motion=None):
    """One of the dead: faded, eyeless, and never quite on the ground."""
    drift = W.Motion(dy=Wave(0.05 * h, 0.0, 0.9, phase))
    figure(c, x, y, h, t, T.GHOST, facing, phase, arms='down', prop=prop, gown=True,
           motion=W.chain(drift, motion), eye=None, beard=prop == 'staff')


def song(c, origin, t, facing=1, length=80, color=T.INK_SOFT, n=3, phase=0.0):
    """A song in the air: lines that swell as they travel — the
    amplitude a wave of the distance."""
    x, y = origin
    for k in range(n):
        note = Wave(Wave.rise(5.0, facing * length), 1.0 / 22, -4.0, phase + 2.1 * k)
        W.Trail(note, facing * length, 'x', (x, y + (k - (n - 1) / 2) * 5), step=3).render(
            c, color, t, 1)


# --- the residents ---------------------------------------------------------------

def cyclops(c, x, y, h, t, facing=-1, blind=False, phase=0.0, motion=None):
    """Polyphemus: a man twice over with one eye, in the middle of his
    face — put out, an X and a stagger."""
    stagger = W.Motion(dx=Wave(0.05 * h, 0.0, 1.1, phase)) if blind else None
    m = figure(c, x, y, h, t, T.INK, facing, phase, arms='out' if blind else 'raised',
               prop=None if blind else 'club', motion=W.chain(stagger, motion))
    eye = (0.036 * h, (HEAD - 0.012) * h)
    if blind:
        W.Orbit.ellipse(eye, 0.03 * h, 0.02 * h).render(c, T.INK, t, 0, m)
        for dx in (-1, 1):
            W.stroke(c, (eye[0] + dx * 0.05 * h, eye[1] - 0.05 * h),
                     (eye[0] - dx * 0.05 * h, eye[1] + 0.05 * h), T.TERRACOTTA,
                     0.025 * h, t=t, motion=m)
    else:
        W.Orbit.ellipse(eye, 0.05 * h, 0.036 * h).render(c, T.PAPYRUS, t, 0, m)
        W.Orbit.ellipse(eye, 0.02 * h, 0.02 * h).render(c, T.INK, t, 0, m)


def witch(c, x, y, h, t, facing=-1, cup=True, singing=True, phase=0.0, motion=None):
    """Circe: a gown, a cup held out (or a wand), and a song."""
    figure(c, x, y, h, t, T.INK, facing, phase, arms='cup' if cup else 'out',
           prop='cup' if cup else 'wand', gown=True, fair=True, motion=motion)
    if singing:
        song(c, (x + facing * 0.2 * h, y - 0.95 * h), t, facing, 1.6 * h, phase=phase)


def nymph(c, x, y, h, t, facing=-1, phase=0.0, motion=None):
    """Calypso: a gown, and an arm that beckons."""
    figure(c, x, y, h, t, T.INK, facing, phase, arms='raised', gown=True, fair=True,
           motion=motion)


def siren(c, x, y, h, t, facing=1, singing=True, phase=0.0, motion=None):
    """A siren as the vases have her: a bird with a woman's head — a
    body and a fan of a tail, two legs, wings that beat, feathered
    along the edge, and the song."""
    hover = W.Motion(dy=Wave(0.04 * h, 0.0, 2.5, phase))
    m = at(x, y, facing, motion, hover)
    root = (-0.04 * h, -0.5 * h)

    def wing(tip, lag, tone):
        flap = W.Motion(angle=Wave(0.3, 0.0, 7.0, phase + lag), pivot=root)
        W.band(c, root, tip,
               lambda L: Wave.bulge(0.09 * h, L, 0.012 * h) + Wave(0.012 * h, 4.0 / L),
               tone, t=t, motion=W.chain(flap, m), step=h / 8)

    wing((-0.6 * h, -0.95 * h), 0.4, T.INK_SOFT)             # the far wing, behind
    body = (0.0, -0.42 * h)
    W.band(c, (-0.22 * h, -0.4 * h), (-0.52 * h, -0.27 * h),
           lambda L: Wave.rise(0.05 * h, L, 0.015 * h) + Wave(0.01 * h, 3.0 / L),
           T.INK, t=t, motion=m)
    W.Orbit.ellipse(body, 0.3 * h, 0.17 * h).render(
        c, T.INK, t, 0, W.chain(W.Motion(angle=-0.15, pivot=body), m))
    for lx in (0.0, 0.07 * h):
        W.band(c, (lx, -0.32 * h), (lx + 0.03 * h, -0.03 * h), 0.012 * h, T.INK, t=t, motion=m)
        W.band(c, (lx - 0.02 * h, -0.012 * h), (lx + 0.15 * h, 0.0),
               lambda L: Wave.fall(0.008 * h, L, 0.003 * h), T.INK, t=t, motion=m)
    W.band(c, (0.2 * h, -0.5 * h), (0.3 * h, -0.74 * h),
           lambda L: Wave.fall(0.014 * h, L, 0.022 * h), T.INK, t=t, motion=m)
    _head(c, h, (0.32 * h, -0.82 * h), t, T.INK, T.PAPYRUS, hair=True, fair=True, m=m)
    wing((-0.5 * h, -1.1 * h), 0.0, T.INK)                   # the near wing, over it
    if singing:
        song(c, (x + facing * 0.45 * h, y - 0.9 * h), t, facing, 2.2 * h, n=3, phase=phase)


def rock(c, x, y, w, h, t, color=T.INK, phase=0.0, motion=None):
    """A boulder: a bump with a ripple on it, flat underneath."""
    bump = Wave.bulge(h, w) + Wave(0.08 * h, 2.3 / w, 0.0, phase + 1.0)
    W.Ribbon(bump.scaled(-0.5), bump.scaled(0.5), w, 'x', (x - w / 2, y),
             step=max(2.0, w / 16)).render(c, color, t, 0, motion)


def scylla(c, x, y, h, t, facing=-1, phase=0.0, motion=None):
    """Scylla: six necks out of a rock, writhing toward whatever
    passes, each with a head and open jaws."""
    rock(c, x, y, 1.2 * h, 0.5 * h, t, T.INK, phase, motion)
    for k in range(6):
        reach = -(0.7 + 0.08 * (k % 3)) * h
        neck = (Wave(Wave(0.05 * h, 0.0, 1.7, phase + 1.1 * k, 0.08 * h),
                     1.0 / (1.1 * h), 0.0, 0.9 * k)
                + Wave.rise(facing * (0.25 + 0.05 * k) * h, reach))
        trail = W.Trail(neck, reach, 'y', (x + (k - 2.5) * 0.14 * h, y - 0.45 * h),
                        step=h / 10)
        trail.render(c, T.INK, t, max(1.0, 0.06 * h), motion)
        hx, hy = trail.buffer[-1]
        W.Orbit.ellipse((hx, hy), 0.09 * h, 0.06 * h).render(c, T.INK, t, 0)
        snap = W.Motion(angle=Wave(0.35, 0.0, 5.0, phase + k), pivot=(hx, hy))
        W.stroke(c, (hx, hy), (hx + facing * 0.16 * h, hy + 0.04 * h), T.INK, 0.03 * h,
                 t=t, motion=snap)
        W.stroke(c, (hx, hy), (hx + facing * 0.15 * h, hy - 0.05 * h), T.INK, 0.03 * h,
                 t=t)


def whirlpool(c, x, y, r, t, phase=0.0, motion=None):
    """Charybdis: a spiral whose arms turn — the radius a wave of the
    parameter, the angle running with time."""
    for k, (rr, tone) in enumerate(((r, T.INK_SOFT), (0.8 * r, T.INK))):
        spiral = W.Orbit(Wave(Wave.rise(rr, 1.0), 3.0, 2.2, math.pi / 2 + phase + k),
                         Wave(Wave.rise(0.38 * rr, 1.0), 3.0, 2.2, phase + k),
                         (x, y), 96)
        spiral.render(c, tone, t, 2 if k else 1, motion, closed=False)


def cow(c, x, y, h, t, facing=1, phase=0.0, motion=None):
    """One of the sun's cattle, grazing: the head bobs, the tail swings."""
    m = at(x, y, facing, motion)
    W.Orbit.ellipse((0.0, -0.5 * h), 0.4 * h, 0.2 * h).render(c, T.INK, t, 0, m)
    for lx in (-0.28, -0.14, 0.14, 0.28):
        W.stroke(c, (lx * h, -0.4 * h), (lx * h, 0.0), T.INK, 0.05 * h, t=t, motion=m)
    bob = W.Motion(dy=Wave(0.03 * h, 0.0, 1.1, phase))
    head = W.chain(bob, m)
    W.Orbit.ellipse((0.5 * h, -0.32 * h), 0.13 * h, 0.09 * h).render(c, T.INK, t, 0, head)
    W.stroke(c, (0.45 * h, -0.5 * h), (0.5 * h, -0.4 * h), T.INK, 0.05 * h, t=t, motion=head)
    for hx, tip in ((0.55, (0.63, -0.58)), (0.47, (0.43, -0.58))):
        W.stroke(c, (hx * h, -0.4 * h), (tip[0] * h, tip[1] * h), T.INK, 0.025 * h,
                 t=t, motion=head)
    swish = W.Motion(angle=Wave(0.3, 0.0, 2.2, phase), pivot=(-0.4 * h, -0.55 * h))
    W.stroke(c, (-0.4 * h, -0.55 * h), (-0.52 * h, -0.22 * h), T.INK, 0.03 * h,
             t=t, motion=W.chain(swish, m))


def bones(c, x, y, h, t, motion=None):
    """What is left of a cow: three ribs on the ground."""
    for k in range(3):
        W.stroke(c, (x + (k - 1) * 0.22 * h, y), (x + (k - 1) * 0.22 * h + 0.1 * h, y - 0.3 * h),
                 T.INK, 0.03 * h, bend=0.06 * h, t=t, motion=motion)


def pig(c, x, y, h, t, facing=1, phase=0.0, motion=None):
    """A man, lately: a pig, trotting."""
    m = at(x, y, facing, motion)
    W.Orbit.ellipse((0.0, -0.32 * h), 0.32 * h, 0.2 * h).render(c, T.INK, t, 0, m)
    W.Orbit.ellipse((0.3 * h, -0.3 * h), 0.13 * h, 0.09 * h).render(c, T.INK, t, 0, m)
    W.Orbit.ellipse((0.42 * h, -0.27 * h), 0.05 * h, 0.035 * h).render(c, T.INK, t, 0, m)
    W.stroke(c, (0.28 * h, -0.38 * h), (0.24 * h, -0.5 * h), T.INK, 0.03 * h, t=t, motion=m)
    for k, lx in enumerate((-0.2, -0.08, 0.1, 0.22)):
        trot = W.Motion(angle=Wave(0.3, 0.0, 8.0, phase + k * math.pi), pivot=(lx * h, -0.25 * h))
        W.stroke(c, (lx * h, -0.25 * h), (lx * h, 0.0), T.INK, 0.045 * h, t=t,
                 motion=W.chain(trot, m))
    W.stroke(c, (-0.3 * h, -0.4 * h), (-0.42 * h, -0.5 * h), T.INK, 0.025 * h, bend=0.05 * h,
             t=t, motion=m)


def giant(c, x, y, h, t, facing=1, phase=0.0, motion=None):
    """A Laestrygonian: a man three times over, an arm back to throw."""
    figure(c, x, y, h, t, T.INK, facing, phase, arms='throw', motion=motion)


def falling_rock(c, x, y, drop, r, t, phase=0.0):
    """A boulder thrown from a height: it falls the drop, and is thrown
    again — a sawtooth of time."""
    fall = W.Motion(dy=Wave.sawtooth(drop / 2, 0.0, 5, 1.3, phase, drop / 2))
    W.Orbit.ellipse((x, y), r, 0.8 * r).render(c, T.INK, t, 0, fall)


# --- things --------------------------------------------------------------------------

def smoke(c, x, y, h, t, phase=0.0, color=T.GHOST, n=2):
    """A plume: rising, wandering more the higher it goes, leaning
    with the wind."""
    for k in range(n):
        drift = (Wave(Wave.rise(0.2 * h, -h), 1.0 / (0.7 * h), -1.2, phase + 1.3 * k)
                 + Wave.rise(0.18 * h, -h))
        W.Trail(drift, -h, 'y', (x + k * 3, y), step=h / 12).render(
            c, color, t, 3 - k)


def tree(c, x, y, h, t, phase=0.0, motion=None):
    """An olive: a trunk and three heads of leaves, swaying."""
    sway = W.Motion(angle=Wave(0.03, 0.0, 0.7, phase))
    m = at(x, y, 1, motion, sway)
    W.band(c, (0.0, 0.0), (0.05 * h, -0.55 * h), lambda L: Wave.fall(0.05 * h, L, 0.03 * h),
           T.INK, t=t, motion=m)
    for cx, cy, rx, ry in ((-0.16, -0.62, 0.28, 0.19), (0.2, -0.68, 0.26, 0.18),
                           (0.02, -0.84, 0.3, 0.2)):
        W.Orbit.ellipse((cx * h, cy * h), rx * h, ry * h).render(c, T.INK, t, 0, m)


def lotus(c, x, y, h, t, phase=0.0, motion=None):
    """Lotus: stems that nod, and blooms the colour of the pot."""
    for k, (dx, hh) in enumerate(((-0.3, 0.9), (0.0, 1.0), (0.3, 0.8))):
        nod = W.Motion(angle=Wave(0.06, 0.0, 1.5, phase + k), pivot=(x + dx * h, y))
        m = W.chain(nod, motion)
        W.stroke(c, (x + dx * h, y), (x + dx * h + 0.05 * h, y - hh * h), T.INK, 0.03 * h,
                 bend=0.04 * h, t=t, motion=m)
        W.Orbit.ellipse((x + dx * h + 0.06 * h, y - hh * h - 0.04 * h), 0.1 * h, 0.07 * h).render(
            c, T.TERRACOTTA, t, 0, m)
        W.Orbit.ellipse((x + dx * h + 0.06 * h, y - hh * h - 0.04 * h), 0.1 * h, 0.07 * h).render(
            c, T.INK, t, 1, m)


def cave(c, x, y, w, h, t, shut=False, inside=False, motion=None):
    """A cave mouth in the hillside — dark from outside; from inside,
    the arch of it, and a boulder if one was rolled across."""
    bump = Wave.bulge(h, w) + Wave(0.05 * h, 2.6 / w, 0.0, 0.7)
    arch = W.Ribbon(bump.scaled(-0.5), bump.scaled(0.5), w, 'x', (x - w / 2, y),
                    step=max(2.0, w / 20))
    if inside:
        arch.render(c, T.PAPYRUS_DK, t, 0, motion)
        arch.render(c, T.INK, t, 2, motion)
        # the mouth, off to the left: daylight in it, or the boulder
        mx, mw, mh = x - 0.34 * w, 0.2 * w, 0.5 * h
        lip = Wave.bulge(mh, mw)
        mouth = W.Ribbon(lip.scaled(-0.5), lip.scaled(0.5), mw, 'x', (mx - mw / 2, y), step=2.0)
        mouth.render(c, T.PAPYRUS, t, 0, motion)
        mouth.render(c, T.INK, t, 2, motion)
        if shut:
            rock(c, mx, y, 1.05 * mw, 0.95 * mh, t, T.INK, motion=motion)
    else:
        arch.render(c, T.INK, t, 0, motion)
        if shut:
            rock(c, x + 0.05 * w, y, 0.55 * w, 0.8 * h, t, T.INK_SOFT, motion=motion)
            rock(c, x + 0.05 * w, y, 0.55 * w, 0.8 * h, t, T.INK, motion=motion)


def walls(c, x, y, w, h, t, fallen=False, motion=None):
    """Troy: a wall with battlements (a square wave for a top edge),
    towers at the ends, a gate — or what a night left of it."""
    if fallen:
        bump = (Wave(0.2 * h, 1.6 / w, 0.0, 0.5) + Wave(0.12 * h, 4.1 / w, 0.0, 2.0)
                + Wave(0.08 * h, 9.0 / w, 0.0, 1.0))
        top = Wave.flat(-0.45 * h) + bump
        W.Ribbon(top.scaled(0.5), Wave.flat(0.225 * h) + bump.scaled(-0.5), w, 'x',
                 (x - w / 2, y), step=max(2.0, w / 40)).render(c, T.INK, t, 0, motion)
        for k in range(2):
            smoke(c, x + (k - 0.5) * 0.5 * w, y - 0.4 * h, 1.4 * h, t, k * 1.7)
        return
    crenel = Wave.square(0.08 * h, 1.0 / (0.12 * w), harmonics=5)
    W.Ribbon(Wave.flat(-0.5 * h) + crenel.scaled(-0.5), Wave.flat(0.5 * h) + crenel.scaled(0.5),
             w, 'x', (x - w / 2, y), step=max(1.0, w / 80)).render(c, T.INK, t, 0, motion)
    for tx in (x - 0.44 * w, x + 0.44 * w):
        W.Ribbon(Wave.flat(0.0), 0.06 * w, -1.35 * h, 'y', (tx, y), step=h).render(
            c, T.INK, t, 0, motion)
    gate = Wave.bulge(0.55 * h, 0.14 * w)
    W.Ribbon(gate.scaled(-0.5), gate.scaled(0.5), 0.14 * w, 'x', (x - 0.07 * w, y),
             step=2.0).render(c, T.PAPYRUS, t, 0, motion)


def horse(c, x, y, h, t, riders=0, motion=None):
    """The wooden horse, on its wheels; hollow, with men in it, when
    they are in it."""
    m = W.chain(motion)
    body = W.Orbit.ellipse((x, y - 0.62 * h), 0.38 * h, 0.2 * h)
    for lx in (-0.24, -0.14, 0.14, 0.24):
        W.band(c, (x + lx * h, y - 0.55 * h), (x + lx * h * 1.05, y - 0.12 * h), 0.03 * h,
               T.INK, t=t, motion=m)
    for wx in (-0.26, 0.26):
        W.Orbit.ellipse((x + wx * h, y - 0.1 * h), 0.1 * h, 0.1 * h).render(c, T.INK, t, 0, m)
        W.Orbit.ellipse((x + wx * h, y - 0.1 * h), 0.035 * h, 0.035 * h).render(c, T.PAPYRUS, t, 0, m)
    W.band(c, (x + 0.3 * h, y - 0.72 * h), (x + 0.5 * h, y - 1.06 * h),
           lambda L: Wave.fall(0.09 * h, L, 0.05 * h), T.INK, t=t, motion=m)
    W.band(c, (x + 0.24 * h, y - 0.78 * h), (x + 0.42 * h, y - 1.1 * h),
           lambda L: Wave.bulge(0.05 * h, L), T.INK, t=t, motion=m)
    head = (x + 0.58 * h, y - 1.08 * h)
    W.Orbit.ellipse(head, 0.15 * h, 0.07 * h).render(
        c, T.INK, t, 0, W.chain(W.Motion(angle=0.45, pivot=head), m))
    W.stroke(c, (x + 0.5 * h, y - 1.12 * h), (x + 0.47 * h, y - 1.24 * h), T.INK, 0.03 * h,
             t=t, motion=m)
    W.stroke(c, (x - 0.36 * h, y - 0.66 * h), (x - 0.52 * h, y - 0.3 * h), T.INK, 0.035 * h,
             bend=0.08 * h, t=t, motion=m)
    if riders:
        body.render(c, T.PAPYRUS, t, 0, m)
        body.render(c, T.INK, t, 2, m)
        for k in range(min(riders, 4)):
            figure(c, x + (k - 1.5) * 0.15 * h, y - 0.5 * h, 0.24 * h, t, T.INK, 1, k * 0.8,
                   motion=m)
    else:
        body.render(c, T.INK, t, 0, m)


def house(c, x, y, w, h, t, motion=None):
    """A house on a hill: walls, a peaked roof (a triangle wave, one
    peak of it), a door."""
    W.Ribbon(Wave.flat(0.0), 0.5 * w, -0.6 * h, 'y', (x, y), step=h).render(c, T.INK, t, 0, motion)
    roof = Wave.triangle(0.2 * h, 1.0 / (2.4 * w), harmonics=4)
    W.Ribbon(roof.scaled(-1), roof, 1.2 * w, 'x', (x - 0.6 * w, y - 0.6 * h),
             step=max(1.0, w / 12)).render(c, T.INK, t, 0, motion)
    W.Ribbon(Wave.flat(0.0), 0.1 * w, -0.32 * h, 'y', (x + 0.15 * w, y), step=h).render(
        c, T.PAPYRUS, t, 0, motion)


def column(c, x, y, h, w, t, motion=None):
    W.Ribbon(Wave.flat(0.0), w / 2, -h, 'y', (x, y), step=h).render(c, T.INK, t, 0, motion)
    W.Ribbon(Wave.flat(0.0), 0.8 * w, -0.06 * h, 'y', (x, y - 0.94 * h), step=h).render(
        c, T.INK, t, 0, motion)


def loom(c, x, y, h, t, phase=0.0, motion=None):
    """Penelope's loom: two posts, a beam, the warp, the cloth so far,
    and the shuttle going across — and, at night, back."""
    for px in (-0.36 * h, 0.36 * h):
        W.Ribbon(Wave.flat(0.0), 0.03 * h, -h, 'y', (x + px, y), step=h).render(c, T.INK, t, 0, motion)
    W.Ribbon(Wave.flat(0.0), 0.03 * h, 0.8 * h, 'x', (x - 0.4 * h, y - 0.96 * h), step=h).render(
        c, T.INK, t, 0, motion)
    for k in range(7):
        wx = x + (k - 3) * 0.1 * h
        W.stroke(c, (wx, y - 0.93 * h), (wx, y - 0.05 * h), T.INK_SOFT, 1, t=t, motion=motion)
    W.Ribbon(Wave.flat(0.0), 0.16 * h, 0.66 * h, 'x', (x - 0.33 * h, y - 0.2 * h), step=h).render(
        c, T.INK_SOFT, t, 0, motion)
    across = W.Motion(dx=Wave(0.28 * h, 0.0, 2.4, phase))
    W.band(c, (x - 0.06 * h, y - 0.4 * h), (x + 0.06 * h, y - 0.4 * h),
           lambda L: Wave.bulge(0.03 * h, L), T.INK, t=t, motion=W.chain(across, motion))


def bronze_wall(c, x, y, w, h, t, motion=None):
    """Aeolus's wall: bronze, all the way round the island."""
    top = Wave(0.04 * h, 3.0 / w, 0.0, 0.3)
    wall = W.Ribbon(Wave.flat(-0.5 * h) + top.scaled(0.5), Wave.flat(0.5 * h) + top.scaled(-0.5),
                    w, 'x', (x - w / 2, y), step=max(2.0, w / 30))
    wall.render(c, T.OCHRE, t, 0, motion)
    wall.render(c, T.INK, t, 1, motion)


def winds(c, rect, t, loose=False, phase=0.0):
    """The winds: streaming lines, faster and wilder let out of the bag."""
    x0, y0, w, h = rect
    n = 4 if loose else 3
    for k in range(n):
        gust = Wave(3 + (7 if loose else 3) * (k % 2), 1.0 / (40 + 8 * k), 5.0 + 1.5 * k,
                    phase + 1.3 * k, y0 + h * (k + 0.5) / n)
        W.Trail(gust, w, 'x', (x0, 0), step=4).render(c, T.GHOST, t, 1)


def raft(c, x, y, w, t, motion=None):
    """A raft: logs lashed, a stump of a mast, a scrap of sail."""
    for k in range(3):
        W.band(c, (x - w / 2, y + k * 0.05 * w), (x + w / 2, y + k * 0.05 * w), 0.022 * w,
               T.INK, t=t, motion=motion)
    W.stroke(c, (x, y), (x, y - 0.55 * w), T.INK, 0.03 * w, t=t, motion=motion)
    belly = Wave.bulge(Wave(0.03 * w, 0.0, 0.9, 0.0, 0.05 * w), 0.4 * w)
    W.Ribbon(belly, Wave.fall(0.05 * w, 0.4 * w, 0.14 * w), 0.4 * w, 'y', (x, y - 0.52 * w),
             step=w / 8).render(c, T.PAPYRUS_DK, t, 0, motion)
    W.Ribbon(belly, Wave.fall(0.05 * w, 0.4 * w, 0.14 * w), 0.4 * w, 'y', (x, y - 0.52 * w),
             step=w / 8).render(c, T.INK, t, 1, motion)


def wreck(c, x, y, w, t, motion=None):
    """What the tide left: planks, and the stump of a mast."""
    for k, (dx, angle, length) in enumerate(((-0.3, 0.2, 0.5), (0.1, -0.35, 0.45), (0.4, 0.6, 0.35))):
        p = (x + dx * w, y)
        q = (p[0] + length * w * math.cos(angle), p[1] - length * w * math.sin(angle) * 0.5)
        W.band(c, p, q, 0.03 * w, T.INK, t=t, motion=motion)
    W.stroke(c, (x + 0.05 * w, y), (x + 0.12 * w, y - 0.3 * w), T.INK, 0.035 * w, t=t, motion=motion)


# --- the sky -----------------------------------------------------------------------

def sun(c, x, y, r, t, color=T.OCHRE, phase=0.0):
    """The sun: a disc, and rays that shimmer and slowly turn."""
    turn = W.Motion(angle=Wave(0.2, 0.0, 0.3, phase), pivot=(x, y))
    for k in range(8):
        a = k * TAU / 8
        pulse = W.Motion(scale=Wave(0.08, 0.0, 1.0, phase + 0.8 * k, 1.0), pivot=(x, y))
        W.stroke(c, (x + 1.3 * r * math.cos(a), y + 1.3 * r * math.sin(a)),
                 (x + 1.9 * r * math.cos(a), y + 1.9 * r * math.sin(a)), color, 2,
                 t=t, motion=W.chain(pulse, turn))
    W.Orbit.ellipse((x, y), r, r).render(c, color, t, 0)
    W.Orbit.ellipse((x, y), r, r).render(c, T.INK, t, 1)


def cloud(c, x, y, w, t, fill=T.PAPYRUS, line=T.INK, phase=0.0):
    """A cloud: one orbit with a bumpy radius (the radius a wave of
    the parameter), flatter underneath, drifting."""
    drift = W.Motion(dx=Wave(0.08 * w, 0.0, 0.15, phase))
    blob = W.Orbit(Wave(Wave(0.07 * w, 4.0, 0.0, phase, 0.42 * w), 1.0, 0.0, math.pi / 2),
                   Wave(Wave(0.05 * w, 4.0, 0.0, phase + 0.4, 0.17 * w), 1.0, 0.0, 0.0)
                   + Wave(0.05 * w, 1.0, 0.0, math.pi / 2),
                   (x, y), 72)
    blob.render(c, fill, t, 0, drift)
    blob.render(c, line, t, 1, drift)


def lightning(c, x, y, h, t, phase=0.0):
    """A bolt, when the moment's sine is near its peak: a flash a
    tenth of the time, never twice the same."""
    if Wave(1.0, 0.0, 6.0, phase)(0, t) > 0.9:
        D.glyph(c, 'bolt', (x, y), h, T.OCHRE, t)


def rain(c, rect, t, n=14, phase=0.0):
    """Rain: slanting strokes, each falling the height of the sky and
    starting again — sawteeth of time."""
    x0, y0, w, h = rect
    for k in range(n):
        x = x0 + w * (k + 0.5) / n
        fall = W.Motion(dy=Wave.sawtooth(0.45 * h, 0.0, 5, 3.0 + 0.13 * k, phase + 0.7 * k, 0.45 * h))
        W.stroke(c, (x, y0), (x - 0.02 * h, y0 + 0.07 * h), T.INK_SOFT, 1, t=t, motion=fall)
