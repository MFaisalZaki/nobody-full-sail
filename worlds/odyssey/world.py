"""The Odyssey pack: Homer's poem as a game of nautical survival.

The world itself is the wine-dark topic from
DiversityPlanning-Scenario-Planning (`topics/winedark`, vendored here
at commit f7b6800): the Iliad and Odyssey as one editable timeline,
sixty-odd schemas, four meters, and terminal lines a telling must
close on. Every passage, choice label and meter cost the game shows
is read off that file's own `;; @` directives. What this pack adds is
the game's voice — the four factions, the newspaper's headlines and
the factions' replies — and nothing of the world.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from nobody.world import Faction, World   # noqa: E402


class Odyssey(World):

    name = 'odyssey'
    title = 'NOBODY'
    subtitle = 'Full Sail'
    domain = 'wine-dark.pddl'
    instance = 'wine-dark-init.pddl'
    rules = ('world.lp', 'facts.lp')
    fates = ('fates.lp',)
    clock = 'years'
    clock_label = 'Year'
    timer = 45
    masthead = 'THE DAILY OMEN'
    tagline = 'All the news the gods see fit to send · Est. 1184 BC'
    benchmark = {'label': 'Odysseus', 'years': 10,
                 'blurb': 'The poem itself: ten years at sea, home alone, '
                          'every man lost, and known by his wife.'}

    factions = (
        Faction('crew', 'The Crew',
                'Your own men. Several have started a mutiny group.',
                fatal=False, icon='oar',
                floor_text='You are alone. That is not the end; it is the poem.'),
        Faction('divine', 'The Gods',
                'Fickle, well-armed, and reading everything you say.',
                fatal=True, icon='bolt',
                floor_text='The sea god has heard enough. The ship, the raft, '
                           'the swimmer: all of it goes down.'),
        Faction('ithaca', 'Ithaca',
                'Patient, mostly. The suitors are eating the patience.',
                fatal=True, icon='loom',
                floor_text='The hall falls. Someone else sits in your chair '
                           'and your wife has stopped unpicking the shroud.'),
        Faction('kleos', 'The Bards',
                'They were briefly singing about you. That was a different year.',
                fatal=True, icon='lyre',
                floor_text='No one sings of you. Nobody, it turns out, was '
                           'your name after all.'),
    )

    #: the engine layer: the third generation solves this world in
    #: seconds at the segment horizons the generator uses (the fifth,
    #: the package default, found no telling of it inside a minute)
    engine_layer = 'encodings-v3'

    #: the axes two tellings must differ on for the generator to count
    #: them as different stories — deeds first, so forks come EARLY
    spread = ('fate', 'arc',
              'did_storm_the_walls', 'did_sack_the_city',
              'did_raid_the_town', 'did_blind_the_cyclops',
              'did_shout_your_name', 'did_steer_for_the_whirlpool',
              'did_pass_the_rock', 'did_slaughter_the_cattle',
              'did_kill_the_suitors', 'crew_left')

    # --- the board, read to the player ------------------------------------

    CREW = {
        'full':    'The crew is at full strength.',
        'thinned': 'The crew is thinned.',
        'remnant': 'A remnant of the crew remains.',
        'alone':   'You are alone.',
    }

    def describe(self, atoms, opening=()):
        layer = self.layer
        opening = set(opening)
        holds = {}
        for a in atoms:
            holds.setdefault(a[0], []).append(a[1:])
        lines = []
        place = next((a[1] for a in holds.get('at', ())
                      if a and a[0] == layer.hero), None)
        if place:
            head = layer.display(place)
            lines.append(head[0].upper() + head[1:] + '.'
                         + (' ' + layer.where[place]
                            if place in layer.where else ''))
        for mark, said in (('inside-horse', 'You are inside the horse.'),
                           ('in-cave', 'You are in the cave.'),
                           ('among-the-dead', 'You are among the dead.')):
            if mark in holds:
                lines.append(said)
        for (keeper,) in holds.get('held-by', ()):
            lines.append(f'{layer.display(keeper)} keeps you here.')
        band = next(iter(holds.get('crew', [()])))
        if band and band[0] in self.CREW:
            lines.append(self.CREW[band[0]])
        alive = {a[0] for a in holds.get('alive', ()) if a}
        party = sorted(c for (c,) in holds.get('with', ()) if c in alive)
        if party:
            lines.append('With you: ' + ', '.join(map(layer.display, party)) + '.')
        if 'ship-whole' in holds:
            lines.append('The ship is whole.')
        elif 'raft-built' in holds:
            lines.append('There is a raft.')
        else:
            lines.append('You have no ship.')
        for name in sorted(layer.reads.keys() & holds.keys()):
            for args in sorted(holds[name]):
                if (name, *args) in opening:
                    continue      # furniture, not residue
                text = layer.reads[name].format(*map(layer.display, args))
                lines.append(text[0].upper() + text[1:] + '.')
        return '\n'.join(lines)

    # --- the newspaper ----------------------------------------------------

    EPISODES = {
        'rites':  'A thigh-bone for the gods',
        'sea':    'Open water',
        'voyage': 'The town on the shore',
        'nostoi': 'News of the other homecomings',
        'divine': 'Something the gods did',
    }

    def episode(self, tags):
        for tag in tags:
            if tag in self.layer.episodes:
                return self.layer.episodes[tag]
        for tag in tags:
            if tag in self.EPISODES:
                return self.EPISODES[tag]
        return 'The wine-dark sea'

    #: the front page, per schema: dry, and reading like a paper that
    #: has covered this man before. {who}/{whom}/… are the beat's
    #: parameters, shown by their display names
    HEADLINES = {
        'propose-the-horse':  'KING OF ITHACA PROPOSES LARGE WOODEN HORSE, DECLINES TO ELABORATE',
        'storm-the-walls':    'FLEET GOES AT THE WALLS IN DAYLIGHT; WALLS UNIMPRESSED',
        'enter-the-horse':    'THIRTY MEN CLIMB INTO HORSE. "IT\'S A PLAN," INSISTS PLANNER',
        'open-the-horse':     'TROY FALLS OVERNIGHT; HORSE "NOT INVOLVED", SAY TROJANS',
        'sack-the-city':      'CITY TAKEN APART IN ONE NIGHT AND MOST OF A MORNING',
        'spare-the-temple':   'TEMPLE SPARED. GODDESS "NOTES IT"',
        'violate-the-temple': 'SOMETHING HAPPENED IN THE TEMPLE; NOBODY WILL SAY WHAT',
        'raise-a-grave':      'OAR PLANTED IN STONES. GODS SAID TO BE "SATISFIED"',
        'claim-the-armour':   'ARMOUR AWARDED TO BEST SPEAKER, NOT BEST FIGHTER',
        'ajax-falls-on-his-sword': 'AJAX FOUND DEAD IN SHEEP PEN; INQUIRY BLAMES THE ARGUMENT',
        'sacrifice-to':       'SMOKE GOES THE RIGHT WAY. {whose} "PLEASED ENOUGH"',
        'sail-on':            'FLEET PUTS OUT FROM {from}; NEXT STOP {to}',
        'raid-the-town':      'TOWN TAKEN IN AN HOUR; MEN REFUSE TO LEAVE FOR THREE DAYS',
        'withdraw-at-once':   'CAPTAIN COUNTS MEN BACK ABOARD BEFORE DARK; MEN FURIOUS',
        'taste-the-lotus':    'CREW SAMPLES LOCAL CUISINE, WOULD RATHER NOT GO HOME NOW',
        'drag-them-back':     'WEEPING SAILORS TIED UNDER BENCHES "FOR THEIR OWN GOOD"',
        'enter-the-cave':     'PARTY ENTERS UNATTENDED CAVE TO SEE WHO OWNS THE CHEESE',
        'take-the-cheese':    'HERO TAKES CHEESE, LEAVES. BARDS DISAPPOINTED',
        'blind-the-cyclops':  'GIANT BLINDED WITH OLIVE STAKE; ENTIRE ISLAND COMPLAINS',
        'escape-the-cave':    'MEN LEAVE CAVE UNDER SHEEP; SHEEP UNAVAILABLE FOR COMMENT',
        'give-a-false-name':  '"NOBODY" DID IT, CYCLOPS TELLS NEIGHBOURS',
        'shout-your-name':    'HERO SHOUTS FULL NAME AND ADDRESS AT BLIND, PRAYING GIANT',
        'lay-the-curse':      'SOMEONE ON A BEACH IS TALKING TO THE SEA. THE SEA IS LISTENING',
        'take-the-bag':       'KING OF WINDS HANDS OVER BAG, SAYS "DON\'T"',
        'keep-watch':         'CAPTAIN STAYS AWAKE NINE DAYS; ITHACA SIGHTED',
        'open-the-bag':       'CREW OPENS BAG BELIEVED TO CONTAIN GOLD. IT DID NOT CONTAIN GOLD',
        'moor-inside':        'ELEVEN SHIPS MOOR INSIDE LOVELY HARBOUR. ONE SHIP LEAVES',
        'moor-outside':       'CAPTAIN TIES UP OUTSIDE PERFECTLY GOOD HARBOUR; CREW MUTTER',
        'drink-the-cup':      'SHORE PARTY ACCEPTS DRINK, NOW PIGS',
        'take-the-herb':      'HERO ACCEPTS BLACK-ROOTED HERB FROM STRANGER',
        'free-the-crew':      'WITCH SWEARS GREAT OATH; BRISTLES RECEDE',
        'stay-the-year':      'FLEET "JUST STAYING A BIT LONGER" — ONE YEAR ON',
        'fall-from-the-roof': '{whom} FALLS OFF ROOF. LADDER "RIGHT THERE"',
        'go-down-to-the-dead': 'HERO GOES TO THE UNDERWORLD TO ASK FOR DIRECTIONS',
        'question-the-shade': '{whom} DRINKS THE BLOOD, REMEMBERS EVERYTHING, TALKS',
        'hear-the-prophecy':  'PROPHET: "LEAVE THE CATTLE ALONE." CREW: "WHAT CATTLE?"',
        'come-back-from-the-dead': 'HERO RETURNS FROM THE DEAD, DOES NOT LOOK BACK',
        'stop-their-ears':    'WAX ISSUED TO ALL HANDS; ALL HANDS CONFUSED',
        'bind-me-to-the-mast': 'CAPTAIN HAS SELF TIED TO MAST TO HEAR A SONG',
        'pass-the-rock':      'SIX MEN LOST TO ROCK; CAPTAIN "HAD TO CHOOSE"',
        'steer-for-the-whirlpool': 'CAPTAIN PICKS WHIRLPOOL OVER MONSTER; SHIP LOST',
        'land-at':            'FLEET LANDS ON ISLAND FAMOUS FOR ONE THING',
        'sail-past':          'FLEET SAILS PAST FREE CATTLE; MEN "WILL REMEMBER THIS"',
        'becalm':             'WIND STOPS. WIND DOES NOT START AGAIN',
        'endure-the-calm':    'CREW STARVES QUIETLY FOR A WEEK; NOBODY TOUCHES ANYTHING',
        'consume-provisions': 'STORES EMPTY. CREW LOOK AT CATTLE. CATTLE LOOK BACK',
        'slaughter-the-cattle': 'SUN\'S CATTLE EATEN WHILE CAPTAIN ASLEEP; SUN "LIVID"',
        'break-the-ship':     'SHIP STRUCK BY LIGHTNING FROM CLEAR SKY. WEATHER "UNRELATED"',
        'the-tide-takes-it':  'TIDE REMOVES ONLY EVIDENCE OF SHIP',
        'wash-ashore':        'MAN FOUND ASLEEP UNDER LEAVES ON NYMPH\'S ISLAND',
        'be-kept':            'SEVEN YEARS LATER: MAN STILL LOOKING AT SEA',
        'refuse-immortality': 'HERO TURNS DOWN ETERNAL LIFE, CITES WIFE',
        'take-immortality':   'HERO TAKES ETERNAL LIFE. THIS PAPER CEASES PUBLICATION',
        'build-a-raft':       'TWENTY TREES DOWN; RAFT "NEARLY DONE"',
        'sail-the-raft':      'RAFT LASTS SEVENTEEN DAYS. STORM LASTS ONE',
        'supplicate':         'NAKED STRANGER ASKS PRINCESS IF SHE IS A GODDESS',
        'tell-your-story':    'STRANGER TELLS ENTIRE STORY AT DINNER; NOBODY INTERRUPTS',
        'be-conveyed-home':   'PHAEACIANS DELIVER SLEEPING MAN TO ITHACA, LEAVE NO NOTE',
        'ambush-the-prince':  'PRINCE GOES OUT TO THE FARMS, DOES NOT COME BACK',
        'land-disguised':     'ELDERLY BEGGAR ARRIVES IN ITHACA; NOTHING TO SEE HERE',
        'land-openly':        'KING WALKS UP HIS OWN ROAD WITH HIS OWN FACE ON',
        'be-known-by-the-scar': 'OLD NURSE DROPS BASIN; "I KNOW THAT KNEE"',
        'reveal-yourself':    'BEGGAR STRAIGHTENS UP IN HUT, STOPS BEING BEGGAR',
        'string-the-bow':     'BEGGAR STRINGS THE BOW SITTING DOWN; HALL GOES QUIET',
        'kill-the-suitors':   'HALL WASHED DOWN AFTER AFTERNOON OF "HOUSEKEEPING"',
        'spare-the-suitors':  'KING PUTS BOW DOWN. SUITORS "WILL NOT FORGET THIS"',
        'make-the-peace':     'FIGHT IN THE ROAD STOPPED WITH ONE SENTENCE',
        'come-home':          'BED CANNOT BE MOVED, CONFIRMS HUSBAND. WIFE CONVINCED',
        'agamemnon-comes-home': 'AGAMEMNON HOME AT LAST; HOME "THE DANGEROUS PART"',
        'menelaus-is-blown-south': 'MENELAUS IN EGYPT "FOR SOME YEARS", REPORTS SAY',
        'ajax-drowns':        'AJAX SURVIVES SHIPWRECK, SAYS SO OUT LOUD, DROWNS',
    }

    def headline(self, name, values):
        text = self.HEADLINES.get(name)
        if text is None:
            return super().headline(name, values)
        schema = self.layer.schema(name)
        bound = schema.bind(values)
        return text.format(**{k: self.layer.display(v).upper()
                              for k, v in bound.items()})

    #: what each faction says, by direction and size of the move —
    #: a paper's second paragraph, one voice per faction
    REACTIONS = {
        'crew': {
            'up':   ['"He knows what he\'s doing," says a sailor, unprompted.',
                     'The oars go a little easier this week.',
                     'Someone has started a song about the captain. It scans.'],
            'down': ['"We had a vote," says Eurylochus. "He wasn\'t at it."',
                     'The benches are emptier and the survivors have noticed.',
                     'A mutiny group has been formed. It meets under the sail.'],
            'gone': ['There is nobody left to be unhappy.'],
        },
        'divine': {
            'up':   ['Olympus, reached for comment, "noted the smoke".',
                     'A grey-eyed goddess is understood to be "not displeased".',
                     'The sea is calmer than it has any reason to be.'],
            'down': ['The sea god has been informed. He has been informed before.',
                     'Thunder, unseasonal. Nobody is saying it is about you.',
                     'A source close to Olympus describes the mood as "wrathful".'],
            'gone': ['The gods are no longer taking the call.'],
        },
        'ithaca': {
            'up':   ['Penelope unpicks a little less of the shroud tonight.',
                     'Word reaches Ithaca and the suitors eat with less appetite.',
                     'The swineherd says he always believed. The swineherd is lying.'],
            'down': ['The suitors have ordered more wine on the household account.',
                     'A loom in Ithaca is being unpicked faster than it is woven.',
                     'Telemachus asked about his father again. Nobody answered.'],
            'gone': ['The hall belongs to other men now.'],
        },
        'kleos': {
            'up':   ['A bard in Sparta has added a verse. It is quite a good verse.',
                     'The name is being said in halls he has never entered.',
                     '"Cunning," the poets are calling it. They were going to call it something else.'],
            'down': ['The bards are working on a version where somebody else did it.',
                     'A verse has been quietly dropped from the evening set.',
                     '"Prudent," the poets are calling it. Nobody sings about prudent.'],
            'gone': ['No song. No name. Nobody.'],
        },
    }

    def reaction(self, faction, delta, name, values):
        table = self.REACTIONS.get(faction.meter)
        if not table:
            return super().reaction(faction, delta, name, values)
        key = 'up' if delta > 0 else 'down'
        pool = table[key]
        # stable per beat, so a replayed month reads the same
        return pool[(abs(delta) + len(name)) % len(pool)]

    #: answers whose gloss wants a parameter in it to mean anything
    LABELS = {
        'sail-on':        'put to sea for {?to}',
        'sail-the-raft':  'put the raft in the water for {?to}',
        'sacrifice-to':   'burn something for {?whose}',
        'drag-them-back': 'drag {?withwhom} off the beach',
        'question-the-shade': 'question the shade of {?whom}',
        'raise-a-grave':  'raise a grave for {?whom}',
    }

    def label(self, name, values):
        text = self.LABELS.get(name)
        if text is None:
            return super().label(name, values)
        return self.layer.schema(name).fill(text, values, self.layer.display)

    def wait_label(self):
        return 'Do nothing. Look at the sea.'

    def dithered_headline(self):
        return 'CAPTAIN STARES AT HORIZON; CREW, GODS, ITHACA AND BARDS ALL NOTICE'

    def dithered_standfirst(self):
        return ('He stood at the stern and did not decide anything, and the '
                'sea decided for him.')

    ENDING_TEXT = {
        'reunited': ('Twenty years, give or take. She asked about the bed and '
                     'he told her, and that was the end of the argument. The '
                     'bards will get it mostly right.'),
        'home': ('He is on his own island, in his own hall, and somebody '
                 'knows it. That is more than most of the fleet got.'),
        'took-immortality': ('He took it. The years stopped counting and so '
                             'did everything else, including this paper.'),
        'ithaca-hold': ('The hall belongs to other men now. Someone else '
                        'sits in your chair and your wife has stopped '
                        'unpicking the shroud.'),
    }

    def ending_text(self, fate, kind):
        for atom in reversed(list(fate)):
            if atom[0] in self.ENDING_TEXT:
                return self.ENDING_TEXT[atom[0]]
        return ''

    def silence_text(self):
        return ('The bards know no more of this road. The library ends here; '
                'grow it with `generate`, or sail another way next time.')


WORLD = Odyssey
