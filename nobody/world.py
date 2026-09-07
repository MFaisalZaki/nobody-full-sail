"""A world pack: the files the engine needs, the game layer the PDDL
carries, and the voice the game speaks in.

Nobody plays any world the polyscene engine can tell stories about, provided
the world's PDDL carries the `;; @` game layer (see `directives.py`).
A pack is a directory:

    world.py            the pack — a `World` subclass, exported as WORLD
    <domain>.pddl       the world model, with the game layer in comments
    <instance>.pddl     the opening board, with the @done / @fail lines
    *.lp                the topic's rules and tables for the engine
    library.json        (generated) the story graph the game plays

The engine side of a pack — the `Topic` the grower builds, grounded
at the opening board or at ANY board of the library — lives in
`grow/`, imported lazily and only there, so the game itself never
needs the engine: a library already grown plays on pygame alone.
"""

import importlib.util
import os
from dataclasses import dataclass, field

from . import directives


@dataclass
class Scene:
    """What a board looks like, for the UI to draw — data, so that a
    pack needs no pygame. A stage (`setting`), a landmark on it, a
    cast of residents each with its props, the crew's band, the
    vessel if any, the hero's state, the residue marks a sprite may
    react to, and the board's reading as a caption."""
    place: str = ''
    setting: str = 'shore'          # 'shore' | 'sea' | 'harbour' | 'cave' | 'hall' | 'underworld'
    landmark: tuple = None          # (sprite, props)
    cast: list = field(default_factory=list)      # [(sprite, props), …]
    crew: str = 'full'              # 'full' | 'thinned' | 'remnant' | 'alone'
    vessel: str = 'ship'            # 'ship' | 'raft' | 'wreck' | None
    hero: dict = field(default_factory=dict)      # 'inside', 'bound', 'kept', 'disguised', 'below', 'facing', 'pose'
    marks: set = field(default_factory=set)
    caption: str = ''


class Faction:
    """One of the four meters the game is played against — the thing
    the world's `@meter` deltas move and the thing that ends the game
    at its floor."""

    def __init__(self, meter, label, blurb='', fatal=True, icon=None,
                 floor_text='', ceiling_text='', short=None):
        self.meter = meter          # the @meter / @meter-bar name
        self.label = label          # how the game names it
        self.short = short or label.replace('The ', '')   # on a small tile
        self.blurb = blurb          # the one-line joke under the label
        self.fatal = fatal          # does hitting the floor end the game
        self.icon = icon or meter   # which glyph the UI draws
        self.floor_text = floor_text
        self.ceiling_text = ceiling_text


class World:
    """The base pack. A subclass names its files and its factions, and
    overrides the prose hooks it wants a better voice for."""

    #: the pack's short name (its directory name by convention)
    name = 'world'
    #: what the game calls itself when playing this world
    title = 'Nobody'
    subtitle = 'a game of survival'
    #: the domain and instance files, relative to the pack directory
    domain = 'domain.pddl'
    instance = 'instance.pddl'
    #: the topic's own .lp files, in load order
    rules = ()
    #: the .lp file(s) holding the terminal lines as fateNeed/2 facts —
    #: loaded when the generator wants tellings that CLOSE, left out
    #: for open stretches of story
    fates = ()
    #: the meter that is the clock, and how it reads
    clock = 'years'
    clock_label = 'Year'
    #: the four factions, in display order (the meters must exist as
    #: @meter-bar rows in the domain)
    factions = ()
    #: feature axes the generator spreads on (must be axes the topic's
    #: program declares — featureAxis/1)
    spread = ()
    #: the engine's encodings generation this world solves under
    #: (None: the package default; 'encodings-v3', …: that layer)
    engine_layer = None
    #: how many seconds the player gets per decision
    timer = 45
    #: the newspaper's masthead and tagline
    masthead = 'THE DAILY RECKONING'
    tagline = ''
    #: the benchmark the score is read against, if the world has one
    benchmark = None
    #: the meter the sky is read from (its floor is a storm), if any
    sky = None

    def __init__(self, root):
        self.root = root
        self._layer = None

    # --- files ------------------------------------------------------------

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    @property
    def domain_path(self):
        return self.path(self.domain)

    @property
    def instance_path(self):
        return self.path(self.instance)

    @property
    def library_path(self):
        return self.path('library.json')

    # --- the game layer ---------------------------------------------------

    @property
    def layer(self):
        if self._layer is None:
            self._layer = directives.parse(self.domain_path, self.instance_path)
        return self._layer

    def faction(self, meter):
        return next((f for f in self.factions if f.meter == meter), None)

    # --- the voice: hooks a pack overrides --------------------------------

    def describe(self, atoms, opening=()):
        """The player's context on a board: `atoms` is the set of TRUE
        ground atoms as tuples. The base reading uses the game layer's
        own tables (`@place`, `@where`, `@reads`); a pack adds what
        only it knows. `opening` is the board the story opened on: a
        mark that was already there is furniture, not residue, and is
        not read."""
        layer = self.layer
        opening = set(opening)
        lines = []
        hero = layer.hero
        if layer.place and hero:
            fluent, idx = layer.place          # the place is the idx-th argument
            place = next((a[idx + 1] for a in atoms
                          if a[0] == fluent and len(a) > idx + 1
                          and a[1] == hero), None)
            if place:
                head = layer.display(place)
                lines.append(head[0].upper() + head[1:] + '.'
                             + (' ' + layer.where[place]
                                if place in layer.where else ''))
        for name in sorted(layer.reads):
            for a in sorted(x for x in atoms if x[0] == name and x not in opening):
                text = layer.reads[name].format(*map(layer.display, a[1:]))
                lines.append(text[0].upper() + text[1:] + '.')
        return '\n'.join(lines)

    def scene(self, atoms, opening=()):
        """What the board looks like: the base reading places the hero
        on a shore with the ship; a pack knows its own islands."""
        layer = self.layer
        place = None
        if layer.place and layer.hero:
            fluent, idx = layer.place          # the place is the idx-th argument
            place = next((a[idx + 1] for a in atoms
                          if a[0] == fluent and len(a) > idx + 1 and a[1] == layer.hero), None)
        return Scene(place=place or '', caption=self.describe(atoms, opening))

    def episode(self, tags):
        """The crisis title for a beat with these tags: the first tag
        the `@episode` table names."""
        for tag in tags:
            if tag in self.layer.episodes:
                return self.layer.episodes[tag]
        return ''

    def headline(self, name, values):
        """The newspaper's headline for a beat: the `@span` line, shouted."""
        return self.layer.span(name, values).rstrip('.').upper()

    def reaction(self, faction, delta, name, values):
        """What a faction says about a beat that moved its meter by
        `delta` (never zero)."""
        if delta > 0:
            return f'{faction.label} approve.'
        return f'{faction.label} are not pleased.'

    def aside(self, name, values):
        """A world beat's one-line report in the newspaper's margin."""
        return self.layer.span(name, values)

    def label(self, name, values):
        """An answer's label: the schema's `@gloss`, unless the pack
        has a fuller one (a sailing wants its port)."""
        return self.layer.gloss(name, values)

    def wait_label(self):
        """The option of doing nothing, where the world has a move."""
        return 'Do nothing. See what happens.'

    def dithered_headline(self):
        return 'NOTHING DECIDED; EVERYONE NOTICES'

    def dithered_standfirst(self):
        return 'The clock ran out and the world moved without you.'

    def ending_text(self, fate, kind):
        """The closing paragraph for a terminal line."""
        return ''

    def silence_text(self):
        """When the library has no more of this story."""
        return ('The library holds no more of this road. Grow it further '
                'with `generate`, or take another.')

    # --- the engine side --------------------------------------------------

    def topic(self, board=None, close=True, spread=None, aim=None):
        """The polyscene Topic for this world, grounded at `board` (a
        list of true-atom strings, or None for the instance's own
        opening) — with the terminal lines loaded when `close` is
        true, and every telling made to close on the line carrying
        the atom `aim` when one is named. Imports polyscene and
        unified_planning on demand: the game never needs them, the
        generator does."""
        from grow.topic import WorldTopic
        return WorldTopic(self, board=board, close=close,
                          spread=self.spread if spread is None else spread,
                          aim=aim)

    def engine(self):
        """The ScenarioEngine class this world solves under."""
        from grow.topic import engine_class
        return engine_class(self.engine_layer)


def load(root):
    """The pack at `root`: its `world.py` exports WORLD, a World
    subclass bound to that directory."""
    root = os.path.abspath(root)
    spec = importlib.util.spec_from_file_location(
        f'nobody_world_{os.path.basename(root)}', os.path.join(root, 'world.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cls = getattr(module, 'WORLD')
    return cls(root)
