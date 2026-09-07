"""A board, drawn: the pack reads the atoms into a Scene, and the stage
draws every island without a word."""

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
from nobody.ui import scene as SC                # noqa: E402
from nobody.ui import theme as T                 # noqa: E402

ODYSSEY = os.path.join(os.path.dirname(HERE), 'worlds', 'odyssey')
SMALL = os.path.join(HERE, 'fixtures', 'odyssey-small.json')

PLACES = ['troy', 'ismaros', 'lotus-land', 'cyclops-island', 'aeolia', 'telepylos',
          'aiaia', 'the-dead', 'strait', 'thrinacia', 'ogygia', 'scheria', 'ithaca']


@pytest.fixture(scope='module')
def world():
    return worlds.load(ODYSSEY)


def board(place, *extra, crew='full', ship=True):
    atoms = [('at', 'odysseus', place), ('crew', crew), ('alive', 'eurylochus'),
             ('with', 'eurylochus')]
    if ship:
        atoms.append(('ship-whole',))
    return atoms + list(extra)


def test_every_island_has_something_to_look_at(world):
    for place in PLACES:
        scene = world.scene(board(place))
        assert scene.place == place
        assert scene.landmark is not None, place
        assert scene.setting in ('shore', 'sea', 'harbour', 'cave', 'hall', 'underworld')


def test_the_marks_change_the_picture(world):
    s = world.scene(board('cyclops-island', ('blinded', 'polyphemus'), ('in-cave',), ('cave-shut',)))
    assert s.setting == 'cave' and s.hero['inside'] == 'cave'
    assert s.landmark[1]['shut'] and dict(s.cast)['cyclops']['blind']
    s = world.scene(board('aiaia', ('swine',)))
    assert dict(s.cast)['swine']['n'] == 3 and s.hero['crew-pose'] == 'none'
    s = world.scene(board('ogygia', ('held-by', 'calypso'), ('raft-built',), crew='alone', ship=False))
    assert s.vessel == 'raft' and s.hero['kept'] and s.hero['pose'] == 'sit'
    s = world.scene(board('ithaca', ('disguised',), ('bow-strung',), ship=False))
    assert s.hero['disguised'] and s.hero['prop'] == 'bow' and s.vessel is None
    s = world.scene(board('troy', ('horse-built',), ('inside-horse',)))
    assert s.landmark[1]['horse'] and s.hero['inside'] == 'horse'
    s = world.scene(board('thrinacia', ('wreckage', 'thrinacia'), ship=False))
    assert s.vessel == 'wreck'


def test_the_caption_keeps_what_the_picture_cannot_show(world):
    caption = world.scene(board('troy')).caption
    assert 'Troy' in caption and 'Eurylochus' in caption
    assert 'full strength' not in caption and 'ship' not in caption


def test_a_plain_world_still_answers(world):
    from nobody.world import World
    plain = World.scene(world, board('troy'))
    assert plain.place == 'troy' and plain.landmark is None and plain.caption


def _ink(surface, colors):
    return sum(1 for x in range(0, surface.get_width(), 2) for y in range(0, surface.get_height(), 2)
               if surface.get_at((x, y))[:3] in colors)


@pytest.mark.parametrize('place', PLACES)
def test_every_stage_draws_and_leaves_ink(world, place):
    pygame.init()
    surface = pygame.Surface((392, 290))
    surface.fill(T.PAPYRUS)
    canvas = D.Canvas(surface, 1.0)
    T.set_scale(1.0)
    scene = world.scene(board(place, ('wrathful',), crew='thinned'))
    stage = SC.Stage(scene, (0, 0, 392, 290))
    for mood in (1.0, 0.5, 0.1):
        stage.draw(canvas, 2.0, mood)
    assert _ink(surface, {T.INK, T.INK_SOFT}) > 300


def test_the_shipped_library_draws_from_the_fixture(world):
    pygame.init()
    library = Library.load(SMALL)
    surface = pygame.Surface((392, 290))
    canvas = D.Canvas(surface, 1.0)
    seen = set()
    for node in library.nodes[:40]:
        scene = world.scene(node.atoms(), library.nodes[0].atoms())
        seen.add(scene.place)
        SC.Stage(scene, (0, 0, 392, 290)).draw(canvas, 1.0, 0.7)
    assert seen
