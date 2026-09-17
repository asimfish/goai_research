"""Laptop screen for the cover: the published workflow showcase page (2x capture) with the wf01 stage filled by the
simulation frames the page plays there (headless Chrome does not paint the <video>)."""
from pathlib import Path

from PIL import Image

SP = Path('/tmp/claude-0/-root-lyf-goai/580e528f-c5d9-41ea-9492-2349138bcbcf/scratchpad')
MEDIA = Path('/root/lyf/goai/final_round/showcase/media/wf01')
shot = Image.open(SP / 'shots' / 'showcase_2x.png').convert('RGB')
S = shot.size[0] / 1440
# stage area of the wf01 panel in 1x page coordinates (left of the stat tiles, under the primitive chips)
x0, y0, x1, y1 = 343, 622, 1232, 952
gap = 10
fw = (x1 - x0 - gap) / 2
fh = fw * 480 / 640
if fh > (y1 - y0):
    fh = y1 - y0
    fw = fh * 640 / 480
for k, name in enumerate(('s02_third.jpg', 's02_head.jpg')):
    fr = Image.open(MEDIA / name).convert('RGB').resize((round(fw * S), round(fh * S)), Image.LANCZOS)
    shot.paste(fr, (round((x0 + k * (fw + gap)) * S), round(y0 * S)))
shot.save(SP / 'cover' / 'screen.png')
print('screen', shot.size, 'frames', round(fw), 'x', round(fh))
