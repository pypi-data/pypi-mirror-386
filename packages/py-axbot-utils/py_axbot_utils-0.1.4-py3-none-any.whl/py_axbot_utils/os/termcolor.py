import io
import os
import sys
import warnings
from typing import Dict, Iterable, List, Optional

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

Attribute = Literal[
    "bold",
    "dark",
    "underline",
    "blink",
    "reverse",
    "concealed",
    "strike",
]

Highlight = Literal[
    "on_black",
    "on_grey",
    "on_red",
    "on_green",
    "on_yellow",
    "on_blue",
    "on_magenta",
    "on_cyan",
    "on_light_grey",
    "on_dark_grey",
    "on_light_red",
    "on_light_green",
    "on_light_yellow",
    "on_light_blue",
    "on_light_magenta",
    "on_light_cyan",
    "on_white",
]

Color = Literal[
    "black",
    "grey",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "light_grey",
    "dark_grey",
    "light_red",
    "light_green",
    "light_yellow",
    "light_blue",
    "light_magenta",
    "light_cyan",
    "white",
]


def __getattr__(name: str) -> List[str]:
    if name == "__ALL__":
        warnings.warn(
            "__ALL__ is deprecated and will be removed in termcolor 3. Use __all__ instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return ["colored", "cprint"]
    msg = f"module '{__name__}' has no attribute '{name}'"
    raise AttributeError(msg)


ATTRIBUTES: Dict[Attribute, int] = {
    "bold": 1,
    "dark": 2,
    "underline": 4,
    "blink": 5,
    "reverse": 7,
    "concealed": 8,
    "strike": 9,
}

HIGHLIGHTS: Dict[Highlight, int] = {
    "on_black": 40,
    "on_grey": 40,  # Actually black but kept for backwards compatibility
    "on_red": 41,
    "on_green": 42,
    "on_yellow": 43,
    "on_blue": 44,
    "on_magenta": 45,
    "on_cyan": 46,
    "on_light_grey": 47,
    "on_dark_grey": 100,
    "on_light_red": 101,
    "on_light_green": 102,
    "on_light_yellow": 103,
    "on_light_blue": 104,
    "on_light_magenta": 105,
    "on_light_cyan": 106,
    "on_white": 107,
}

COLORS: Dict[Color, int] = {
    "black": 30,
    "grey": 30,  # Actually black but kept for backwards compatibility
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "light_grey": 37,
    "dark_grey": 90,
    "light_red": 91,
    "light_green": 92,
    "light_yellow": 93,
    "light_blue": 94,
    "light_magenta": 95,
    "light_cyan": 96,
    "white": 97,
}


RESET = "\033[0m"


def _can_do_colour(*, no_color: Optional[bool] = None, force_color: Optional[bool] = None) -> bool:
    """Check env vars and for tty/dumb terminal"""
    # First check overrides:
    # "User-level configuration files and per-instance command-line arguments should
    # override $NO_COLOR. A user should be able to export $NO_COLOR in their shell
    # configuration file as a default, but configure a specific program in its
    # configuration file to specifically enable color."
    # https://no-color.org
    if no_color is not None and no_color:
        return False
    if force_color is not None and force_color:
        return True

    # Then check env vars:
    if "ANSI_COLORS_DISABLED" in os.environ:
        return False
    if "NO_COLOR" in os.environ:
        return False
    if "FORCE_COLOR" in os.environ:
        return True

    # Then check system:
    if os.environ.get("TERM") == "dumb":
        return False
    if not hasattr(sys.stdout, "fileno"):
        return False

    try:
        return os.isatty(sys.stdout.fileno())
    except io.UnsupportedOperation:
        return sys.stdout.isatty()


def colored(
    text: object,
    color: Optional[Color] = None,
    on_color: Optional[Highlight] = None,
    attrs: Optional[Iterable[Attribute]] = None,
    *,
    no_color: Optional[bool] = None,
    force_color: Optional[bool] = None,
) -> str:
    """Colorize text.

    Available text colors:
        black, red, green, yellow, blue, magenta, cyan, white,
        light_grey, dark_grey, light_red, light_green, light_yellow, light_blue,
        light_magenta, light_cyan.

    Available text highlights:
        on_black, on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_white,
        on_light_grey, on_dark_grey, on_light_red, on_light_green, on_light_yellow,
        on_light_blue, on_light_magenta, on_light_cyan.

    Available attributes:
        bold, dark, underline, blink, reverse, concealed.

    Example:
        colored('Hello, World!', 'red', 'on_black', ['bold', 'blink'])
        colored('Hello, World!', 'green')
    """
    result = str(text)
    if not _can_do_colour(no_color=no_color, force_color=force_color):
        return result

    fmt_str = "\033[%dm%s"
    if color is not None:
        result = fmt_str % (COLORS[color], result)

    if on_color is not None:
        result = fmt_str % (HIGHLIGHTS[on_color], result)

    if attrs is not None:
        for attr in attrs:
            result = fmt_str % (ATTRIBUTES[attr], result)

    result += RESET

    return result
