"""Drawing helpers: the canvas, wrapped text, buttons — and the
pictures, every one of them sine waves from the engine in `wave`: the
sea, the meander, the four factions' glyphs, the ship, the eye on its
prow, the gulls. Nothing here needs an asset."""

import math
from contextlib import contextmanager

import pygame

try:
    from pygame import gfxdraw          # antialiased edges for the filled shapes
except ImportError:                     # pragma: no cover — not every build has it
    gfxdraw = None

from . import theme as T
from . import wave as W
from .wave import Wave


# --- the canvas -------------------------------------------------------------

class Canvas:
    """A surface addressed in logical units. Every coordinate is
    multiplied by `k` and shifted by `origin` on the way in, so the
    screens draw in the 440x880 world and the pixels land wherever the
    window is: two device pixels per unit on a Retina display, fewer
    when the window was shrunk to fit the screen, letterboxed when it
    was resized to another shape. Text comes in as theme Glyphs, which
    were rasterised at the same scale."""

    def __init__(self, surface, k=1.0, origin=(0, 0)):
        self.surface = surface
        self.k = float(k)
        self.ox, self.oy = origin

    # -- the mapping --

    def x(self, v):
        return round(self.ox + v * self.k)

    def y(self, v):
        return round(self.oy + v * self.k)

    def pt(self, p):
        return self.x(p[0]), self.y(p[1])

    def pts(self, ps):
        ox, oy, k = self.ox, self.oy, self.k
        return [(round(ox + x * k), round(oy + y * k)) for x, y in ps]

    def area(self, r):
        """A logical rect (or x, y, w, h) as a device Rect. Edges are
        mapped, not sizes, so neighbours stay flush."""
        x, y, w, h = r
        x0, y0 = self.x(x), self.y(y)
        return pygame.Rect(x0, y0, self.x(x + w) - x0, self.y(y + h) - y0)

    def length(self, v):
        return max(0, round(v * self.k))

    def stroke(self, w):
        """A line width: 0 stays 0 (filled), anything else at least a pixel."""
        return 0 if w == 0 else max(1, round(w * self.k))

    def bounds(self):
        """The whole surface, letterbox included, in logical units."""
        w, h = self.surface.get_size()
        return (-self.ox / self.k, -self.oy / self.k, w / self.k, h / self.k)

    # -- the primitives --

    def fill(self, color):
        self.surface.fill(color)

    def rect(self, color, r, width=0, border_radius=0):
        pygame.draw.rect(self.surface, color, self.area(r), width=self.stroke(width),
                         border_radius=self.length(border_radius))

    def line(self, color, a, b, width=1):
        pygame.draw.line(self.surface, color, self.pt(a), self.pt(b), self.stroke(width))

    def lines(self, color, closed, points, width=1):
        pygame.draw.lines(self.surface, color, closed, self.pts(points), self.stroke(width))

    def polygon(self, color, points, width=0):
        ps = self.pts(points)
        if width == 0 and gfxdraw is not None and len(ps) >= 3:
            gfxdraw.filled_polygon(self.surface, ps, color)
            gfxdraw.aapolygon(self.surface, ps, color)
        else:
            pygame.draw.polygon(self.surface, color, ps, self.stroke(width))

    def ellipse(self, color, r, width=0):
        area = self.area(r)
        if width == 0 and gfxdraw is not None and area.width > 2 and area.height > 2:
            cx, cy = area.center
            rx, ry = area.width // 2, area.height // 2
            gfxdraw.filled_ellipse(self.surface, cx, cy, rx, ry, color)
            gfxdraw.aaellipse(self.surface, cx, cy, rx, ry, color)
        else:
            pygame.draw.ellipse(self.surface, color, area, self.stroke(width))

    def circle(self, color, center, radius, width=0):
        c, rad = self.pt(center), self.length(radius)
        if width == 0 and gfxdraw is not None and rad > 1:
            gfxdraw.filled_circle(self.surface, c[0], c[1], rad, color)
            gfxdraw.aacircle(self.surface, c[0], c[1], rad, color)
        else:
            pygame.draw.circle(self.surface, color, c, rad, self.stroke(width))

    def blit(self, glyph, pos):
        """A theme Glyph (or a raw surface, already at device scale)."""
        self.surface.blit(getattr(glyph, 'image', glyph), self.pt(pos))

    def dim(self, color, alpha):
        """A translucent veil over everything, letterbox included."""
        veil = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        veil.fill((*color, alpha))
        self.surface.blit(veil, (0, 0))

    @contextmanager
    def clip(self, r):
        """Draw only inside the logical rect `r` for the duration."""
        old = self.surface.get_clip()
        self.surface.set_clip(self.area(r))
        try:
            yield
        finally:
            self.surface.set_clip(old)


# --- text ------------------------------------------------------------------

def wrap(font, text, width):
    """`text` as lines no wider than `width` units (words kept whole;
    explicit newlines respected)."""
    out = []
    for para in str(text).split('\n'):
        words = para.split(' ')
        line = ''
        for w in words:
            trial = (line + ' ' + w).strip()
            if font.size(trial)[0] <= width or not line:
                line = trial
            else:
                out.append(line)
                line = w
        out.append(line)
    return out


def text(surface, s, pos, font, color, width=None, align='left',
         line_gap=2, max_lines=None):
    """Draw `s` at `pos`, wrapped to `width` when given. Returns the
    height used."""
    x, y = pos
    lines = wrap(font, s, width) if width else [str(s)]
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip('.,;') + '…'
    h = 0
    for line in lines:
        img = font.render(line, True, color)
        if align == 'center':
            dx = ((width or 0) - img.get_width()) // 2
        elif align == 'right':
            dx = (width or 0) - img.get_width()
        else:
            dx = 0
        surface.blit(img, (x + dx, y + h))
        h += img.get_height() + line_gap
    return h


def text_height(font, s, width, line_gap=2, max_lines=None):
    lines = wrap(font, s, width)
    if max_lines:
        lines = lines[:max_lines]
    return len(lines) * (font.get_height() + line_gap)


# --- shapes ----------------------------------------------------------------

def rrect(surface, color, rect, radius=10, width=0):
    surface.rect(color, rect, width=width, border_radius=radius)


def shadow_rect(surface, rect, radius=10, offset=4):
    """A soft drop: the card floating on the sea."""
    r = pygame.Rect(rect).move(offset, offset)
    surface.rect(T.SEA_DARK, r, border_radius=radius)


def hrule(surface, x1, x2, y, color=T.INK, width=1):
    surface.line(color, (x1, y), (x2, y), width)


def meander(surface, rect, color=T.OCHRE, cell=12, width=2):
    """A Greek key along the top edge of `rect`: a square wave, as
    Fourier drew it — the first odd harmonics, the ringing left in as
    the brush would leave it — one battlement every cell and a half."""
    x0, y0, w, h = rect
    key = Wave.square(0.4 * h, 1.0 / (1.5 * cell), harmonics=5, K=y0 + h / 2)
    W.Trail(key, w, 'x', (x0, 0), step=max(0.5, cell / 16)).render(surface, color, 0.0, width)


def sea_wave(amp, wavelength, speed=1.0, row=0, y=0.0, texture=0.0):
    """One row of the sea: a long swell, rows staggered in phase, and
    with `texture` a quicker, lower ripple riding on it."""
    swell = Wave(amp, 1.0 / wavelength, speed, W.TAU * 17 * row / wavelength, y)
    if not texture:
        return swell
    return swell + Wave(amp * texture, 2.7 / wavelength, 1.6 * speed, 0.9 * row)


def waves(surface, rect, color, rows=5, amp=4, wavelength=48, width=2,
          t=0.0, speed=1.0, texture=0.0):
    """Rows of long waves rolling at `speed`: the sea under everything."""
    x0, y0, w, h = rect
    for r in range(rows):
        y = y0 + h * (r + 0.5) / rows
        W.Trail(sea_wave(amp, wavelength, speed, r, y, texture), w, 'x', (x0, 0),
                step=4).render(surface, color, t, width)


def button(surface, rect, label, font, fill=T.TERRACOTTA, ink=T.PAPYRUS,
           hover=False, radius=12, border=T.INK, small=None):
    """A chunky rounded button with a wrapped label; returns its rect."""
    r = pygame.Rect(rect)
    shadow_rect(surface, r, radius, 3)
    surface.rect(T.TERRA_DK if hover else fill, r, border_radius=radius)
    surface.rect(border, r, width=2, border_radius=radius)
    lines = wrap(font, label, r.width - 24)
    total = len(lines) * (font.get_height() + 1)
    if small:
        total += small[1].get_height() + 2
    y = r.y + (r.height - total) // 2
    for line in lines:
        img = font.render(line, True, ink)
        surface.blit(img, (r.x + (r.width - img.get_width()) // 2, y))
        y += font.get_height() + 1
    if small:
        s, f = small
        img = f.render(s, True, ink)
        surface.blit(img, (r.x + (r.width - img.get_width()) // 2, y + 2))
    return r


def choice(surface, rect, number, label, font, fill=T.TERRACOTTA, ink=T.PAPYRUS,
           hover=False, radius=12, border=T.INK, small=None, max_lines=2):
    """An answer to a crisis: a numbered button whose label is a
    sentence, set left after the number, two lines of it at most,
    with a small line under it when there is one; returns its rect."""
    r = pygame.Rect(rect)
    shadow_rect(surface, r, radius, 3)
    surface.rect(T.TERRA_DK if hover else fill, r, border_radius=radius)
    surface.rect(border, r, width=2, border_radius=radius)
    x = r.x + 34
    w = r.width - 34 - 12
    lines = wrap(font, label, w)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(' ,;') + '…'
    total = len(lines) * (font.get_height() + 1)
    tiny = T.font(11, italic=True)
    if small:
        total += tiny.get_height() + 1
    y = r.y + (r.height - total) // 2
    for line in lines:
        surface.blit(font.render(line, True, ink), (x, y))
        y += font.get_height() + 1
    if small:
        surface.blit(tiny.render(small, True, ink), (x, y + 1))
    # the number, in a ring at the left
    cx, cy = r.x + 17, r.centery
    surface.circle(ink, (cx, cy), 9, width=1)
    num = T.font(11, bold=True).render(str(number), True, ink)
    surface.blit(num, (cx - num.get_width() // 2, cy - num.get_height() // 2))
    return r


def bar(surface, rect, value, lo, hi, fill, back=T.SEA_LIGHT, radius=6):
    r = pygame.Rect(rect)
    surface.rect(back, r, border_radius=radius)
    frac = 0 if hi == lo else max(0.0, min(1.0, (value - lo) / (hi - lo)))
    if frac > 0:
        inner = pygame.Rect(r.x, r.y, max(int(r.width * frac), radius * 2 if frac > 0.02 else 0), r.height)
        surface.rect(fill, inner, border_radius=radius)
    surface.rect(T.INK, r, width=1, border_radius=radius)


def badge(surface, pos, delta, font):
    """A +8 / −12 pill."""
    good = delta > 0
    s = f'+{delta}' if good else f'−{abs(delta)}'
    img = font.render(s, True, T.PAPYRUS)
    w, h = img.get_width() + 12, img.get_height() + 4
    r = pygame.Rect(pos[0], pos[1], w, h)
    surface.rect(T.GOOD if good else T.BAD, r, border_radius=h // 2)
    surface.blit(img, (r.x + 6, r.y + 2))
    return r


# --- glyphs: the four factions, drawn black-figure ---------------------------

def glyph(surface, name, center, size, color=T.INK, t=0.0, motion=None):
    """A faction's emblem, `size` across at `center`, built in its own
    coordinates from the engine's parts and carried there (and through
    `motion`, when it has one) by the matrix mode."""
    s = size / 2
    at = W.chain(W.Motion(dx=center[0], dy=center[1]), motion)
    if name == 'oar':
        # a long shaft, and a blade that swells and comes to a point
        W.stroke(surface, (-s, -s), (0.35 * s, 0.35 * s), color, max(2, int(size / 9)),
                 t=t, motion=at)
        W.band(surface, (0.15 * s, 0.15 * s), (s, s),
               lambda L: Wave.bulge(0.24 * s, L), color, t=t, motion=at, step=s / 6)
    elif name == 'bolt':
        # lightning, the emblem: two slanted bands, the upper widening
        # to the notch, the lower tapering to the point — straight but
        # for a tremor along each
        tremor = lambda L: Wave(0.015 * s, 2.5 / L, 0.0, 0.7)
        W.band(surface, (0.15 * s, -s), (-0.3 * s, 0.2 * s),
               lambda L: Wave.rise(0.12 * s, L, 0.1 * s), color, t=t, motion=at,
               step=s / 6, centre=tremor)
        W.band(surface, (0.25 * s, -0.1 * s), (-0.3 * s, s),
               lambda L: Wave.fall(0.14 * s, L, 0.02 * s), color, t=t, motion=at,
               step=s / 6, centre=tremor)
    elif name == 'loom':
        # a temple front: a pediment (a triangle wave, one peak of it)
        # over an entablature, three columns and a step — flat waves
        roof = Wave.triangle(0.325 * s, 1.0 / (4 * s), harmonics=4)
        W.Ribbon(roof.scaled(-1), roof, 2 * s, 'x', (-s, -0.35 * s),
                 step=s / 6).render(surface, color, t, 0, at)
        W.Ribbon(Wave.flat(), 0.11 * s, 2 * s, 'x', (-s, -0.19 * s),
                 step=2 * s).render(surface, color, t, 0, at)
        for k in (-0.7, 0.0, 0.7):
            W.Ribbon(Wave.flat(), 0.12 * s, 0.9 * s, 'y', (k * s, -0.05 * s),
                     step=s).render(surface, color, t, 0, at)
        W.Ribbon(Wave.flat(), 0.1 * s, 2 * s, 'x', (-s, 0.9 * s),
                 step=2 * s).render(surface, color, t, 0, at)
    elif name == 'lyre':
        # a sound-box (an orbit), two arms bowing out, a yoke, strings
        w = max(2, int(size / 9))
        W.Orbit.ellipse((0, 0.6 * s), 0.55 * s, 0.35 * s).render(surface, color, t, 0, at)
        W.stroke(surface, (-0.45 * s, 0.35 * s), (-0.7 * s, -0.85 * s), color, w,
                 bend=-0.18 * s, t=t, motion=at)
        W.stroke(surface, (0.45 * s, 0.35 * s), (0.7 * s, -0.85 * s), color, w,
                 bend=0.18 * s, t=t, motion=at)
        W.stroke(surface, (-0.75 * s, -0.7 * s), (0.75 * s, -0.7 * s), color, w,
                 t=t, motion=at)
        for k in (-0.3, -0.1, 0.1, 0.3):
            W.stroke(surface, (k * s, -0.7 * s), (0.6 * k * s, 0.3 * s), color, 1,
                     t=t, motion=at)
    elif name == 'hourglass':
        # one ribbon whose half-width is a cosine down the height: full
        # at the top, nothing at the waist, full (and crossed) at the foot
        waist = Wave(0.7 * s, 1.0 / (4 * s), 0.0, math.pi / 2)
        W.Ribbon(Wave.flat(), waist, 2 * s, 'y', (0, -s),
                 step=s / 6).render(surface, color, t, 2, at)
    else:
        W.Orbit.ellipse((0, 0), s, s).render(surface, color, t, 0, at)


# --- the ship, the eye, the gulls ----------------------------------------------

class Ship:
    """A black-figure ship, side on — hull, stern post, ram, bow post,
    oars, sail, mast, yard, stays — built once from ribbons and
    strokes in its own coordinates (the centre at the origin, `size`
    across) and rendered wherever, through whatever motion. The sail
    billows in a wind that comes and goes; the oars row, each a little
    behind the one before."""

    def __init__(self, size):
        self.size = size
        s = self.s = size / 2
        L = 1.6 * s
        # the hull: a slab with a little belly to the keel
        self.hull = W.Ribbon(Wave.bulge(0.02 * s, L, 0.17 * s), Wave.bulge(0.03 * s, L, 0.11 * s),
                             L, 'x', (-0.85 * s, 0), step=s / 8)
        # the stern post, rising and curling aft; the ram, jutting
        # forward and up to a point; a short post at the bow
        self.stern = W.Ribbon(Wave.rise(-0.14 * s, -0.5 * s), Wave.fall(0.03 * s, -0.5 * s, 0.025 * s),
                              -0.5 * s, 'y', (-0.85 * s, 0.12 * s), step=s / 10)
        self.ram = W.Ribbon(Wave.rise(-0.22 * s, 0.38 * s), Wave.fall(0.1 * s, 0.38 * s, 0.012 * s),
                            0.38 * s, 'x', (0.7 * s, 0.2 * s), step=s / 10)
        self.bow = W.Ribbon(Wave.rise(0.06 * s, -0.28 * s), Wave.fall(0.02 * s, -0.28 * s, 0.015 * s),
                            -0.28 * s, 'y', (0.66 * s, 0.08 * s), step=s / 10)
        # the sail: a trapezoid whose sides bow out and whose belly
        # fills and slackens
        gust = Wave(0.03 * s, 0.0, 0.9, 0.0, 0.04 * s)
        flutter = Wave(0.02 * s, 0.0, 0.9, 0.5, 0.03 * s)
        self.sail = W.Ribbon(Wave.bulge(gust, 0.75 * s),
                             Wave.fall(0.08 * s, 0.75 * s, 0.42 * s) + Wave.bulge(flutter, 0.75 * s),
                             0.75 * s, 'y', (0, -1.0 * s), step=s / 8)
        # the oars, from their tholes; and the rowing
        self.oars = []
        for k in range(6):
            x = -0.6 * s + k * 0.22 * s
            thole = (x, 0.15 * s)
            self.oars.append((thole, (x - 0.12 * s, 0.55 * s),
                              W.Motion(angle=Wave(0.1, 0.0, 1.6, 0.3 * k), pivot=thole)))

    def render(self, canvas, center, color=T.INK, sail=T.PAPYRUS, t=0.0, motion=None, eye=None,
               rim=None):
        """With `rim`, every part is first drawn a little larger in that
        colour: a chalk line round a black ship on dark water."""
        s = self.s
        at = W.chain(W.Motion(dx=center[0], dy=center[1]), motion)
        passes = ((rim, 4, color), (color, 0, sail)) if rim else ((color, 0, sail),)
        for ink, extra, cloth in passes:
            for part in (self.hull, self.stern, self.ram, self.bow):
                part.render(canvas, ink, t, extra, at)
            for thole, tip, row in self.oars:
                W.stroke(canvas, thole, tip, ink, 2 + extra, t=t, motion=W.chain(row, at))
            if extra:
                self.sail.render(canvas, ink, t, 2 + extra, at)
            else:
                self.sail.render(canvas, cloth, t, 0, at)
                self.sail.render(canvas, ink, t, 2, at)
            W.stroke(canvas, (0, 0.05 * s), (0, -1.1 * s), ink, 3 + extra, t=t, motion=at)      # mast
            W.stroke(canvas, (-0.5 * s, -1.0 * s), (0.5 * s, -1.0 * s), ink, 3 + extra, t=t, motion=at)  # yard
            W.stroke(canvas, (0, -1.05 * s), (-0.8 * s, -0.05 * s), ink, 1 + extra, t=t, motion=at)   # stays
            W.stroke(canvas, (0, -1.05 * s), (0.85 * s, -0.02 * s), ink, 1 + extra, t=t, motion=at)
        if eye:
            _eye(canvas, (0.745 * s, -0.02 * s), 0.073 * s, eye, t, at)


def ship(surface, center, size, color=T.INK, sail=T.PAPYRUS, t=0.0, motion=None, eye=None):
    """A black-figure ship, side on: hull, ram, mast, sail, oars."""
    Ship(size).render(surface, center, color, sail, t, motion, eye)


def eye(surface, center, size, color=T.INK, t=0.0, motion=None):
    """The apotropaic eye painted on a prow: two orbits."""
    W.Orbit.ellipse(center, size, 0.55 * size).render(surface, color, t, 2, motion)
    W.Orbit.ellipse(center, 0.4 * size, 0.4 * size).render(surface, color, t, 0, motion)


_eye = eye      # `Ship.render` takes the eye's colour under that name


def gull(surface, center, span, color=T.FOAM, t=0.0, phase=0.0, motion=None, width=1):
    """A gull: two wings, each a bowed line flapping about the body,
    the far wing a beat behind the near one."""
    at = W.chain(W.Motion(dx=center[0], dy=center[1]), motion)
    for side, lag in ((-1, 0.0), (1, 0.35)):
        flap = W.Motion(angle=Wave(-0.45 * side, 0.0, 9.0, phase + lag))
        bow = Wave(0.12 * span, 0.0, 9.0, phase + lag)
        W.stroke(surface, (0, 0), (side * span / 2, -0.15 * span), color, width,
                 bend=lambda L, bow=bow: Wave.bulge(bow, L), t=t,
                 motion=W.chain(flap, at), step=span / 8)
