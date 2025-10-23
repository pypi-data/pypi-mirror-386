from typing import TypeAlias


ColorValue: TypeAlias = str
r"""An `ANSI color`.

String representing an `ANSI escape sequence` used for **colored text in terminal**.

Example values include:
- `"\x1b[31m"` = Red text
- `"\x1b[42m"` = Green background
- `"\x1b[1;34m"` = Bold Blue text
- `"\x1b[38;2;143;188;143m"` = Dark Sea Green text (true color)

The **equality** of the string may vary depending on:
- The **prefix** used:
    - `\x1b`
    - `\033`
- The **color format**:
    - `30-37` = standard colors
    - `40-47` = background standard colors
    - `90-97` = bright colors
    - `100-107` = background bright colors
    - `38;5;N` = 256 colors
    - `48;5;N` = background 256 colors
    - `38;2;R;G;B` = true color
    - `48;2;R;G;B` = background true color
"""
ColorCode: TypeAlias = int | str
"""`ANSI color code`.

An `ANSI color code` can be represented as either:
- An `integer` in either these ranges:
    - `30-37` = standard color
    - `40-47` = standard color background
    - `90-97` = bright color
    - `100-107` = bright color background
- A `string` of either these formats:
    - `38;5;N` = 256 color
    - `48;5;N` = 256 color background
    - `38;2;R;G;B` = true color
    - `48;2;R;G;B` = true color background
"""
HexCode: TypeAlias = str
"""`Hexadecimal color code`.

Should include either `3` or `6` hexadecimal digits, optionally prefixed with a `"#"`.

Example values include:
- `"#ff0000"` = Red (6-digits)
- `"#f00"` = Red (3-digits)
"""
