"""The window: how big, where, and how sharp.

The screens draw a 440x880 world. This opens a window for it that fits
the screen — under the menu bar, clear of the dock or the taskbar — and
asks for a high-DPI surface, so that on a Retina display the game gets
two device pixels per logical unit to draw on rather than one that the
system then stretches. The window can be resized afterwards; the app
letterboxes."""

import ctypes
import ctypes.util
import glob
import os

import pygame

from . import theme as T

#: what the system puts above a window's content: a title bar (and, in
#: the fit, a little air around the whole thing)
TITLE_BAR = 28
AIR = 16


def usable_bounds(display=0):
    """The part of the screen a window may use, as (x, y, w, h) in
    points: SDL's usable bounds, which exclude the menu bar, the dock
    and the taskbar. pygame does not expose the call, so it is reached
    through ctypes in the SDL that pygame loaded; failing that, the
    desktop with a tenth shaved off the top and the bottom."""
    try:
        return _sdl_usable_bounds(display)
    except Exception:
        sizes = pygame.display.get_desktop_sizes()
        w, h = sizes[display] if display < len(sizes) else (T.W, T.H)
        return 0, h // 10, w, h - 2 * (h // 10)


class _SDLRect(ctypes.Structure):
    _fields_ = [('x', ctypes.c_int), ('y', ctypes.c_int),
                ('w', ctypes.c_int), ('h', ctypes.c_int)]


def _sdl_libraries():
    """Where a pygame wheel keeps its SDL2, per platform, then whatever
    the system has."""
    root = os.path.dirname(pygame.__file__)
    found = (glob.glob(os.path.join(root, '.dylibs', 'libSDL2-*.dylib'))
             + glob.glob(os.path.join(root, '..', 'pygame.libs', 'libSDL2-*.so*'))
             + glob.glob(os.path.join(root, '..', 'pygame_ce.libs', 'libSDL2-*.so*'))
             + glob.glob(os.path.join(root, 'SDL2.dll')))
    system = ctypes.util.find_library('SDL2')
    if system:
        found.append(system)
    return found


def _sdl_usable_bounds(display):
    for path in _sdl_libraries():
        try:
            sdl = ctypes.CDLL(path)
            fn = sdl.SDL_GetDisplayUsableBounds
        except (OSError, AttributeError):
            continue
        fn.argtypes = [ctypes.c_int, ctypes.POINTER(_SDLRect)]
        fn.restype = ctypes.c_int
        r = _SDLRect()
        if fn(display, ctypes.byref(r)) == 0 and r.w > 0 and r.h > 0:
            return r.x, r.y, r.w, r.h
    raise OSError('SDL_GetDisplayUsableBounds is out of reach')


def fit_scale(usable, top=TITLE_BAR + AIR, side=AIR):
    """The largest scale, 1.0 at most, at which the whole window — its
    title bar included — fits inside `usable` (x, y, w, h)."""
    _, _, w, h = usable
    return max(0.1, min(1.0, (h - top) / T.H, (w - side) / T.W))


def open_window(title, scale=None, display=0):
    """A resizable, high-DPI window showing the logical world at
    `scale` — or, when none is asked for, as large as fits the screen's
    usable area. Placed inside that area, so nothing starts under the
    dock."""
    usable = usable_bounds(display)
    if scale is None:
        scale = fit_scale(usable)
    size = (max(1, round(T.W * scale)), max(1, round(T.H * scale)))
    ux, uy, uw, uh = usable
    pos = (ux + max(0, (uw - size[0]) // 2),
           uy + TITLE_BAR + max(0, (uh - TITLE_BAR - size[1]) // 2))
    window = pygame.Window(title, size, position=pos, resizable=True,
                           allow_high_dpi=True)
    window.minimum_size = (T.W // 2, T.H // 2)
    return window
