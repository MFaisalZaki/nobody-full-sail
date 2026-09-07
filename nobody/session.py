"""One game: a walk through the library under the rules of survival.

The rules are the ones the game it apes plays by. Four factions hold
your fate, each a meter; a crisis lands, you have seconds to pick one
of a few answers; every answer moves the meters, and the world reacts
in print. Let a fatal faction hit its floor and it is over. Reach a
terminal line of the world and the story closes on its own ending.

What differs is where the crises come from: not a hand-written deck
but the story graph the scenario engine grew. A crisis is a node of
the graph; its options are the hero's own beats out of that node,
each the first beat of a whole admissible future; the world's beats
out of a node are what happens when nobody decides. The meters are
the PDDL's own `@meter` costs, summed along the path — which is why
the same board reached two ways can stand at different numbers, as it
should.
"""

import random

from . import press


class Option:
    """One answer to a crisis."""

    def __init__(self, label, beat, to, kind='choice'):
        self.label = label
        self.beat = beat            # (name, [params]) — None for 'wait'
        self.to = to                # the node it leads to
        self.kind = kind            # 'choice' | 'wait'

    def __repr__(self):
        return f'<Option {self.kind}: {self.label}>'


class Crisis:
    def __init__(self, node, title, context, options):
        self.node = node
        self.title = title
        self.context = context
        self.options = options


class Epilogue:
    def __init__(self, kind, title, text, score):
        self.kind = kind            # 'ending' | 'lost' | 'silence'
        self.title = title
        self.text = text
        self.score = score          # {'crises', 'years', 'benchmark'}


class Session:

    #: what every faction loses when the clock runs out on a decision
    DITHER = 5

    def __init__(self, world, library, seed=None):
        self.world = world
        self.library = library
        self.layer = world.layer
        self.random = random.Random(seed)
        bars = self.layer.meter_bars
        self.meters = {m: bars[m][2] for m in bars}
        self.at = 0
        self.opening = library.nodes[0].atoms()
        self.crises = 0             # decisions taken
        self.history = []           # [(beat, deltas, node)] every beat played
        self.pages = []             # the newspaper, issue by issue
        self.over = False
        self.outcome = None
        self.cause = None           # the faction that ended it, if one did
        self._page = None
        # the opening may itself be the world's move
        self._settle(asides=[])

    # --- reading the state ------------------------------------------------

    @property
    def node(self):
        return self.library.nodes[self.at]

    @property
    def atoms(self):
        return self.node.atoms()

    def meter(self, name):
        return self.meters.get(name, 0)

    @property
    def clock(self):
        return self.meters.get(self.world.clock, 0)

    def clock_text(self):
        return f'{self.world.clock_label} {self.clock}'

    def intro(self):
        return self.world.describe(self.atoms, self.opening)

    def bar(self, meter):
        """(value, lo, hi) for a meter."""
        lo, hi, _ = self.layer.meter_bars.get(meter, (0, 100, 0))
        return self.meters.get(meter, 0), lo, hi

    # --- the crisis -------------------------------------------------------

    def options(self, node=None):
        node = self.node if node is None else node
        layer = self.layer
        hero, world = [], []
        for name, params, to in node.kids:
            (hero if layer.is_choice(name, params) else world).append(
                (name, list(params), to))
        options = []
        labels = [self.world.label(n, p) for n, p, _ in hero]
        for (name, params, to), label in zip(hero, labels):
            if labels.count(label) > 1:
                # twins — the first argument that differs joins the label
                twins = [p for (n, p, _), l in zip(hero, labels)
                         if l == label and n == name]
                at = next((i for i in range(len(params))
                           if len({t[i] for t in twins if i < len(t)}) > 1), None)
                if at is not None:
                    label = f'{label} — {layer.display(params[at])}'
            options.append(Option(label, (name, params), to))
        if world and hero:
            options.append(Option(self.world.wait_label(), None, None, 'wait'))
        return options, world

    def crisis(self):
        """The crisis at the current node: its title (the episode the
        options belong to), the board as the player reads it, and the
        options. None when the game is over."""
        if self.over:
            return None
        options, world = self.options()
        tags = []
        for o in options:
            if o.beat:
                tags += self.layer.schema(o.beat[0]).tags
        for name, params, _ in world:
            tags += self.layer.schema(name).tags
        title = self.world.episode(self._ranked(tags))
        return Crisis(self.at, title,
                      self.world.describe(self.atoms, self.opening), options)

    @staticmethod
    def _ranked(tags):
        seen, out = {}, []
        for t in tags:
            seen[t] = seen.get(t, 0) + 1
        for t in sorted(seen, key=lambda t: -seen[t]):
            out.append(t)
        return out

    # --- playing ----------------------------------------------------------

    def choose(self, index):
        """Answer the crisis with option `index`. Returns the page."""
        assert not self.over, 'the game is over'
        options, world = self.options()
        option = options[index]
        self.crises += 1
        if option.kind == 'wait':
            # the world's own beat leads the page: it is what happened
            name, params, to = self.random.choice(world)
            beat = (name, params)
        else:
            beat, to = option.beat, option.to
        deltas = self._apply(beat, to)
        self.at = to
        self._asides = []
        self._settle(asides=self._asides)
        page = press.compose(self.world, self._dateline(beat), beat, deltas,
                             asides=self._asides)
        self.pages.append(page)
        self._page = page
        self._judge()
        return page

    def timeout(self):
        """The clock ran out: every faction loses a little, and the
        world decides — its own beat if it has one, else one of the
        hero's, at random."""
        assert not self.over, 'the game is over'
        options, world = self.options()
        self.crises += 1
        penalty = {}
        for f in self.world.factions:
            lo, hi, _ = self.layer.meter_bars.get(f.meter, (0, 100, 0))
            before = self.meters.get(f.meter, 0)
            self.meters[f.meter] = max(lo, before - self.DITHER)
            penalty[f.meter] = self.meters[f.meter] - before
        if world:
            name, params, to = self.random.choice(world)
        else:
            picked = self.random.choice([o for o in options if o.beat])
            (name, params), to = picked.beat, picked.to
        deltas = self._apply((name, params), to)
        for m, d in deltas.items():
            penalty[m] = penalty.get(m, 0) + d
        self.at = to
        self._asides = []
        self._settle(asides=self._asides)
        page = press.compose(self.world, self._dateline((name, params)),
                             (name, params), penalty, asides=self._asides,
                             dithered=True)
        page.standfirst = (page.standfirst + ' ' if page.standfirst else '') \
            + self.layer.tell(name, params)
        self.pages.append(page)
        self._page = page
        self._judge()
        return page

    # --- the machinery ----------------------------------------------------

    def _dateline(self, beat):
        return f'{self.clock_text()} · ' + \
            self.world.episode(self.layer.schema(beat[0]).tags)

    def _apply(self, beat, to=None):
        """Move the meters by a beat's `@meter` costs, clamped to the
        bars; returns the actual deltas.

        A meter the world keeps as a LADDER (`@ladder`) is also
        snapped to its rung whenever the rung changes between the
        board left and the board `to` reached: the number is a
        display of the world's own state, and when the world says
        the hall is lost the number says zero."""
        name, params = beat
        schema = self.layer.schema(name)
        deltas = {}
        for meter, delta in schema.meter.items():
            lo, hi, _ = self.layer.meter_bars.get(meter, (0, 10 ** 9, 0))
            before = self.meters.get(meter, 0)
            after = max(lo, min(hi, before + delta))
            self.meters[meter] = after
            deltas[meter] = after - before
        if to is not None:
            here = self.rungs(self.node.atoms())
            there = self.rungs(self.library.nodes[to].atoms())
            for meter, rung in there.items():
                if rung != here.get(meter) and rung is not None:
                    before = self.meters.get(meter, 0) - deltas.get(meter, 0)
                    self.meters[meter] = rung
                    deltas[meter] = rung - before
        self.history.append((beat, deltas, self.at))
        return deltas

    def rungs(self, atoms):
        """{meter: the value its ladder's rung stands for} on a board."""
        out = {}
        for meter, ladder in self.layer.ladders.items():
            fluent, rungs = ladder['fluent'], ladder['rungs']
            rung = next((a[1] for a in atoms if a[0] == fluent and len(a) == 2), None)
            out[meter] = rungs.get(rung) if rung is not None else None
        return out

    _asides = ()

    def _settle(self, asides):
        """Play the world's own beats until a node with a decision on
        it, an ending, or a leaf; collects them into `asides`. Returns
        None (the page is composed by the caller)."""
        self._asides = asides
        while not self.over:
            node = self.node
            if node.fate:
                break
            options, world = self.options(node)
            if any(o.beat for o in options):
                break
            if not world:
                break
            name, params, to = self.random.choice(world)
            deltas = self._apply((name, params), to)
            asides.append(((name, params), deltas))
            self.at = to
        return None

    def _judge(self):
        """Is it over? A fatal floor first (the paper reports the
        beat, then the consequence), then a terminal line, then a
        leaf the library never grew past."""
        if self.over:
            return
        for f in self.world.factions:
            lo, _, _ = self.layer.meter_bars.get(f.meter, (0, 100, 0))
            if f.fatal and self.meters.get(f.meter, 0) <= lo:
                self.over, self.cause = True, f
                self.outcome = Epilogue('lost', f'{f.label}: lost',
                                        f.floor_text, self.score())
                return
        node = self.node
        if node.fate:
            title = self.layer.ending([tuple(a) for a in node.fate])
            kind = 'ending'
            closed = self.layer.closed(node.atoms())
            if closed and closed[0] == 'fail':
                kind = 'lost'
            self.over = True
            self.outcome = Epilogue(kind, title, self.world.ending_text(
                node.fate, kind), self.score())
            return
        if not node.kids:
            self.over = True
            self.outcome = Epilogue('silence', 'The bards fall silent',
                                    self.world.silence_text(), self.score())

    @property
    def silent(self):
        """Over only because the library ran out here — the one kind
        of end that growing the library can undo."""
        return self.over and self.outcome is not None \
            and self.outcome.kind == 'silence'

    def revive(self):
        """The library has grown under the current node: judge again.
        Returns True when the story goes on."""
        if not self.silent:
            return not self.over
        self.over, self.outcome = False, None
        self._settle(asides=self._asides if self._asides else [])
        self._judge()
        return not self.over

    def score(self):
        return {'crises': self.crises, 'years': self.clock,
                'beats': len(self.history),
                'benchmark': self.world.benchmark}

    def epilogue(self):
        return self.outcome

    # --- the log ----------------------------------------------------------

    def log(self):
        """Every issue of the paper so far, oldest first."""
        return list(self.pages)
