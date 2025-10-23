import random

from ._special import RESET
from ._annotations import ColorCode, ColorValue, HexCode


def colorize(
    string: str,
    color: ColorValue,
) -> str:
    """Applies color to the given string. Appends RESET code to the end automatically

    Args:
        string (str): text to paint
        color (ColorValue): paint color

    Returns:
        str: colored string
    """
    return str(color) + string + RESET


def from_ansi(
    foreground: ColorCode | None = None,
    background: ColorCode | None = None,
) -> ColorValue:
    """Creates a color from the given color code. Can be given both a foreground color and background color

    `NOTE`: colors made using this function will not be equivalent to other colors defined in the RGB format regarding ANSI formatting,
    when comparing using the `==` operator, as their string representations will be different

    Args:
        foreground (ColorCode | None, optional): foreground color. Defaults to None.
        background (ColorCode | None, optional): background color. Defaults to None.

    Raises:
        ValueError: both `foreground` and `background` was set to be None

    Returns:
        ColorValue: ANSI color code as str
    """
    if foreground is None and background is None:
        raise ValueError("both param 'foreground' and 'background' was `None`")
    color = ""
    if foreground is not None:
        color += f"\x1b[38;5;{foreground}m"
    if background is not None:
        color += f"\x1b[48;5;{background}m"
    return color


def from_hex(
    foreground: HexCode = "#ffffff",
    background: HexCode | None = None,
) -> ColorValue:
    """Creates a color from the given hex code. Can be given both a foreground color and background color
    The "#" in the hex codes are optional

    Args:
        foreground (HexCode, optional): foreground hex color. Defaults to "#ffffff".
        background (HexCode | None, optional): background hex color. Defaults to None.

    Returns:
        ColorValue: ANSI color code as str
    """
    foreground = foreground.lower()
    if foreground.startswith("#"):
        foreground = foreground.lstrip("#")
    if len(foreground) == 3:
        foreground = "".join([c * 2 for c in foreground])

    red = int(foreground[0:2], 16)
    green = int(foreground[2:4], 16)
    blue = int(foreground[4:6], 16)
    color = "\x1b[38;2;{};{};{}m".format(red, green, blue)

    if background is None:
        return color

    background = background.lower()
    if background.startswith("#"):
        background = background.lstrip("#")
    if len(background) == 3:
        background = "".join([c * 2 for c in background])

    red = int(background[0:2], 16)
    green = int(background[2:4], 16)
    blue = int(background[4:6], 16)
    color += "\x1b[48;2;{};{};{}m".format(red, green, blue)
    return color


def from_random(
    foreground: bool = True,
    background: bool = False,
) -> ColorValue:
    """Creates a random RGB color. Random background color is optional

    Args:
        foreground (bool, optional): whether to colorize the foreground with a random color. Defaults to True.
        background (bool, optional): whether to colorize the background with a random color. Defaults to False.
        bold (bool, optional): applies bold style. Defaults to False.
        reverse (bool, optional): swaps foreground and background. Defaults to False.
        underline (bool, optional): adds an underline. Defaults to False.

    Raises:
        ValueError: both `foreground` and `background` was set to be False

    Returns:
        ColorValue: ANSI color code as str
    """
    if not foreground and not background:
        raise ValueError("either param 'foreground' or 'background' has to be True")
    color = ""
    if foreground:
        color += "\x1b[38;2;{};{};{}m".format(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
    if background:
        color += "\x1b[48;2;{};{};{}m".format(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
    return color


def from_rgb(
    red: int = 0,
    green: int = 0,
    blue: int = 0,
    *,
    background: bool = False,
) -> ColorValue:
    """Creates a color from the given channels, which is red, green and blue. Can be given both a foreground color and background color

    Args:
        red (int, optional): red color channel. Defaults to 0.
        green (int, optional): green color channel. Defaults to 0.
        blue (int, optional): blue color channel. Defaults to 0.
        background (bool, optional): colors background instead of foreground. Defaults to False.

    Returns:
        ColorValue: ANSI color code as str
    """
    layer = 38 if not background else 48
    color = "\x1b[{};2;{};{};{}m".format(layer, red, green, blue)
    return color
