"""Install a finished figure-studio figure into the paper tree and the dashboard media.
usage: install_fig.py --build <img2ppt build dir> --s5 <S5 final png> --project <figstudio project id> --name <figure basename> --figdir <paper figures dir> [--margin 12]
Writes figures/pdf/<name>.pdf (vector, cropped from render/editable.pdf), figures/png/<name>.png (S5 raster cropped), figures/svg/<name>.svg,
keeps the figure it replaces in figures/{pdf,png,svg}_prev/, copies deliverables into figures/figstudio/<project>/deliverables/ and, with --media, mirrors the deliverables into a gallery dir.
A project holds both language variants (<name> and <name>_en), so every record that is not already named after the figure
carries the variant suffix: scene.resolved_en.json, validation_en.json, fonts_en.json, render_en.png."""
import argparse, shutil, json
from pathlib import Path
from PIL import Image, ImageChops
import pypdfium2 as pdfium
ap = argparse.ArgumentParser(); ap.add_argument('--build', required=True); ap.add_argument('--s5', required=True); ap.add_argument('--project', required=True); ap.add_argument('--name', required=True); ap.add_argument('--figdir', required=True); ap.add_argument('--margin', type=int, default=12); ap.add_argument('--media', default=None, help='optional: also mirror deliverables into this gallery dir')
ap.add_argument('--crop', choices=('union', 'render'), default='union',
                help="union: S5 raster ∪ reconstruction render (rounds 1-3, where the rebuild tracked the raster's extent); "
                     'render: the reconstruction only (round 4+, where the rebuild sets its own canvas usage)')
a = ap.parse_args(); B = Path(a.build); F = Path(a.figdir)
M = Path(a.media) / a.project if a.media else None
SFX = '_en' if a.name.endswith('_en') else ''   # without it the English install overwrites the Chinese records
if M: M.mkdir(parents=True, exist_ok=True)
im = Image.open(a.s5).convert('RGB'); W, H = im.size
def bbox_of(img):
    bg = Image.new('RGB', img.size, (255, 255, 255)); diff = ImageChops.difference(img, bg).convert('L').point(lambda v: 255 if v > 24 else 0)
    return diff.getbbox()
# crop box = union of the S5 raster content and the reconstruction's own render (the rebuilt scene may route connectors outside the raster's extent)
x0, y0, x1, y1 = bbox_of(im)
rp = B / 'render' / 'page_001.png'
if rp.exists():
    rim = Image.open(rp).convert('RGB'); sx, sy = W / rim.width, H / rim.height
    rb = bbox_of(rim)
    if rb:
        rx0, ry0, rx1, ry1 = rb
        if a.crop == 'render':
            x0, y0, x1, y1 = rx0 * sx, ry0 * sy, rx1 * sx, ry1 * sy
        else:
            x0, y0, x1, y1 = min(x0, rx0 * sx), min(y0, ry0 * sy), max(x1, rx1 * sx), max(y1, ry1 * sy)
m = a.margin; x0, y0, x1, y1 = max(0, x0 - m), max(0, y0 - m), min(W, x1 + m), min(H, y1 + m)
print(f'content bbox px ({"reconstruction render" if a.crop == "render" else "union of S5 raster and render"})',
      (round(x0), round(y0), round(x1), round(y1)))
for sub in ('pdf', 'png', 'svg'):
    (F / sub).mkdir(exist_ok=True); old = F / sub / f'{a.name}.{sub}'; keep = F / f'{sub}_prev'; keep.mkdir(exist_ok=True)
    if old.exists() and not (keep / old.name).exists(): shutil.copy2(old, keep / old.name); print('kept previous', keep / old.name)
# vector pdf: crop the LibreOffice render of the PPTX page (slide 960 pt wide → scale pt/px)
pdf = pdfium.PdfDocument(str(B / 'render' / 'editable.pdf')); page = pdf[0]; pw, ph = page.get_size(); s = pw / W
l, r, t, b = x0 * s, x1 * s, ph - y0 * s, ph - y1 * s
page.set_mediabox(l, b, r, t); page.set_cropbox(l, b, r, t); pdf.save(str(F / 'pdf' / f'{a.name}.pdf')); print('pdf', F / 'pdf' / f'{a.name}.pdf', round(r - l, 1), 'x', round(t - b, 1), 'pt')
src_png = Image.open(rp).convert('RGB') if (a.crop == 'render' and rp.exists()) else im
sc = src_png.width / W
src_png.crop((round(x0 * sc), round(y0 * sc), round(x1 * sc), round(y1 * sc))).save(F / 'png' / f'{a.name}.png')
print('png', (round((x1 - x0) * sc), round((y1 - y0) * sc)), 'from', 'render' if src_png is not im else 'S5 raster')
shutil.copy2(B / 'svg' / 'page_001.svg', F / 'svg' / f'{a.name}.svg')
D = F / 'figstudio' / a.project / 'deliverables'; D.mkdir(parents=True, exist_ok=True)
for src, dst in ((B / 'editable.pptx', f'{a.name}_editable.pptx'), (B / 'render' / 'editable.pdf', f'{a.name}_editable_render.pdf'), (B / 'render' / 'page_001.png', f'{a.name}_render_libreoffice.png'), (B / 'scene.resolved.json', f'scene.resolved{SFX}.json'), (B / 'validation.json', f'validation{SFX}.json'), (B / 'fonts.json', f'fonts{SFX}.json')):
    shutil.copy2(src, D / dst)
if M:
    for src, dst in ((B / 'editable.pptx', f'{a.name}_editable.pptx'), (F / 'svg' / f'{a.name}.svg', f'{a.name}_editable.svg'), (F / 'pdf' / f'{a.name}.pdf', f'{a.name}_vector.pdf'), (B / 'render' / 'page_001.png', f'render{SFX}.png')):
        shutil.copy2(src, M / dst)
print('installed', a.name, '→', F, *(('and media', M) if M else ()))
