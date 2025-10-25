Simple Python class with ANSI escape codes for styling and coloring terminal output

---

## Installation

Just copy `pytermcolors.py` into your project folder

---

## Example

```python
from pytermcolors import colorize, Color

print(colorize("Hello World!", fg=Color.FG_CYAN, bg=Color.BG_WHITE, bold=True, italic=True))
print(colorize("Warning!", fg=Color.FG_YELLOW, bold=True, underline=True))
print(colorize("Error!", fg=Color.FG_RED, strike=True))
```

![example](res/example.png)
