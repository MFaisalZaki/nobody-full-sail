"""Drawing helpers: wrapped text, buttons, the meander, the glyphs, the
ship. Everything is primitives, so nothing here needs an asset."""

import math

import pygame

from . import theme as T


# --- text ------------------------------------------------------------------

def wrap(font, text, width):
    """`text` as lines no wider than `width` pixels (words kept whole;
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
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)


def shadow_rect(surface, rect, radius=10, offset=4):
    """A soft drop: the card floating on the sea."""
    r = pygame.Rect(rect).move(offset, offset)
    pygame.draw.rect(surface, T.SEA_DARK, r, border_radius=radius)


def hrule(surface, x1, x2, y, color=T.INK, width=1):
    pygame.draw.line(surface, color, (x1, y), (x2, y), width)


def meander(surface, rect, color=T.OCHRE, cell=12, width=2):
    """A Greek key along the top edge of `rect`, one cell after
    another: the border every vase has."""
    x0, y0, w, h = rect
    n = max(1, w // cell)
    s = cell
    for i in range(n):
        x = x0 + i * s
        y = y0
        # one key: a squared spiral drawn as a polyline
        pts = [(x, y + s), (x, y), (x + s, y), (x + s, y + s * 0.66),
               (x + s * 0.33, y + s * 0.66), (x + s * 0.33, y + s * 0.33),
               (x + s * 0.66, y + s * 0.33)]
        pygame.draw.lines(surface, color, False, pts, width)


def waves(surface, rect, color, rows=5, amp=4, wavelength=48, width=2,
          phase=0.0):
    """Rows of long sine waves: the sea under everything."""
    x0, y0, w, h = rect
    for r in range(rows):
        y = y0 + h * (r + 0.5) / rows
        pts = []
        for x in range(x0, x0 + w + 1, 4):
            pts.append((x, y + amp * math.sin((x + r * 17) / wavelength * 2 * math.pi + phase)))
        pygame.draw.lines(surface, color, False, pts, width)


def button(surface, rect, label, font, fill=T.TERRACOTTA, ink=T.PAPYRUS,
           hover=False, radius=12, border=T.INK, small=None):
    """A chunky rounded button with a wrapped label; returns its rect."""
    r = pygame.Rect(rect)
    shadow_rect(surface, r, radius, 3)
    pygame.draw.rect(surface, T.TERRA_DK if hover else fill, r, border_radius=radius)
    pygame.draw.rect(surface, border, r, width=2, border_radius=radius)
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
    pygame.draw.rect(surface, back, r, border_radius=radius)
    frac = 0 if hi == lo else max(0.0, min(1.0, (value - lo) / (hi - lo)))
    if frac > 0:
        inner = pygame.Rect(r.x, r.y, max(int(r.width * frac), radius * 2 if frac > 0.02 else 0), r.height)
        pygame.draw.rect(surface, fill, inner, border_radius=radius)
    pygame.draw.rect(surface, T.INK, r, width=1, border_radius=radius)


def badge(surface, pos, delta, font):
    """A +8 / −12 pill."""
    good = delta > 0
    s = f'+{delta}' if good else f'−{abs(delta)}'
    img = font.render(s, True, T.PAPYRUS)
    w, h = img.get_width() + 12, img.get_height() + 4
    r = pygame.Rect(pos[0], pos[1], w, h)
    pygame.draw.rect(surface, T.GOOD if good else T.BAD, r, border_radius=h // 2)
    surface.blit(img, (r.x + 6, r.y + 2))
    return r


# --- glyphs: the four factions, drawn black-figure ---------------------------

def glyph(surface, name, center, size, color=T.INK):
    cx, cy = center
    s = size / 2
    if name == 'oar':
        # a long oar, blade down-right
        pygame.draw.line(surface, color, (cx - s, cy - s), (cx + s * 0.4, cy + s * 0.4), max(2, int(size / 9)))
        pygame.draw.polygon(surface, color, [
            (cx + s * 0.3, cy + s * 0.2), (cx + s, cy + s * 0.55),
            (cx + s * 0.75, cy + s), (cx + s * 0.15, cy + s * 0.55)])
    elif name == 'bolt':
        pygame.draw.polygon(surface, color, [
            (cx + s * 0.2, cy - s), (cx - s * 0.55, cy + s * 0.15),
            (cx - s * 0.05, cy + s * 0.15), (cx - s * 0.3, cy + s),
            (cx + s * 0.6, cy - s * 0.2), (cx + s * 0.1, cy - s * 0.2)])
    elif name == 'loom':
        # a temple front: pediment over three columns
        pygame.draw.polygon(surface, color, [
            (cx - s, cy - s * 0.35), (cx, cy - s), (cx + s, cy - s * 0.35)])
        pygame.draw.rect(surface, color, (cx - s, cy - s * 0.3, size, s * 0.22))
        for k in (-0.7, 0, 0.7):
            pygame.draw.rect(surface, color, (cx + k * s - s * 0.12, cy - s * 0.05, s * 0.24, s * 0.9))
        pygame.draw.rect(surface, color, (cx - s, cy + s * 0.8, size, s * 0.2))
    elif name == 'lyre':
        # a sound-box, two arms curving up and out, a yoke, strings
        w = max(2, int(size / 9))
        pygame.draw.ellipse(surface, color, (cx - s * 0.55, cy + s * 0.25, s * 1.1, s * 0.7))
        pygame.draw.lines(surface, color, False, [
            (cx - s * 0.45, cy + s * 0.35), (cx - s * 0.85, cy - s * 0.2),
            (cx - s * 0.7, cy - s * 0.85)], w)
        pygame.draw.lines(surface, color, False, [
            (cx + s * 0.45, cy + s * 0.35), (cx + s * 0.85, cy - s * 0.2),
            (cx + s * 0.7, cy - s * 0.85)], w)
        pygame.draw.line(surface, color, (cx - s * 0.75, cy - s * 0.7),
                         (cx + s * 0.75, cy - s * 0.7), w)
        for k in (-0.3, -0.1, 0.1, 0.3):
            pygame.draw.line(surface, color, (cx + k * s, cy - s * 0.7),
                             (cx + k * s * 0.6, cy + s * 0.3), 1)
    elif name == 'hourglass':
        pygame.draw.polygon(surface, color, [
            (cx - s * 0.7, cy - s), (cx + s * 0.7, cy - s), (cx, cy),
            (cx + s * 0.7, cy + s), (cx - s * 0.7, cy + s), (cx, cy)], 2)
    else:
        pygame.draw.circle(surface, color, (cx, cy), s)


def ship(surface, center, size, color=T.INK, sail=T.PAPYRUS):
    """A black-figure ship, side on: hull, ram, mast, sail, oars."""
    cx, cy = center
    s = size / 2
    hull = [(cx - s, cy), (cx - s * 0.85, cy + s * 0.3), (cx + s * 0.75, cy + s * 0.3),
            (cx + s * 1.05, cy - s * 0.05), (cx + s * 0.9, cy - s * 0.02),
            (cx + s * 0.7, cy + s * 0.05), (cx - s * 0.8, cy + s * 0.05),
            (cx - s * 0.95, cy - s * 0.3)]
    pygame.draw.polygon(surface, color, hull)
    # oars
    for k in range(6):
        x = cx - s * 0.6 + k * s * 0.22
        pygame.draw.line(surface, color, (x, cy + s * 0.15), (x - s * 0.12, cy + s * 0.55), 2)
    # sail, then the mast and yard over it
    pygame.draw.polygon(surface, sail, [
        (cx - s * 0.5, cy - s * 1.0), (cx + s * 0.5, cy - s * 1.0),
        (cx + s * 0.42, cy - s * 0.25), (cx - s * 0.42, cy - s * 0.25)])
    pygame.draw.polygon(surface, color, [
        (cx - s * 0.5, cy - s * 1.0), (cx + s * 0.5, cy - s * 1.0),
        (cx + s * 0.42, cy - s * 0.25), (cx - s * 0.42, cy - s * 0.25)], 2)
    pygame.draw.line(surface, color, (cx, cy + s * 0.05), (cx, cy - s * 1.1), 3)
    pygame.draw.line(surface, color, (cx - s * 0.5, cy - s * 1.0), (cx + s * 0.5, cy - s * 1.0), 3)
    # stays
    pygame.draw.line(surface, color, (cx, cy - s * 1.05), (cx - s * 0.8, cy - s * 0.05), 1)
    pygame.draw.line(surface, color, (cx, cy - s * 1.05), (cx + s * 0.85, cy - s * 0.02), 1)


def eye(surface, center, size, color=T.INK):
    """The apotropaic eye painted on a prow."""
    cx, cy = center
    pygame.draw.ellipse(surface, color, (cx - size, cy - size * 0.55, size * 2, size * 1.1), 2)
    pygame.draw.circle(surface, color, (cx, cy), size * 0.4)
