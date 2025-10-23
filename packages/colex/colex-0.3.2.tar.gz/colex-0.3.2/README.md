# Colex

Library with constants and functions for working with colors

## Installation

Install using either `pip` or `rye`:

```bash
pip install colex
```

```bash
rye install colex
```

## Getting started

```python
import colex  # Every public namespace is available under `colex`

print(colex.RED + "Hello red!")
print("Still red...")
print(colex.RESET, "Back to normal")

# Optionally, you can import submodules or constants like this
from colex import color, style, RESET
print(style.ITALIC + color.GREEN + "Hello italic green" + RESET)

# You may want to use this helper function to have color param at the end
from colex import colorize

print(colorize("Hello blue!", colex.BLUE))

# Note that `colex` is using ANSI escape codes,
# therefore any string can be annotated with `ColorValue`
from colex import ColorValue

my_color: ColorValue = "\x1b[31m"  # The ANSI code for red
print(my_color + "Hello red, again")
```

## Rational

Originally, using colors in my projects was done by simply printing `"\x1b[31m"` and such. Eventually, the color strings were assigned to constants with understandable names, like `RED`. They were put in a seperate module, a `color.py`, that was copied around projects when I needed to do colors. After some time, I found it messy when it ended up looking:

```python
import color
from color import ColorValue

class Color:  # This was used as a mixin component
    color: ColorValue = color.RED  # Too many occurances of "color" for me to stay sane
```

It was then nice in itself to distinguish the namespace `colex` from `color`. I then ended up with:

```python
import colex
from colex import ColorValue

class Color:
    color: ColorValue = colex.RED
```

Having a different namespace was nice, but the main advantage was having `colex` on `PyPI`. This way, I didn't need to copy over a `color.py` file everytime, but I could instead just install it using the desired package manager.

It also became easier to develop `charz`, as the color aspect was split into it's own package.

## Includes

- Annotations
  - `ColorValue`
  - `ColorCode`
  - `HexCode`
- Functions
  - `colorize`
  - `from_ansi`
  - `from_hex`
  - `from_random`
  - `from_rgb`
- Constants
  - `NONE`
  - `RESET`
- Modules with constants
  - `color`
    - HTML/CSS named colors
  - `style`
    - `BOLD`
    - `FAINT`
    - `ITALIC`
    - `UNDERLINE`
    - `BLINK`
    - `RAPID_BLINK`
    - `REVERSE`
    - `CONCEAL`
    - `STRIKETHROUGH`
  
## Versioning

`colex` uses [SemVer](https://semver.org), according to [The Cargo Book](https://doc.rust-lang.org/cargo/reference/semver.html).

## License

MIT
