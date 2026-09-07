"""The directive parser against the shipped Odyssey world, and against
a small authored fragment where every answer is known by hand."""

import os
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from nobody import directives   # noqa: E402

ODYSSEY = os.path.join(os.path.dirname(HERE), 'worlds', 'odyssey')


def _fragment(tmp_path, text):
    p = tmp_path / 'w.pddl'
    p.write_text(textwrap.dedent(text))
    return str(p)


def test_schema_directives_attach_to_the_action_that_follows(tmp_path):
    layer = directives.parse(_fragment(tmp_path, '''
        ;; @title Toy
        ;; @hero ann
        ;; @meter-bar mood 0 100 40
        ;; @gloss say hello
        ;; @tell {?who} says hello to
        ;; @tell {?whom}.
        ;; @span You greeted {?whom}.
        ;; @meter mood+5 time+1
        ;; @tag start
        ;; @intensity 2
        ;; @directed ?who ?whom
        (:action greet
         :parameters (?who - person ?whom - person)
         :precondition (and)
         :effect (and))
        ;; @gloss (the roof falls in)
        ;; @kind event
        ;; @meter mood-30
        (:action roof-falls
         :parameters (?where - place)
         :precondition (and)
         :effect (and))
        ;; @done (home) (safe ann)
        ;; @fail (dead ann)
    '''))
    assert layer.title == 'Toy' and layer.hero == 'ann'
    assert layer.meter_bars == {'mood': (0, 100, 40)}
    g = layer.schemas['greet']
    assert g.params == ['?who', '?whom']
    assert g.tell == '{?who} says hello to {?whom}.'
    assert g.meter == {'mood': 5, 'time': 1}
    assert g.tags == ['start'] and g.intensity == 2
    assert g.directed == ('?who', '?whom') and g.is_offer
    assert layer.tell('greet', ['ann', 'bob']) == 'Ann says hello to Bob.'
    assert layer.span('greet', ['ann', 'bob']) == 'You greeted Bob.'
    assert layer.actor('greet', ['ann', 'bob']) == 'ann'
    assert layer.is_choice('greet', ['ann', 'bob'])
    assert not layer.is_choice('greet', ['bob', 'ann'])
    r = layer.schemas['roof-falls']
    assert r.is_event and not r.is_offer and r.meter == {'mood': -30}
    assert layer.actor('roof-falls', ['x']) is None
    assert layer.done == [[('home',), ('safe', 'ann')]]
    assert layer.fail == [[('dead', 'ann')]]
    assert layer.closed({('home',), ('safe', 'ann'), ('x',)}) == \
        ('done', [('home',), ('safe', 'ann')])
    assert layer.closed({('home',)}) is None


def test_the_odyssey_world_reads_whole():
    layer = directives.parse(os.path.join(ODYSSEY, 'wine-dark.pddl'),
                             os.path.join(ODYSSEY, 'wine-dark-init.pddl'))
    assert layer.title == 'Wine-Dark'
    assert layer.hero == 'odysseus'
    assert set(layer.meter_bars) == {'crew', 'divine', 'ithaca', 'kleos',
                                     'years'}
    assert layer.meter_bars['crew'] == (0, 100, 100)
    assert layer.ladders['ithaca']['fluent'] == 'ithaca-hold'
    assert layer.ladders['crew']['rungs']['full'] == 100
    assert layer.episodes['cyclops'] == 'The cave on the high shore'
    assert layer.names['lotus-land'] == 'the land of the lotus-eaters'
    assert layer.place == ('at', 1)
    assert len(layer.schemas) >= 60
    shout = layer.schemas['shout-your-name']
    assert shout.meter == {'kleos': 20, 'divine': -10}
    assert shout.is_offer and shout.directed == ('?who', '?whom')
    assert 'hubris' in shout.tags
    assert layer.gloss('shout-your-name',
                       ['odysseus', 'polyphemus', 'cyclops-island']).startswith(
        'Shout your real name across the water')
    curse = layer.schemas['lay-the-curse']
    assert curse.is_event and curse.observe == 'unwitnessed'
    assert layer.schemas['keep-watch'].foreknown == 'aeolus'
    assert layer.schemas['be-kept'].meter['years'] == 7
    # terminal lines come from the instance file
    assert [('home',), ('reunited',)] in layer.done
    assert [('ithaca-hold', 'lost')] in layer.fail
    assert layer.ending([('home',), ('reunited',)]) == 'Home, and known'
    # the world's beats are nobody's choice
    assert not layer.is_choice('open-the-bag', ['eurylochus', 'wind-bag'])
    assert layer.is_choice('keep-watch', ['odysseus', 'wind-bag'])
    # a two-line @tell joins
    assert layer.tell('blind-the-cyclops',
                      ['odysseus', 'polyphemus', 'eurylochus']).startswith(
        'The stake goes in hissing. The sound')
