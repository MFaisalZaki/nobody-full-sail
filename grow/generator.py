"""Growing a library with the scenario engine.

This is the half of the game that needs polyscene (and through it
clingo and the planner). The game itself never imports it: a library
already grown plays on pygame alone. Install the `grow` extra
(`pip install -e '.[grow]'`) to use it.

A library is grown one SEGMENT at a time. A segment is one grounding
of the world at one board (`grow.topic.WorldTopic(board=…)`), at the
engine's horizon: the seed telling from there, then — at every beat
of it — every alternative the engine admits (`ScenarioEngine.continuations`:
the prefix pinned, a different beat required, distinct by action class,
each alternative carrying its own best future), and menus of their own
for the alternatives taken early. The tellings are woven into one graph
(`polyscene.weave.graph`) and grafted onto the library at the board
they grew from. Every tail node is a place the next segment can grow
from, so a story-length graph is grown out of horizon-sized solves.

Which node grows next is a policy. `walk` plays the graph the way a
player would — a random walk from the opening, taking choices at
random — and grows the first ungrown node it reaches, so the graph is
richest where play actually goes; `depth` grows the shallowest ungrown
node first. `aim` is the backcast: every telling must close on the
terminal line carrying a named atom — the way the homecoming got in.
"""

import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED

from nobody.library import Library

# --- one segment, in a worker process ------------------------------------------

def grow_segment(world_root, board, close, horizon, choices, branch, budget,
                 tellings, quiet=True, aim=None):
    """Ground the world at `board` (None: its opening) and tell the
    segment: the seed, then the alternatives at beats 1..`branch`
    (`choices` ways at each), each with its own best future. Returns
    the tellings woven into a graph, as plain data:

        {'nodes': [{'board': [atoms], 'kids': [[name, [params], to]],
                    'fate': [[…]] | None, 'seg_depth': n}, …],
         'told': n, 'dry': bool, 'seconds': s}

    A plain function so a process pool can run it: clingo state is
    per process, and one grounding is one process's worth of memory."""
    import warnings
    from nobody import world as worlds
    from polyscene import beats, graph

    say = (lambda t: None) if quiet else \
        (lambda t: print(t, file=sys.stderr, flush=True))
    t0 = time.monotonic()
    world = worlds.load(world_root)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        engine = world.engine()(world.topic(board=board, close=close, aim=aim),
                                horizon=horizon)
        say(f'      grounded in {time.monotonic() - t0:.1f}s')
        seeds = engine.outcome(budget=budget, k=1)
        if not seeds:
            return {'nodes': [], 'told': 0, 'dry': bool(seeds.exhausted),
                    'seconds': time.monotonic() - t0}
        seed = seeds[0]
        told = [seed]
        say(f'      seed: {len(seed.plan.actions)} beats')
        asked = set()

        def alternatives(scenario, cut):
            """The other things to do at beat `cut` of `scenario`, up
            to the menu size, each with its own best future — asked
            once per prefix, and never past the telling cap."""
            road = beats(scenario)
            if len(road) < cut or len(told) >= tellings:
                return []
            prefix = road[:cut - 1]
            if prefix in asked:
                return []
            asked.add(prefix)
            have = len({r[cut - 1] for r in map(beats, told)
                        if r[:cut - 1] == prefix and len(r) >= cut})
            want = min(choices - have, tellings - len(told))
            if want <= 0:
                return []
            # alternatives that differ in KIND: three different
            # things to do, not three ports to sail for
            alts = list(engine.continuations(scenario, cut, budget=budget,
                                             k=want, distinct='schema'))
            told.extend(alts)
            say(f'      beat {cut}: +{len(alts)} alternative(s) '
                f'({len(told)} told)')
            return alts

        # the spine: a full menu at EVERY beat of the seed telling,
        # so the road the engine likes best is a road of decisions
        heads = []
        for cut in range(1, len(beats(seed)) + 1):
            for alt in alternatives(seed, cut):
                heads.append((alt, cut))
        # the head: alternatives taken in the first `branch` beats get
        # menus of their own for `branch` beats more, so the opening
        # of a segment is bushy however the player turns
        while heads:
            alt, cut = heads.pop(0)
            if cut >= branch * 2:
                continue
            for nxt in alternatives(alt, cut + 1):
                if cut + 1 < branch:
                    heads.append((nxt, cut + 1))
        nodes = graph(told)
        fates = {i: [list(a) for a in s.fate] for i, s in enumerate(told)
                 if s.fate}
        # depth within the segment, for marking the bushy head grown
        seg_depth = {0: 0}
        queue = [0]
        while queue:
            g = queue.pop(0)
            for c in nodes[g]['kids'].values():
                if c not in seg_depth:
                    seg_depth[c] = seg_depth[g] + 1
                    queue.append(c)
        out = []
        for g, node in enumerate(nodes):
            fate = next((fates[i] for i in node['told'] if i in fates), None)
            out.append({'board': sorted(a for a, v in node['board'] if v == 'true'),
                        'kids': [[name, list(params), c]
                                 for (name, params), c in sorted(node['kids'].items())],
                        'fate': fate, 'seg_depth': seg_depth.get(g, 0)})
        return {'nodes': out, 'told': len(told), 'dry': False,
                'seconds': time.monotonic() - t0}


# --- growing ----------------------------------------------------------------

class Generator:
    """Grow a library for a world with the scenario engine.

    `horizon`   beats per segment solve (the engine's window)
    `choices`   the menu size: alternatives wanted at each beat of a
                segment's seed telling (its spine)
    `branch`    how many beats deep the alternatives themselves get
                menus (the bushy head at the segment's opening)
    `budget`    seconds of solving per round
    `tellings`  cap on tellings per segment
    `segments`  cap on segments grown in one call (None: until every
                node is grown or the time is up)
    `seconds`   wall-clock cap for one call (None: none)
    `depth`     nodes at or beyond this depth are not grown further
    `close`     'auto' loads the terminal lines for a segment whose
                depth plus horizon reaches `close_from`, retrying open
                when the closed solve finds nothing; 'always' / 'never'
    `policy`    'walk' (random play-throughs pick the node) or 'depth'
    `aim`       an atom of a terminal line every telling must close on
                (a backcast: 'reunited' plants homecomings); with it,
                only nodes at `aim_from` or deeper are grown, closed
    `workers`   segments grown in parallel (processes)
    `say`       progress lines (a callable; stderr by default)
    `seed`      the random seed of the walk policy
    """

    def __init__(self, world, horizon=8, choices=3, branch=2, budget=60,
                 tellings=None, segments=None, seconds=None, depth=48,
                 close='auto', close_from=14, policy='walk', workers=1,
                 say=None, seed=None, aim=None, aim_from=0):
        self.world = world
        self.horizon = horizon
        self.choices = choices
        self.branch = branch
        self.budget = budget
        # the spine alone is (choices - 1) per beat of the seed; the
        # head adds its own — a generous cap that a segment rarely meets
        self.tellings = tellings or (1 + (choices - 1) * horizon
                                     + (choices - 1) ** 2 * max(0, branch))
        self.segments = segments
        self.seconds = seconds
        self.depth = depth
        self.close = close
        self.close_from = close_from
        self.policy = policy
        self.aim = aim
        self.aim_from = aim_from
        self.workers = max(1, workers)
        self.say = say or (lambda text: print(text, file=sys.stderr, flush=True))
        self.random = random.Random(seed)

    # --- the opening ------------------------------------------------------

    def open(self, library=None):
        """The library to grow: the given one, or a fresh one opened on
        the instance's own board."""
        if library is None:
            library = Library(self.world.name)
            library.meta = {'horizon': self.horizon, 'choices': self.choices,
                            'branch': self.branch, 'budget': self.budget,
                            'spread': list(self.world.spread),
                            'engine': self.world.engine_layer or 'default'}
        if not library.nodes:
            task = self.world.topic().ground()
            static = task.get_static_fluents()
            board = [str(e) for e, v in task.initial_values.items()
                     if e.fluent() not in static and v.is_true()]
            root = library.add(board, 0)
            self._mark(library, root)
        return library

    # --- choosing where to grow -------------------------------------------

    def pick(self, library, busy):
        """The next node to grow, by the policy — None when none is
        open."""
        candidates = [i for i in library.open_nodes(self.depth) if i not in busy
                      and i not in getattr(self, '_aimless', ())
                      and library.nodes[i].depth >= (self.aim_from if self.aim else 0)]
        if not candidates:
            return None
        if self.policy == 'depth':
            return min(candidates, key=lambda i: (library.nodes[i].depth, i))
        layer = self.world.layer
        for _ in range(64):
            at = 0
            for _ in range(self.depth + 1):
                node = library.nodes[at]
                if node.open and at not in busy and node.depth < self.depth \
                        and at not in getattr(self, '_aimless', ()) \
                        and node.depth >= (self.aim_from if self.aim else 0):
                    return at
                if not node.kids or node.fate:
                    break
                # play like a player: a hero's choice at random, the
                # world's beat where the world moves
                hero = [k for k in node.kids if layer.is_choice(k[0], k[1])]
                pool = hero or node.kids
                at = self.random.choice(pool)[2]
        # the walks kept landing on grown ground: fall back to depth
        return min(candidates, key=lambda i: (library.nodes[i].depth, i))

    def should_close(self, depth):
        if self.close == 'always' or self.aim:
            return True
        if self.close == 'never':
            return False
        return depth + self.horizon >= self.close_from

    # --- the loop ---------------------------------------------------------

    def grow(self, library=None, save=None):
        """Grow `library` until the caps say stop. `save` is a path
        written after every segment, so a long run can be watched and
        interrupted."""
        library = self.open(library)
        t_start = time.monotonic()
        grown, busy = 0, {}
        self._aimless = set()
        pool = ProcessPoolExecutor(max_workers=self.workers)

        def submit(at):
            node = library.nodes[at]
            close = self.should_close(node.depth)
            self.say(f'segment {grown + len(busy) + 1}: node {at} at depth '
                     f'{node.depth}' + (', closing' if close else ', open'))
            future = pool.submit(grow_segment, self.world.root,
                                 None if at == 0 else node.board, close,
                                 self.horizon, self.choices, self.branch,
                                 self.budget, self.tellings, True, self.aim)
            busy[future] = (at, close)

        def budget_left():
            if self.segments is not None and grown + len(busy) >= self.segments:
                return False
            if self.seconds is not None and time.monotonic() - t_start >= self.seconds:
                return False
            return True

        try:
            while True:
                while len(busy) < self.workers and budget_left():
                    at = self.pick(library, {a for a, _ in busy.values()})
                    if at is None:
                        break
                    submit(at)
                if not busy:
                    self.say('nothing left to grow' if budget_left()
                             else 'the cap is met')
                    break
                done, _ = wait(list(busy), return_when=FIRST_COMPLETED)
                for future in done:
                    at, close = busy.pop(future)
                    grown += 1
                    try:
                        result = future.result()
                    except Exception as e:      # a worker died: say so, go on
                        self.say(f'    node {at}: worker failed: {e!r}')
                        library.nodes[at].dry = True
                        continue
                    node = library.nodes[at]
                    if not result['nodes']:
                        if close and self.close == 'auto' and not self.aim:
                            # nothing closes from here inside the
                            # horizon: grow open story instead
                            self.say(f'    node {at}: nothing closes here '
                                     f'({result["seconds"]:.0f}s); retrying open')
                            future = pool.submit(
                                grow_segment, self.world.root,
                                None if at == 0 else node.board, False,
                                self.horizon, self.choices, self.branch,
                                self.budget, self.tellings)
                            busy[future] = (at, False)
                            continue
                        if self.aim:
                            # an aimed run must not leave the node dry
                            # for the ordinary walk: only note it
                            self.say(f'    node {at}: nothing reaches '
                                     f'{self.aim} from here ({result["seconds"]:.0f}s)')
                            self._aimless.add(at)
                            continue
                        node.dry = True
                        self.say(f'    node {at}: nothing to tell '
                                 f'({result["seconds"]:.0f}s)')
                        continue
                    added = self.stitch(library, at, result['nodes'])
                    self.say(f'    node {at}: {result["told"]} telling(s), '
                             f'+{added} node(s) in {result["seconds"]:.0f}s; '
                             f'{library.stats()}')
                    if save:
                        library.save(save)
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        return library

    # --- one node, on demand ----------------------------------------------

    def grow_at(self, library, at):
        """Grow node `at` now, in this process, grown or not — the
        way to plant a long road from a chosen board (an aimed
        backcast from the opening, say). Returns the nodes added."""
        library = self.open(library)
        node = library.nodes[at]
        result = grow_segment(self.world.root, None if at == 0 else node.board,
                              self.should_close(node.depth), self.horizon,
                              self.choices, self.branch, self.budget,
                              self.tellings, quiet=False, aim=self.aim)
        if not result['nodes']:
            self.say(f'    node {at}: nothing to tell ({result["seconds"]:.0f}s)')
            return 0
        added = self.stitch(library, at, result['nodes'])
        self.say(f'    node {at}: {result["told"]} telling(s), +{added} node(s) '
                 f'in {result["seconds"]:.0f}s; {library.stats()}')
        return added

    def start(self, library, at):
        """Begin growing node `at` in a worker process, for a caller
        that cannot wait (the game, at a road the library ran out
        on). Returns a future; hand it to `finish` when done."""
        node = library.nodes[at]
        close = self.should_close(node.depth)
        self._pool = getattr(self, '_pool', None) or ProcessPoolExecutor(max_workers=1)
        return self._pool.submit(grow_segment, self.world.root,
                                 None if at == 0 else node.board, close,
                                 self.horizon, self.choices, self.branch,
                                 self.budget, self.tellings)

    def finish(self, library, at, future):
        """Graft what `start`'s future grew onto `library` at `at`.
        Returns the number of nodes added (0 when nothing could be
        told there, and the node is marked dry)."""
        result = future.result()
        if not result['nodes']:
            library.nodes[at].dry = True
            return 0
        return self.stitch(library, at, result['nodes'])

    # --- stitching --------------------------------------------------------

    def stitch(self, library, at, nodes):
        """Graft a segment's graph onto the library at node `at`, whose
        board is the graph's root. Existing edges are followed, not
        duplicated; the bushy head is marked grown."""
        before = len(library)
        mapping = {0: at}
        library.nodes[at].grown = True

        def visit(g, l):
            gnode = nodes[g]
            lnode = library.nodes[l]
            if gnode['fate'] and lnode.fate is None:
                lnode.fate = gnode['fate']
            # a node with a full menu is grown; a lone tail node is
            # a place the next segment can grow from
            if gnode['seg_depth'] < self.branch or len(gnode['kids']) >= self.choices:
                lnode.grown = True
            for name, params, c in gnode['kids']:
                to = lnode.kid(name, params)
                if to is None:
                    to = library.add(nodes[c]['board'], lnode.depth + 1, parent=l)
                    lnode.kids.append((name, list(params), to))
                    self._mark(library, to)
                if c not in mapping:
                    mapping[c] = to
                    visit(c, to)

        visit(0, at)
        return len(library) - before

    def _mark(self, library, i):
        """A node standing on a terminal line is an ending whether or
        not a telling closed there."""
        node = library.nodes[i]
        if node.fate is None:
            closed = self.world.layer.closed(node.atoms())
            if closed:
                node.fate = [list(a) for a in closed[1]]
