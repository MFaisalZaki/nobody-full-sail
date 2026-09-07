"""The drawing engine: one sine, three ways of drawing it, a matrix,
a clock that loops — and the pictures made of them."""

import math
import os
import sys

import pytest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame                                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from nobody.ui import draw as D                  # noqa: E402
from nobody.ui import theme as T                 # noqa: E402
from nobody.ui import wave as W                  # noqa: E402
from nobody.ui.wave import TAU, Wave             # noqa: E402


# --- the wave ---------------------------------------------------------------

def test_the_five_parameters_do_what_they_say():
    assert Wave(amplitude=2, frequency=0.25, offset=1)(1) == pytest.approx(3)      # A·sin(π/2) + K
    assert Wave(amplitude=1, speed=TAU / 4)(0, t=1) == pytest.approx(1)            # ω·t
    assert Wave(amplitude=1, phase=math.pi / 2)(0) == pytest.approx(1)             # φ
    assert Wave.flat(7)(123, t=456) == 7


def test_sampling_is_the_same_wave():
    w = Wave(1.5, 0.1, 0.7, 0.3, 2.0)
    us = [0.0, 1.0, 2.5, 10.0]
    assert w.sample(us, t=3.0) == pytest.approx([w(u, 3.0) for u in us])


def test_a_parameter_may_itself_be_a_wave():
    # the amplitude breathes with time: (2 + sin(π/2)) · sin(π/2)
    breathing = Wave(amplitude=Wave(1, 0, TAU / 4, 0, 2), frequency=0.25)
    assert breathing(1, t=1) == pytest.approx(3)
    assert breathing.sample([1], t=1) == pytest.approx([3])
    # the phase modulated along x: one axis feeding the other
    modulated = Wave(amplitude=1, phase=Wave(math.pi / 2, 0.5))
    assert modulated(0.5) == pytest.approx(1)


def test_waves_add_into_fourier_synthesis():
    a, b = Wave(1, 0.25), Wave(0.5, 0.75)
    both = a + b
    assert both(1) == pytest.approx(a(1) + b(1))
    assert (both + Wave.flat(1))(1) == pytest.approx(a(1) + b(1) + 1)
    assert sum([a, b])(1) == pytest.approx(a(1) + b(1))
    square = Wave.square(1, 1, harmonics=8)
    assert square(0.25) == pytest.approx(1, abs=0.1) and square(0.75) == pytest.approx(-1, abs=0.1)
    triangle = Wave.triangle(1, 1)
    assert triangle(0.25) == pytest.approx(1, abs=0.06) and triangle(0) == pytest.approx(0)


def test_a_wave_fixed_at_one_x_is_a_wave_of_time_and_its_slope_is_a_sine():
    w = Wave(3, 0.02, 0.5, 0.4, 10)
    assert w.fix(7)(0, t=2.5) == pytest.approx(w(7, 2.5))
    h = 1e-4
    assert w.slope()(7, 2.5) == pytest.approx((w(7 + h, 2.5) - w(7 - h, 2.5)) / (2 * h), rel=1e-4)
    assert w.scaled(2)(7, 2.5) == pytest.approx(2 * w(7, 2.5))


def test_the_shapes_span_what_they_say():
    assert Wave.bulge(4, 10)(0) == pytest.approx(0) and Wave.bulge(4, 10)(5) == pytest.approx(4)
    assert Wave.bulge(4, 10)(10) == pytest.approx(0, abs=1e-9)
    assert Wave.rise(4, 10)(0) == pytest.approx(0) and Wave.rise(4, 10)(10) == pytest.approx(4)
    assert Wave.fall(4, 10)(0) == pytest.approx(4) and Wave.fall(4, 10)(10) == pytest.approx(0, abs=1e-9)
    assert Wave.rise(4, -10)(-10) == pytest.approx(4)      # a span the other way


# --- the timeline ------------------------------------------------------------------

def test_the_timeline_accumulates_and_loops_without_a_jump():
    tl = W.Timeline(W.PERIOD - 0.5)
    assert tl.step(1.0) == pytest.approx(0.5)
    for speed in (0.8, 1.2, 0.37, 9.0, 6.0):
        w = Wave(1, 0, speed)
        assert w(0, 0.5) == pytest.approx(w(0, W.PERIOD + 0.5), abs=1e-6)


# --- the matrix mode -----------------------------------------------------------------

def test_a_motion_is_an_affine_matrix_of_sines():
    turn = W.Motion(angle=math.pi / 2)
    assert turn.point((1, 0)) == pytest.approx((0, 1))
    about = W.Motion(angle=math.pi, pivot=(1, 1))
    assert about.point((2, 1)) == pytest.approx((0, 1))
    bob = W.Motion(dy=Wave(3, 0, TAU / 4), scale=Wave(0.5, 0, 0, 0, 1))
    assert bob.point((2, 0), t=1) == pytest.approx((2, 3))
    assert W.move([(1, 0)], [turn, turn])[0] == pytest.approx((-1, 0))
    assert W.chain(None, turn, [about, None]) == [turn, about]


# --- the assets ----------------------------------------------------------------------

def test_a_ribbon_binds_paired_vertices_about_its_centre():
    r = W.Ribbon(Wave.flat(0), Wave.bulge(3, 10), 10, 'x', (0, 0), step=5)
    pts = r.vectors()
    assert len(pts) == 6                                      # 3 steps, two edges
    assert pts[1] == pytest.approx((5, -3)) and pts[4] == pytest.approx((5, 3))
    assert pts[0] == pytest.approx((0, 0)) and pts[-1] == pytest.approx((0, 0))
    down = W.Ribbon(Wave.flat(1), 2, 10, 'y', (0, 0), step=10).vectors()
    assert down[0] == pytest.approx((-1, 0)) and down[-1] == pytest.approx((3, 0))


def test_a_trail_runs_along_either_axis_and_backwards():
    along = W.Trail(Wave.flat(2), 4, 'x', (1, 1), step=2).vectors()
    assert along == pytest.approx([(1, 3), (3, 3), (5, 3)])
    up = W.Trail(Wave.flat(0), -4, 'y', (0, 10), step=2).vectors()
    assert up == pytest.approx([(0, 10), (0, 8), (0, 6)])


def test_an_orbit_is_a_lissajous_figure():
    o = W.Orbit.ellipse((1, 2), 4, 2, samples=64)
    for x, y in o.vectors():
        assert ((x - 1) / 4) ** 2 + ((y - 2) / 2) ** 2 == pytest.approx(1)
    going = W.Orbit(Wave(1, 0, TAU / 4), Wave(1, 0, TAU / 4, math.pi / 2))
    assert going.at(0, t=1) == pytest.approx((1, 0), abs=1e-9)


# --- the pictures ---------------------------------------------------------------------

def _canvas(size=120):
    pygame.init()
    surface = pygame.Surface((size, size))
    surface.fill(T.SEA)
    return D.Canvas(surface, 1.0), surface


def _inked(surface, color):
    return sum(1 for x in range(surface.get_width()) for y in range(surface.get_height())
               if surface.get_at((x, y))[:3] == color)


@pytest.mark.parametrize('name', ['oar', 'bolt', 'loom', 'lyre', 'hourglass', 'circle'])
def test_every_glyph_leaves_ink_and_stays_inside_its_box(name):
    canvas, surface = _canvas()
    D.glyph(canvas, name, (60, 60), 40, T.INK, t=0.7)
    assert _inked(surface, T.INK) > 20
    for x in range(120):
        for y in range(120):
            if surface.get_at((x, y))[:3] == T.INK:
                assert 34 <= x <= 86 and 34 <= y <= 86


def test_the_ship_sails_in_its_box_and_moves_when_told():
    canvas, surface = _canvas(240)
    ship = D.Ship(120)
    ship.render(canvas, (120, 140), T.INK, T.PAPYRUS, t=1.0, eye=T.PAPYRUS)
    assert _inked(surface, T.INK) > 400 and _inked(surface, T.PAPYRUS) > 100
    still = ship.hull.vectors()
    lifted = ship.hull.vectors(motion=W.Motion(dy=Wave(10, 0, TAU / 4)), t=1.0)
    assert lifted[0][1] == pytest.approx(still[0][1] + 10)


def test_the_sea_the_meander_and_a_gull_render():
    canvas, surface = _canvas()
    D.waves(canvas, (0, 0, 120, 60), T.FOAM, rows=2, amp=4, wavelength=40, t=2.0, speed=1.0, texture=0.3)
    D.meander(canvas, (10, 80, 100, 12), T.OCHRE)
    D.gull(canvas, (60, 100), 20, T.PAPYRUS, t=0.3)
    D.eye(canvas, (100, 100), 6, T.PAPYRUS)
    assert _inked(surface, T.FOAM) > 100 and _inked(surface, T.OCHRE) > 50
    assert _inked(surface, T.PAPYRUS) > 10
