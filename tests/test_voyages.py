"""The record of voyages and the chart of every road they took."""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from nobody import world as worlds                     # noqa: E402
from nobody import voyages                             # noqa: E402
from nobody.library import Library                     # noqa: E402
from nobody.session import Session                     # noqa: E402

ODYSSEY = os.path.join(os.path.dirname(HERE), 'worlds', 'odyssey')
SMALL = os.path.join(HERE, 'fixtures', 'odyssey-small.json')


@pytest.fixture(scope='module')
def world():
    return worlds.load(ODYSSEY)


@pytest.fixture(scope='module')
def library():
    return Library.load(SMALL)


def played(world, library, seed):
    s = Session(world, library, seed=seed)
    while not s.over:
        s.choose(s.random.randrange(len(s.crisis().options)))
    return s


def test_a_voyage_is_written_down_road_and_all(world, library, tmp_path):
    s = played(world, library, 3)
    rec = voyages.record(s, when='2026-09-07 12:00')
    assert rec['kind'] == s.outcome.kind and rec['title'] == s.outcome.title
    assert rec['crises'] == s.crises and rec['when'] == '2026-09-07 12:00'
    assert len(rec['road']) == len(s.pages)
    for step, page in zip(rec['road'], s.pages):
        assert step['beat'] == [page.beat[0], list(page.beat[1])]
        assert step['span'] and not step['span'].endswith('.')
        assert step['dithered'] == page.dithered
    path = str(tmp_path / 'runs.json')
    voyages.save_run(world, rec, path=path)
    voyages.save_run(world, rec, path=path, keep=1)
    assert voyages.load_runs(world, path=path) == [rec]
    assert json.load(open(path))[world.name] == [rec]
    assert voyages.load_runs(world, path=str(tmp_path / 'missing.json')) == []


def test_the_chart_merges_roads_by_their_shared_steps():
    step = lambda node, name, span, **k: dict(node=node, beat=[name, []], span=span, **k)   # noqa: E731
    runs = [
        {'kind': 'lost', 'title': 'The Gods: lost',
         'road': [step(0, 'a', 'A'), step(1, 'b', 'B')]},
        {'kind': 'ending', 'title': 'Home',
         'road': [step(0, 'a', 'A'), step(1, 'c', 'C', dithered=True), step(5, 'd', 'D')]},
        {'kind': 'silence', 'title': 'Silent', 'road': [step(0, 'x', 'X')]},
        {'kind': 'ending', 'title': 'Home',
         'road': [step(0, 'a', 'A'), step(1, 'c', 'C'), step(5, 'd', 'D')]},
        {'kind': 'lost', 'title': 'old record, no road'},
    ]
    rows, lanes = voyages.chart(runs)
    assert lanes == 3
    got = [(r.span, r.lane, r.parent, r.count, r.dithered, r.ends, r.latest) for r in rows]
    assert got == [
        ('A', 0, None, 3, False, [], True),            # the trunk: the road most took
        ('C', 0, 0, 2, True, [], True),                # its most-travelled continuation
        ('D', 0, 1, 2, False, [('ending', 'Home')] * 2, True),
        ('B', 1, 0, 1, False, [('lost', 'The Gods: lost')], False),   # a departure, own lane
        ('X', 2, None, 1, False, [('silence', 'Silent')], False),     # another, from the start
    ]
    assert voyages.chart([]) == ([], 0)
    assert voyages.chart([{'kind': 'lost'}]) == ([], 0)


def test_the_chart_of_real_voyages_holds_every_step(world, library):
    runs = [voyages.record(played(world, library, seed), when='x') for seed in range(6)]
    rows, lanes = voyages.chart(runs)
    assert sum(r.count for r in rows if r.parent is None) == len(runs)
    assert sum(len(r.ends) for r in rows) == len(runs)
    assert 1 <= lanes <= len(runs)
    assert sum(1 for r in rows if r.latest) == len(runs[-1]['road'])
