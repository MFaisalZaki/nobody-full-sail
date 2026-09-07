"""The window and the canvas: logical units in, device pixels out, at
whatever scale the screen affords."""

import os
import sys

import pytest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame                                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from nobody import world as worlds               # noqa: E402
from nobody.library import Library               # noqa: E402
from nobody.ui import draw as D                  # noqa: E402
from nobody.ui import theme as T                 # noqa: E402
from nobody.ui.app import App, CrisisScreen      # noqa: E402
from nobody.ui.window import AIR, TITLE_BAR, fit_scale   # noqa: E402

ODYSSEY = os.path.join(os.path.dirname(HERE), 'worlds', 'odyssey')
SMALL = os.path.join(HERE, 'fixtures', 'odyssey-small.json')


@pytest.fixture(autouse=True)
def one_to_one():
    """The render scale is module state; every test starts and ends at 1."""
    T.set_scale(1.0)
    yield
    T.set_scale(1.0)


def test_the_canvas_maps_units_to_pixels():
    c = D.Canvas(pygame.Surface((100, 100)), k=2.0, origin=(10, 4))
    assert c.pt((5, 7)) == (20, 18)
    assert c.area((1, 2, 3, 4)) == pygame.Rect(12, 8, 6, 8)
    assert c.area(pygame.Rect(1, 2, 3, 4)) == pygame.Rect(12, 8, 6, 8)
    assert c.length(6) == 12
    assert c.stroke(0) == 0 and c.stroke(1) == 2
    assert c.bounds() == (-5, -2, 50, 50)


def test_a_stroke_never_thins_to_nothing():
    c = D.Canvas(pygame.Surface((10, 10)), k=0.3)
    assert c.stroke(1) == 1


def test_neighbouring_areas_stay_flush():
    c = D.Canvas(pygame.Surface((100, 100)), k=1.37)
    a, b = c.area((0, 0, 10, 10)), c.area((10, 0, 10, 10))
    assert a.right == b.left


def test_fonts_follow_the_scale():
    pygame.font.init()
    one = T.font(16)
    T.set_scale(2.0)
    two = T.font(16)
    assert two.font.get_height() >= 2 * one.font.get_height() - 2
    assert abs(two.get_height() - one.get_height()) <= 2
    assert abs(two.size('wine-dark')[0] - one.size('wine-dark')[0]) <= 2
    glyph = two.render('Nobody', True, T.INK)
    assert glyph.image.get_height() == two.font.get_height()
    assert glyph.get_height() == two.get_height()


def test_the_fit_keeps_the_window_inside_the_usable_screen():
    # a 14" MacBook Pro: a 33-point menu bar, a dock, 860 points left
    s = fit_scale((0, 33, 1512, 860))
    assert s < 1.0
    assert T.H * s + TITLE_BAR + AIR <= 860
    # a big monitor: no reason to shrink
    assert fit_scale((0, 0, 2560, 1440)) == 1.0
    # a screen that is narrow rather than short
    s = fit_scale((0, 0, 300, 2000))
    assert T.W * s + AIR <= 300


def test_the_screens_render_at_twice_the_size():
    world = worlds.load(ODYSSEY)
    library = Library.load(SMALL)
    app = App(world, library, headless=True, seed=1, timer=45, scale=2.0)
    assert app.frame().get_size() == (880, 1760)
    assert T.scale() == 2.0
    app.new_game()
    assert isinstance(app.screen, CrisisScreen)
    frame = app.frame()
    # the card's papyrus, just inside its ink border, at device scale
    assert frame.get_at((2 * 30, 2 * 400))[:3] == T.PAPYRUS
    # the sea, in the margin
    assert frame.get_at((2 * 4, 2 * 400))[:3] in (T.SEA, T.SEA_LIGHT)
    pygame.quit()
