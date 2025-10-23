# img2ascii_pro
Convert any image into colorful ASCII art directly in your terminal or export it as HTML or text

---

## Installation
Install from **PyPI** using:
```bash
pip install img2ascii-pro
```
---
Convert any image to ASCII art:
img2ascii_pro myphoto.jpg
---
Command Options

| Option                 | Description                                                   |
| ---------------------- | ------------------------------------------------------------- |
| `--width`              | Set the output width (default: 100)                           |
| `--preset`             | Choose a character preset: `realistic`, `minimal`, or `block` |
| `--invert`             | Invert the character brightness for dark/light reversal       |
| `--html output.html`   | Save the result as a colored HTML file                        |
| `--outfile output.txt` | Save the ASCII result to a plain text file                    |
---
Import and Use in Python

from PIL import Image
from img2ascii_pro import *

img = Image.open("photo.jpg")
ascii_lines, _, _, _ = image_to_ascii(img, width=100, chars=PRESETS["block"])

for line in ascii_lines:
    print(line)
