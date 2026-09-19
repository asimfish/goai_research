"""Single-value ring meter (the deck's teal on a light track), transparent hole and background — a picture asset with a
declared provenance; the number itself stays native text on the slide.   usage: donut.py <fraction> <out.png>"""
import sys

from PIL import Image, ImageDraw

frac = float(sys.argv[1])
out = sys.argv[2]
S = 8                                   # supersampling
N = 360 * S
im = Image.new('RGBA', (N, N), (0, 0, 0, 0))
dr = ImageDraw.Draw(im)
pad, ring = 6 * S, 52 * S
box = [pad, pad, N - pad, N - pad]
dr.pieslice(box, 0, 360, fill=(226, 232, 240, 255))                       # track
dr.pieslice(box, -90, -90 + 360 * frac, fill=(21, 96, 130, 255))          # value, from 12 o'clock
hole = [pad + ring, pad + ring, N - pad - ring, N - pad - ring]
dr.ellipse(hole, fill=(0, 0, 0, 0))
im = im.resize((360, 360), Image.LANCZOS)
im.save(out)
print(out, im.size)
