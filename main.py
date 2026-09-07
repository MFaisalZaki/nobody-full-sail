"""Nobody: Full Sail — a game of survival, played over the story space
a scenario engine generated.

    python main.py play                      # the game (pygame)
    python main.py walk                      # a text play-through
    python main.py stats                     # what the library holds
    python main.py shot DIR                  # render every screen to PNG
    python main.py generate [--seconds N]    # grow the library (needs the grow extra)

Every command takes --world DIR (default: worlds/odyssey).
"""

import argparse
import gc
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from nobody import world as worlds        # noqa: E402
from nobody.library import Library         # noqa: E402

NEEDS_GROW = ('growing the library needs the scenario engine: '
              "pip install -e '.[grow]' (polyscene, clingo, the planner)")


def needs_grow(what):
    """The engine is an optional extra: say so, plainly, when it is
    missing — rather than failing inside a solve."""
    import importlib.util
    if importlib.util.find_spec('polyscene') is None:
        sys.exit(f'{what}: {NEEDS_GROW}')


def cmd_generate(args):
    needs_grow('generate')
    from grow.generator import Generator
    world = worlds.load(args.world)
    path = args.out or world.library_path
    library = Library.load(path) if (args.resume and os.path.exists(path)) else None
    gen = Generator(world, horizon=args.horizon, choices=args.choices,
                    branch=args.branch, budget=args.budget,
                    segments=args.segments, seconds=args.seconds,
                    depth=args.depth, close=args.close,
                    close_from=args.close_from, policy=args.policy,
                    workers=args.workers, seed=args.seed, aim=args.aim,
                    aim_from=args.aim_from)
    if args.at is not None:
        library = gen.open(library)
        gen.grow_at(library, args.at)
    else:
        library = gen.grow(library, save=path)
    library.save(path)
    print(f'{path}: {library.stats()}')


def cmd_stats(args):
    world = worlds.load(args.world)
    library = Library.load(args.out or world.library_path)
    print(library.stats())
    print('meta:', library.meta)
    from collections import Counter
    fates = Counter(world.layer.ending([tuple(a) for a in n.fate])
                    for n in library.nodes if n.fate)
    print('endings:', dict(fates))
    layer = world.layer
    menu = Counter(sum(1 for k in n.kids if layer.is_choice(k[0], k[1]))
                   for n in library.nodes if n.kids)
    print('hero choices per node with kids:', dict(sorted(menu.items())))


def cmd_walk(args):
    from nobody.session import Session
    world = worlds.load(args.world)
    library = Library.load(args.out or world.library_path)
    session = Session(world, library, seed=args.seed)
    print(session.intro())
    while not session.over:
        if session.lone() is not None:
            page = session.take()
            print(f'\n{world.masthead}: {page.headline}  (the only road)')
            for line in page.lines:
                print('  ' + line)
            continue
        crisis = session.crisis()
        print(f'\n── {session.clock_text()} · {crisis.title} ──')
        print(crisis.context)
        for i, option in enumerate(crisis.options, 1):
            print(f'  {i}. {option.label}')
        pick = session.random.randrange(len(crisis.options)) if args.auto else None
        if pick is None:
            try:
                pick = int(input('> ')) - 1
            except (ValueError, EOFError):
                pick = 0
        page = session.choose(pick)
        print(f'\n{world.masthead}: {page.headline}')
        for line in page.lines:
            print('  ' + line)
        print('  ' + ' · '.join(f'{f.label} {session.meters[f.meter]}'
                                for f in world.factions))
    print('\n' + session.epilogue().text)


def cmd_play(args):
    from nobody.ui.app import run
    if args.live:
        needs_grow('--live')
    world = worlds.load(args.world)
    path = args.out or world.library_path
    library = Library.load(path)
    run(world, library, timer=args.timer, scale=args.scale, live=args.live,
        library_path=path)


def cmd_shot(args):
    from nobody.ui.app import screenshots
    world = worlds.load(args.world)
    library = Library.load(args.out or world.library_path)
    screenshots(world, library, args.dir, seed=args.seed, scale=args.scale)


def main(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--world', default=os.path.join(HERE, 'worlds', 'odyssey'),
                        help='the world pack directory (default: worlds/odyssey)')
    common.add_argument('--out', default=None,
                        help='the library file (default: the world\'s library.json)')
    p = argparse.ArgumentParser(description=__doc__, parents=[common],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)

    g = sub.add_parser('generate', parents=[common],
                       help='grow the library with the engine')
    g.add_argument('--horizon', type=int, default=8)
    g.add_argument('--choices', type=int, default=3)
    g.add_argument('--branch', type=int, default=2)
    g.add_argument('--budget', type=float, default=60)
    g.add_argument('--segments', type=int, default=None)
    g.add_argument('--seconds', type=float, default=None)
    g.add_argument('--depth', type=int, default=48)
    g.add_argument('--close', choices=['auto', 'always', 'never'], default='auto')
    g.add_argument('--close-from', type=int, default=14)
    g.add_argument('--policy', choices=['walk', 'depth'], default='walk')
    g.add_argument('--workers', type=int, default=1)
    g.add_argument('--seed', type=int, default=None)
    g.add_argument('--resume', action='store_true',
                   help='grow the existing library rather than a fresh one')
    g.add_argument('--aim', default=None,
                   help='an atom of a terminal line every telling must close '
                        'on (reunited: plant homecomings); use with --resume, '
                        'a longer --horizon and --aim-from')
    g.add_argument('--aim-from', type=int, default=0,
                   help='with --aim, grow only nodes at this depth or deeper')
    g.add_argument('--at', type=int, default=None,
                   help='grow exactly this node once, grown or not (0: the '
                        'opening) — for planting a long road')
    g.set_defaults(fn=cmd_generate)

    s = sub.add_parser('stats', parents=[common], help='what the library holds')
    s.set_defaults(fn=cmd_stats)

    w = sub.add_parser('walk', parents=[common], help='a text play-through')
    w.add_argument('--auto', action='store_true', help='choose at random')
    w.add_argument('--seed', type=int, default=None)
    w.set_defaults(fn=cmd_walk)

    y = sub.add_parser('play', parents=[common], help='the game')
    y.add_argument('--timer', type=float, default=None,
                   help='seconds per decision (default: the world\'s)')
    y.add_argument('--scale', type=float, default=None,
                   help='the window as a fraction of the 440x880 world '
                        '(default: as large as fits the screen, clear of '
                        'the dock; the window can be resized either way)')
    y.add_argument('--live', action='store_true',
                   help='when a road runs out, grow the library there with '
                        'the engine (needs clingo and the planner; a '
                        'grounding takes a while) and save it')
    y.set_defaults(fn=cmd_play)

    z = sub.add_parser('shot', parents=[common], help='render every screen to PNG files')
    z.add_argument('dir')
    z.add_argument('--seed', type=int, default=1)
    z.add_argument('--scale', type=float, default=1.0,
                   help='pixels per logical unit (2 for a Retina-sharp picture)')
    z.set_defaults(fn=cmd_shot)

    args = p.parse_args(argv)
    # clingo objects (under generate / --live) must not outlive controlled
    # teardown: every exit path runs through here
    status = 0
    try:
        args.fn(args)
    except KeyboardInterrupt:
        print('interrupted', file=sys.stderr)
        status = 130
    except Exception:
        traceback.print_exc()
        status = 1
    gc.collect()
    sys.exit(status)


if __name__ == '__main__':
    main()
