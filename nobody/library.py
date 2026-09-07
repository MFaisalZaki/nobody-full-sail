"""The library: the story graph the game plays.

A library is a graph of BOARDS joined by BEATS. Every node is a state
of the world (its true atoms); every edge is one ground beat the
scenario engine told from that state, and where it leads. The player
walks the graph: at a node the hero's own beats are the choices, the
world's beats are what happens, and a node on a terminal line is an
ending.

The file format is plain JSON, so the game needs neither the engine
nor a planner to play. Boards are stored as deltas from a parent (a
board is sixty atoms; a beat changes three), node 0 whole. How a
library is GROWN — the engine, re-grounded at any board of it — lives
in `grow/`, which the game never imports.
"""

import json
import os
import re

_ATOM = re.compile(r'^([\w-]+)(?:\((.*)\))?$')


def atom_tuple(text):
    """`at(odysseus, troy)` → ('at', 'odysseus', 'troy'); `home` → ('home',)."""
    m = _ATOM.match(text.strip())
    if not m:
        return (text.strip(),)
    name, args = m.group(1), m.group(2)
    if not args:
        return (name,)
    return (name, *[a.strip() for a in args.split(',')])


class Node:
    __slots__ = ('board', 'kids', 'fate', 'depth', 'grown', 'dry', 'parent')

    def __init__(self, board, depth=0, parent=None):
        self.board = sorted(board)    # true atoms, as strings
        self.kids = []                # [(schema, [params], to)]
        self.fate = None              # [[atom words], …] when terminal
        self.depth = depth
        self.grown = False            # a segment grew its alternatives here
        self.dry = False              # a segment found nothing to tell here
        self.parent = parent          # the node that first led here

    def atoms(self):
        return {atom_tuple(a) for a in self.board}

    def kid(self, name, params):
        for n, p, to in self.kids:
            if n == name and list(p) == list(params):
                return to
        return None

    @property
    def open(self):
        """Can a segment still grow here?"""
        return not self.grown and not self.dry and self.fate is None


class Library:

    def __init__(self, world_name, nodes=None, meta=None):
        self.world = world_name
        self.nodes = list(nodes or [])
        self.meta = dict(meta or {})

    # --- shape ------------------------------------------------------------

    def __len__(self):
        return len(self.nodes)

    def add(self, board, depth, parent=None):
        self.nodes.append(Node(board, depth, parent))
        return len(self.nodes) - 1

    def open_nodes(self, max_depth=None):
        return [i for i, n in enumerate(self.nodes)
                if n.open and (max_depth is None or n.depth < max_depth)]

    def reach(self, at):
        """What lies beyond node `at`: (roads, endings, beats) — how
        many roads run on from it (its leaves), how many of them close
        on an ending, and how many beats the longest of them runs.
        The library is a tree, so this is one walk; results are kept."""
        cache = self.__dict__.setdefault('_reach', {})
        if at in cache:
            return cache[at]
        stack, order = [at], []
        while stack:
            i = stack.pop()
            order.append(i)
            stack.extend(to for _, _, to in self.nodes[i].kids if to not in cache)
        for i in reversed(order):
            node = self.nodes[i]
            if not node.kids:
                cache[i] = (1, 1 if node.fate else 0, 0)
                continue
            roads = endings = beats = 0
            for _, _, to in node.kids:
                r, e, b = cache[to]
                roads, endings, beats = roads + r, endings + e, max(beats, b + 1)
            cache[i] = (roads, endings, beats)
        return cache[at]

    def stats(self):
        """A few numbers about the graph."""
        edges = sum(len(n.kids) for n in self.nodes)
        forks = sum(1 for n in self.nodes if len(n.kids) > 1)
        endings = sum(1 for n in self.nodes if n.fate)
        deepest = max((n.depth for n in self.nodes), default=0)
        return {'nodes': len(self.nodes), 'edges': edges, 'forks': forks,
                'endings': endings, 'grown': sum(1 for n in self.nodes if n.grown),
                'open': len(self.open_nodes()),
                'dry': sum(1 for n in self.nodes if n.dry),
                'deepest': deepest}

    # --- the file ---------------------------------------------------------

    def save(self, path):
        out = []
        for i, n in enumerate(self.nodes):
            d = {'kids': [[name, list(p), to] for name, p, to in n.kids],
                 'depth': n.depth}
            if n.parent is None or i == 0:
                d['board'] = n.board
            else:
                base = set(self.nodes[n.parent].board)
                here = set(n.board)
                d['parent'] = n.parent
                d['add'] = sorted(here - base)
                d['del'] = sorted(base - here)
            if n.fate:
                d['fate'] = n.fate
            if n.grown:
                d['grown'] = True
            if n.dry:
                d['dry'] = True
            out.append(d)
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump({'world': self.world, 'meta': self.meta, 'nodes': out},
                      f, ensure_ascii=False, separators=(',', ':'))
        os.replace(tmp, path)

    @classmethod
    def load(cls, path):
        with open(path, encoding='utf-8') as f:
            d = json.load(f)
        nodes = []
        for i, e in enumerate(d.get('nodes', [])):
            if 'board' in e:
                board = e['board']
                parent = e.get('parent')
            else:
                parent = e['parent']
                board = (set(nodes[parent].board) - set(e.get('del', []))) \
                    | set(e.get('add', []))
            node = Node(board, e.get('depth', 0), parent)
            node.kids = [(n, list(p), to) for n, p, to in e.get('kids', [])]
            node.fate = e.get('fate')
            node.grown = bool(e.get('grown', False))
            node.dry = bool(e.get('dry', False))
            nodes.append(node)
        return cls(d.get('world', ''), nodes, d.get('meta', {}))
