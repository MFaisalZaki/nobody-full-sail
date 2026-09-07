"""The bestiary's people: drawn as the vases draw them, from the
engine's parts, in every pose the stage asks for."""

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
from nobody.ui import sprites as S               # noqa: E402
from nobody.ui import theme as T                 # noqa: E402


def _canvas(w=160, h=160):
    pygame.init()
    surface = pygame.Surface((w, h))
    surface.fill(T.SEA)
    return D.Canvas(surface, 1.0), surface


def _where(surface, color):
    pts = [(x, y) for x in range(surface.get_width()) for y in range(surface.get_height())
           if surface.get_at((x, y))[:3] == color]
    return pts


# --- the joints ------------------------------------------------------------------

def test_a_joint_bends_downward_and_reaches_no_further_than_its_bones():
    # a hand below and ahead of the shoulder: the elbow hangs back, between them
    elbow, hand = S._joint((0, 0), (10, 30), 20)
    assert hand == (10, 30)
    assert elbow[0] < 5 and 0 < elbow[1] < 30
    assert math.hypot(*elbow) == pytest.approx(20) and math.hypot(hand[0] - elbow[0], hand[1] - elbow[1]) == pytest.approx(20)
    # a hand level with the shoulder: the elbow drops
    elbow, _ = S._joint((0, 0), (30, 0), 20)
    assert elbow[1] > 0
    # a mark out of reach: the arm straight, the hand short of it
    elbow, hand = S._joint((0, 0), (0, -100), 20)
    assert hand == pytest.approx((0, -40)) and elbow == pytest.approx((0, -20))


# --- the figures ---------------------------------------------------------------------

POSES = [dict(), dict(crest=True, prop='spear'), dict(arms='raised', prop='bow', crest=True),
         dict(arms='out', gown=True, beard=True, prop='bag'), dict(arms='up'),
         dict(pose='sit', arms='cup', prop='cup'), dict(pose='sit', gown=True, prop='staff'),
         dict(pose='lie', arms='raised', prop='flower'), dict(walk=1.0), dict(lean=0.3, prop='stick'),
         dict(gown=True, fair=True, arms='raised'), dict(arms='throw'), dict(facing=-1, prop='spear')]


@pytest.mark.parametrize('kw', POSES)
def test_a_figure_leaves_ink_and_stands_on_its_feet(kw):
    canvas, surface = _canvas()
    S.figure(canvas, 80, 140, 60, 0.4, **kw)
    ink = _where(surface, T.INK)
    assert len(ink) > 200
    xs, ys = [p[0] for p in ink], [p[1] for p in ink]
    if kw.get('pose') == 'lie':
        assert max(xs) - min(xs) > 0.8 * 60        # long on the ground
    else:
        assert min(ys) < 140 - 0.8 * 60            # a head's worth above the ground
        assert max(ys) <= 140 + 0.05 * 60          # nothing below it but a spear's butt
        assert min(xs) > 20 and max(xs) < 140     # within a height either way of the feet


def test_a_figure_has_an_eye_and_a_belt_scratched_in_the_eyes_colour():
    canvas, surface = _canvas()
    S.figure(canvas, 80, 140, 60, 0.0)
    marks = _where(surface, T.PAPYRUS)
    assert marks
    ys = [y for _, y in marks]
    assert min(ys) < 140 - 0.85 * 60              # the eye, up in the head
    assert any(abs(y - (140 - 0.58 * 60)) <= 1 for y in ys)     # the belt, at the waist


def test_a_fair_face_is_painted_in_the_light():
    canvas, surface = _canvas()
    S.figure(canvas, 80, 150, 120, 0.0, gown=True, fair=True)
    light = [p for p in _where(surface, T.PAPYRUS) if p[1] < 150 - 0.8 * 120]
    assert len(light) > 100                       # a face, not a dot


def test_the_dead_have_no_eyes_and_the_cyclops_one():
    canvas, surface = _canvas()
    S.shade(canvas, 80, 140, 60, 0.0)
    assert not _where(surface, T.PAPYRUS) and _where(surface, T.GHOST)
    canvas, surface = _canvas()
    S.cyclops(canvas, 80, 150, 100, 0.0)
    eye = [p for p in _where(surface, T.PAPYRUS) if p[1] < 150 - 0.85 * 100]
    assert len(eye) > 40
    canvas, surface = _canvas()
    S.cyclops(canvas, 80, 150, 100, 0.0, blind=True)
    assert _where(surface, T.TERRACOTTA)


def test_a_siren_is_a_bird_with_a_womans_head():
    canvas, surface = _canvas()
    S.siren(canvas, 80, 140, 50, 0.3, singing=False)
    ink = _where(surface, T.INK)
    assert len(ink) > 300 and _where(surface, T.INK_SOFT)      # a body, and the far wing
    assert _where(surface, T.PAPYRUS)                           # her face


def test_a_figure_survives_being_very_small_and_very_large():
    canvas, surface = _canvas(400, 400)
    S.figure(canvas, 20, 30, 5, 0.0, crest=True, prop='spear')
    S.figure(canvas, 200, 390, 300, 0.0, gown=True, fair=True, arms='out', prop='cup')
    assert _where(surface, T.INK)
