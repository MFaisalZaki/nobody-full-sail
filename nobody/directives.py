"""The game layer of a PDDL world, read off its `;; @` directives.

A polyscene world keeps everything the planner needs in PDDL proper and
everything a GAME needs in comment directives beside the schema they
belong to — `@gloss` (the choice label), `@tell` (the passage), `@span`
(what it will have been, in one line), `@meter` (what it costs, per
meter), `@tag`, `@kind`, `@intensity`, `@directed`, `@foreknown` — plus
a header of world-level directives: `@meter-bar`, `@ladder`, `@ending`,
`@name`, `@where`, `@reads`, `@episode`, `@hero`, and the instance's
`@done` / `@fail` terminal lines.

The topics that author those directives read them with no code at all
(their narration classes restate the prose in Python). This module is
the first reader: it turns the directives into plain data, so a game
can play any world written that way without a line of world-specific
code — and so the prose lives in ONE place, beside the schema.

Nothing here parses PDDL semantics. Parameters are read off the
`:parameters` line for their names and order only, which is what a
`{?who}` placeholder in a template needs.
"""

import re
from dataclasses import dataclass, field

_DIRECTIVE = re.compile(r'^\s*;;\s*(?:\[deferred\]\s*)?@([A-Za-z][\w-]*)\s*(.*?)\s*$')
_ACTION = re.compile(r'\(:action\s+([\w-]+)')
_PARAMS = re.compile(r':parameters\s*\((.*?)\)', re.S)
_METER = re.compile(r'([A-Za-z][\w-]*)([+-]\d+)')
_ATOM = re.compile(r'\(([^()]*)\)')

#: directives that describe the schema they precede, not the world
SCHEMA_KEYS = frozenset({
    'gloss', 'tell', 'span', 'meter', 'tag', 'kind', 'intensity', 'sign',
    'directed', 'observe', 'foreknown'})


@dataclass
class Schema:
    """One action schema's game layer."""
    name: str
    params: list = field(default_factory=list)
    gloss: str = ''
    tell: str = ''
    span: str = ''
    meter: dict = field(default_factory=dict)     # {meter: delta}
    tags: list = field(default_factory=list)
    kind: str = None                              # 'event', 'investigate', …
    intensity: int = None
    sign: str = None
    directed: tuple = None                        # (actor param, target param)
    observe: str = None
    foreknown: str = None                         # the episode that unlocks it

    @property
    def is_event(self):
        """The world's own beat: nobody's act, never an offer."""
        return self.kind == 'event'

    @property
    def is_offer(self):
        """A beat the player may choose. The authoring convention: an
        event is never an offer, and a parenthesised gloss marks a
        beat that reads as the world's even when it is typed as an
        act ("(they open the bag)")."""
        return not self.is_event and not self.gloss.startswith('(')

    def actor_param(self):
        """The parameter that names whose act this is: the `@directed`
        actor, else the first parameter."""
        if self.directed:
            return self.directed[0]
        return self.params[0] if self.params else None

    def bind(self, values):
        """{param name without '?': value} for one ground beat."""
        return {p.lstrip('?'): v for p, v in zip(self.params, values)}

    def fill(self, text, values, display=str):
        """A template with every `{?param}` replaced by the bound
        value's display form."""
        bound = self.bind(values)
        return re.sub(r'\{\?([\w-]+)\}',
                      lambda m: display(bound.get(m.group(1), '?')), text)


@dataclass
class GameLayer:
    """A world's game layer: the header directives and every schema's."""
    title: str = ''
    notes: list = field(default_factory=list)
    hero: str = None
    ties: list = field(default_factory=list)
    wants: list = field(default_factory=list)         # (fluent words, weight)
    visible: list = field(default_factory=list)
    episodes: dict = field(default_factory=dict)      # tag -> title
    meter_bars: dict = field(default_factory=dict)    # name -> (lo, hi, start)
    ladders: dict = field(default_factory=dict)       # name -> {'fluent', 'rungs'}
    endings: dict = field(default_factory=dict)       # atom -> how it reads
    names: dict = field(default_factory=dict)         # word -> display form
    where: dict = field(default_factory=dict)         # place -> line
    reads: dict = field(default_factory=dict)         # fluent -> template
    place: tuple = None                               # (fluent, arg index)
    done: list = field(default_factory=list)          # [[atom tuple, …], …]
    fail: list = field(default_factory=list)
    schemas: dict = field(default_factory=dict)       # name -> Schema
    other: dict = field(default_factory=dict)         # anything else, kept

    # --- reading -----------------------------------------------------------

    def display(self, word):
        """A world name in prose: its `@name`, or itself capitalised."""
        word = str(word)
        if word in self.names:
            return self.names[word]
        return ' '.join(w.capitalize() for w in re.split(r'[-_]', word))

    def schema(self, name):
        return self.schemas.get(name) or Schema(name)

    def gloss(self, name, values):
        s = self.schema(name)
        if not s.gloss:
            return ' '.join(self.display(w) for w in (name, *values))
        return s.fill(s.gloss, values, self.display)

    def tell(self, name, values):
        s = self.schema(name)
        if not s.tell:
            return ' '.join(self.display(w) for w in (name, *values))
        return s.fill(s.tell, values, self.display)

    def span(self, name, values):
        s = self.schema(name)
        if not s.span:
            return self.tell(name, values)
        return s.fill(s.span, values, self.display)

    def actor(self, name, values):
        """Who acted a ground beat (None for an event)."""
        s = self.schema(name)
        if s.is_event:
            return None
        p = s.actor_param()
        return s.bind(values).get(p.lstrip('?')) if p else None

    def is_choice(self, name, values):
        """Whether a ground beat is the hero's own offer."""
        s = self.schema(name)
        return s.is_offer and (self.hero is None
                               or self.actor(name, values) == self.hero)

    def fates(self):
        """Every terminal line, done first: [(kind, [atom tuple, …])]."""
        return ([('done', line) for line in self.done]
                + [('fail', line) for line in self.fail])

    def closed(self, atoms):
        """The first terminal line every atom of which is in `atoms`
        (a set of atom tuples), as (kind, line) — or None."""
        for kind, line in self.fates():
            if all(a in atoms for a in line):
                return kind, line
        return None

    def ending(self, line):
        """How a closed line reads: the `@ending` of its LAST atom that
        has one — a line lists the general before the specific
        (`(home) (reunited)`), and the specific reading is the one
        that names the line — else the atoms' own words."""
        for atom in reversed(list(line)):
            if atom[0] in self.endings:
                return self.endings[atom[0]]
        return ' '.join(self.display(w) for a in line for w in a)


def parse_atoms(text):
    """`(home) (ithaca-hold lost)` → [('home',), ('ithaca-hold', 'lost')]."""
    return [tuple(m.group(1).split()) for m in _ATOM.finditer(text)]


def _split_kv(text):
    """`alone=0 remnant=20` → {'alone': '0', 'remnant': '20'} in order."""
    out = {}
    for tok in text.split():
        if '=' in tok:
            k, v = tok.split('=', 1)
            out[k] = v
    return out


def parse(*paths):
    """The game layer of the files at `paths` (a domain and, usually,
    its instance), read in order."""
    layer = GameLayer()
    for path in paths:
        with open(path, encoding='utf-8') as f:
            _read(layer, f.read())
    return layer


def _read(layer, text):
    pending = {}     # schema directives waiting for their (:action
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = _DIRECTIVE.match(line)
        if m:
            key, value = m.group(1), m.group(2)
            if key in SCHEMA_KEYS:
                pending.setdefault(key, []).append(value)
            else:
                _header(layer, key, value)
            continue
        a = _ACTION.search(line)
        if a and not line.lstrip().startswith(';'):
            name = a.group(1)
            # the parameter list may sit on the next line(s)
            block = '\n'.join(lines[i:i + 6])
            p = _PARAMS.search(block)
            params = ([t for t in p.group(1).split() if t.startswith('?')]
                      if p else [])
            layer.schemas[name] = _schema(name, params, pending)
            pending = {}


def _schema(name, params, pending):
    s = Schema(name, params)
    s.gloss = ' '.join(pending.get('gloss', [])).strip()
    s.tell = ' '.join(pending.get('tell', [])).strip()
    s.span = ' '.join(pending.get('span', [])).strip()
    for text in pending.get('meter', []):
        for meter, delta in _METER.findall(text):
            s.meter[meter] = s.meter.get(meter, 0) + int(delta)
    for text in pending.get('tag', []):
        s.tags += text.split()
    if 'kind' in pending:
        s.kind = pending['kind'][-1].strip() or None
    if 'intensity' in pending:
        s.intensity = int(pending['intensity'][-1])
    if 'sign' in pending:
        s.sign = pending['sign'][-1].strip() or None
    if 'directed' in pending:
        parts = pending['directed'][-1].split()
        s.directed = tuple(parts[:2]) if len(parts) >= 2 else None
    if 'observe' in pending:
        s.observe = pending['observe'][-1].strip() or None
    if 'foreknown' in pending:
        s.foreknown = pending['foreknown'][-1].strip() or None
    return s


def _header(layer, key, value):
    words = value.split()
    if key == 'title':
        layer.title = value
    elif key == 'note':
        layer.notes.append(value)
    elif key == 'hero':
        layer.hero = words[0] if words else None
    elif key == 'ties':
        layer.ties += words
    elif key == 'wants':
        if words:
            try:
                weight = int(words[-1])
                layer.wants.append((tuple(words[:-1]), weight))
            except ValueError:
                layer.wants.append((tuple(words), 0))
    elif key == 'visible':
        layer.visible += words
    elif key == 'episode':
        if words:
            layer.episodes[words[0]] = ' '.join(words[1:])
    elif key == 'meter-bar':
        if len(words) >= 4:
            layer.meter_bars[words[0]] = (int(words[1]), int(words[2]),
                                          int(words[3]))
    elif key == 'ladder':
        if words:
            kv = _split_kv(' '.join(words[1:]))
            fluent = kv.pop('on', words[0])
            layer.ladders[words[0]] = {
                'fluent': fluent,
                'rungs': {k: int(v) for k, v in kv.items()}}
    elif key == 'ending':
        if words:
            layer.endings[words[0]] = ' '.join(words[1:])
    elif key == 'name':
        if words:
            layer.names[words[0]] = ' '.join(words[1:])
    elif key == 'where':
        if words:
            layer.where[words[0]] = ' '.join(words[1:])
    elif key == 'reads':
        if words:
            layer.reads[words[0]] = ' '.join(words[1:])
    elif key == 'place':
        if len(words) >= 2:
            layer.place = (words[0], int(words[1]))
    elif key == 'done':
        layer.done.append(parse_atoms(value))
    elif key == 'fail':
        layer.fail.append(parse_atoms(value))
    else:
        layer.other.setdefault(key, []).append(value)
