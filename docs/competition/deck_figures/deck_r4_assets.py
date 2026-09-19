"""Deck figures · round 4 — asset sheet D + one standalone illustration for the deck's overview page
(「从研究方案到 OpenLab 工作流与仿真执行（整体方案）」: literature database → structured knowledge → synthesis plan → OpenLab steps).
Same rules as deck_assets_a/c: text-free flat vector cells on white, matched to deck_assets_a's style."""
import json
from pathlib import Path

RUN = Path('/root/lyf/goai/final_round/figstudio/figure-studio-runs')
NAS = '/mnt/nas/data/lyf/goai/deck_figstudio'
STYLE_REF = f'{NAS}/deck_assets_a/outputs/ASSETS/generated/SHEET.png'
CHEM_REF = f'{NAS}/deck_assets_c/outputs/ASSETS/generated/SHEET.png'

CELLS = [
    ('bookbrain', 'an open book lying flat, with a glowing network of connected small nodes rising above it like a constellation (AI reading the literature)'),
    ('papers', 'three overlapping journal-article pages, the top one showing a small crystal-structure figure and a small scatter-plot figure, body text drawn as grey lines'),
    ('notebook', 'an open laboratory notebook: the left page a sketched crystal structure of linked polyhedra, the right page three small round powder swatches (white, pale orange, dark grey) above a few grey lines'),
    ('furnacebench', 'a horizontal tube furnace on a lab bench, with two small reagent bottles, a small crucible and a mortar standing in front of it'),
    ('balance', 'an analytical balance with a glass draft shield, a small weighing boat with white powder on its pan'),
    ('mortar', 'an agate mortar with a pestle, pale powder inside'),
    ('crucible', 'a white corundum crucible with pale powder inside and its lid leaning beside it'),
    ('thermal', 'a temperature-programme icon: a small chart card with a stepped rising line that ends in a flat plateau, a small flame symbol under the card (no numbers)'),
    ('gasline', 'a gas cylinder with a regulator and a hose leading into a horizontal quartz tube (controlled atmosphere)'),
    ('phosphor', 'a small sample dish of powder glowing bright blue-white under a handheld UV lamp held above it (luminescent phosphor)'),
    ('stepboard', 'a clipboard with three rows, each row a filled circle bullet followed by a grey line and a green check mark (an experimental procedure)'),
    ('simlab', 'a computer monitor showing a simple 3D simulation scene of a lab bench with a small robot arm and a grid floor (digital twin of an experiment)'),
]


def sheet_prompt():
    lines = '\n'.join(f'  row {i // 4 + 1}, column {i % 4 + 1}: {d}' for i, (_n, d) in enumerate(CELLS))
    return f"""Use your IMAGE GENERATION tool to output ONE image. Image generation only.

Reference images (look at them first):
- {STYLE_REF} → the EXACT drawing style to match: flat vector illustrations, clean dark outlines, soft flat colours, no gradients, no 3D.
- {CHEM_REF} → the same style applied to chemistry objects; the new sheet must sit next to these without a visible style change.

AN ASSET SHEET for conference-slide figures about an AI system that reads chemistry literature and drives an automated laboratory:
a regular grid of 4 columns × 3 rows of SEPARATE small illustrations on a PURE WHITE background. Every illustration is centred in its own
cell with generous white space around it (nothing touches a neighbour). NO text, NO letters, NO numbers, NO chemical formulas, NO labels,
NO borders, NO grid lines, NO background tint, NO ground shadows.

Colour accents: deep blue, teal, a little orange and green — calm and professional.

The cells, in reading order:
{lines}

Wide 16:9 landscape, white background, nothing else on the sheet."""


def isolab_prompt():
    return f"""Use your IMAGE GENERATION tool to output ONE image. Image generation only.

Reference images (look at them first):
- {STYLE_REF} → the drawing style to match: flat vector, clean dark outlines, soft flat colours, no gradients, no photo-realism.

ONE illustration for a conference slide: an ISOMETRIC cut-away view of a small automated chemistry laboratory room, seen from above at
about 30 degrees, on a PURE WHITE background. Two walls at the back, no ceiling. Along the walls: lab benches with a box furnace, a glovebox
with two round ports, a fume hood, an analytical balance under a small draft shield, racks of sample vials, and a computer workstation with
one monitor. In the centre of the room a robotic arm on a workstation is holding a small vial above a rack. A small mobile cart with
reagent bottles stands near a bench. Clean floor with a subtle tile pattern. No people, NO text, NO letters, NO numbers, NO labels, NO logos.

Colour accents: deep blue, teal, light grey, a little orange — calm and professional. Wide 16:9 landscape, white background, nothing else."""


def main():
    d = RUN / 'deck_assets_d' / 'outputs' / 'ASSETS'
    (d / 'prompts').mkdir(parents=True, exist_ok=True)
    (d / 'generated').mkdir(exist_ok=True)
    (d / 'prompts' / 'SHEET.md').write_text('# deck_assets_d · overview-page asset sheet\n\n## IMAGE PROMPT\n' + sheet_prompt() + '\n', encoding='utf-8')
    (d / 'prompts' / 'ISOLAB.md').write_text('# deck_assets_d · isometric automated laboratory\n\n## IMAGE PROMPT\n' + isolab_prompt() + '\n',
                                             encoding='utf-8')
    rows = [dict(candidate_id='SHEET', prompt_path='outputs/ASSETS/prompts/SHEET.md', target_image_path='outputs/ASSETS/generated/SHEET.png',
                 reference_image_paths=['../deck_assets_a/outputs/ASSETS/generated/SHEET.png', '../deck_assets_c/outputs/ASSETS/generated/SHEET.png'],
                 skip=False, size='16:9'),
            dict(candidate_id='ISOLAB', prompt_path='outputs/ASSETS/prompts/ISOLAB.md', target_image_path='outputs/ASSETS/generated/ISOLAB.png',
                 reference_image_paths=['../deck_assets_a/outputs/ASSETS/generated/SHEET.png'], skip=False, size='16:9')]
    (d / 'prompt-index.json').write_text(json.dumps(dict(stage='ASSETS', project_id='deck_assets_d', grid=[4, 3], cells=[n for n, _ in CELLS],
                                                         candidates=rows, rows=rows), ensure_ascii=False, indent=1), encoding='utf-8')
    print('deck_assets_d:', len(CELLS), 'cells; prompts', len(sheet_prompt()), '/', len(isolab_prompt()), 'chars')


if __name__ == '__main__':
    main()
