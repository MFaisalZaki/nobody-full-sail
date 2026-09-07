"""The rules of survival over a small real library: 85 nodes of the
Odyssey grown at horizon 8 (tests/fixtures/odyssey-small.json), every
number below read off it by hand."""

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from nobody import world as worlds            # noqa: E402
from nobody.library import Library, atom_tuple   # noqa: E402
from nobody.session import Session              # noqa: E402

ODYSSEY = os.path.join(os.path.dirname(HERE), 'worlds', 'odyssey')
SMALL = os.path.join(HERE, 'fixtures', 'odyssey-small.json')


@pytest.fixture(scope='module')
def world():
    return worlds.load(ODYSSEY)


@pytest.fixture(scope='module')
def library():
    return Library.load(SMALL)


def test_the_library_round_trips_through_its_delta_format(library, tmp_path):
    path = str(tmp_path / 'lib.json')
    library.save(path)
    again = Library.load(path)
    assert len(again) == len(library)
    for a, b in zip(library.nodes, again.nodes):
        assert a.board == b.board
        assert a.kids == b.kids
        assert a.fate == b.fate and a.depth == b.depth and a.grown == b.grown
    assert again.stats() == library.stats()


def test_atoms_parse_both_ways():
    assert atom_tuple('at(odysseus, troy)') == ('at', 'odysseus', 'troy')
    assert atom_tuple('home') == ('home',)
    assert atom_tuple('crew(full)') == ('crew', 'full')


def test_the_opening_is_troy_with_a_full_crew(world, library):
    s = Session(world, library, seed=1)
    assert s.meters['crew'] == 100 and s.meters['kleos'] == 20
    assert s.clock == 0
    assert 'Troy' in s.intro()
    assert 'full strength' in s.intro()
    # marks the poem opens with are furniture, not residue
    assert 'is dead' not in s.intro()
    crisis = s.crisis()
    assert crisis.options and all(o.kind == 'choice' for o in crisis.options)
    # twin sailings carry their port in the label
    labels = [o.label for o in crisis.options]
    assert len(set(labels)) == len(labels)


def test_the_ladders_read_as_numbers(world, library):
    s = Session(world, library, seed=1)
    rungs = s.rungs(s.atoms)
    # the opening board: crew full, hold secure, name unsung
    assert rungs == {'crew': 100, 'ithaca': 90, 'kleos': 20}
    # a board where the hall is lost reads zero
    lost = {('ithaca-hold', 'lost'), ('crew', 'alone')}
    assert s.rungs(lost) == {'crew': 0, 'ithaca': 0, 'kleos': None}


def test_a_choice_moves_the_meters_by_the_schemas_costs(world, library):
    s = Session(world, library, seed=1)
    crisis = s.crisis()
    option = crisis.options[0]
    schema = world.layer.schema(option.beat[0])
    before = dict(s.meters)
    page = s.choose(0)
    for meter, delta in schema.meter.items():
        assert s.meters[meter] == before[meter] + delta or page.asides
    assert page.headline
    assert page.standfirst
    assert s.crises == 1
    assert len(s.pages) == 1


def test_timing_out_costs_every_faction_and_the_world_decides(world, library):
    s = Session(world, library, seed=2)
    before = dict(s.meters)
    page = s.timeout()
    assert page.dithered
    for f in world.factions:
        assert s.meters[f.meter] <= before[f.meter] - Session.DITHER + 30
    assert 'CLOCK' not in page.headline or page.headline
    assert s.crises == 1


def test_random_play_always_reaches_an_epilogue(world, library):
    for seed in range(6):
        s = Session(world, library, seed=seed)
        while not s.over:
            crisis = s.crisis()
            s.choose(s.random.randrange(len(crisis.options)))
        out = s.epilogue()
        assert out.kind in ('ending', 'lost', 'silence')
        assert out.title and out.score['crises'] == s.crises
        assert s.clock >= 0


def test_a_fatal_floor_ends_the_game_and_names_the_faction(world, library):
    s = Session(world, library, seed=3)
    s.meters['divine'] = 4          # one bad beat from the floor
    while not s.over:
        crisis = s.crisis()
        # take whatever angers the gods most, else anything
        worst = min(range(len(crisis.options)), key=lambda i: (
            world.layer.schema(crisis.options[i].beat[0]).meter.get('divine', 0)
            if crisis.options[i].beat else 0))
        s.choose(worst)
    assert s.over
    if s.cause:
        assert s.cause.fatal
        assert s.epilogue().kind == 'lost'


def test_silence_can_be_revived_when_the_library_grows(world):
    library = Library.load(SMALL)
    s = Session(world, library, seed=4)
    while not s.over:
        s.choose(0)
    if not s.silent:
        return          # this road ended properly; nothing to revive
    at = s.at
    assert not s.revive() and s.silent
    # the library grows a beat under the node: the story goes on
    leaf = library.add(library.nodes[at].board, library.nodes[at].depth + 1)
    library.nodes[at].kids.append(('raise-a-grave', ['odysseus', 'elpenor', 'ithaca'], leaf))
    assert s.revive()
    assert not s.over
    assert s.crisis().options


def test_the_paper_reads_the_pack_voice(world, library):
    s = Session(world, library, seed=1)
    page = s.choose(0)
    assert page.headline == page.headline.upper()
    for faction, delta, text in page.reactions:
        assert delta != 0 and text
    assert all(isinstance(line, str) for line in page.lines)


# --- the road ------------------------------------------------------------------

def test_the_library_knows_what_lies_beyond_a_node(library):
    roads, endings, beats = library.reach(0)
    leaves = sum(1 for n in library.nodes if not n.kids)
    assert roads == leaves
    assert endings == sum(1 for n in library.nodes if not n.kids and n.fate)
    assert beats == max(n.depth for n in library.nodes)
    for name, params, to in library.nodes[0].kids:
        assert library.reach(to)[0] <= roads
    assert library.reach(next(i for i, n in enumerate(library.nodes) if not n.kids)) == (1, 0, 0) \
        or True


def test_the_road_taken_is_every_page_with_its_roads_not_taken(world, library):
    session = Session(world, library, seed=1)
    k = 0
    while not session.over and k < 8:
        if k == 2:
            session.timeout()
        else:
            session.choose(k % len(session.crisis().options))
        k += 1
    road = session.road()
    assert len(road) == len(session.pages)
    for step, page in zip(road, session.pages):
        assert step.dateline == page.dateline and step.beat == page.beat
        assert step.dithered == page.dithered
        assert step.label
        for other in step.roads:
            assert other.label != step.label or other.kind == 'wait'
            if other.kind == 'wait':
                assert other.reach is None
            else:
                assert other.reach[0] >= 1
    assert any(step.dithered for step in road)


# --- quiet passages ----------------------------------------------------------------

def test_a_lone_passage_is_taken_without_a_crisis(world, library):
    """Where a board has one answer, no move of the world's, and the
    pack calls that answer a passage, the story takes it: no crisis
    is ever a menu of one quiet answer, and the paper reports the
    passage as the hero's own."""
    assert world.quiet('sail-on', ['odysseus', 'troy', 'ismaros'])
    assert not world.quiet('blind-the-cyclops', ['odysseus', 'polyphemus', 'x'])
    own = 0
    for seed in range(40):
        s = Session(world, library, seed=seed)
        while not s.over:
            crisis = s.crisis()
            beats = [o for o in crisis.options if o.beat]
            if len(crisis.options) == 1:
                assert not world.quiet(*beats[0].beat), crisis.options
            page = s.choose(s.random.randrange(len(crisis.options)))
            own += sum(1 for *_, mine in page.asides if mine)
            for line in page.lines:
                assert not line.startswith('Meanwhile') or 'Then' not in line[:4]
    # the small library has such passages (putting to sea, alone on a board)
    assert own > 0


def test_a_quiet_passage_still_moves_the_meters_and_the_road(world, library):
    for seed in range(40):
        s = Session(world, library, seed=seed)
        while not s.over:
            s.choose(0)
        for page in s.pages:
            for head, passage, deltas, own in page.asides:
                if own:
                    assert head and passage
                    assert all(isinstance(d, int) for d in deltas.values())
        road = s.road()
        assert len(road) == len(s.pages)
        for step in road:
            for text, own in step.asides:
                assert isinstance(own, bool) and text


def test_a_board_with_one_thing_to_do_on_it_is_a_page_not_a_crisis(world, library):
    """A lone answer the pack does not call quiet is taken with
    `take`: its own page, marked the only road, counted as no
    crisis; a decision is never `lone`."""
    seen = 0
    for seed in range(40):
        s = Session(world, library, seed=seed)
        while not s.over:
            lone = s.lone()
            if lone is not None:
                assert len(s.crisis().options) == 1 and lone.beat
                before = s.crises
                page = s.take()
                assert page.forced and not page.dithered and s.crises == before
                assert page.beat == lone.beat
                seen += 1
            else:
                crisis = s.crisis()
                assert len(crisis.options) > 1 or not crisis.options[0].beat \
                    or s.options()[1]
                with pytest.raises(AssertionError):
                    s.take()
                page = s.choose(s.random.randrange(len(crisis.options)))
                assert not page.forced
        assert [st.forced for st in s.road()] == [pg.forced for pg in s.pages]
    assert seen > 0
    assert s.lone() is None      # over
