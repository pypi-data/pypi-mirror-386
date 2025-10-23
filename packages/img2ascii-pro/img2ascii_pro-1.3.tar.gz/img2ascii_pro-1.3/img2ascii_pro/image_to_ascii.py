from PIL import Image
import argparse
import re

PRESETS = {
    "realistic": "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. ",
    "minimal": "@%#*+=-:. ",
    "block": "█▓▒░ "
}

def map_pixel_to_char(val, chars):
    num_chars = len(chars)
    idx = int((val / 255) * (num_chars - 1))
    return chars[idx]

def rgb_to_ansi(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

def rgb_to_html(r, g, b):
    return f"rgb({r},{g},{b})"

def image_to_ascii(img: Image.Image, width=100, chars=None, scale=0.55):
    w_orig, h_orig = img.size
    height = int((h_orig / w_orig) * width * scale)
    if height <= 0:
        height = 1

    img_small = img.resize((width, height))
    img_rgb = img_small.convert("RGB")
    img_gray = img_small.convert("L")

    pixels_rgb = img_rgb.getdata()
    pixels_gray = img_gray.getdata()

    ascii_lines = []
    for y in range(height):
        row = ""
        for x in range(width):
            p_gray = pixels_gray[y * width + x]
            p_rgb = pixels_rgb[y * width + x]
            char = map_pixel_to_char(p_gray, chars)
            color = rgb_to_ansi(*p_rgb)
            row += f"{color}{char}"
        row += "\033[0m"
        ascii_lines.append(row)
    return ascii_lines, pixels_rgb, width, height

def ascii_to_html(ascii_lines, pixels_rgb, width, height, chars=None):
    html = ['<html><body style="background:black;"><pre style="font-family:monospace; line-height: 80%;">']
    for y in range(height):
        line = ""
        for x in range(width):
            r, g, b = pixels_rgb[y*width + x]
            char = ascii_lines[y][x]
            line += f'<span style="color:{rgb_to_html(r,g,b)}">{char}</span>'
        html.append(line + "<br>")
    html.append("</pre></body></html>")
    return "\n".join(html)
