"""Deck figures · round 3 — a third asset sheet with the project's CHEMISTRY workflow (author: unify slides 10/11 with the
deck's chemistry narrative: literature evidence → structured conditions → precursor prediction → synthesis plan → OpenLab)."""
import json
from pathlib import Path

RUN = Path('/root/lyf/goai/final_round/figstudio/figure-studio-runs')
NAS = '/mnt/nas/data/lyf/goai/deck_figstudio'
CAST = f'{NAS}/deck_cast/outputs/CAST/generated/CAST.png'
STYLE_REF = f'{NAS}/deck_assets_a/outputs/ASSETS/generated/SHEET.png'

CELLS = [
    ('litdb', 'a tall stack of journal papers next to a small database cylinder, a magnifier leaning on the stack'),
    ('structure', 'a crystal-structure cluster: three linked tetrahedra with small spheres at the corners and two larger spheres between them'),
    ('phasediagram', 'a ternary phase diagram triangle with a few region lines and one highlighted point'),
    ('condtable', 'a synthesis-condition table: a grid of rows and columns with a small thermometer icon and a small clock icon in the header'),
    ('precursors', 'four reagent jars in a row, each with a different pale powder inside, plain blank labels'),
    ('recipe', 'a ranked list card: three rows, each row a tiny group of three jars followed by a horizontal score bar, the top row highlighted'),
    ('furnace', 'a box furnace with its door open, a glowing crucible inside (solid-state reaction)'),
    ('fluxgrowth', 'a platinum crucible with melt and a few small faceted crystals growing at the bottom (high-temperature solution growth)'),
    ('xrd', 'a page showing a powder X-ray diffraction pattern: a baseline with several sharp peaks of different heights'),
    ('workflow', 'a computer screen showing a workflow graph: about eight small nodes connected by arrows, some nodes ticked green'),
    ('robotlab', 'an automated laboratory workstation: a robot arm holding a vial over a rack of vials next to a balance'),
    ('plan', 'a synthesis-plan document: a page with a small flask icon at the top, three checklist rows and a green check badge'),
]


def prompt():
    lines = '\n'.join(f'  row {i // 4 + 1}, column {i % 4 + 1}: {d}' for i, (_n, d) in enumerate(CELLS))
    return f"""Use your IMAGE GENERATION tool to output ONE image. Image generation only.

Reference images (look at them first):
- {STYLE_REF} → the EXACT drawing style to match: flat vector illustrations, clean dark outlines, soft flat colours, no gradients, no 3D.
- {CAST} → the project's characters (no character is needed on this sheet; it is here only so the style stays in the same family).

AN ASSET SHEET for conference-slide figures about AI-driven inorganic materials synthesis: a regular grid of 4 columns × 3 rows of SEPARATE small illustrations on a PURE WHITE background. Every illustration is centred in its own cell with generous white space around it (nothing touches a neighbour). NO text, NO letters, NO numbers, NO chemical formulas, NO labels, NO borders, NO grid lines, NO background tint, NO ground shadows.

Colour accents: deep blue, teal, a little orange and green — calm and professional, suitable for an academic talk about chemistry.

The cells, in reading order:
{lines}

Wide 16:9 landscape, white background, nothing else on the sheet."""


def main():
    d = RUN / 'deck_assets_c' / 'outputs' / 'ASSETS'
    (d / 'prompts').mkdir(parents=True, exist_ok=True)
    (d / 'generated').mkdir(exist_ok=True)
    (d / 'prompts' / 'SHEET.md').write_text('# deck_assets_c · chemistry asset sheet\n\n## IMAGE PROMPT\n' + prompt() + '\n', encoding='utf-8')
    row = dict(candidate_id='SHEET', prompt_path='outputs/ASSETS/prompts/SHEET.md', target_image_path='outputs/ASSETS/generated/SHEET.png',
               reference_image_paths=['../deck_assets_a/outputs/ASSETS/generated/SHEET.png', '../deck_cast/outputs/CAST/generated/CAST.png'],
               skip=False, size='16:9')
    (d / 'prompt-index.json').write_text(json.dumps(dict(stage='ASSETS', project_id='deck_assets_c', grid=[4, 3],
                                                         cells=[n for n, _ in CELLS], candidates=[row], rows=[row]),
                                                    ensure_ascii=False, indent=1), encoding='utf-8')
    print('deck_assets_c:', len(CELLS), 'cells, prompt', len(prompt()), 'chars')


if __name__ == '__main__':
    main()
