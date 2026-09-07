"""The game loop and its screens.

Title → crisis → front page → crisis … → epilogue → title. A crisis
screen shows the four meters, the dateline, the board on a papyrus
card, the answers as buttons and the clock running down; the front
page shows the paper; the epilogue shows how it ended and the score.
`run` opens a window sized to the screen and drawn at its full
resolution; `screenshots` renders every screen headlessly to PNG
files, which is how the look is checked without a display.
"""

import json
import math
import os
import time

import pygame

from ..session import Session
from . import draw as D
from . import theme as T
from . import wave as W
from .wave import Wave
from .window import open_window

RUNS_FILE = os.path.join(os.path.expanduser('~'), '.nobody', 'runs.json')


# --- the record of past voyages ----------------------------------------------

def load_runs(world):
    try:
        with open(RUNS_FILE, encoding='utf-8') as f:
            return json.load(f).get(world.name, [])
    except (OSError, ValueError):
        return []


def save_run(world, record):
    try:
        os.makedirs(os.path.dirname(RUNS_FILE), exist_ok=True)
        try:
            with open(RUNS_FILE, encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}
        data.setdefault(world.name, []).append(record)
        data[world.name] = data[world.name][-50:]
        with open(RUNS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1)
    except OSError:
        pass


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
        if self.session.over:
            self.screen = EpilogueScreen(self)
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
        self.buttons = [
            Button((40, 560, w, 56), 'Take the tiller', app.new_game),
            Button((40, 628, w, 48), 'How it is played', self.how),
        ]
        self.showing_how = False
        self.runs = load_runs(app.world)
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
                         riding(self.swell, cx, 400), eye=T.PAPYRUS)
        tag = T.font(16, italic=True).render('A game of nautical survival', True, T.FOAM)
        surface.blit(tag, ((T.W - tag.get_width()) // 2, 500))
        m = app.mouse() if not app.headless else (-1, -1)
        for b in self.buttons:
            b.draw(surface, T.font(22, bold=True), b.rect.collidepoint(m))
        # the record
        if self.runs:
            best = max(self.runs, key=lambda r: (r.get('crises', 0), r.get('years', 0)))
            line = (f'{len(self.runs)} voyage(s) so far · best: {best.get("title", "?")}, '
                    f'{best.get("crises", 0)} crises, {best.get("years", 0)} years')
        else:
            line = 'No voyages yet. The score to beat is the poem\'s own.'
        D.text(surface, line, (30, 700), T.font(13), T.DIM, width=T.W - 60,
               align='center')
        credit = ('Every story in this game was generated by polyscene, '
                  'a scenario engine, from a PDDL model of the poem.')
        D.text(surface, credit, (30, 780), T.font(12, italic=True), T.DIM,
               width=T.W - 60, align='center')
        keys = T.font(12).render('Enter: play · H: how · A: adviser · Esc: quit', True, T.DIM)
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
            'Keys: 1–4 answer · Enter continue · A show what an answer costs · L the log.',
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
        self.deadline = time.monotonic() + app.timer if app.timer else None
        self.paused_at = None
        self.buttons = []
        self.showing_log = False
        self.ship = D.Ship(150)
        self.swell = D.sea_wave(3, 70, 0.6, row=1)
        self.layout()

    def layout(self):
        options = self.crisis.options
        n = len(options)
        bottom = T.H - 24
        h = 58 if n <= 3 else 50
        gap = 10
        y = bottom - n * (h + gap) + gap
        self.buttons = []
        for i, o in enumerate(options):
            small = None
            if self.app.adviser and o.beat:
                schema = self.session.layer.schema(o.beat[0])
                moved = ', '.join(f'{self.app.world.faction(m).label if self.app.world.faction(m) else m} '
                                  f'{d:+d}' for m, d in schema.meter.items()
                                  if self.app.world.faction(m))
                small = moved or 'no cost to anyone'
            self.buttons.append(Button((24, y + i * (h + gap), T.W - 48, h),
                                       o.label, i, small))
        self.card_bottom = y - 14

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
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            m = self.app.mouse()
            for b in self.buttons:
                if b.rect.collidepoint(m):
                    self.answer(b.action)
                    return
        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                i = event.key - pygame.K_1
                if i < len(self.buttons):
                    self.answer(i)
            elif event.key == pygame.K_l:
                self.showing_log = True
                self.paused_at = time.monotonic()
            elif event.key == pygame.K_a:
                self.layout()

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
        # the card
        r = wrap_card(surface, (24, 142, T.W - 48, self.card_bottom - 142), crisis.title)
        y = r.y + 26 + D.text_height(T.font(15, bold=True), crisis.title.upper(), r.width - 32, max_lines=2) + 6
        D.hrule(surface, r.x + 16, r.right - 16, y, T.INK_SOFT)
        y += 10
        body = T.font(16)
        room = r.bottom - y - 12
        max_lines = max(1, room // (body.get_height() + 3))
        used = D.text(surface, crisis.context, (r.x + 16, y), body, T.INK,
                      width=r.width - 32, line_gap=3, max_lines=max_lines)
        # a vignette where the card has room: the ship on the water,
        # painted the way a cup would carry it
        if r.bottom - (y + used) > 190:
            vy = r.bottom - 96
            with surface.clip((r.x + 12, vy - 70, r.width - 24, 150)):
                D.waves(surface, (r.x + 12, vy - 8, r.width - 24, 60), T.INK_SOFT,
                        rows=3, amp=3, wavelength=70, width=1, t=t, speed=0.6)
                self.ship.render(surface, (r.centerx, vy), T.INK, T.PAPYRUS_DK, t,
                                 riding(self.swell, r.centerx - (r.x + 12), vy))
            D.meander(surface, (r.x + 10, r.bottom - 20, r.width - 20, 12),
                      T.OCHRE, cell=12, width=2)
        # the answers
        m = app.mouse() if not app.headless else (-1, -1)
        for i, b in enumerate(self.buttons):
            hover = b.rect.collidepoint(m)
            fill = T.OLIVE if crisis.options[i].kind == 'wait' else T.TERRACOTTA
            b.draw(surface, T.font(17, bold=True), hover, fill=fill)
            key = T.font(12, bold=True).render(str(i + 1), True, T.PAPYRUS)
            surface.blit(key, (b.rect.x + 8, b.rect.y + 6))
        if self.showing_log:
            draw_log(surface, app)


# --- the front page ---------------------------------------------------------------

class PaperScreen:

    def __init__(self, app, page):
        self.app = app
        self.page = page
        self.session = app.session
        self.button = Button((24, T.H - 24 - 56, T.W - 48, 56),
                             self.next_label(), self.next)
        self.showing_log = False

    def next_label(self):
        if self.session.silent and self.app.live:
            return 'Ask the Muse for more'
        if self.session.over:
            return 'And then'
        return 'Next crisis'

    def next(self):
        if self.session.silent and self.app.live:
            self.app.screen = ComposingScreen(self.app)
        elif self.session.over:
            self.app.screen = EpilogueScreen(self.app)
        else:
            self.app.screen = CrisisScreen(self.app)

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
            y += D.text(surface, 'MEANWHILE', (x, y), T.font(12, bold=True), T.WINE) + 2
            for head, passage, deltas in page.asides:
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
        # back page — the state of the nation, in the original's terms
        if not self.session.over and y < bottom - 110:
            D.hrule(surface, x, x + w, y, T.INK_SOFT, 1)
            y += 6
            y += D.text(surface, 'WHERE THINGS STAND', (x, y), T.font(12, bold=True), T.WINE) + 2
            room = bottom - y - 4
            small = T.font(13)
            lines = max(1, room // (small.get_height() + 2))
            D.text(surface, self.session.intro(), (x, y), small, T.INK_SOFT,
                   width=w, max_lines=lines)
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
            self.app.screen = CrisisScreen(self.app)
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
            Button((24, T.H - 24 - 56, T.W - 48, 56), 'Sail again', app.new_game),
            Button((24, T.H - 24 - 56 - 66, T.W - 48, 50), 'Back to shore', app.to_title),
        ]
        score = self.outcome.score
        if not app.headless:        # a screenshot run is not a voyage
            save_run(app.world, {'title': self.outcome.title, 'kind': self.outcome.kind,
                                 'crises': score['crises'], 'years': score['years'],
                                 'when': time.strftime('%Y-%m-%d %H:%M')})

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            m = self.app.mouse()
            for b in self.buttons:
                if b.rect.collidepoint(m):
                    b.action()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.app.new_game()
            elif event.key == pygame.K_ESCAPE:
                self.app.to_title()

    def tick(self):
        pass

    def draw(self, surface):
        app, world, out = self.app, self.app.world, self.outcome
        sea(surface)
        meters(surface, app)
        kind = {'ending': 'THE POEM ENDS', 'lost': 'IT IS OVER',
                'silence': 'THE BARDS FALL SILENT'}[out.kind]
        r = wrap_card(surface, (24, 104, T.W - 48, T.H - 104 - 160), kind)
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
            b.draw(surface, T.font(20, bold=True), b.rect.collidepoint(m),
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
    app.new_game()
    k = 0
    while not app.session.over and k < steps:
        if isinstance(app.screen, CrisisScreen):
            if k == 1:
                app.adviser = True
                app.screen.layout()
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
        else:
            break
    if isinstance(app.screen, PaperScreen):
        app.screen.next()
    if isinstance(app.screen, EpilogueScreen):
        shot('90-epilogue')
    else:
        # force an ending for the picture: dither until it is over
        while not app.session.over:
            app.session.timeout()
        app.screen = EpilogueScreen(app)
        shot('90-epilogue')
    pygame.quit()
    return shots
