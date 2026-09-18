#!/usr/bin/env python3
"""Explainer slides for the layer-by-layer knowledge forest, built on the competition deck template.

Four native slides on the template's content layout (title + the two blue title-bar rectangles every content
slide carries), one idea per slide and little text:

1. how the forest is assembled — three one-line statements (data → structure → animation) beside two schematic
   frames (level 2 and level 8) that show cards on the frame collapsing into the dot tree
2. levels 1–4 and 3. levels 5–8 — one schematic frame per level in a 2 × 2 grid, a header and one line each
4. a reference table: level / what is added / source file / what it hangs on, plus the card grammar

The frames are the animation page rendered with `?schematic=1` (blank card blocks + curves to parents, no
text), so the slides read as diagrams; the full-text posters and the GIF carry the labels.  All other template
slides are dropped from the output.

usage: deck_explainer.py --deck template.pptx --img <dir with deck_S1..8.png> --out out.pptx [--model 10] [--font 微软雅黑]
"""
import argparse
import copy
import re
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main', 'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
NAVY, TEAL, ORANGE, INK, MUTED, LINE, PURPLE = '154A97', '156082', 'E97132', '13202C', '5A6A7A', 'D7DEE6', '7A4FD6'
SLIDE_W = 13.333
ASPECT = 2.013  # width / height of the schematic frames

# (numeral, name, count, one line under the picture, [新增, 来源, 挂法] for the table)
LEVELS = [
    ('一', '调研主题与预期目标', 13, '5 个预期目标 + 8 个子主题，全部挂在中心「调研主题」',
     ['5 个预期目标 Q1–Q5、8 个 MECE 子主题', '正式案例 inputs/scope.md（研究者开始前自己的问题树）', '挂在中心；目标按它服务的子主题方向排布']),
    ('二', '文献树八分支', 8, '八个分支 A–H 各占一个扇区；上一级收缩为圆点',
     ['A–H：身份 / 结构 / 替代 / 路线 / 变量 / 表征 / 失败 / 配方篮子', '证据包 taxonomy.md §2（MECE 切分）', '挂在中心，每个分支一个扇区；从这一级起已展开的级收缩为圆点']),
    ('三', '叶节点', 35, '35 个叶节点挂到所属分支；描边色 = 证据等级',
     ['35 个叶节点，每个是一类证据主张', 'taxonomy.md 各叶的判定 / 支撑 key', '挂在所属分支的圆点上，同一扇区内按顺序排开']),
    ('四', '文献', 51, '51 篇文献挂到它支撑的叶节点；实心橙 = 目标相直接报道',
     ['51 篇通过引用闸门的文献', 'references.bib + papers.jsonl（DOI、题名、年份、期刊）', '挂在它支撑的第一个叶节点；颜色 = 证据距离（D0 … X）']),
    ('五', '元素与化合物', 41, '12 个元素 + 29 个化合物挂到定义它的叶或分支；紫虚线 = AI 假设目标',
     ['12 个元素、29 个化合物 / 相', '条件总表产物字段 + 人工别名表；元素由化学式解析', '挂在定义它的叶节点或分支；紫虚线 = AI 假设目标，尚未合成']),
    ('六', '合成路线与条件记录', 35, '6 条路线 + 29 条条件记录挂到路线上；角标 = A / B / C 区',
     ['6 条路线（含水热空白）、29 条逐字段条件记录 A1、B1–B6、C1–C22', '论文 §3 合成条件总表，逐单元格转成卡片', '记录挂在自己的路线圆点上；副标题 = 温度–时间']),
    ('七', '结论 · 方向 · 缺口', 16, '4 条结论 + 4 个 AI 方向 + 8 条缺口，挂在 H / G 分支',
     ['4 条综述结论、4 个 AI 实验方向、8 条证据缺口', 'claim_evidence.jsonl §7、ideas/experiment_directions.md、taxonomy §5', '挂在 H 配方篮子 / G 失败边界；橙 = 结论，紫虚线 = AI，灰虚线 = 未闭合']),
    ('八', '长出的新树', 12, 'RECIPE 预测 3 + 工作流 5 + 同根调研 4，挂在 E / D / A 分支',
     ['RECIPE 前驱体组合 3、OpenLab 工作流 5、同根调研 4', 'precursor_predictions.md、站点 showcase、补充案例 ledger', '挂在 E / D / A 分支；紫 = 模型预测（未验证），深青 = 仿真工作流']),
]


def set_title(el, text):
    """Replace the runs of a copied title element with one run, keeping paragraph / run properties."""
    txBody = el.find('p:txBody', NS)
    paras = txBody.findall('a:p', NS)
    for extra in paras[1:]:
        txBody.remove(extra)
    p = paras[0]
    runs = p.findall('a:r', NS)
    for r in runs[1:]:
        p.remove(r)
    for br in p.findall('a:br', NS):
        p.remove(br)
    if runs:
        runs[0].find('a:t', NS).text = text
    else:
        r = copy.deepcopy(p.find('a:endParaRPr', NS))
        rn = p.makeelement('{%s}r' % NS['a'], {})
        if r is not None:
            r.tag = '{%s}rPr' % NS['a']
            rn.append(r)
        t = rn.makeelement('{%s}t' % NS['a'], {})
        t.text = text
        rn.append(t)
        p.insert(0, rn)


def copy_shape(el, dst_spTree, next_id):
    c = copy.deepcopy(el)
    c.find('p:nvSpPr/p:cNvPr', NS).set('id', str(next_id[0]))
    next_id[0] += 1
    dst_spTree.append(c)
    return c


def ea(run, font):
    rPr = run._r.get_or_add_rPr()
    for tag in ('a:ea', 'a:cs'):
        e = rPr.find(tag, NS)
        if e is None:
            e = rPr.makeelement('{%s}%s' % (NS['a'], tag[2:]), {})
            rPr.append(e)
        e.set('typeface', font)


class Deck:
    def __init__(self, deck, model, font):
        self.prs = Presentation(deck)
        self.model = self.prs.slides[model - 1]
        self.layout = self.model.slide_layout
        self.bars = [sh for sh in self.model.shapes if re.match(r'矩形 [23]$', sh.name)]
        assert len(self.bars) == 2, [sh.name for sh in self.model.shapes]
        self.font = font
        self.keep = []

    def new_slide(self, title):
        slide = self.prs.slides.add_slide(self.layout)
        for ph in list(slide.placeholders):
            if ph.placeholder_format.type != 1:
                ph._element.getparent().remove(ph._element)
        spTree = slide.shapes._spTree
        next_id = [max(int(c.get('id')) for c in spTree.iter('{%s}cNvPr' % NS['p'])) + 1]
        for b in self.bars:
            copy_shape(b._element, spTree, next_id)
        t_new = slide.shapes.title
        t_model = copy.deepcopy(self.model.shapes.title._element)
        t_new._element.getparent().replace(t_new._element, t_model)
        t_model.find('p:nvSpPr/p:cNvPr', NS).set('id', str(next_id[0]))
        set_title(t_model, title)
        self.keep.append(slide)
        return slide

    # ---- primitives
    def text(self, slide, x, y, w, h, paras, size=10.5, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line=1.15):
        """paras: list of paragraphs; each paragraph is a string or a list of (text, {bold, color, size}) runs."""
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Emu(0)
        tf.margin_top = tf.margin_bottom = Emu(0)
        tf.vertical_anchor = anchor
        for i, para in enumerate(paras):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            p.line_spacing = line
            runs = [(para, {})] if isinstance(para, str) else para
            for txt, st in runs:
                r = p.add_run()
                r.text = txt
                f = r.font
                f.name = self.font
                ea(r, self.font)
                f.size = Pt(st.get('size', size))
                f.bold = st.get('bold', bold)
                f.color.rgb = RGBColor.from_string(st.get('color', color))
        return tb

    def rect(self, slide, x, y, w, h, fill='FFFFFF', line=LINE, rounded=True, line_w=0.75, dash=False):
        shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        if rounded:
            shp.adjustments[0] = 0.06
        shp.fill.solid()
        shp.fill.fore_color.rgb = RGBColor.from_string(fill)
        if line:
            shp.line.color.rgb = RGBColor.from_string(line)
            shp.line.width = Pt(line_w)
            if dash:
                ln = shp.line._get_or_add_ln()
                ln.append(ln.makeelement(qn('a:prstDash'), {'val': 'dash'}))
        else:
            shp.line.fill.background()
        shp.shadow.inherit = False
        shp.text_frame.text = ''
        return shp

    def circle(self, slide, x, y, d, fill, label, size=12):
        c = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
        c.fill.solid()
        c.fill.fore_color.rgb = RGBColor.from_string(fill)
        c.line.fill.background()
        c.shadow.inherit = False
        tf = c.text_frame
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Emu(0)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = label
        r.font.name = self.font
        ea(r, self.font)
        r.font.size = Pt(size)
        r.font.bold = True
        r.font.color.rgb = RGBColor.from_string('FFFFFF')
        return c

    def picture(self, slide, path, x, y, w, h=None):
        pic = slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w), height=Inches(h) if h else None)
        pic.line.color.rgb = RGBColor.from_string(LINE)
        pic.line.width = Pt(0.75)
        return pic

    def arrow_down(self, slide, x, y, w=0.3, h=0.24):
        ar = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
        ar.fill.solid()
        ar.fill.fore_color.rgb = RGBColor.from_string(ORANGE)
        ar.line.fill.background()
        ar.shadow.inherit = False
        return ar

    # ---- slides
    def overview(self, img):
        s = self.new_slide('知识森林是怎么一层层搭起来的')
        # left: three statements, one line each
        blocks = [
            (TEAL, '数据从哪来', '全部由提交包生成：scope、taxonomy、references、claim_evidence、条件总表、ideas；共 380 个节点、1420 条边，每个节点记着出处文件。'),
            (NAVY, '结构怎么定', '中心是调研主题，文献树的八个分支 A–H 各占一个扇区；每个新节点挂到它的父节点：文献 → 叶节点 → 分支 → 中心。'),
            (ORANGE, '动画怎么演', '第 k 级只把本级节点做成贴外框的卡片，用曲线连回父节点；已展开的级收缩成中心的圆点树，八级依次展开。'),
        ]
        y = 1.5
        for i, (col, head, line) in enumerate(blocks):
            self.circle(s, 0.55, y + 0.02, 0.44, col, str(i + 1), 14)
            self.text(s, 1.15, y - 0.02, 5.6, 0.4, [[(head, {'bold': True, 'size': 15, 'color': col})]])
            self.text(s, 1.15, y + 0.48, 5.6, 1.0, [[(line, {'size': 11, 'color': INK})]], line=1.3)
            y += 1.72
        # right: two schematic frames — cards on the frame (level 2) collapse into the dot tree (level 8)
        pw = 5.0
        ph = pw / ASPECT
        x = SLIDE_W - 0.6 - pw
        y1 = 1.3
        self.picture(s, img / 'deck_S2.png', x, y1, pw, ph)
        self.text(s, x, y1 + ph + 0.06, pw, 0.3, [[('第二级　', {'bold': True, 'size': 10, 'color': NAVY}), ('8 张分支卡片贴在外框，第一级已收缩成中心的圆点', {'size': 10, 'color': INK})]])
        y2 = y1 + ph + 0.42
        self.arrow_down(s, x + pw / 2 - 0.15, y2)
        y2 += 0.3
        self.picture(s, img / 'deck_S8.png', x, y2, pw, ph)
        self.text(s, x, y2 + ph + 0.06, pw, 0.3, [[('第八级　', {'bold': True, 'size': 10, 'color': NAVY}), ('前七级都收成圆点树，长出的新树挂在外框', {'size': 10, 'color': INK})]])
        return s

    def levels(self, img, first, last):
        s = self.new_slide(f'逐层展开：第{LEVELS[first - 1][0]}到第{LEVELS[last - 1][0]}级')
        pw = 4.8
        ph = pw / ASPECT
        gap_x = 0.5
        x0 = (SLIDE_W - 2 * pw - gap_x) / 2
        row_h = 0.36 + ph + 0.3 + 0.06
        for i, (cn, name, count, one, _) in enumerate(LEVELS[first - 1:last]):
            k = first + i
            x = x0 + (i % 2) * (pw + gap_x)
            y = 1.2 + (i // 2) * row_h
            self.circle(s, x, y + 0.03, 0.3, NAVY, str(k), 10)
            self.text(s, x + 0.4, y, pw - 0.4, 0.36, [[(f'第{cn}级 · {name}', {'bold': True, 'size': 12.5, 'color': NAVY}), (f'　{count} 张卡片', {'size': 10.5, 'color': MUTED})]], anchor=MSO_ANCHOR.MIDDLE)
            self.picture(s, img / f'deck_S{k}.png', x, y + 0.36, pw, ph)
            self.text(s, x, y + 0.36 + ph + 0.05, pw, 0.26, [[(one, {'size': 10, 'color': INK})]])
        return s

    def table(self):
        s = self.new_slide('八级一览：新增 · 来源 · 挂法')
        cols = [('级', 0.5), ('新增', 3.6), ('来源（提交包里的文件）', 4.05), ('挂法', 4.08)]
        x0, y0 = 0.55, 1.25
        rows = len(LEVELS) + 1
        shp = s.shapes.add_table(rows, len(cols), Inches(x0), Inches(y0), Inches(sum(w for _, w in cols)), Inches(0.42 * rows))
        tbl = shp.table
        tblPr = tbl._tbl.tblPr
        tblPr.set('firstRow', '1')
        tblPr.set('bandRow', '0')
        sid = tblPr.find(qn('a:tableStyleId'))
        if sid is None:
            sid = tblPr.makeelement(qn('a:tableStyleId'), {})
            tblPr.append(sid)
        sid.text = '{2D5ABB26-0587-4C30-8999-92F81FD0307C}'  # No Style, No Grid
        for j, (_, w) in enumerate(cols):
            tbl.columns[j].width = Inches(w)
        tbl.rows[0].height = Inches(0.4)
        for i in range(1, rows):
            tbl.rows[i].height = Inches(0.56)

        def cell(i, j, runs, fill, align=PP_ALIGN.LEFT, size=9.5):
            c = tbl.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.08)
            c.margin_top = c.margin_bottom = Inches(0.04)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            c.fill.fore_color.rgb = RGBColor.from_string(fill)
            tf = c.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = align
            p.line_spacing = 1.12
            for txt, st in runs:
                r = p.add_run()
                r.text = txt
                r.font.name = self.font
                ea(r, self.font)
                r.font.size = Pt(st.get('size', size))
                r.font.bold = st.get('bold', False)
                r.font.color.rgb = RGBColor.from_string(st.get('color', INK))
            # borders: no side lines, a hairline under every row (lnL/lnR/lnT/lnB must precede the fill in tcPr)
            tcPr = c._tc.get_or_add_tcPr()
            fill_el = tcPr.find(qn('a:solidFill'))
            for tag in ('a:lnL', 'a:lnR', 'a:lnT', 'a:lnB'):
                ln = tcPr.makeelement(qn(tag), {'w': str(int(Pt(0.75))), 'cap': 'flat', 'cmpd': 'sng', 'algn': 'ctr'})
                if tag == 'a:lnB':
                    sf = ln.makeelement(qn('a:solidFill'), {})
                    sf.append(sf.makeelement(qn('a:srgbClr'), {'val': LINE}))
                    ln.append(sf)
                else:
                    ln.append(ln.makeelement(qn('a:noFill'), {}))
                if fill_el is not None:
                    fill_el.addprevious(ln)
                else:
                    tcPr.append(ln)

        for j, (h, _) in enumerate(cols):
            cell(0, j, [(h, {'bold': True, 'color': 'FFFFFF', 'size': 10.5})], NAVY, align=PP_ALIGN.CENTER if j == 0 else PP_ALIGN.LEFT)
        for i, (cn, name, count, _, (added, source, hang)) in enumerate(LEVELS, start=1):
            fill = 'FFFFFF' if i % 2 else 'F7F9FB'
            cell(i, 0, [(str(i), {'bold': True, 'color': NAVY, 'size': 11})], fill, align=PP_ALIGN.CENTER)
            cell(i, 1, [(name + '　', {'bold': True, 'color': NAVY}), (added, {'color': INK})], fill)
            cell(i, 2, [(source, {'color': MUTED})], fill)
            cell(i, 3, [(hang, {'color': INK})], fill)
        # card grammar, one line
        gy = 6.62
        self.text(s, x0, gy, 1.0, 0.3, [[('卡片语法', {'bold': True, 'size': 10, 'color': NAVY})]], anchor=MSO_ANCHOR.MIDDLE)
        items = [(ORANGE, 'FFFFFF', False, '实心橙 = 综述结论'), ('FDEEE2', ORANGE, False, '等级色 = 文献·化合物'), ('FFFFFF', TEAL, False, '描边 = 条件·叶节点'), ('FFFFFF', PURPLE, True, '紫虚线 = AI 方向'), ('F4F6F8', MUTED, True, '灰虚线 = 证据缺口'), (TEAL, 'FFFFFF', False, '深青 = 仿真工作流')]
        x = x0 + 1.05
        for fill, line, dash, label in items:
            self.rect(s, x, gy + 0.04, 0.34, 0.22, fill=fill, line=line, rounded=True, line_w=1.25, dash=dash)
            self.text(s, x + 0.42, gy, 1.5, 0.3, [[(label, {'size': 9, 'color': INK})]], anchor=MSO_ANCHOR.MIDDLE)
            x += 1.85
        return s

    def finish(self, out):
        # drop every template slide that is not one of ours
        sldIdLst = self.prs.slides._sldIdLst
        keep_ids = {s.slide_id for s in self.keep}
        for sldId in list(sldIdLst):
            if int(sldId.get('id')) not in keep_ids:
                self.prs.part.drop_rel(sldId.rId)
                sldIdLst.remove(sldId)
        self.prs.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--deck', required=True)
    ap.add_argument('--img', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--model', type=int, default=10)
    ap.add_argument('--font', default='微软雅黑')
    a = ap.parse_args()
    d = Deck(a.deck, a.model, a.font)
    img = Path(a.img)
    d.overview(img)
    d.levels(img, 1, 4)
    d.levels(img, 5, 8)
    d.table()
    d.finish(a.out)
    print('wrote', a.out, 'slides', len(d.keep))


if __name__ == '__main__':
    main()
