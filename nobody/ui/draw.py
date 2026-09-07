"""Drawing helpers: the canvas, wrapped text, buttons, the meander, the
glyphs, the ship. Everything is primitives, so nothing here needs an
asset."""

import math
from contextlib import contextmanager

import pygame

try:
    from pygame import gfxdraw          # antialiased edges for the filled shapes
except ImportError:                     # pragma: no cover — not every build has it
    gfxdraw = None

from . import theme as T


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
        return [self.pt(p) for p in ps]

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
    """A Greek key along the top edge of `rect`, one cell after
    another: the border every vase has."""
    x0, y0, w, h = rect
    n = max(1, int(w // cell))
    s = cell
    for i in range(n):
        x = x0 + i * s
        y = y0
        # one key: a squared spiral drawn as a polyline
        pts = [(x, y + s), (x, y), (x + s, y), (x + s, y + s * 0.66),
               (x + s * 0.33, y + s * 0.66), (x + s * 0.33, y + s * 0.33),
               (x + s * 0.66, y + s * 0.33)]
        surface.lines(color, False, pts, width)


def waves(surface, rect, color, rows=5, amp=4, wavelength=48, width=2,
          phase=0.0):
    """Rows of long sine waves: the sea under everything."""
    x0, y0, w, h = rect
    step = 4
    for r in range(rows):
        y = y0 + h * (r + 0.5) / rows
        pts = []
        x = x0
        while x <= x0 + w:
            pts.append((x, y + amp * math.sin((x + r * 17) / wavelength * 2 * math.pi + phase)))
            x += step
        if len(pts) > 1:
            surface.lines(color, False, pts, width)


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

def glyph(surface, name, center, size, color=T.INK):
    cx, cy = center
    s = size / 2
    if name == 'oar':
        # a long oar, blade down-right
        surface.line(color, (cx - s, cy - s), (cx + s * 0.4, cy + s * 0.4), max(2, int(size / 9)))
        surface.polygon(color, [
            (cx + s * 0.3, cy + s * 0.2), (cx + s, cy + s * 0.55),
            (cx + s * 0.75, cy + s), (cx + s * 0.15, cy + s * 0.55)])
    elif name == 'bolt':
        surface.polygon(color, [
            (cx + s * 0.2, cy - s), (cx - s * 0.55, cy + s * 0.15),
            (cx - s * 0.05, cy + s * 0.15), (cx - s * 0.3, cy + s),
            (cx + s * 0.6, cy - s * 0.2), (cx + s * 0.1, cy - s * 0.2)])
    elif name == 'loom':
        # a temple front: pediment over three columns
        surface.polygon(color, [
            (cx - s, cy - s * 0.35), (cx, cy - s), (cx + s, cy - s * 0.35)])
        surface.rect(color, (cx - s, cy - s * 0.3, size, s * 0.22))
        for k in (-0.7, 0, 0.7):
            surface.rect(color, (cx + k * s - s * 0.12, cy - s * 0.05, s * 0.24, s * 0.9))
        surface.rect(color, (cx - s, cy + s * 0.8, size, s * 0.2))
    elif name == 'lyre':
        # a sound-box, two arms curving up and out, a yoke, strings
        w = max(2, int(size / 9))
        surface.ellipse(color, (cx - s * 0.55, cy + s * 0.25, s * 1.1, s * 0.7))
        surface.lines(color, False, [
            (cx - s * 0.45, cy + s * 0.35), (cx - s * 0.85, cy - s * 0.2),
            (cx - s * 0.7, cy - s * 0.85)], w)
        surface.lines(color, False, [
            (cx + s * 0.45, cy + s * 0.35), (cx + s * 0.85, cy - s * 0.2),
            (cx + s * 0.7, cy - s * 0.85)], w)
        surface.line(color, (cx - s * 0.75, cy - s * 0.7),
                     (cx + s * 0.75, cy - s * 0.7), w)
        for k in (-0.3, -0.1, 0.1, 0.3):
            surface.line(color, (cx + k * s, cy - s * 0.7),
                         (cx + k * s * 0.6, cy + s * 0.3), 1)
    elif name == 'hourglass':
        surface.polygon(color, [
            (cx - s * 0.7, cy - s), (cx + s * 0.7, cy - s), (cx, cy),
            (cx + s * 0.7, cy + s), (cx - s * 0.7, cy + s), (cx, cy)], 2)
    else:
        surface.circle(color, (cx, cy), s)


def ship(surface, center, size, color=T.INK, sail=T.PAPYRUS):
    """A black-figure ship, side on: hull, ram, mast, sail, oars."""
    cx, cy = center
    s = size / 2
    hull = [(cx - s, cy), (cx - s * 0.85, cy + s * 0.3), (cx + s * 0.75, cy + s * 0.3),
            (cx + s * 1.05, cy - s * 0.05), (cx + s * 0.9, cy - s * 0.02),
            (cx + s * 0.7, cy + s * 0.05), (cx - s * 0.8, cy + s * 0.05),
            (cx - s * 0.95, cy - s * 0.3)]
    surface.polygon(color, hull)
    # oars
    for k in range(6):
        x = cx - s * 0.6 + k * s * 0.22
        surface.line(color, (x, cy + s * 0.15), (x - s * 0.12, cy + s * 0.55), 2)
    # sail, then the mast and yard over it
    surface.polygon(sail, [
        (cx - s * 0.5, cy - s * 1.0), (cx + s * 0.5, cy - s * 1.0),
        (cx + s * 0.42, cy - s * 0.25), (cx - s * 0.42, cy - s * 0.25)])
    surface.polygon(color, [
        (cx - s * 0.5, cy - s * 1.0), (cx + s * 0.5, cy - s * 1.0),
        (cx + s * 0.42, cy - s * 0.25), (cx - s * 0.42, cy - s * 0.25)], 2)
    surface.line(color, (cx, cy + s * 0.05), (cx, cy - s * 1.1), 3)
    surface.line(color, (cx - s * 0.5, cy - s * 1.0), (cx + s * 0.5, cy - s * 1.0), 3)
    # stays
    surface.line(color, (cx, cy - s * 1.05), (cx - s * 0.8, cy - s * 0.05), 1)
    surface.line(color, (cx, cy - s * 1.05), (cx + s * 0.85, cy - s * 0.02), 1)


def eye(surface, center, size, color=T.INK):
    """The apotropaic eye painted on a prow."""
    cx, cy = center
    surface.ellipse(color, (cx - size, cy - size * 0.55, size * 2, size * 1.1), 2)
    surface.circle(color, (cx, cy), size * 0.4)
