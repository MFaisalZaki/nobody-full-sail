"""The newspaper: what the world says about what you just did.

After every decision the game shows a front page — the headline for
the beat, the passage as its standfirst, one paragraph per faction
whose meter moved, and the world's own beats that followed in the
margin. The prose comes from the world pack (its headline and reaction
hooks) and from the PDDL's own `@tell` lines; this module only lays
the page out.
"""


class Page:
    """One front page."""

    def __init__(self, dateline, headline, standfirst, reactions, asides,
                 deltas, beat, dithered=False, forced=False):
        self.dateline = dateline        # "Year 3 · The cave on the high shore"
        self.headline = headline
        self.standfirst = standfirst    # the beat's own passage
        self.reactions = reactions      # [(faction, delta, text)]
        self.asides = asides            # [(headline, passage, deltas, own)]: the beats that
                                        # followed — the world's, or (own) the hero's only road
        self.deltas = deltas            # {meter: delta} for the player's beat
        self.beat = beat                # (name, [params])
        self.dithered = dithered
        self.forced = forced            # the only road from the board before: no decision

    @property
    def lines(self):
        """The page as plain lines, for the text walk and the log."""
        out = [self.standfirst] if self.standfirst else []
        for faction, delta, text in self.reactions:
            out.append(f'{faction.label} {delta:+d}: {text}')
        for head, passage, deltas, own in self.asides:
            moved = ', '.join(f'{m} {d:+d}' for m, d in sorted(deltas.items()) if d)
            out.append(f'{"Then" if own else "Meanwhile"} — {head}'
                       + (f' ({moved})' if moved else ''))
            if passage:
                out.append('    ' + passage)
        return out


def compose(world, dateline, beat, deltas, asides=(), dithered=False, forced=False):
    """The page for the player's `beat` (name, params) that moved the
    meters by `deltas`, with the beats that followed as `asides`
    [(beat, deltas, own)] — the world's own, or (own) the hero's when
    his was the only road and the story took it."""
    name, params = beat
    layer = world.layer
    if dithered:
        headline = world.dithered_headline()
        standfirst = world.dithered_standfirst()
    else:
        headline = world.headline(name, params)
        standfirst = layer.tell(name, params)
    reactions = []
    for faction in world.factions:
        delta = deltas.get(faction.meter, 0)
        if delta:
            reactions.append((faction, delta,
                              world.reaction(faction, delta, name, params)))
    margin = []
    for aside in asides:
        (aname, aparams), adeltas = aside[0], aside[1]
        own = bool(aside[2]) if len(aside) > 2 else False
        margin.append((world.headline(aname, aparams),
                       layer.tell(aname, aparams),
                       {m: d for m, d in adeltas.items() if d}, own))
    return Page(dateline, headline, standfirst, reactions, margin, deltas,
                beat, dithered=dithered, forced=forced)
