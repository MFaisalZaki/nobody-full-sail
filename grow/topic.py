"""The engine side of a world pack: a polyscene Topic grounded at the
opening board, or at any board the library reached.

Kept out of `world.py` so that importing a pack costs nothing: this
module pulls in polyscene and unified_planning, which the game proper
never needs — a pre-generated library plays on pygame alone.
"""

import os

import clingo
from unified_planning.io import PDDLReader

import polyscene
from polyscene import Scenario, ScenarioEngine, Topic


def engine_class(layer=None):
    """The ScenarioEngine for an encodings generation: the package's
    default when `layer` is None, else a one-line subclass selecting
    `encodings-vN` (or `encodings` for the first) — the seam the
    engine's README names for choosing a layer."""
    if not layer:
        return ScenarioEngine
    path = os.path.join(os.path.dirname(polyscene.__file__), layer)
    if not os.path.isdir(path):
        raise ValueError(f'no such encodings layer: {layer}')
    return type(f'Engine_{layer.replace("-", "_")}', (ScenarioEngine,),
                {'ENCODINGS_DIR': path})


class BeatScenario(Scenario):
    """The engine's digest plus this game's one read of the model: the
    terminal line a telling closed on (the topic's shown
    fateClosed/2), as a list of atom tuples in the domain's own
    spelling — or None for a telling left open."""

    def __init__(self, task, plan, model, horizon=None, cost=None):
        super().__init__(task, plan, model, horizon=horizon, cost=cost)
        shown = next((s for s in self.shown if s.match('fateClosed', 2)), None)
        self.fate = None
        if shown is not None:
            back = lambda s: s.replace('_', '-')
            atoms = []
            for var in shown.arguments[0].arguments:
                v = var.arguments[0]
                if v.type == clingo.SymbolType.String:     # nullary fluent
                    atoms.append((back(v.string),))
                else:                                      # variable((name, constant(arg)…))
                    atoms.append((back(v.arguments[0].string),
                                  *(back(c.arguments[0].string)
                                    for c in v.arguments[1:])))
            self.fate = atoms


class WorldTopic(Topic):
    """A pack as the engine sees it."""

    scenario_class = BeatScenario
    fluent_predicates = ('tieFluent', 'ladderAxis')
    class_predicates = ('directedPos', 'deedAxis')
    # the two abstract members, given per instance below; class-level
    # defaults so the ABC lets the class instantiate
    domain = None
    encodings = ()

    def __init__(self, world, board=None, close=True, spread=(), aim=None):
        super().__init__(spread=spread)
        self.world = world
        self.name = world.name
        self.board = None if board is None else set(map(str, board))
        self.close = close
        #: an atom of a terminal line every telling must close on
        #: ('reunited': the homecoming) — needs `close`
        self.aim = aim
        self.domain = world.domain_path
        self.problem = world.instance_path
        files = list(world.rules) + (list(world.fates) if close else [])
        self.encodings = [world.path(f) for f in files]

    def ground(self):
        """The instance — the file's own opening, or the same task
        re-opened at `board`: every non-static atom false except the
        board's own. Static fluents keep the file's values: they are
        the world's furniture, and a board never moves it."""
        task = PDDLReader().parse_problem(self.domain, self.problem)
        if self.board is None:
            return task
        static = task.get_static_fluents()
        em = task.environment.expression_manager
        for expr in list(task.initial_values):
            if expr.fluent() in static:
                continue
            task.set_initial_value(
                expr, em.TRUE() if str(expr) in self.board else em.FALSE())
        return task

    def facts(self, task):
        """Nothing, unless the run aims at one ending: then a constraint
        in the check part that every telling close on the line whose
        atoms include `aim` — the backcast a homecoming needs, since
        the engine's own tiers will not walk twenty beats to reach one
        on their own."""
        if not self.aim or not self.close:
            return ''
        atom = self.aim.replace('-', '_')
        return ('#program base.\n'
                f'aimed(F) :- fateNeed(F, variable(@q("{atom}"))).\n'
                '#program check(t).\n'
                ':- query(t), aimed(F), not fateClosed(F, t).\n')
