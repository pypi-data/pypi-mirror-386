from .image_to_ascii import PRESETS, image_to_ascii, ascii_to_html
from PIL import Image
import argparse
import re
def main():
    parser = argparse.ArgumentParser(description="Advanced Colored ASCII Art with presets and HTML output")
    parser.add_argument("input", help="input image path")
    parser.add_argument("--width", type=int, default=100)
    parser.add_argument("--preset", choices=PRESETS.keys(), default="realistic", help="choose character preset")
    parser.add_argument("--scale", type=float, default=0.55)
    parser.add_argument("--invert", action="store_true")
    parser.add_argument("--outfile", type=str, default=None, help="save ASCII to text file")
    parser.add_argument("--html", type=str, help="save output as HTML file")
    args = parser.parse_args()

    img = Image.open(args.input)
    chars = PRESETS[args.preset]
    if args.invert:
        chars = chars[::-1]

    ascii_lines, pixels_rgb, width, height = image_to_ascii(img, width=args.width, chars=chars, scale=args.scale)

    for line in ascii_lines:
        print(line)

    if args.html:
        html_content = ascii_to_html(ascii_lines, pixels_rgb, width, height, chars)
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Saved HTML output to {args.html}")

    if args.outfile:    
        with open(args.outfile, "w", encoding="utf-8") as f:
            for line in ascii_lines:
                clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
                f.write(clean_line + "\n")
        print(f"Saved ASCII art to {args.outfile}")

if __name__ == "__main__":
    main()

