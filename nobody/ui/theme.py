"""Colours and type. One palette — wine-dark sea, terracotta, papyrus,
black-figure black — and a serif for everything, because the poem is
the oldest thing in the room."""

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

_fonts = {}


def font(size, bold=False, italic=False):
    """A serif at `size` — the system's, if it has one we know;
    pygame's own face otherwise."""
    key = (size, bold, italic)
    if key not in _fonts:
        name = pygame.font.match_font(
            ['dejavuserif', 'freeserif', 'liberationserif', 'georgia',
             'timesnewroman', 'times'], bold=bold, italic=italic)
        f = pygame.font.Font(name, size) if name else pygame.font.Font(None, size + 4)
        if name is None:
            f.set_bold(bold)
            f.set_italic(italic)
        _fonts[key] = f
    return _fonts[key]


def mono(size):
    key = ('mono', size)
    if key not in _fonts:
        name = pygame.font.match_font(['dejavusansmono', 'liberationmono',
                                       'freemono', 'couriernew'])
        _fonts[key] = pygame.font.Font(name, size) if name else pygame.font.Font(None, size + 2)
    return _fonts[key]
