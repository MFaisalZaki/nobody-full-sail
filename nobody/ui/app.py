"""The game loop and its screens.

Title → crisis → front page → crisis … → epilogue → title. A crisis
screen shows the four meters, the dateline, the board on a papyrus
card, the answers as buttons and the clock running down; the front
page shows the paper; the epilogue shows how it ended and the score.
`run` opens a window sized to the screen and drawn at its full
resolution; `screenshots` renders every screen headlessly to PNG
files, which is how the look is checked without a display.
"""

import math
import os
import time

import pygame

from ..session import Session
from ..voyages import chart as voyage_chart, load_runs, record as voyage_record, save_run
from . import draw as D
from . import scene as SC
from . import theme as T
from . import wave as W
from .wave import Wave
from .window import open_window

# --- the app --------------------------------------------------------------------

class App:

    def __init__(self, world, library, timer=None, scale=None, headless=False,
                 seed=None, live=False, library_path=None):
        self.world = world
        self.library = library
        self.timer = world.timer if timer is None else timer
        self.scale = scale
        self.seed = seed
        self.headless = headless
        #: grow the library with the engine when a road runs out (needs
        #: clingo and the planner; a grounding takes a while)
        self.live = live
        self.library_path = library_path
        self._generator = None
        if headless:
            os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
            os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
        pygame.init()
        T.forget()          # fonts of an earlier session, if any, are dead
        title = f'{world.title}: {world.subtitle}'
        if headless:
            # a plain surface, `scale` device pixels per logical unit
            self.window = None
            k = 1.0 if scale is None else scale
            self.surface = pygame.Surface((max(1, round(T.W * k)),
                                           max(1, round(T.H * k))))
        else:
            # as large as fits the screen unless a scale was asked for;
            # high-DPI, so the surface may hold more pixels than that
            self.window = open_window(title, scale)
            self.surface = self.window.get_surface()
        self.canvas = None
        self._fitted = None
        self.fit()
        self.clock = pygame.time.Clock()
        self.time = W.Timeline()        # the accumulator every wave is read at
        self.session = None
        self.screen = TitleScreen(self)
        self.adviser = False        # impact previews on the buttons
        self.hover = None
        self.running = True

    # --- flow -------------------------------------------------------------

    def new_game(self):
        self.session = Session(self.world, self.library, seed=self.seed)
        self.onward()

    def onward(self):
        """The next screen of the story: its end, the only road on
        (played, and its page shown — a board with one thing to do on
        it is not a crisis), or the next crisis."""
        session = self.session
        if session.over:
            self.screen = EpilogueScreen(self)
        elif session.lone() is not None:
            self.screen = PaperScreen(self, session.take())
        else:
            self.screen = CrisisScreen(self)

    def to_title(self):
        self.screen = TitleScreen(self)

    def generator(self):
        if self._generator is None:
            from grow.generator import Generator     # needs the grow extra
            self._generator = Generator(self.world, workers=1,
                                        say=lambda text: None)
        return self._generator

    def fit(self):
        """The canvas for the surface as it is now: the largest 1:2
        area that fits, centred — the whole window at first, a
        letterboxed part of it once the window was resized. Fonts
        follow the scale. Cheap unless the size changed."""
        if self.window is not None:
            self.surface = self.window.get_surface()
        size = self.surface.get_size()
        if size == self._fitted:
            return
        sw, sh = size
        k = max(0.1, min(sw / T.W, sh / T.H))
        T.set_scale(k)
        self.canvas = D.Canvas(self.surface, k,
                               ((sw - T.W * k) / 2, (sh - T.H * k) / 2))
        self._fitted = size

    def mouse(self):
        """The pointer in logical units. The window reports points;
        the surface may hold more pixels than that."""
        x, y = pygame.mouse.get_pos()
        if self.window is not None:
            ww, wh = self.window.size
            sw, sh = self.surface.get_size()
            x, y = x * sw / ww, y * sh / wh
        c = self.canvas
        return math.floor((x - c.ox) / c.k), math.floor((y - c.oy) / c.k)

    def run(self):
        while self.running:
            self.time.step(self.clock.tick(60) / 1000.0)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_a:
                    self.adviser = not self.adviser
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE \
                        and isinstance(self.screen, TitleScreen):
                    self.running = False
                else:
                    self.screen.handle(event)
            self.fit()
            self.screen.tick()
            self.screen.draw(self.canvas)
            if self.window is not None:
                self.window.flip()
        pygame.quit()

    def frame(self):
        """Draw the current screen once, off-window (for screenshots);
        the surface drawn on."""
        self.time.step(1 / 60)
        self.fit()
        self.screen.tick()
        self.screen.draw(self.canvas)
        return self.surface


# --- pieces every screen shares --------------------------------------------------

def sea(surface, t=0.0):
    """The deep water, still unless given the time."""
    surface.fill(T.SEA)
    x, y, w, h = surface.bounds()       # the letterbox, if any, is sea too
    D.waves(surface, (x, y, w, h), T.SEA_LIGHT, rows=max(1, round(h / 63)),
            amp=3, wavelength=110, width=1, t=t, speed=0.8, texture=0.2)


def riding(swell, x, y, roll=0.2):
    """The motion of something afloat at (x, y) on `swell`: it rises
    with the water there and tilts with the water's slope."""
    return W.Motion(dy=swell.fix(x), angle=swell.slope().fix(x).scaled(roll), pivot=(x, y))


def meters(surface, app, y=14):
    """The four factions along the top: glyph, name, bar, number."""
    session = app.session
    n = len(app.world.factions)
    gap = 8
    w = (T.W - gap * (n + 1)) // n
    for i, f in enumerate(app.world.factions):
        x = gap + i * (w + gap)
        r = pygame.Rect(x, y, w, 78)
        D.rrect(surface, T.PAPYRUS, r, 10)
        D.rrect(surface, T.INK, r, 10, width=2)
        value, lo, hi = session.bar(f.meter)
        frac = 0 if hi == lo else (value - lo) / (hi - lo)
        low = f.fatal and frac <= 0.25
        D.glyph(surface, f.icon, (x + 18, y + 20), 22, T.BAD if low else T.INK)
        label = T.font(13, bold=True).render(f.short, True, T.INK)
        surface.blit(label, (x + 36, y + 8))
        num = T.font(13, bold=True).render(str(value), True, T.BAD if low else T.INK_SOFT)
        surface.blit(num, (x + w - num.get_width() - 8, y + 30))
        color = T.BAD if low else (T.OLIVE if frac > 0.5 else T.OCHRE)
        D.bar(surface, (x + 8, y + 52, w - 16, 14), value, lo, hi, color,
              back=T.PAPYRUS_DK)


def wrap_card(surface, rect, title=None):
    """A papyrus card with a meander along the top."""
    r = pygame.Rect(rect)
    D.shadow_rect(surface, r, 12, 5)
    D.rrect(surface, T.PAPYRUS, r, 12)
    D.rrect(surface, T.INK, r, 12, width=2)
    D.meander(surface, (r.x + 10, r.y + 6, r.width - 20, 12), T.OCHRE, cell=12, width=2)
    if title:
        f = T.font(15, bold=True)
        D.text(surface, title.upper(), (r.x + 16, r.y + 26), f, T.WINE,
               width=r.width - 32, align='left', max_lines=2)
    return r


class Button:
    def __init__(self, rect, label, action, small=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action
        self.small = small

    def draw(self, surface, font, hover, fill=T.TERRACOTTA):
        small = (self.small, T.font(12, italic=True)) if self.small else None
        D.button(surface, self.rect, self.label, font, fill=fill,
                 hover=hover, small=small)


# --- the title ------------------------------------------------------------------

class TitleScreen:

    def __init__(self, app):
        self.app = app
        w = T.W - 80
        self.runs = load_runs(app.world)
        charted = sum(1 for r in self.runs if r.get('road'))
        self.buttons = [
            Button((40, 548, w, 54), 'Take the tiller', app.new_game),
            Button((40, 612, w, 46), 'How it is played', self.how),
            Button((40, 668, w, 46), 'The roads you have taken', self.chart,
                   f'{charted} voyage{"s" if charted != 1 else ""} charted' if charted
                   else 'none yet'),
        ]
        self.showing_how = False
        self.ship = D.Ship(220)
        self.swell = D.sea_wave(5, 90, 1.2, row=1, texture=0.3)   # the row the ship sits in
        # two gulls on Lissajous paths over the masthead, nearer (and
        # larger) when lower
        self.gulls = [
            (W.Orbit(Wave(90, 0.0, 0.17, 0.0), Wave(14, 0.0, 0.34, 1.0), (T.W // 2, 290)),
             Wave(0.12, 0.0, 0.34, 1.0 + math.pi / 2, 1.0), 0.0),
            (W.Orbit(Wave(70, 0.0, 0.13, 2.1), Wave(10, 0.0, 0.26, 0.4), (T.W // 2 - 40, 262)),
             Wave(0.1, 0.0, 0.26, 0.4 + math.pi / 2, 0.85), 2.4),
        ]

    def how(self):
        self.showing_how = not self.showing_how

    def chart(self):
        self.app.screen = ChartScreen(self.app, self.runs, back=self)

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            m = self.app.mouse()
            if self.showing_how:
                self.showing_how = False
                return
            for b in self.buttons:
                if b.rect.collidepoint(m):
                    b.action()
        elif event.type == pygame.KEYDOWN:
            if self.showing_how:
                self.showing_how = False
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.app.new_game()
            elif event.key == pygame.K_h:
                self.how()
            elif event.key == pygame.K_r:
                self.chart()

    def tick(self):
        pass

    def draw(self, surface):
        app, world = self.app, self.app.world
        t = app.time.t
        sea(surface, t)
        # the masthead
        D.meander(surface, (30, 60, T.W - 60, 14), T.OCHRE, cell=14, width=2)
        title = T.font(64, bold=True).render(world.title, True, T.PAPYRUS)
        surface.blit(title, ((T.W - title.get_width()) // 2, 86))
        sub = T.font(30).render(world.subtitle.upper(), True, T.OCHRE)
        surface.blit(sub, ((T.W - sub.get_width()) // 2, 160))
        D.meander(surface, (30, 206, T.W - 60, 14), T.OCHRE, cell=14, width=2)
        # the ship on the water, riding the middle wave; gulls above
        for orbit, size, phase in self.gulls:
            D.gull(surface, orbit.at(0, t), 14, T.FOAM, t, phase,
                   motion=W.Motion(scale=size, pivot=orbit.at(0, t)))
        D.waves(surface, (0, 300, T.W, 200), T.FOAM, rows=3, amp=5,
                wavelength=90, width=2, t=t, speed=1.2, texture=0.3)
        cx = T.W // 2
        self.ship.render(surface, (cx, 400), T.INK, T.PAPYRUS, t,
                         riding(self.swell, cx, 400), eye=T.PAPYRUS, rim=T.FOAM)
        tag = T.font(16, italic=True).render('A game of nautical survival', True, T.FOAM)
        surface.blit(tag, ((T.W - tag.get_width()) // 2, 500))
        m = app.mouse() if not app.headless else (-1, -1)
        for i, b in enumerate(self.buttons):
            b.draw(surface, T.font(22 if i == 0 else 18, bold=True), b.rect.collidepoint(m),
                   fill=T.TERRACOTTA if i == 0 else T.SEA_LIGHT)
        # the record
        if self.runs:
            best = max(self.runs, key=lambda r: (r.get('crises', 0), r.get('years', 0)))
            line = (f'{len(self.runs)} voyage(s) so far · best: {best.get("title", "?")}, '
                    f'{best.get("crises", 0)} crises, {best.get("years", 0)} years')
        else:
            line = 'No voyages yet. The score to beat is the poem\'s own.'
        D.text(surface, line, (30, 738), T.font(13), T.DIM, width=T.W - 60,
               align='center')
        credit = ('Every story in this game was generated by polyscene, '
                  'a scenario engine, from a PDDL model of the poem.')
        D.text(surface, credit, (30, 780), T.font(12, italic=True), T.DIM,
               width=T.W - 60, align='center')
        keys = T.font(12).render('Enter: play · H: how · R: the roads · A: adviser · Esc: quit',
                                 True, T.DIM)
        surface.blit(keys, ((T.W - keys.get_width()) // 2, 850))
        if self.showing_how:
            self.draw_how(surface)

    def draw_how(self, surface):
        world = self.app.world
        surface.dim(T.SEA_DARK, 200)
        r = wrap_card(surface, (24, 60, T.W - 48, T.H - 120), 'How it is played')
        y = r.y + 60
        f = T.font(15)
        paras = [
            'You are Odysseus, and everything that happens next is your fault.',
            'A crisis lands every scene. You have '
            f'{int(self.app.timer)} seconds to answer it. Every answer pleases '
            'somebody and costs you somebody else.',
        ]
        for fa in world.factions:
            paras.append(f'{fa.label} — {fa.blurb}'
                         + ('' if fa.fatal else ' (Losing them all is not the end. It is the poem.)'))
        paras += [
            'Let a faction hit the floor and it is over. Reach an ending the poem '
            'allows and the bards will sing it, more or less accurately.',
            'The story is not written in advance. Every crisis and every answer was '
            'generated by a scenario engine from a model of the poem, and every road '
            'you can take is one the engine found sound.',
            'Keys: 1–4 answer · ↑ ↓ read an answer first · Enter continue · A what an answer costs · L the log.',
        ]
        for p in paras:
            y += D.text(surface, p, (r.x + 16, y), f, T.INK, width=r.width - 32) + 8
        hint = T.font(13, italic=True).render('(click or press any key)', True, T.INK_SOFT)
        surface.blit(hint, (r.x + (r.width - hint.get_width()) // 2, r.bottom - 30))


# --- the crisis -----------------------------------------------------------------

class CrisisScreen:

    def __init__(self, app):
        self.app = app
        self.session = app.session
        self.crisis = self.session.crisis()
        self.world_beats = self.session.options()[1]   # what the world may do, if you wait
        self.deadline = time.monotonic() + app.timer if app.timer else None
        self.paused_at = None
        self.buttons = []
        self.focus = None           # the answer under the pointer, or reached by the keys
        self.showing_log = False
        self.scene = app.world.scene(self.session.atoms, self.session.opening)
        self.stage = None
        self.layout()

    def layout(self):
        """The answers, each a sentence of what you would be doing, on
        a button of its own: two lines of it, and under it what it
        costs (the adviser) or, for doing nothing, what green means."""
        options = self.crisis.options
        n = len(options)
        bottom = T.H - 24
        h = 64 if n <= 3 else (56 if n == 4 else 48)
        gap = 8
        y = bottom - n * (h + gap) + gap
        self.buttons = []
        for i, o in enumerate(options):
            small = None
            if o.kind == 'wait':
                small = self.app.world.wait_hint()
            elif self.app.adviser and o.beat:
                schema = self.session.layer.schema(o.beat[0])
                moved = ', '.join(f'{self.app.world.faction(m).label if self.app.world.faction(m) else m} '
                                  f'{d:+d}' for m, d in schema.meter.items()
                                  if self.app.world.faction(m))
                small = moved or 'no cost to anyone'
            self.buttons.append(Button((24, y + i * (h + gap), T.W - 48, h),
                                       o.label, i, small))
        self.card_bottom = y - 14
        self.stage = None       # the card's shape may have changed

    def seconds_left(self):
        if self.deadline is None:
            return None
        return max(0.0, self.deadline - time.monotonic())

    def handle(self, event):
        if self.showing_log:
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                self.showing_log = False
                if self.paused_at is not None and self.deadline is not None:
                    self.deadline += time.monotonic() - self.paused_at
                self.paused_at = None
            return
        if event.type == pygame.MOUSEMOTION:
            m = self.app.mouse()
            self.focus = next((i for i, b in enumerate(self.buttons)
                               if b.rect.collidepoint(m)), self.focus if self.keyed else None)
            if self.focus is not None:
                self.keyed = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            m = self.app.mouse()
            for b in self.buttons:
                if b.rect.collidepoint(m):
                    self.answer(b.action)
                    return
        elif event.type == pygame.KEYDOWN:
            n = len(self.buttons)
            if pygame.K_1 <= event.key <= pygame.K_9:
                i = event.key - pygame.K_1
                if i < n:
                    self.answer(i)
            elif event.key in (pygame.K_DOWN, pygame.K_TAB) and n:
                self.focus = 0 if self.focus is None else (self.focus + 1) % n
                self.keyed = True
            elif event.key == pygame.K_UP and n:
                self.focus = n - 1 if self.focus is None else (self.focus - 1) % n
                self.keyed = True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and self.focus is not None:
                self.answer(self.focus)
            elif event.key == pygame.K_l:
                self.showing_log = True
                self.paused_at = time.monotonic()
            elif event.key == pygame.K_a:
                self.layout()

    keyed = False       # the focus was reached by the keys, so the mouse leaves it alone

    def answer(self, i):
        page = self.session.choose(i)
        self.app.screen = PaperScreen(self.app, page)

    def tick(self):
        if self.app.adviser != getattr(self, '_adviser', None):
            self._adviser = self.app.adviser
            self.layout()
        if self.showing_log:
            return
        left = self.seconds_left()
        if left is not None and left <= 0:
            page = self.session.timeout()
            self.app.screen = PaperScreen(self.app, page)

    def draw(self, surface):
        app, session, crisis = self.app, self.session, self.crisis
        t = app.time.t
        sea(surface)
        meters(surface, app)
        # the dateline
        f = T.font(14, bold=True)
        date = f.render(f'{session.clock_text()}  ·  Crisis {session.crises + 1}'.upper(),
                        True, T.OCHRE)
        surface.blit(date, (24, 104))
        # the clock
        left = self.seconds_left()
        if left is not None:
            urgent = left < 10
            secs = T.font(16, bold=True).render(f'{int(left):>2}s', True,
                                                T.BAD if urgent else T.PAPYRUS)
            surface.blit(secs, (T.W - 24 - secs.get_width(), 102))
            glass = (T.W - 34 - secs.get_width() - 10, 112)
            breath = W.Motion(scale=Wave(0.12, 0.0, 6.0, 0.0, 1.0), pivot=glass) if urgent else None
            D.glyph(surface, 'hourglass', glass, 16, T.BAD if urgent else T.PAPYRUS,
                    t, breath)
            frac = left / app.timer if app.timer else 0
            D.bar(surface, (24, 126, T.W - 48, 6), frac, 0, 1,
                  T.BAD if urgent else T.OCHRE, back=T.SEA_LIGHT, radius=3)
        # the card: the board, drawn — the same state the meters and
        # the caption describe, looked at — over a caption of what a
        # picture cannot carry (names, mostly)
        r = wrap_card(surface, (24, 142, T.W - 48, self.card_bottom - 142), crisis.title)
        y = r.y + 26 + D.text_height(T.font(15, bold=True), crisis.title.upper(), r.width - 32, max_lines=2) + 6
        D.hrule(surface, r.x + 16, r.right - 16, y, T.INK_SOFT)
        y += 8
        legend = T.font(13)
        lines = min(3, len(D.wrap(legend, self.scene.caption, r.width - 32)))
        caption_h = lines * (legend.get_height() + 2)
        stage = (r.x + 12, y, r.width - 24, r.bottom - 26 - caption_h - y)
        if self.stage is None or self.stage.rect != stage:
            self.stage = SC.Stage(self.scene, stage)
        mood = 1.0
        if app.world.sky:
            value, lo, hi = session.bar(app.world.sky)
            mood = 0.0 if hi == lo else (value - lo) / (hi - lo)
        self.stage.draw(surface, t, mood)
        D.hrule(surface, r.x + 16, r.right - 16, stage[1] + stage[3] + 2, T.INK_SOFT)
        D.text(surface, self.scene.caption, (r.x + 16, stage[1] + stage[3] + 8), legend,
               T.INK_SOFT, width=r.width - 32, max_lines=3)
        D.meander(surface, (r.x + 10, r.bottom - 20, r.width - 20, 12),
                  T.OCHRE, cell=12, width=2)
        # the answers: what you would be doing, in a sentence each; the
        # green one is the world's move, not yours
        m = app.mouse() if not app.headless else (-1, -1)
        size = 14 if len(self.buttons) <= 4 else 13
        for i, b in enumerate(self.buttons):
            hover = b.rect.collidepoint(m) or i == self.focus
            fill = T.OLIVE if crisis.options[i].kind == 'wait' else T.TERRACOTTA
            D.choice(surface, b.rect, i + 1, b.label, T.font(size, bold=True), fill=fill,
                     hover=hover, small=b.small)
        if self.focus is not None and self.focus < len(self.buttons):
            self.describe(surface, self.focus, r)
        if self.showing_log:
            draw_log(surface, app)

    def describe(self, surface, i, card):
        """What the answer under the pointer does: its passage, and
        what it costs whom — over the foot of the card."""
        world, layer = self.app.world, self.session.layer
        option = self.crisis.options[i]
        body, small = T.font(13), T.font(12, italic=True)
        w = card.width - 56
        costs = []
        if option.beat:
            passage = layer.tell(option.beat[0], option.beat[1])
            schema = layer.schema(option.beat[0])
            for meter, delta in schema.meter.items():
                f = world.faction(meter)
                if f:
                    costs.append((f.icon, delta))
                elif meter == world.clock:
                    costs.append((None, delta))
        else:
            told = [layer.tell(name, params) for name, params, _ in self.world_beats[:3]]
            passage = 'The world moves, and you read about it. One of these, at random:\n' \
                + '\n'.join('— ' + t for t in told)
        lines = min(5, len(D.wrap(body, passage, w)))
        h = 14 + lines * (body.get_height() + 2) + 6 + 20 + 10
        r = pygame.Rect(card.x + 12, card.bottom - 22 - h, card.width - 24, h)
        D.shadow_rect(surface, r, 8, 3)
        D.rrect(surface, T.PAPYRUS, r, 8)
        D.rrect(surface, T.INK, r, 8, width=1)
        y = r.y + 10
        y += D.text(surface, passage, (r.x + 16, y), body, T.INK, width=w, max_lines=5) + 4
        x = r.x + 16
        if not costs:
            D.text(surface, 'costs nothing, as far as anyone can tell' if option.beat
                   else 'costs whatever the world decides it costs', (x, y), small, T.INK_SOFT)
        for icon, delta in costs:
            if icon:
                D.glyph(surface, icon, (x + 8, y + 8), 14, T.INK)
                x += 20
                D.badge(surface, (x, y), delta, T.font(12, bold=True))
                x += 44
            else:
                unit = world.clock_label.lower() + ('s' if abs(delta) != 1 else '')
                D.text(surface, f'{delta:+d} {unit}', (x, y + 1), small, T.INK_SOFT)
                x += 60


# --- the front page ---------------------------------------------------------------

class PaperScreen:

    def __init__(self, app, page):
        self.app = app
        self.page = page
        self.session = app.session
        self.button = Button((24, T.H - 24 - 56, T.W - 48, 56),
                             self.next_label(), self.next)
        self.showing_log = False
        # the board after the beat, for the paper's picture
        self.scene = app.world.scene(self.session.atoms, self.session.opening)
        self.stage = None

    def next_label(self):
        if self.session.silent and self.app.live:
            return 'Ask the Muse for more'
        if self.session.over:
            return 'And then'
        if self.session.lone() is not None:
            return 'Take the only road'
        return 'Next crisis'

    def next(self):
        if self.session.silent and self.app.live:
            self.app.screen = ComposingScreen(self.app)
        else:
            self.app.onward()

    def handle(self, event):
        if self.showing_log:
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                self.showing_log = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button.rect.collidepoint(self.app.mouse()):
                self.next()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_RIGHT):
                self.next()
            elif event.key == pygame.K_l:
                self.showing_log = True

    def tick(self):
        pass

    def draw(self, surface):
        app, page, world = self.app, self.page, self.app.world
        t = app.time.t
        sea(surface)
        meters(surface, app)
        r = pygame.Rect(24, 104, T.W - 48, self.button.rect.y - 118)
        D.shadow_rect(surface, r, 4, 5)
        surface.rect(T.PAPYRUS, r)
        surface.rect(T.INK, r, width=2)
        x, y, w = r.x + 14, r.y + 10, r.width - 28
        # masthead
        head = T.font(26, bold=True).render(world.masthead, True, T.INK)
        surface.blit(head, (r.x + (r.width - head.get_width()) // 2, y))
        y += head.get_height() + 2
        D.hrule(surface, x, x + w, y, T.INK, 2)
        y += 4
        line = T.font(11).render(f'{page.dateline}   ·   {world.tagline}', True, T.INK_SOFT)
        if line.get_width() > w:
            line = T.font(11).render(page.dateline, True, T.INK_SOFT)
        surface.blit(line, (r.x + (r.width - line.get_width()) // 2, y))
        y += line.get_height() + 3
        D.hrule(surface, x, x + w, y, T.INK, 1)
        y += 10
        # the headline
        hf = T.font(24 if len(page.headline) < 48 else 20, bold=True)
        y += D.text(surface, page.headline, (x, y), hf, T.INK, width=w, line_gap=0,
                    max_lines=4) + 6
        if page.dithered:
            y += D.text(surface, 'THE CLOCK RAN OUT. EVERY FACTION −5.', (x, y),
                        T.font(13, bold=True), T.BAD, width=w) + 4
        elif page.forced:
            y += D.text(surface, 'THE ONLY ROAD FROM THERE. NOTHING TO DECIDE.', (x, y),
                        T.font(13, bold=True), T.WINE, width=w) + 4
        # the standfirst
        y += D.text(surface, page.standfirst, (x, y), T.font(15, italic=True), T.INK,
                    width=w, line_gap=2, max_lines=5) + 8
        D.hrule(surface, x, x + w, y, T.INK_SOFT, 1)
        y += 8
        # the factions
        body = T.font(14)
        bottom = r.bottom - 10
        for faction, delta, text in page.reactions:
            if y > bottom - 40:
                break
            D.glyph(surface, faction.icon, (x + 12, y + 10), 18, T.INK)
            badge = D.badge(surface, (x + 28, y), delta, T.font(12, bold=True))
            name = T.font(14, bold=True).render(faction.label, True, T.INK)
            surface.blit(name, (badge.right + 6, y + 1))
            y += 22
            y += D.text(surface, text, (x + 28, y), body, T.INK, width=w - 28,
                        max_lines=3) + 6
        if page.asides and y < bottom - 40:
            D.hrule(surface, x, x + w, y, T.INK_SOFT, 1)
            y += 6
            heading = 'AND THEN' if page.asides[0][3] else 'MEANWHILE'
            y += D.text(surface, heading, (x, y), T.font(12, bold=True), T.WINE) + 2
            for head, passage, deltas, own in page.asides:
                if y > bottom - 30:
                    break
                moved = '  '.join(f'{world.faction(m).label} {d:+d}' for m, d in deltas.items()
                                  if world.faction(m))
                y += D.text(surface, head, (x, y), T.font(13, bold=True), T.INK, width=w,
                            max_lines=2)
                if moved:
                    y += D.text(surface, moved, (x, y), T.font(12, italic=True), T.INK_SOFT,
                                width=w, max_lines=1)
                y += 4
        # where things stand: the board after the beat, as the paper's
        # photograph — the state of the nation, in the original's
        # terms, drawn; a caption for what a picture cannot carry
        if not self.session.over and y < bottom - 110:
            D.hrule(surface, x, x + w, y, T.INK_SOFT, 1)
            y += 6
            y += D.text(surface, 'WHERE THINGS STAND', (x, y), T.font(12, bold=True), T.WINE) + 4
            legend = T.font(12, italic=True)
            caption = self.scene.caption.replace('\n', ' ')
            lines = min(2, len(D.wrap(legend, caption, w)))
            caption_h = lines * (legend.get_height() + 2)
            stage = (x, y, w, bottom - y - caption_h - 8)
            if self.stage is None or self.stage.rect != stage:
                self.stage = SC.Stage(self.scene, stage)
            mood = 1.0
            if world.sky:
                value, lo, hi = self.session.bar(world.sky)
                mood = 0.0 if hi == lo else (value - lo) / (hi - lo)
            self.stage.draw(surface, t, mood)
            surface.rect(T.INK, stage, width=1)
            D.text(surface, caption, (x, stage[1] + stage[3] + 4), legend, T.INK_SOFT,
                   width=w, max_lines=2)
        m = app.mouse() if not app.headless else (-1, -1)
        self.button.label = self.next_label()
        self.button.draw(surface, T.font(20, bold=True), self.button.rect.collidepoint(m),
                         fill=T.WINE if self.session.over else T.TERRACOTTA)
        if self.showing_log:
            draw_log(surface, app)


# --- the log ----------------------------------------------------------------------

def draw_log(surface, app):
    surface.dim(T.SEA_DARK, 200)
    r = wrap_card(surface, (24, 100, T.W - 48, T.H - 200), 'The log')
    y = r.y + 60
    f = T.font(13)
    pages = app.session.log()
    if not pages:
        D.text(surface, 'Nothing has happened yet. Give it a moment.', (r.x + 16, y), f, T.INK)
    for page in pages[-14:]:
        head = D.wrap(T.font(13, bold=True), page.headline, r.width - 32)[0]
        y += D.text(surface, head, (r.x + 16, y), T.font(13, bold=True), T.INK,
                    width=r.width - 32, max_lines=1)
        y += D.text(surface, page.dateline, (r.x + 16, y), T.font(11, italic=True),
                    T.INK_SOFT, width=r.width - 32, max_lines=1) + 4
        if y > r.bottom - 40:
            break
    hint = T.font(13, italic=True).render('(any key to close)', True, T.INK_SOFT)
    surface.blit(hint, (r.x + (r.width - hint.get_width()) // 2, r.bottom - 28))


# --- the Muse ---------------------------------------------------------------------

class ComposingScreen:
    """The library ran out here and live growth is on: the engine is
    grounding the world at this board and telling what comes next.
    Twenty seconds to a minute, with the sea to look at."""

    def __init__(self, app):
        self.app = app
        self.session = app.session
        self.t0 = time.monotonic()
        self.future = app.generator().start(app.library, self.session.at)
        self.failed = None
        self.ship = D.Ship(90)
        self.swell = D.sea_wave(3, 60, 2.0, row=1)

    def handle(self, event):
        pass

    def tick(self):
        if not self.future.done():
            return
        try:
            added = self.app.generator().finish(self.app.library, self.session.at,
                                                self.future)
        except Exception as e:      # the worker died: say so, end the story
            self.failed = repr(e)
            added = 0
        if added and self.app.library_path:
            try:
                self.app.library.save(self.app.library_path)
            except OSError:
                pass
        if added and self.session.revive():
            self.app.onward()
        else:
            self.app.screen = EpilogueScreen(self.app)

    def draw(self, surface):
        t = self.app.time.t
        sea(surface, t)
        meters(surface, self.app)
        r = wrap_card(surface, (24, 260, T.W - 48, 300), 'The Muse is composing')
        y = r.y + 64
        y += D.text(surface, 'The library holds no more of this road, so the '
                    'engine is telling what comes next: grounding the world '
                    'where you stand, and finding every sound thing that '
                    'could follow.', (r.x + 16, y), T.font(15), T.INK,
                    width=r.width - 32) + 12
        dt = int(time.monotonic() - self.t0)
        D.text(surface, f'{dt}s — usually under a minute.', (r.x + 16, y),
               T.font(14, italic=True), T.INK_SOFT, width=r.width - 32)
        D.waves(surface, (r.x + 16, r.bottom - 70, r.width - 32, 40), T.INK_SOFT,
                rows=2, amp=3, wavelength=60, width=1, t=t, speed=2.0)
        self.ship.render(surface, (r.centerx, r.bottom - 52), T.INK, T.PAPYRUS_DK, t,
                         riding(self.swell, r.centerx - (r.x + 16), r.bottom - 52))


# --- the epilogue ------------------------------------------------------------------

class EpilogueScreen:

    def __init__(self, app):
        self.app = app
        self.session = app.session
        self.outcome = self.session.epilogue()
        self.buttons = [
            Button((24, T.H - 24 - 46 - 58 - 62, T.W - 48, 52), 'The road you took', self.road),
            Button((24, T.H - 24 - 46 - 58, T.W - 48, 48), 'Sail again', app.new_game),
            Button((24, T.H - 24 - 46, T.W - 48, 46), 'Back to shore', app.to_title),
        ]
        if not app.headless:        # a screenshot run is not a voyage
            save_run(app.world, voyage_record(self.session))

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            m = self.app.mouse()
            for b in self.buttons:
                if b.rect.collidepoint(m):
                    b.action()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                self.road()
            elif event.key == pygame.K_ESCAPE:
                self.app.to_title()

    def road(self):
        self.app.screen = RoadScreen(self.app, back=self)

    def tick(self):
        pass

    def draw(self, surface):
        app, world, out = self.app, self.app.world, self.outcome
        sea(surface)
        meters(surface, app)
        kind = {'ending': 'THE POEM ENDS', 'lost': 'IT IS OVER',
                'silence': 'THE BARDS FALL SILENT'}[out.kind]
        r = wrap_card(surface, (24, 104, T.W - 48, T.H - 104 - 206), kind)
        y = r.y + 60
        if out.kind == 'lost' and self.session.cause:
            D.glyph(surface, self.session.cause.icon, (r.x + 34, y + 16), 30, T.BAD)
            dx = 44
        else:
            dx = 0
        y += D.text(surface, out.title, (r.x + 16 + dx, y), T.font(26, bold=True),
                    T.WINE if out.kind == 'lost' else T.INK, width=r.width - 32 - dx) + 8
        y += D.text(surface, out.text, (r.x + 16, y), T.font(15, italic=True), T.INK,
                    width=r.width - 32, line_gap=3) + 14
        D.hrule(surface, r.x + 16, r.right - 16, y, T.INK_SOFT)
        y += 12
        s = out.score
        rows = [('Crises answered', str(s['crises'])),
                (f'{world.clock_label}s at sea', str(s['years'])),
                ('Scenes lived', str(s['beats']))]
        for k, v in rows:
            D.text(surface, k, (r.x + 16, y), T.font(15), T.INK)
            img = T.font(15, bold=True).render(v, True, T.INK)
            surface.blit(img, (r.right - 16 - img.get_width(), y))
            y += 24
        if world.benchmark:
            b = world.benchmark
            verdict = (f'{b["label"]} took {b["years"]} years. '
                       + ('You took longer.' if s['years'] > b['years']
                          else 'You were quicker, for whatever that is worth.'))
            y += 6
            y += D.text(surface, verdict, (r.x + 16, y), T.font(14, italic=True),
                        T.INK_SOFT, width=r.width - 32) + 4
            D.text(surface, b['blurb'], (r.x + 16, y), T.font(12), T.INK_SOFT,
                   width=r.width - 32)
        m = app.mouse() if not app.headless else (-1, -1)
        for i, b in enumerate(self.buttons):
            b.draw(surface, T.font(19 if i else 20, bold=True), b.rect.collidepoint(m),
                   fill=(T.WINE, T.TERRACOTTA, T.SEA_LIGHT)[i])


# --- the road ------------------------------------------------------------------------

KIND = {'ending': 'THE POEM ENDS', 'lost': 'IT IS OVER', 'silence': 'THE BARDS FALL SILENT'}


class RoadScreen:
    """The road you took, charted: every decision a box on a spine,
    the roads not taken beside it in grey with what lay down them, the
    ending at the foot. It scrolls; Esc goes back to the epilogue."""

    SPINE, BOX_X, BOX_W, ALT_X, ALT_W, GAP = 44, 60, 196, 268, 148, 26

    def __init__(self, app, back):
        self.app, self.back = app, back
        self.session = app.session
        self.steps = self.session.road()
        self.scroll = 0.0
        self.top = 132
        half = (T.W - 58) // 2
        self.buttons = [
            Button((24, T.H - 24 - 48, half, 48), 'Sail again', app.new_game),
            Button((34 + half, T.H - 24 - 48, half, 48), 'Back to shore', app.to_title),
        ]
        self.bottom = self.buttons[0].rect.y - 14

    # -- the chart's measure --

    def measure(self):
        """Each step's box and alternatives as rects at scroll 0."""
        y, laid = self.top + 4, []
        head, label, small, tiny = (T.font(10, bold=True), T.font(13, bold=True),
                                    T.font(10, italic=True), T.font(9))
        alt_font = T.font(11)
        for step in self.steps:
            h = 8 + head.get_height() + 2
            h += D.text_height(label, step.label, self.BOX_W - 16, max_lines=4)
            if step.dithered:
                h += head.get_height() + 2
            if step.forced or (step.reach and step.reach[0] > 1):
                h += tiny.get_height() + 2
            for aside, own in step.asides[:2]:
                h += D.text_height(small, ('Then: ' if own else 'Meanwhile: ') + aside,
                                   self.BOX_W - 16, max_lines=2)
            h += 6
            alts, ay = [], y
            for road in step.roads:
                ah = 6 + D.text_height(alt_font, road.label, self.ALT_W - 12, max_lines=3) \
                    + D.text_height(tiny, self.note(road), self.ALT_W - 12, max_lines=2) + 4
                alts.append(pygame.Rect(self.ALT_X, ay, self.ALT_W, ah))
                ay += ah + 6
            box = pygame.Rect(self.BOX_X, y, self.BOX_W, h)
            laid.append((step, box, alts))
            y += max(h, ay - y - 6) + self.GAP
        end = pygame.Rect(self.BOX_X, y, self.BOX_W, 58)
        return laid, end

    @staticmethod
    def note(road):
        """What lay down a road not taken, in a line."""
        if road.reach is None:
            return "the world's move"
        roads, endings, beats = road.reach
        note = f'{roads} road{"s" if roads != 1 else ""}'
        if endings:
            note += f' · {endings} ending{"s" if endings != 1 else ""}'
        if beats:
            note += f' · {beats} beats on'
        return note

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            m = self.app.mouse()
            for b in self.buttons:
                if b.rect.collidepoint(m):
                    b.action()
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y * 36
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.screen = self.back
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.app.new_game()
            elif event.key in (pygame.K_DOWN, pygame.K_j):
                self.scroll += 48
            elif event.key in (pygame.K_UP, pygame.K_k):
                self.scroll -= 48
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll += self.bottom - self.top
            elif event.key == pygame.K_PAGEUP:
                self.scroll -= self.bottom - self.top
            elif event.key == pygame.K_HOME:
                self.scroll = 0
            elif event.key == pygame.K_END:
                self.scroll = 10 ** 6

    def tick(self):
        pass

    def draw(self, surface):
        app, world = self.app, self.app.world
        t = app.time.t
        sea(surface)
        meters(surface, app)
        laid, end = self.measure()
        span = end.bottom + 12 - self.top
        self.scroll = max(0.0, min(self.scroll, max(0, span - (self.bottom - self.top))))
        # the header
        title = T.font(14, bold=True).render('THE ROAD YOU TOOK', True, T.OCHRE)
        surface.blit(title, (24, 104))
        s = self.session.score()
        gone = sum(r.reach[0] for st in self.steps for r in st.roads if r.reach)
        line = f'{s["crises"]} crises · {s["years"]} {world.clock_label.lower()}s · {gone} roads not taken'
        D.text(surface, line, (24, 104), T.font(11), T.DIM, width=T.W - 48, align='right')
        D.hrule(surface, 24, T.W - 24, 124, T.OCHRE, 2)
        off = -self.scroll
        with surface.clip((0, self.top, T.W, self.bottom - self.top)):
            # the spine, top to the ending
            if laid:
                first, last = laid[0][1], end
                W.stroke(surface, (self.SPINE, first.y + off), (self.SPINE, last.centery + off),
                         T.TERRACOTTA, 3, t=t)
            for k, (step, box, alts) in enumerate(laid):
                b = box.move(0, off)
                if b.bottom < self.top - 10 or b.y > self.bottom + 10:
                    continue
                W.stroke(surface, (self.SPINE, b.centery), (b.x, b.centery), T.TERRACOTTA, 3, t=t)
                W.Orbit.ellipse((self.SPINE, b.centery), 6, 6).render(surface, T.TERRACOTTA, t, 0)
                W.Orbit.ellipse((self.SPINE, b.centery), 6, 6).render(surface, T.INK, t, 1)
                D.shadow_rect(surface, b, 6, 3)
                D.rrect(surface, T.PAPYRUS_DK if step.forced else T.PAPYRUS, b, 6)
                D.rrect(surface, T.INK, b, 6, width=2)
                y = b.y + 8
                y += D.text(surface, step.dateline.upper(), (b.x + 8, y), T.font(10, bold=True),
                            T.WINE, width=b.width - 16, max_lines=1) + 2
                y += D.text(surface, step.label, (b.x + 8, y), T.font(13, bold=True), T.INK,
                            width=b.width - 16, max_lines=4)
                if step.dithered:
                    y += D.text(surface, 'THE CLOCK RAN OUT', (b.x + 8, y), T.font(10, bold=True),
                                T.BAD) + 2
                if step.forced:
                    y += D.text(surface, 'the only road from there', (b.x + 8, y),
                                T.font(9, italic=True), T.INK_SOFT) + 2
                elif step.reach and step.reach[0] > 1:
                    y += D.text(surface, f'one of {step.reach[0]} roads from here', (b.x + 8, y),
                                T.font(9), T.INK_SOFT) + 2
                for aside, own in step.asides[:2]:
                    y += D.text(surface, ('Then: ' if own else 'Meanwhile: ') + aside, (b.x + 8, y),
                                T.font(10, italic=True), T.INK_SOFT, width=b.width - 16, max_lines=2)
                # the branches first, then the boxes over them
                for a in alts:
                    a = a.move(0, off)
                    W.stroke(surface, (b.right, b.centery), (a.x, a.centery), T.DIM, 1.5,
                             bend=-0.25 * abs(a.centery - b.centery) if a.centery != b.centery else None,
                             t=t)
                for road, a in zip(step.roads, alts):
                    a = a.move(0, off)
                    D.rrect(surface, T.PAPYRUS_DK, a, 5)
                    D.rrect(surface, T.DIM, a, 5, width=1)
                    yy = a.y + 5
                    yy += D.text(surface, road.label, (a.x + 6, yy), T.font(11), T.INK_SOFT,
                                 width=a.width - 12, max_lines=3)
                    D.text(surface, self.note(road), (a.x + 6, yy), T.font(9), T.DIM,
                           width=a.width - 12, max_lines=2)
            # the ending
            e = end.move(0, off)
            out = self.session.outcome
            W.stroke(surface, (self.SPINE, e.centery), (e.x, e.centery), T.TERRACOTTA, 3, t=t)
            D.shadow_rect(surface, e, 6, 3)
            D.rrect(surface, T.WINE if out and out.kind != 'ending' else T.INK, e, 6)
            D.rrect(surface, T.OCHRE, e, 6, width=2)
            if out:
                D.text(surface, KIND[out.kind], (e.x + 8, e.y + 8), T.font(10, bold=True), T.OCHRE)
                D.text(surface, out.title, (e.x + 8, e.y + 24), T.font(13, bold=True), T.PAPYRUS,
                       width=e.width - 16, max_lines=2)
        # what the chart is
        legend = T.font(10, italic=True).render(
            'the road, in red; beside it, grey, the roads you did not take · scroll, Esc back',
            True, T.DIM)
        surface.blit(legend, ((T.W - legend.get_width()) // 2, self.bottom + 1))
        m = app.mouse() if not app.headless else (-1, -1)
        for i, b in enumerate(self.buttons):
            b.draw(surface, T.font(18, bold=True), b.rect.collidepoint(m),
                   fill=T.TERRACOTTA if i == 0 else T.SEA_LIGHT)


# --- every road, so far --------------------------------------------------------------

class ChartScreen:
    """Every road the player has taken, on one chart: the record's
    voyages merged into a tree and drawn top to bottom — a dot and a
    line per step, the most-travelled road down the first lane, each
    departure from it on a lane of its own, the endings found at the
    tips. The latest voyage in red. It scrolls; Esc goes back."""

    X0, LANE, ROW = 34, 11, 21

    def __init__(self, app, runs, back):
        self.app, self.back = app, back
        self.runs = list(runs)
        self.rows, self.lanes = voyage_chart(self.runs)
        self.uncharted = sum(1 for r in self.runs if not r.get('road'))
        self.scroll = 0.0
        self.top = 132
        half = (T.W - 58) // 2
        self.buttons = [
            Button((24, T.H - 24 - 48, half, 48), 'Take the tiller', app.new_game),
            Button((34 + half, T.H - 24 - 48, half, 48), 'Back to shore', app.to_title),
        ]
        self.bottom = self.buttons[0].rect.y - 14

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            m = self.app.mouse()
            for b in self.buttons:
                if b.rect.collidepoint(m):
                    b.action()
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y * 36
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.screen = self.back
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.app.new_game()
            elif event.key in (pygame.K_DOWN, pygame.K_j):
                self.scroll += 48
            elif event.key in (pygame.K_UP, pygame.K_k):
                self.scroll -= 48
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll += self.bottom - self.top
            elif event.key == pygame.K_PAGEUP:
                self.scroll -= self.bottom - self.top
            elif event.key == pygame.K_HOME:
                self.scroll = 0
            elif event.key == pygame.K_END:
                self.scroll = 10 ** 6

    def tick(self):
        pass

    def lane_x(self, lane):
        step = min(self.LANE, 160 / max(1, self.lanes))
        return self.X0 + lane * step

    def draw(self, surface):
        app, world = self.app, self.app.world
        t = app.time.t
        sea(surface, t)
        rows = self.rows
        # the header
        title = T.font(14, bold=True).render('THE ROADS YOU HAVE TAKEN', True, T.OCHRE)
        surface.blit(title, (24, 104))
        charted = len(self.runs) - self.uncharted
        endings = sum(1 for r in self.runs if r.get('kind') == 'ending')
        line = (f'{charted} voyage{"s" if charted != 1 else ""} · {len(rows)} steps · '
                f'{endings} ending{"s" if endings != 1 else ""} reached')
        D.text(surface, line, (24, 104), T.font(11), T.DIM, width=T.W - 48, align='right')
        D.hrule(surface, 24, T.W - 24, 124, T.OCHRE, 2)
        span = len(rows) * self.ROW + 40
        self.scroll = max(0.0, min(self.scroll, max(0, span - (self.bottom - self.top))))
        off = self.top + 8 - self.scroll
        text_x = self.lane_x(self.lanes) + 8
        if not rows:
            D.text(surface, 'No road yet. Take the tiller, and every voyage from now '
                   'on is charted here: the road it took, beside every road '
                   'before it.', (36, self.top + 20), T.font(15), T.FOAM,
                   width=T.W - 72)
        with surface.clip((0, self.top, T.W, self.bottom - self.top)):
            ys = [off + i * self.ROW + self.ROW // 2 for i in range(len(rows))]
            # the lines first: each step to the one it followed
            for i, row in enumerate(rows):
                x, y = self.lane_x(row.lane), ys[i]
                color = T.TERRACOTTA if row.latest else T.FOAM
                if row.parent is None:
                    py, px = self.top + 2 - self.scroll, x
                else:
                    py, px = ys[row.parent], self.lane_x(rows[row.parent].lane)
                if y < self.top - self.ROW and py < self.top - self.ROW:
                    continue
                if px == x:
                    W.stroke(surface, (x, py), (x, y), color, 2 if row.latest else 1.5, t=t)
                else:
                    # a departure: out of the parent's dot, over to its lane, down
                    W.stroke(surface, (px, py), (x, py + self.ROW * 0.6), color,
                             2 if row.latest else 1.5, bend=-3, t=t)
                    W.stroke(surface, (x, py + self.ROW * 0.6), (x, y), color,
                             2 if row.latest else 1.5, t=t)
            # then the dots and the words
            small, body = T.font(9), T.font(12)
            for i, row in enumerate(rows):
                x, y = self.lane_x(row.lane), ys[i]
                if y < self.top - self.ROW or y > self.bottom + self.ROW:
                    continue
                dot = T.TERRACOTTA if row.latest else T.PAPYRUS
                W.Orbit.ellipse((x, y), 4, 4).render(surface, dot, t, 0)
                if row.dithered:
                    W.Orbit.ellipse((x, y), 4, 4).render(surface, T.BAD, t, 1)
                ink = T.PAPYRUS if row.latest else T.FOAM
                tx = text_x
                img = body.render(row.span, True, ink)
                surface.blit(img, (tx, y - img.get_height() // 2))
                tx += img.get_width() + 6
                if row.count > 1:
                    img = small.render(f'×{row.count}', True, T.DIM)
                    surface.blit(img, (tx, y - img.get_height() // 2))
                    tx += img.get_width() + 6
                for kind, name in row.ends[:1]:
                    color = {'ending': T.GOOD, 'lost': T.BAD}.get(kind, T.DIM)
                    img = T.font(10, bold=True).render(
                        f'· {name}' + (f' ×{len(row.ends)}' if len(row.ends) > 1 else ''),
                        True, color)
                    if tx + img.get_width() > T.W - 24:
                        img = T.font(10, bold=True).render('·', True, color)
                    surface.blit(img, (tx, y - img.get_height() // 2))
        legend = 'your latest voyage in red · a red ring: the clock ran out · scroll, Esc back'
        if self.uncharted:
            legend = f'{self.uncharted} earlier voyage{"s" if self.uncharted != 1 else ""} ' \
                     'went uncharted · ' + legend
        img = T.font(10, italic=True).render(legend, True, T.DIM)
        surface.blit(img, ((T.W - img.get_width()) // 2, self.bottom + 1))
        m = app.mouse() if not app.headless else (-1, -1)
        for i, b in enumerate(self.buttons):
            b.draw(surface, T.font(18, bold=True), b.rect.collidepoint(m),
                   fill=T.TERRACOTTA if i == 0 else T.SEA_LIGHT)


# --- entry points ------------------------------------------------------------------

def run(world, library, timer=None, scale=None, live=False, library_path=None):
    App(world, library, timer=timer, scale=scale, live=live,
        library_path=library_path).run()


def screenshots(world, library, out_dir, seed=1, steps=6, scale=1.0):
    """Render title, a crisis, its paper, the log, and the epilogue of
    a scripted play-through to PNG files in `out_dir`, at `scale`
    pixels per logical unit (2 for a picture as sharp as a Retina
    display shows it)."""
    os.makedirs(out_dir, exist_ok=True)
    app = App(world, library, headless=True, seed=seed, timer=45, scale=scale)
    shots = []

    def shot(name):
        path = os.path.join(out_dir, f'{name}.png')
        pygame.image.save(app.frame(), path)
        shots.append(path)

    shot('01-title')
    app.screen.showing_how = True
    shot('02-how')
    app.screen.showing_how = False
    # the chart, over a few voyages played through at random (the
    # record on disk is not touched: a screenshot run is not a voyage)
    runs = []
    for s in range(4):
        played = Session(world, library, seed=seed + s)
        while not played.over:
            if played.lone() is not None:
                played.take()
            else:
                played.choose(played.random.randrange(len(played.crisis().options)))
        runs.append(voyage_record(played, when='never'))
    app.screen = ChartScreen(app, runs, back=app.screen)
    shot('03-voyages')
    app.new_game()
    k = 0
    while not app.session.over and k < steps:
        if isinstance(app.screen, CrisisScreen):
            if k == 1:
                app.adviser = True
                app.screen.layout()
            if k == 3:
                app.screen.focus = 0
            shot(f'{10 + k:02d}-crisis')
            app.adviser = False
            n = len(app.screen.crisis.options)
            app.screen.answer(k % n)
            shot(f'{10 + k:02d}-paper')
            if k == 2:
                app.screen.showing_log = True
                shot(f'{10 + k:02d}-log')
                app.screen.showing_log = False
            app.screen.next()
            k += 1
        elif isinstance(app.screen, PaperScreen):
            if app.screen.page.forced and 'only' not in ''.join(shots):
                shot(f'{10 + k:02d}-only-road')
            app.screen.next()
        else:
            break
    while isinstance(app.screen, PaperScreen):
        app.screen.next()
    if isinstance(app.screen, EpilogueScreen):
        shot('90-epilogue')
    else:
        # force an ending for the picture: dither until it is over
        while not app.session.over:
            app.session.timeout()
        app.screen = EpilogueScreen(app)
        shot('90-epilogue')
    app.screen.road()
    shot('91-road')
    pygame.quit()
    return shots
