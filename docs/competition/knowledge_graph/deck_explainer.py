#!/usr/bin/env python3
"""Explainer slides for the layer-by-layer knowledge forest, built on the competition deck template.

Three native slides on the template's content layout (title + the two blue title-bar rectangles every content
slide carries): one on how the forest is assembled (data → structure → animation), then two slides that walk
through the eight levels four at a time (thumbnail of the level + what is added / where it comes from / what it
hangs on).  All other template slides are dropped from the output so the file holds only these three.

usage: deck_explainer.py --deck template.pptx --img <dir with deck_L1..8.png> --out out.pptx [--model 10] [--font 微软雅黑]
"""
import argparse
import copy
import re
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main', 'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
NAVY, TEAL, ORANGE, INK, MUTED, LINE, PURPLE, GOLD = '154A97', '156082', 'E97132', '13202C', '5A6A7A', 'D7DEE6', '7A4FD6', 'B0841A'

LEVELS = [
    ('一', '调研主题与预期目标', 13, ['5 个预期目标 Q1–Q5 与 8 个 MECE 子主题', '正式案例 inputs/scope.md（调研开始前研究者自己的问题树）', '全部挂在中心「调研主题」；目标按它服务的子主题方向排布']),
    ('二', '文献树八分支', 8, ['A–H 八个分支：身份 / 结构 / 替代 / 路线 / 变量 / 表征 / 失败 / 配方篮子', '证据包 taxonomy.md §2，按 MECE 规则切分', '挂在中心，每个分支占一个扇区；从这一级起，已展开的级收缩为圆点']),
    ('三', '叶节点', 35, ['35 个叶节点，每个是一类证据主张，带证据等级与支撑文献数', 'taxonomy.md 各叶的「判定 / 支撑 key」', '挂在所属分支的圆点上，同一扇区内按顺序排开']),
    ('四', '文献', 51, ['51 篇全部通过引用闸门的文献', 'references.bib + papers.jsonl（DOI、题名、年份、期刊）', '挂在它支撑的第一个叶节点；颜色 = 证据距离，实心橙是唯一的目标相直接报道']),
    ('五', '元素与化合物', 41, ['12 个元素 + 29 个化合物 / 相', '条件总表产物字段与人工别名表；元素由化学式解析', '挂在定义它的叶节点或分支；紫色虚线 = AI 假设目标，尚未合成']),
    ('六', '合成路线与条件记录', 35, ['6 条路线 + 29 条逐字段条件记录（A1、B1–B6、C1–C22）', '论文 §3 合成条件总表，逐单元格转成卡片', '记录挂在自己的路线圆点上；副标题 = 温度–时间，角标 = A / B / C 区']),
    ('七', '结论 · 实验方向 · 证据缺口', 16, ['4 条综述结论 + 4 个 AI 实验方向 + 8 条证据缺口', 'claim_evidence.jsonl §7、ideas/experiment_directions.md、taxonomy §5', '挂在 H 配方篮子 / G 失败边界分支；实心橙 = 结论，紫虚线 = AI，灰虚线 = 未闭合']),
    ('八', '长出的新树', 12, ['RECIPE 首选前驱体组合 3 + OpenLab 工作流 5 + 同根调研 4', 'precursor_predictions.md、站点 showcase、补充案例 ledger', '挂在 E / D / A 分支；紫 = 模型预测（未验证），深青 = 仿真工作流']),
]


def set_title(el, text):
    txBody = el.find('p:txBody', NS)
    paras = txBody.findall('a:p', NS)
    p0 = paras[0]
    runs = p0.findall('a:r', NS)
    rpr = copy.deepcopy(runs[0].find('a:rPr', NS)) if runs and runs[0].find('a:rPr', NS) is not None else None
    for r in runs:
        p0.remove(r)
    for extra in paras[1:]:
        txBody.remove(extra)
    r = p0.makeelement('{%s}r' % NS['a'], {})
    if rpr is not None:
        r.append(rpr)
    t = r.makeelement('{%s}t' % NS['a'], {})
    t.text = text
    r.append(t)
    end = p0.find('a:endParaRPr', NS)
    if end is not None:
        end.addprevious(r)
    else:
        p0.append(r)


def copy_shape(el, dst_spTree, next_id):
    new = copy.deepcopy(el)
    for cnv in new.iter('{%s}cNvPr' % NS['p']):
        cnv.set('id', str(next_id[0]))
        next_id[0] += 1
    dst_spTree.append(new)
    return new


def ea(run, font):
    """python-pptx sets the Latin typeface only; the East-Asian one needs its own element."""
    rPr = run._r.get_or_add_rPr()
    for tag in ('ea', 'cs'):
        el = rPr.find('{%s}%s' % (NS['a'], tag))
        if el is None:
            el = rPr.makeelement('{%s}%s' % (NS['a'], tag), {})
            rPr.append(el)
        el.set('typeface', font)


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

    def rect(self, slide, x, y, w, h, fill='FFFFFF', line=LINE, rounded=True, line_w=0.75):
        shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        if rounded:
            shp.adjustments[0] = 0.06
        shp.fill.solid()
        shp.fill.fore_color.rgb = RGBColor.from_string(fill)
        if line:
            shp.line.color.rgb = RGBColor.from_string(line)
            shp.line.width = Pt(line_w)
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

    # ---- slides
    def overview(self, img):
        s = self.new_slide('知识森林是怎么一层层搭起来的')
        # left: three mechanism blocks
        blocks = [
            ('1', TEAL, '数据从哪来', ['全部由提交包生成：scope.md、taxonomy.md、references.bib、claim_evidence.jsonl、条件总表、ideas/ 与补充案例 ledger', 'build_graph.py 读这些文件得到 380 个节点、1420 条边；每个节点都记着自己的出处文件']),
            ('2', NAVY, '结构怎么定', ['中心是调研主题；文献树的八个分支 A–H 各占一个扇区', '每个新节点挂到它的父节点：文献 → 叶节点 → 分支 → 中心；化合物 → 定义它的叶；条件记录 → 路线']),
            ('3', ORANGE, '动画怎么演', ['第 k 级只把本级节点做成贴外框的文字卡片，用曲线连回父节点', '已展开的级收缩成中心的圆点树；卡片与圆点互相形变，底部字幕说明本级由什么构成']),
        ]
        y = 1.25
        for num, col, head, lines in blocks:
            self.circle(s, 0.5, y + 0.04, 0.42, col, num, 14)
            self.text(s, 1.05, y, 4.85, 0.35, [[(head, {'bold': True, 'size': 14, 'color': col})]])
            self.text(s, 1.05, y + 0.38, 4.85, 1.3, [[('· ' + t, {'size': 10.5, 'color': INK})] for t in lines], line=1.2)
            y += 1.78
        # right: four snapshots of the growth
        picks = [(2, '第二级 · 八分支'), (4, '第四级 · 51 篇文献'), (6, '第六级 · 路线与条件记录'), (8, '第八级 · 长出的新树')]
        gx, gy, pw, ph = 6.35, 1.2, 3.3, 1.64
        for i, (k, cap) in enumerate(picks):
            x = gx + (i % 2) * (pw + 0.2)
            yy = gy + (i // 2) * (ph + 0.62)
            self.picture(s, img / f'deck_L{k}.png', x, yy, pw, ph)
            self.text(s, x, yy + ph + 0.06, pw, 0.3, [[(cap, {'bold': True, 'size': 10.5, 'color': NAVY})]])
        # arrows between the snapshots (reading order)
        for (x1, y1, x2, y2) in [(gx + pw + 0.02, gy + ph / 2, gx + pw + 0.18, gy + ph / 2), (gx + pw + 0.02, gy + ph + 0.62 + ph / 2, gx + pw + 0.18, gy + ph + 0.62 + ph / 2)]:
            ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x1), Inches(y1 - 0.1), Inches(0.16), Inches(0.2))
            ar.fill.solid(); ar.fill.fore_color.rgb = RGBColor.from_string(ORANGE); ar.line.fill.background(); ar.shadow.inherit = False
        # bottom: card grammar
        gy2 = 6.45
        self.rect(s, 0.5, gy2, 12.3, 0.62, fill='F7F9FB', line=LINE)
        self.text(s, 0.65, gy2 + 0.1, 1.2, 0.4, [[('卡片语法', {'bold': True, 'size': 10.5, 'color': NAVY})]], anchor=MSO_ANCHOR.MIDDLE)
        items = [(ORANGE, 'FFFFFF', '实心橙 = 综述结论'), ('FDEEE2', ORANGE, '等级色 = 文献·化合物'), ('FFFFFF', TEAL, '描边卡 = 条件·叶节点'), ('FFFFFF', PURPLE, '紫虚线 = AI 方向'), ('F4F6F8', MUTED, '灰虚线 = 证据缺口'), (TEAL, 'FFFFFF', '深青 = 仿真工作流')]
        x = 1.85
        for fill, line, label in items:
            sw = self.rect(s, x, gy2 + 0.19, 0.34, 0.24, fill=fill, line=line, rounded=True, line_w=1.25)
            self.text(s, x + 0.42, gy2 + 0.1, 1.5, 0.4, [[(label, {'size': 9, 'color': INK})]], anchor=MSO_ANCHOR.MIDDLE)
            x += 1.8
        return s

    def levels(self, img, first, last):
        s = self.new_slide(f'逐层展开：第{LEVELS[first - 1][0]}到第{LEVELS[last - 1][0]}级')
        cells = LEVELS[first - 1:last]
        cw, chh = 6.15, 2.88
        for i, (cn, name, count, (added, source, hang)) in enumerate(cells):
            x = 0.45 + (i % 2) * (cw + 0.28)
            y = 1.18 + (i // 2) * (chh + 0.16)
            self.rect(s, x, y, cw, chh, fill='FFFFFF', line=LINE)
            k = first + i
            self.picture(s, img / f'deck_L{k}.png', x + 0.12, y + 0.42, 3.9, 1.94)
            self.circle(s, x + 0.12, y + 0.08, 0.3, NAVY, str(k), 10)
            self.text(s, x + 0.5, y + 0.06, cw - 0.6, 0.34, [[(f'第{cn}级 · {name}', {'bold': True, 'size': 12.5, 'color': NAVY}), (f'（{count}）', {'size': 11, 'color': MUTED})]], anchor=MSO_ANCHOR.MIDDLE)
            tx = x + 4.14
            self.text(s, tx, y + 0.42, cw - 4.26, chh - 0.5, [
                [('新增  ', {'bold': True, 'size': 9.5, 'color': TEAL}), (added, {'size': 9.5})],
                [('来源  ', {'bold': True, 'size': 9.5, 'color': TEAL}), (source, {'size': 9.5, 'color': MUTED})],
                [('挂法  ', {'bold': True, 'size': 9.5, 'color': TEAL}), (hang, {'size': 9.5})],
            ], line=1.18)
            # thin caption under the picture: what the eye should look at
            look = {1: '中心：研究者与调研主题；13 张卡片沿外框', 2: '8 张分支卡片；上一级已缩成圆点', 3: '35 张叶卡片，颜色 = 证据等级', 4: '51 张文献卡片，两车道砖形排布', 5: '元素小卡 + 化合物卡，紫虚线为假设目标', 6: '路线（深青）与 29 条条件记录（A/B/C 区）', 7: '结论（橙）· 方向（紫虚线）· 缺口（灰虚线）', 8: '预测（紫）· 工作流（深青）· 案例（描边）'}[k]
            self.text(s, x + 0.12, y + 2.42, 3.9, 0.36, [[(look, {'size': 8.5, 'color': MUTED})]], anchor=MSO_ANCHOR.MIDDLE)
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
    d.finish(a.out)
    print('wrote', a.out, 'slides', len(d.keep))


if __name__ == '__main__':
    main()
