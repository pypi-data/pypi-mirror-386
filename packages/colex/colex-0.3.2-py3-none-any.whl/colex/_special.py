from ._annotations import ColorValue


# Placeholder for no color, does not reset ANSI color
NONE: ColorValue = ""
# ANSI reset code
RESET = "\x1b[0m"
