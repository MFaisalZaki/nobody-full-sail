"""The record of past voyages, and the chart of every road they took.

Every game that ends is written down: how it ended, the score, when,
and the road — each decision as (the board it was made on, the beat
taken). Roads from the same opening share their first steps, so the
record is a tree, and the title screen charts it the way the game
charts a single voyage: the road most often taken down the trunk,
every departure from it on a lane of its own, the endings found at
the tips. Nothing here needs pygame: `chart` lays the tree out as
rows, and the screen draws them.
"""

import json
import os
import time

RUNS_FILE = os.path.join(os.path.expanduser('~'), '.nobody', 'runs.json')


# --- the file ----------------------------------------------------------------------

def load_runs(world, path=RUNS_FILE):
    """This world's voyages, oldest first."""
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f).get(world.name, [])
    except (OSError, ValueError):
        return []


def save_run(world, record, path=RUNS_FILE, keep=50):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}
        data.setdefault(world.name, []).append(record)
        data[world.name] = data[world.name][-keep:]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1)
    except OSError:
        pass


# --- one voyage --------------------------------------------------------------------

def record(session, when=None):
    """A finished game, for the record: its outcome, its score, when
    it was played, and the road — one entry per decision, with the
    board it was made on, the beat taken and how the paper spanned
    it, and whether the clock ran out on it."""
    out = session.outcome
    score = session.score()
    layer = session.layer
    road = []
    for step in session.road():
        name, params = step.beat
        road.append({'node': step.node, 'beat': [name, list(params)],
                     'span': layer.span(name, params).rstrip('.'),
                     'dithered': bool(step.dithered)})
    return {'title': out.title if out else '', 'kind': out.kind if out else 'silence',
            'crises': score['crises'], 'years': score['years'],
            'when': when or time.strftime('%Y-%m-%d %H:%M'), 'road': road}


# --- every voyage, as one tree ------------------------------------------------------

class Row:
    """One step of the chart: a beat some voyages took from a board.

    `lane` is the column its dot sits in (the trunk is 0; a departure
    from a road already drawn takes the next free column); `parent`
    the row it follows (None for a first step); `count` how many
    voyages took it; `dithered` whether the clock ran out on any of
    them; `ends` the outcomes of the voyages that ended here, as
    [(kind, title)]; `latest` whether the most recent voyage took it."""

    __slots__ = ('span', 'lane', 'parent', 'count', 'dithered', 'ends', 'latest', 'depth')

    def __init__(self, span, lane, parent, depth):
        self.span, self.lane, self.parent, self.depth = span, lane, parent, depth
        self.count, self.dithered, self.ends, self.latest = 0, False, [], False


class _Twig:
    __slots__ = ('key', 'span', 'kids', 'count', 'dithered', 'ends', 'latest', 'order')

    def __init__(self, key, span, order):
        self.key, self.span, self.order = key, span, order
        self.kids, self.count, self.dithered, self.ends, self.latest = {}, 0, False, [], False


def chart(runs):
    """The roads of `runs` (records with a road) merged and laid out
    as rows, trunk first: at each board the beat most voyages took
    comes first and keeps its lane; the others follow it, each after
    the whole of the road it starts, on the next free lane. Returns
    (rows, lanes) — the rows in drawing order and how many lanes
    they use. Records without a road (kept before the chart was)
    are left out; count them yourself."""
    root = _Twig(None, '', 0)
    charted = [r for r in runs if r.get('road')]
    latest = charted[-1] if charted else None
    for order, run in enumerate(charted):
        twig = root
        road = run['road']
        for i, step in enumerate(road):
            key = (step.get('node'), tuple(step['beat'][0:1]), tuple(step['beat'][1]))
            kid = twig.kids.get(key)
            if kid is None:
                kid = twig.kids[key] = _Twig(key, step.get('span', ''), order)
            kid.count += 1
            kid.dithered = kid.dithered or bool(step.get('dithered'))
            if run is latest:
                kid.latest = True
            if i == len(road) - 1:
                kid.ends.append((run.get('kind', 'silence'), run.get('title', '')))
            twig = kid
    rows = []

    def lay(twig, lane, parent, depth):
        """Rows for twig's kids; returns the highest lane used."""
        top = lane
        kids = sorted(twig.kids.values(), key=lambda k: (-k.count, k.order))
        for j, kid in enumerate(kids):
            kid_lane = lane if j == 0 else top + 1
            row = Row(kid.span, kid_lane, parent, depth)
            row.count, row.dithered, row.ends, row.latest = \
                kid.count, kid.dithered, list(kid.ends), kid.latest
            rows.append(row)
            top = max(top, lay(kid, kid_lane, len(rows) - 1, depth + 1), kid_lane)
        return top

    lanes = lay(root, 0, None, 0) + 1 if root.kids else 0
    return rows, lanes
