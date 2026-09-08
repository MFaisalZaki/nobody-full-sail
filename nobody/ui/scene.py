"""The stage: a board, drawn. Given a world's Scene (which island, what
stands on it, who is there, the crew, the vessel) and the time, this
composes the sprites into one moving picture in a rectangle of the
crisis card — the same state the meters along the top and the caption
below it describe, only looked at.

The sky reads the gods' meter: sun when they are pleased, cloud as
they sour, lightning and rain at the floor. The sea rises with it,
and with the sea god's wrath. The land is a ribbon whose top edge is
hills; the crew are as many figures as the band says; the ship, the
raft or the wreckage is what the board says it is."""

import math

from . import draw as D
from . import sprites as S
from . import theme as T
from . import wave as W
from .wave import Wave

#: how many men stand on the beach for each band of the crew meter
CREW = {'full': 5, 'thinned': 3, 'remnant': 1, 'alone': 0}


class Stage:
    """One board's picture, in a rectangle: built once per crisis, drawn
    every frame."""

    def __init__(self, scene, rect):
        self.scene = scene
        self.x0, self.y0, self.w, self.h = rect
        self.rect = rect
        self.s = min(self.w / 392, self.h / 290)     # the sprite scale
        self.hero_h = 44 * self.s
        self.horizon = self.y0 + 0.56 * self.h
        self.shore = self.x0 + (0.4 * self.w if scene.setting == 'shore' else 0)
        rise = 0.24 if scene.landmark and scene.landmark[0] == 'headland' else 0.15
        L = self.x0 + self.w + 40 - self.shore
        self.hills = (Wave.rise(-rise * self.h, L) + Wave(0.02 * self.h, 2.5 / L, 0.0, 1.0)
                      + Wave(0.012 * self.h, 6.0 / L, 0.0, 2.3))
        self.land_top = self.horizon + 0.04 * self.h
        size = 0.36 * self.h
        self.ship = D.Ship(size)
        self.wavelength = 0.24 * self.w

    # -- geometry --

    def ground(self, x):
        """Where the land is under x (the beach's own height at the shore)."""
        return self.land_top + self.hills(max(0.0, x - self.shore))

    def on_land(self, f):
        """The point on the ground at fraction `f` of the stage's width."""
        x = self.x0 + f * self.w
        return x, self.ground(x)

    def sea_row(self, r=1, rows=5):
        return self.horizon - 0.02 * self.h + 0.5 * self.h * (r + 0.5) / rows

    def storm_of(self, mood):
        """0 (a clear day) to 1 (the gods at the floor)."""
        storm = 1.0 - mood
        if 'wrathful' in self.scene.marks:
            storm = max(storm, 0.45)
        return max(0.0, min(1.0, storm))

    # -- drawing --

    def draw(self, c, t, mood=1.0):
        sc = self.scene
        storm = self.storm_of(mood)
        with c.clip(self.rect):
            if sc.setting == 'underworld':
                self.underworld(c, t)
            elif sc.setting == 'hall':
                self.hall(c, t)
            elif sc.setting == 'cave':
                self.cave(c, t)
            else:
                self.sky(c, t, storm)
                self.water(c, t, storm)
                if sc.setting == 'shore':
                    self.land(c, t)
                self.landmark(c, t)
                self.cast(c, t)
                if sc.setting == 'shore':
                    self.party(c, t)
                elif sc.vessel in ('ship', 'raft'):
                    self.party(c, t, x=self.deck, motion=self.ride, aboard=True)
                else:
                    self.swimmers(c, t)
                if storm > 0.75:
                    S.rain(c, (self.x0, self.y0, self.w, 0.9 * self.h), t)

    def sky(self, c, t, storm):
        x0, y0, w, h = self.rect
        always_sun = bool(self.scene.landmark and self.scene.landmark[1].get('sun'))
        if storm < 0.5 or always_sun:
            r = (0.09 if always_sun else 0.06) * h
            fx = 0.84 if always_sun else {'sea': 0.6, 'harbour': 0.5}.get(self.scene.setting, 0.72)
            S.sun(c, x0 + fx * w, y0 + 0.17 * h, r, t)
        dark = storm > 0.6
        S.clouds(c, (x0, y0, w, h), t, fill=T.INK if dark else T.PAPYRUS, storm=storm)
        if dark:
            S.lightning(c, x0 + 0.3 * w, y0 + 0.3 * h, 0.18 * h, t)
            S.lightning(c, x0 + 0.62 * w, y0 + 0.28 * h, 0.14 * h, t, phase=2.4)

    def water(self, c, t, storm):
        x0, y0, w, h = self.rect
        amp, speed = 2 + 6 * storm, 0.5 + 1.5 * storm
        self.swell = D.sea_wave(amp, self.wavelength, speed, row=1)
        D.waves(c, (x0, self.horizon - 0.02 * h, w, 0.5 * h), T.INK_SOFT, rows=5, amp=amp,
                wavelength=self.wavelength, width=1, t=t, speed=speed, texture=0.25)
        self.vessel(c, t)

    def vessel(self, c, t):
        sc = self.scene
        if sc.setting == 'shore':
            x = self.x0 + 0.15 * self.w
        else:
            x = self.x0 + 0.5 * self.w
        y = self.sea_row(1) - 0.12 * self.h
        ride = W.Motion(dy=self.swell.fix(x - self.x0),
                        angle=self.swell.slope().fix(x - self.x0).scaled(0.2), pivot=(x, y))
        self.ride, self.deck = ride, (x, y)
        if sc.vessel == 'ship':
            self.ship.render(c, (x, y), T.INK, T.PAPYRUS_DK, t, ride)
        elif sc.vessel == 'raft':
            S.raft(c, x, y + 0.05 * self.h, 0.3 * self.h, t, ride)
        elif sc.vessel == 'wreck' and sc.setting == 'shore':
            S.wreck(c, self.shore + 0.1 * self.w, self.ground(self.shore + 0.1 * self.w),
                    0.28 * self.h, t)
        elif sc.vessel == 'wreck':
            S.wreck(c, x - 0.12 * self.w, y + 0.12 * self.h, 0.24 * self.h, t, ride)

    def land(self, c, t):
        """The land: a ribbon from the shore to the edge whose top is
        the hills, and a beach that slopes down into the water."""
        x0, y0, w, h = self.rect
        bottom = y0 + h + 10
        L = x0 + w + 40 - self.shore
        # the shoreline: down into the sea leftward, convex, with a ripple
        beach = (Wave.rise(0.52 * h, -0.44 * w) + Wave.bulge(-0.07 * h, -0.44 * w)
                 + Wave(0.012 * h, 3.0 / (0.44 * w), 0.0, 0.8))
        for top, length in ((Wave.flat(self.land_top) + self.hills, L),
                            (Wave.flat(self.land_top) + beach, -0.44 * w)):
            centre = Wave.flat(bottom / 2) + top.scaled(0.5)
            half = Wave.flat(bottom / 2) + top.scaled(-0.5)
            W.Ribbon(centre, half, length, 'x', (self.shore, 0), step=6).render(
                c, T.PAPYRUS_DK, t, 0)
            for k in (1, 2, 3):        # the lie of the land, in faint contours
                W.Trail(top + Wave.flat(0.11 * k * h) + Wave(0.01 * k * h, 1.7 / abs(length), 0.0, k),
                        length, 'x', (self.shore, 0), step=6).render(c, T.DUNE, t, 1)
            W.Trail(top, length, 'x', (self.shore, 0), step=6).render(c, T.INK, t, 1)

    # -- what stands on the land --

    def landmark(self, c, t):
        mark = self.scene.landmark
        if not mark:
            return
        name, props = mark
        fn = getattr(self, 'mark_' + name.replace('-', '_'), None)
        if fn:
            fn(c, t, props)

    def mark_walls(self, c, t, props):
        x, y = self.on_land(0.97)
        S.walls(c, x, y - 0.02 * self.h, 0.36 * self.w, 0.22 * self.h, t,
                fallen=props.get('fallen'))
        if props.get('horse'):
            hx, hy = self.on_land(0.6)
            riders = 0
            if props.get('inside'):
                riders = 1 + CREW[self.scene.crew]
            S.horse(c, hx, hy, 0.21 * self.h, t, riders=riders)

    def mark_town(self, c, t, props):
        for f, w in ((0.72, 0.08), (0.84, 0.1), (0.95, 0.07)):
            x, y = self.on_land(f)
            S.house(c, x, y, w * self.w, 0.16 * self.h, t)
        if props.get('raided'):
            x, y = self.on_land(0.84)
            S.smoke(c, x, y - 0.2 * self.h, 0.35 * self.h, t)

    def mark_lotus(self, c, t, props):
        for f, k in ((0.68, 0), (0.92, 1)):
            x, y = self.on_land(f)
            S.lotus(c, x, y, 0.12 * self.h, t, phase=k * 1.4)

    def mark_cave(self, c, t, props):
        x, y = self.on_land(0.93)
        S.cave(c, x, y, 0.28 * self.w, 0.3 * self.h, t, shut=props.get('shut'))

    def mark_bronze_wall(self, c, t, props):
        x, y = self.on_land(0.84)
        S.bronze_wall(c, x, y - 0.02 * self.h, 0.5 * self.w, 0.16 * self.h, t)

    def mark_cliffs(self, c, t, props):
        x0, y0, w, h = self.rect
        top = y0 + 0.3 * h
        H = h - 0.3 * h + 10
        for side, edge in ((1, x0), (-1, x0 + w)):
            rough = Wave(0.03 * w, 2.5 / H, 0.0, 1.0 if side > 0 else 2.2) + Wave(0.012 * w, 6.0 / H, 0.0, 0.4)
            centre = Wave.flat(edge + side * 0.05 * w) + rough
            W.Ribbon(centre, 0.17 * w, H, 'y', (0, top), step=6).render(c, T.INK, t, 0)
        self.cliff_top = top

    def mark_hall(self, c, t, props):
        pass

    def mark_trench(self, c, t, props):
        pass

    def mark_rocks(self, c, t, props):
        x0, y0, w, h = self.rect
        S.rock(c, x0 + 0.14 * w, self.horizon + 0.08 * h, 0.26 * w, 0.24 * h, t, T.INK, 0.3)

    def mark_headland(self, c, t, props):
        pass

    def mark_tree(self, c, t, props):
        x, y = self.on_land(0.86)
        S.tree(c, x, y, 0.42 * self.h, t)

    def mark_court(self, c, t, props):
        pass

    def mark_home(self, c, t, props):
        pass

    # -- the residents --

    def cast(self, c, t):
        for name, props in self.scene.cast:
            fn = getattr(self, 'cast_' + name.replace('-', '_'), None)
            if fn:
                fn(c, t, props)

    def cast_spearmen(self, c, t, props):
        for k in range(props.get('n', 3)):
            x, y = self.on_land(0.68 + 0.07 * k)
            S.figure(c, x, y, 0.9 * self.hero_h, t, facing=-1, phase=k * 1.1, prop='spear')

    def cast_lotus_eaters(self, c, t, props):
        for k in range(props.get('n', 3)):
            x, y = self.on_land(0.66 + 0.11 * k)
            S.figure(c, x, y, 0.9 * self.hero_h, t, facing=-1, phase=k * 1.3, pose='lie',
                     arms='raised', prop='flower')

    def cast_cyclops(self, c, t, props):
        if props.get('inside'):
            x, y = self.x0 + 0.66 * self.w, self.y0 + 0.86 * self.h
        else:
            x, y = self.on_land(0.72)
        S.cyclops(c, x, y, 2.3 * self.hero_h, t, facing=-1, blind=props.get('blind'))

    def cast_aeolus(self, c, t, props):
        x, y = self.on_land(0.74)
        S.figure(c, x, y, 1.1 * self.hero_h, t, facing=-1, arms='out', gown=True, beard=True,
                 prop='bag' if props.get('bag') else None)

    def cast_winds(self, c, t, props):
        x0, y0, w, h = self.rect
        S.winds(c, (x0, y0 + 0.08 * h, w, 0.36 * h), t, loose=props.get('loose'))

    def cast_giants(self, c, t, props):
        x0, y0, w, h = self.rect
        top = getattr(self, 'cliff_top', y0 + 0.3 * h)
        for k, f in enumerate((0.1, 0.9)):
            x = x0 + f * w
            S.giant(c, x, top, 1.5 * self.hero_h, t, facing=1 if f < 0.5 else -1, phase=k * 2.0)
            S.falling_rock(c, x + (0.13 if f < 0.5 else -0.13) * w, top - 0.2 * h,
                           self.horizon - top + 0.25 * h, 0.03 * h, t, phase=k * 2.0)

    def cast_circe(self, c, t, props):
        x, y = self.x0 + 0.645 * self.w, self.y0 + 0.86 * self.h
        S.witch(c, x, y, 1.05 * self.hero_h, t, facing=-1, cup=props.get('cup', True))

    def cast_swine(self, c, t, props):
        for k in range(props.get('n', 3)):
            S.pig(c, self.x0 + (0.41 + 0.05 * k) * self.w, self.y0 + 0.86 * self.h,
                  0.45 * self.hero_h, t, facing=1, phase=k * 0.9)

    def cast_shades(self, c, t, props):
        y = self.y0 + 0.84 * self.h
        for k in range(props.get('n', 5)):
            S.shade(c, self.x0 + (0.58 + 0.085 * k) * self.w, y, 0.95 * self.hero_h, t,
                    phase=k * 1.4, facing=-1, prop='staff' if k == 0 and props.get('prophet') else None)

    def cast_sirens(self, c, t, props):
        x0, y0, w, h = self.rect
        for k, f in enumerate((0.1, 0.19)):
            S.siren(c, x0 + f * w, self.horizon - 0.15 * h, 0.85 * self.hero_h, t, facing=1,
                    singing=props.get('singing', True), phase=k * 1.7)

    def cast_scylla(self, c, t, props):
        x0, y0, w, h = self.rect
        S.scylla(c, x0 + 0.9 * w, self.horizon - 0.02 * h, 2.4 * self.hero_h, t, facing=-1)

    def cast_charybdis(self, c, t, props):
        x0, y0, w, h = self.rect
        S.whirlpool(c, x0 + 0.76 * w, self.horizon + 0.34 * h, 0.1 * w, t)

    def cast_cattle(self, c, t, props):
        n = props.get('n', 4)
        if props.get('eaten'):
            x, y = self.on_land(0.7)
            S.bones(c, x, y, 0.5 * self.hero_h, t)
            S.smoke(c, x + 0.1 * self.w, y - 0.05 * self.h, 0.4 * self.h, t)
            n = 1
        for k in range(n):
            x, y = self.on_land(0.66 + 0.09 * k)
            S.cow(c, x, y, 0.75 * self.hero_h, t, facing=1 if k % 2 else -1, phase=k * 1.2)

    def cast_calypso(self, c, t, props):
        x, y = self.on_land(0.78)
        S.nymph(c, x, y, 1.05 * self.hero_h, t, facing=-1)

    def cast_alcinous(self, c, t, props):
        x, y = self.x0 + 0.835 * self.w, self.y0 + 0.86 * self.h
        W.Ribbon(Wave.flat(0.0), 0.05 * self.w, -0.14 * self.h, 'y', (x + 0.02 * self.w, y),
                 step=20).render(c, T.INK_SOFT, t, 0)
        S.figure(c, x, y, 1.05 * self.hero_h, t, facing=-1, pose='sit', arms='out', gown=True,
                 beard=True, prop='staff')

    def cast_nausicaa(self, c, t, props):
        x, y = self.x0 + 0.645 * self.w, self.y0 + 0.86 * self.h
        S.figure(c, x, y, self.hero_h, t, facing=-1, arms='raised', gown=True, fair=True)
        if props.get('ball', True):
            hop = W.Motion(dy=Wave.bounce(-0.14 * self.h, 0.0, 4, 2.4, 0.0, 0.0),
                           scale=Wave.bounce(0.25, 0.0, 3, 2.4, 0.0, 0.85), pivot=(x - 0.13 * self.w, y))
            W.Orbit.ellipse((x - 0.13 * self.w, y - 0.03 * self.h), 0.03 * self.h, 0.03 * self.h).render(
                c, T.TERRACOTTA, t, 0, hop)

    def cast_suitors(self, c, t, props):
        y = self.y0 + 0.86 * self.h
        for k in range(props.get('n', 4)):
            x = self.x0 + (0.42, 0.485, 0.61, 0.675)[k % 4] * self.w
            if props.get('dead'):
                S.figure(c, x, y, 0.95 * self.hero_h, t, facing=1, pose='lie', phase=k)
            else:
                S.figure(c, x, y, 0.95 * self.hero_h, t, facing=-1, pose='sit', arms='cup',
                         prop='cup', phase=k * 1.3)

    def cast_penelope(self, c, t, props):
        x, y = self.x0 + 0.85 * self.w, self.y0 + 0.86 * self.h
        S.loom(c, x + 0.02 * self.w, y, 0.28 * self.h, t)
        S.figure(c, x - 0.065 * self.w, y, self.hero_h, t, facing=1, arms='out', gown=True, fair=True)

    # -- the hero and the crew --

    def party(self, c, t, floor=None, x=None, motion=None, aboard=False):
        sc, hero = self.scene, self.scene.hero
        if hero.get('inside') == 'horse':
            return
        n = CREW.get(sc.crew, 0)
        if aboard:
            hx, hy = x
            s = self.ship.s                      # half the ship: the hull runs -0.85s .. 0.75s
            self.hero_figure(c, hx + 0.08 * s, hy + 0.04 * s, t, motion)
            for k in range(min(n, 4)):
                S.figure(c, hx - (0.2 + 0.19 * k) * s, hy + 0.06 * s, 0.55 * self.hero_h, t,
                         facing=1, pose='sit', phase=k * 0.9, motion=motion)
            return
        if x is None:
            hx = self.shore + 0.14 * self.w if sc.setting == 'shore' else self.x0 + 0.3 * self.w
        else:
            hx = x
        hy = self.ground(hx) if floor is None else floor
        if hero.get('kept'):
            hx = self.shore + 0.05 * self.w
            hy = self.ground(hx)
        self.hero_figure(c, hx, hy, t, motion)
        pose = hero.get('crew-pose', 'stand')
        if pose == 'none':
            n = 0
        for k in range(n):
            cx = hx - (0.05 + 0.04 * k) * self.w
            if sc.setting == 'shore':
                cx = max(cx, self.shore + 0.015 * self.w)
            cy = self.ground(cx) if floor is None else floor
            S.figure(c, cx, cy, 0.9 * self.hero_h, t, facing=1, phase=k * 1.1, pose=pose,
                     arms='raised' if pose == 'lie' else 'down', prop='flower' if pose == 'lie' else None,
                     motion=motion)

    def swimmers(self, c, t):
        """No vessel and open water: heads and arms above the swell,
        the hero first, riding it."""
        row = self.sea_row(1)
        n = CREW.get(self.scene.crew, 0)
        with c.clip((self.x0, self.y0, self.w, row - self.y0 + 0.01 * self.h)):
            for k in range(n + 1):
                x = self.x0 + (0.5 - 0.06 * k) * self.w
                h = self.hero_h if k == 0 else 0.9 * self.hero_h
                bob = W.Motion(dy=self.swell.fix(x - self.x0), pivot=(x, row))
                S.figure(c, x, row + 0.42 * h, h, t, facing=1, arms='raised' if k == 0 else 'up',
                         crest=k == 0, phase=k * 1.3, motion=bob)

    def hero_figure(self, c, x, y, t, motion=None):
        hero = self.scene.hero
        disguised = hero.get('disguised')
        prop = hero.get('prop') or ('stick' if disguised else 'spear')
        arms = 'raised' if prop == 'bow' else ('out' if hero.get('below') else 'down')
        S.figure(c, x, y, self.hero_h, t, facing=hero.get('facing', 1), pose=hero.get('pose', 'stand'),
                 arms=arms, crest=not disguised, prop=prop, lean=0.3 if disguised else 0.0, motion=motion)
        if hero.get('bound'):
            for k in range(3):
                yy = y - (0.35 + 0.15 * k) * self.hero_h
                W.stroke(c, (x - 0.12 * self.hero_h, yy), (x + 0.12 * self.hero_h, yy), T.INK_SOFT, 1.5,
                         t=t, motion=motion)

    # -- the other stages --

    def cave(self, c, t):
        x0, y0, w, h = self.rect
        floor = y0 + 0.86 * h
        props = self.scene.landmark[1] if self.scene.landmark else {}
        S.cave(c, x0 + 0.5 * w, floor, 0.94 * w, 0.72 * h, t, shut=props.get('shut'), inside=True)
        W.stroke(c, (x0, floor), (x0 + w, floor), T.INK, 1.5, t=t)
        self.cast(c, t)
        self.party(c, t, floor=floor, x=x0 + 0.32 * w)

    def hall(self, c, t):
        x0, y0, w, h = self.rect
        floor = y0 + 0.86 * h
        for k in range(4):
            S.column(c, x0 + (0.36 + 0.19 * k) * w, floor, 0.66 * h, 0.035 * w, t)
        W.Ribbon(Wave.flat(0.0), 0.03 * h, 0.66 * w, 'x', (x0 + 0.32 * w, y0 + 0.17 * h), step=40).render(
            c, T.INK, t, 0)
        W.stroke(c, (x0, floor), (x0 + w, floor), T.INK, 1.5, t=t)
        name = self.scene.landmark[0] if self.scene.landmark else ''
        if name == 'hall':
            S.smoke(c, x0 + 0.835 * w, floor - 0.06 * h, 0.5 * h, t, n=2)
            W.Orbit.ellipse((x0 + 0.835 * w, floor - 0.03 * h), 0.05 * w, 0.02 * h).render(c, T.INK, t, 0)
        self.cast(c, t)
        self.party(c, t, floor=floor, x=x0 + 0.22 * w)

    def underworld(self, c, t):
        x0, y0, w, h = self.rect
        floor = y0 + 0.84 * h
        W.Ribbon(Wave.flat(0.0), 0.3 * h, 1.2 * w, 'x', (x0 - 0.1 * w, floor + 0.3 * h), step=40).render(
            c, T.INK_SOFT, t, 0)
        S.clouds(c, (x0, y0, w, h), t, fill=T.INK, line=T.INK, storm=0.5, phase=1.0)
        tx = x0 + 0.46 * w
        W.Ribbon(Wave.flat(0.0), 0.05 * w, 0.06 * h, 'y', (tx, floor - 0.03 * h), step=20).render(
            c, T.INK, t, 0)
        W.Ribbon(Wave.flat(0.0), 0.035 * w, 0.03 * h, 'y', (tx, floor - 0.015 * h), step=20).render(
            c, T.WINE, t, 0)
        self.cast(c, t)
        self.party(c, t, floor=floor, x=x0 + 0.34 * w)
