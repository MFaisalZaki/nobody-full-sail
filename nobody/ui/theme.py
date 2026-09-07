"""Colours and type. One palette — wine-dark sea, terracotta, papyrus,
black-figure black — and a serif for everything, because the poem is
the oldest thing in the room."""

import math

import pygame

# the wine-dark palette
SEA        = (18, 27, 52)        # the deep water the whole game floats on
SEA_DARK   = (10, 15, 32)
SEA_LIGHT  = (34, 52, 92)
FOAM       = (232, 238, 244)
PAPYRUS    = (242, 232, 207)     # the card, the newspaper
PAPYRUS_DK = (222, 208, 176)
INK        = (26, 24, 22)        # black-figure black
INK_SOFT   = (70, 62, 54)
TERRACOTTA = (196, 98, 56)
TERRA_DK   = (150, 70, 40)
OCHRE      = (224, 164, 88)      # gold leaf, the meander
OLIVE      = (108, 122, 74)
WINE       = (110, 34, 48)
GOOD       = (96, 150, 90)
BAD        = (186, 60, 52)
DIM        = (130, 138, 150)

#: logical size — a phone held upright; the window scales it
W, H = 440, 880

SERIF = ['dejavuserif', 'freeserif', 'liberationserif', 'georgia',
         'timesnewroman', 'times']
MONO = ['dejavusansmono', 'liberationmono', 'freemono', 'couriernew']

#: the render scale: device pixels per logical unit. The app sets it
#: from the surface it is drawing on — 2.0 for a 1:1 window on a Retina
#: display, 1.85 when the window was shrunk to clear the dock — and
#: every font is opened at that size, so text is rasterised at the
#: resolution it is shown at rather than drawn small and stretched.
_k = 1.0
_fonts = {}
_names = {}


def set_scale(k):
    """Render at `k` device pixels per logical unit from now on. Fonts
    opened at another scale are dropped."""
    global _k
    k = max(0.1, float(k))
    if k != _k:
        _k = k
        _fonts.clear()


def scale():
    return _k


class Glyph:
    """A rendered line of text: the pixels, measured in logical units,
    so that layout arithmetic stays in the 440x880 world."""
    __slots__ = ('image', 'k')

    def __init__(self, image, k):
        self.image = image
        self.k = k

    def get_width(self):
        return math.ceil(self.image.get_width() / self.k)

    def get_height(self):
        return math.ceil(self.image.get_height() / self.k)

    def get_size(self):
        return self.get_width(), self.get_height()


class Face:
    """A font opened at `size * k` pixels and measured in logical
    units: `render` gives a Glyph, `size` and `get_height` answer in
    the units the screens lay themselves out in."""
    __slots__ = ('font', 'k')

    def __init__(self, font, k):
        self.font = font
        self.k = k

    def render(self, text, antialias=True, color=(0, 0, 0)):
        return Glyph(self.font.render(text, antialias, color), self.k)

    def size(self, text):
        w, h = self.font.size(text)
        return math.ceil(w / self.k), math.ceil(h / self.k)

    def get_height(self):
        return math.ceil(self.font.get_height() / self.k)


def _open(names, size, bold=False, italic=False, fallback_pad=4):
    """`names` (the first the system has) at `size` logical units,
    pygame's own face when it has none of them."""
    key = (tuple(names), bold, italic)
    if key not in _names:
        _names[key] = pygame.font.match_font(names, bold=bold, italic=italic)
    name = _names[key]
    px = max(1, round(size * _k))
    if name:
        f = pygame.font.Font(name, px)
    else:
        f = pygame.font.Font(None, max(1, round((size + fallback_pad) * _k)))
        f.set_bold(bold)
        f.set_italic(italic)
    return Face(f, _k)


def font(size, bold=False, italic=False):
    """A serif at `size` — the system's, if it has one we know;
    pygame's own face otherwise."""
    key = (size, bold, italic)
    if key not in _fonts:
        _fonts[key] = _open(SERIF, size, bold, italic)
    return _fonts[key]


def mono(size):
    key = ('mono', size)
    if key not in _fonts:
        _fonts[key] = _open(MONO, size, fallback_pad=2)
    return _fonts[key]
