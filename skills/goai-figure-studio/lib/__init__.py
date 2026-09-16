"""Native-object figure design system: one ink, one type scale, one glyph family.

    from auto_figure.lib import Figure, FAM
    f = Figure(1536, 1024, notes='...')
    z = f.zone('z1', [26, 28, 1484, 402], '文献证据', 'lit')
    f.card_stack('c1', [60, 92, 450, 262], '结构基础', ['低温与高温多晶型'], fam='lit', glyph='polyhedron', container=z)
    f.finish([z]); f.write('scene.json')

Everything is a native text / shape / line element, so super_img2ppt can hand back an editable PPTX and a
vector PDF. No part of a generated raster is ever reused as an image asset.
"""
from .scene import Scene, INK as SCENE_INK, CJK, LATIN
from .motifs import Motifs
from .framework import (Framework, R4, FAM, CONN, ITEM, HAIR, TOKEN_EDGE, TOKEN_FILL, INK, HEAD,
                        W_ZONE, W_CARD, W_TOKEN, W_CONN, W_STEP, W_PILL, W_RULE, pack_pill_rows,
                        TYPE_PT, TYPE_PT_EN, MIN_PRINT_PT, BOLD_ROLES, PRINT_TAG)
from .figure import Figure, R5

__all__ = ['Scene', 'Motifs', 'Framework', 'Figure', 'R4', 'R5', 'FAM', 'CONN', 'ITEM', 'HAIR',
           'TOKEN_EDGE', 'TOKEN_FILL', 'INK', 'HEAD', 'SCENE_INK', 'CJK', 'LATIN',
           'W_ZONE', 'W_CARD', 'W_TOKEN', 'W_CONN', 'W_STEP', 'W_PILL', 'W_RULE', 'pack_pill_rows',
           'TYPE_PT', 'TYPE_PT_EN', 'MIN_PRINT_PT', 'BOLD_ROLES', 'PRINT_TAG']
