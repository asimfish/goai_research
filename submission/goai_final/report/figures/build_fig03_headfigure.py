"""Build a Nature-style graphical abstract for the LLZO-adjacent silicate survey.

The artwork is deliberately a continuous scientific composition rather than a
card-based workflow.  The SVG is the source for the PDF, PNG and the editable
Draw.io image cell.  Text is kept short and added deterministically so that the
chemical claims remain under editorial control.
"""
from __future__ import annotations

import base64
import html
from pathlib import Path


W, H = 1600, 900
OUT = Path(__file__).resolve().parent
SVG_PATH = OUT / "svg" / "fig03_research_roadmap.svg"
PNG_PATH = OUT / "png" / "fig03_research_roadmap.png"
PDF_PATH = OUT / "pdf" / "fig03_research_roadmap.pdf"
DRAWIO_PATH = OUT / "drawio" / "fig03_research_roadmap.drawio"


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def text(x: float, y: float, s: str, size: float = 20, color: str = "#385363",
         anchor: str = "middle", weight: str = "400", italic: bool = False) -> str:
    slant = ' font-style="italic"' if italic else ""
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
            f'dominant-baseline="middle" font-family="Noto Sans CJK SC,Source Han Sans CN,Arial,sans-serif" '
            f'font-size="{size}px" font-weight="{weight}" fill="{color}"{slant}>{esc(s)}</text>')


def line(x1: float, y1: float, x2: float, y2: float, stroke: str = "#58717F",
         width: float = 2.0, dash: str = "") -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}"{d}/>'


def path(d: str, stroke: str = "none", width: float = 1.0, fill: str = "none",
         opacity: float = 1.0, dash: str = "", marker: str = "") -> str:
    da = f' stroke-dasharray="{dash}"' if dash else ""
    ma = f' marker-end="url(#{marker})"' if marker else ""
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" '
            f'opacity="{opacity}" stroke-linecap="round" stroke-linejoin="round"{da}{ma}/>' )


def circle(cx: float, cy: float, r: float, fill: str, stroke: str = "none",
           width: float = 1.0, opacity: float = 1.0) -> str:
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{width}" opacity="{opacity}"/>')


def poly(points: str, fill: str, stroke: str = "none", width: float = 1.0,
         opacity: float = 1.0) -> str:
    return (f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{width}" opacity="{opacity}"/>')


def tetra(cx: float, cy: float, scale: float, tint: str) -> str:
    """A small translucent coordination polyhedron used as a schematic motif."""
    p1 = f"{cx},{cy-scale} {cx+scale*0.92},{cy+scale*0.48} {cx-scale*0.92},{cy+scale*0.48}"
    p2 = f"{cx},{cy-scale} {cx+scale*0.92},{cy+scale*0.48} {cx},{cy+scale*0.78}"
    p3 = f"{cx},{cy-scale} {cx},{cy+scale*0.78} {cx-scale*0.92},{cy+scale*0.48}"
    return (poly(p1, tint, "#486979", 1.4, .70)
            + poly(p2, tint, "#486979", 1.1, .42)
            + poly(p3, "#B8D2D0", "#486979", 1.1, .34)
            + circle(cx, cy-scale, scale*.11, "#C65B4C", "#7B3D37", .7)
            + circle(cx+scale*.92, cy+scale*.48, scale*.10, "#C65B4C", "#7B3D37", .7)
            + circle(cx-scale*.92, cy+scale*.48, scale*.10, "#C65B4C", "#7B3D37", .7))


def build_svg() -> str:
    a: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<defs>',
        '<linearGradient id="phase" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F5F8F8"/><stop offset="1" stop-color="#DCE9EA"/></linearGradient>',
        '<linearGradient id="amber" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F4D9A3"/><stop offset="1" stop-color="#C88929"/></linearGradient>',
        '<linearGradient id="teal" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#BCD6D5"/><stop offset="1" stop-color="#477C80"/></linearGradient>',
        '<filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur in="SourceAlpha" stdDeviation="5" result="blur"/><feOffset dy="5" result="off"/><feComponentTransfer><feFuncA type="linear" slope=".17"/></feComponentTransfer><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<marker id="arrow" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="11" markerHeight="11" markerUnits="userSpaceOnUse" orient="auto"><path d="M 0 0 L 12 6 L 0 12 Z" fill="#607E88"/></marker>',
        '<marker id="arrowAmber" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="11" markerHeight="11" markerUnits="userSpaceOnUse" orient="auto"><path d="M 0 0 L 12 6 L 0 12 Z" fill="#B8791E"/></marker>',
        '</defs>',
        f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>',
        text(800, 44, "从组成空间到可检验合成", 31, "#183A4A", weight="700"),
        text(800, 78, "Ba–Y–Si–O 近邻  ·  候选前驱体  ·  批量相区与单晶结构  ·  结果反馈", 16, "#657C86"),
    ]

    # Left: a continuous composition landscape rather than a panel of cards.
    a += [text(225, 128, "组成空间", 21, "#183A4A", weight="700"),
          path("M 80 490 L 225 175 L 370 490 Z", "#6C8994", 2.0, "url(#phase)"),
          path("M 112 455 C 145 398 175 350 224 250 C 266 344 307 395 340 455", "#B8CDD0", 1.5, "none", .9),
          path("M 130 461 C 167 401 189 365 224 295 C 259 365 287 401 322 461", "#B8CDD0", 1.2, "none", .8),
          path("M 152 466 C 180 422 203 390 224 340 C 250 391 268 423 296 466", "#B8CDD0", 1.1, "none", .8),
          poly("207,398 225,347 245,386 231,431", "#D59729", "#A86C18", 1.4, .82),
          circle(225, 383, 7, "#B8791E", "#805317", 1.2),
          text(225, 525, "Ba–Y–Si–O / Ba–Zn–Si–O / Y–Si–O", 15, "#516A75"),
          text(225, 550, "局部候选区与竞争相", 15, "#A86C18", weight="600"),
          text(85, 500, "Ba", 14, "#627A84", anchor="start"),
          text(355, 500, "Y", 14, "#627A84", anchor="end"),
          text(225, 184, "Zn", 14, "#627A84"),
          # small neighboring motifs
          tetra(121, 320, 26, "#9FB8C4"), tetra(326, 315, 26, "#9FB8C4"),
          path("M 372 374 C 442 337 494 300 552 263", "#7895A0", 2.2, "none", .9, marker="arrow")]

    # Central object: a lattice-like schematic with depth and no enclosing box.
    a += [text(800, 126, "候选晶相", 22, "#183A4A", weight="700"),
          text(800, 151, "结构模型待实验确认", 15, "#657C86"),
          '<g filter="url(#soft)">']
    positions = [(650,235,54,"#5A9797"),(755,220,62,"#6CA4A2"),(866,237,52,"#4E8587"),
                 (700,330,65,"#4E8587"),(812,322,58,"#72AAA6"),(925,335,64,"#5A9797"),
                 (760,425,55,"#72AAA6"),(870,425,60,"#4C8186")]
    for x,y,s,c in positions:
        a.append(tetra(x,y,s,c))
    # connectors and larger cations, drawn after polyhedra for a crystal-lattice feel
    for x1,y1,x2,y2 in [(650,235,755,220),(755,220,866,237),(700,330,812,322),(812,322,925,335),
                        (700,330,760,425),(812,322,870,425),(755,220,700,330),(866,237,925,335)]:
        a.append(line(x1,y1,x2,y2,"#6F8A91",1.5))
    for x,y,r,c in [(676,275,17,"#B1C89E"),(838,270,15,"#AABF95"),(968,280,18,"#B1C89E"),
                    (760,370,14,"#B8A5C6"),(895,380,16,"#AABF95"),(690,407,12,"#B8A5C6")]:
        a.append(circle(x,y,r,c,"#6D7F7A",1.1,.94))
    a += ['</g>',
          path("M 548 600 C 630 569 676 534 717 486", "#7895A0", 2.2, "none", .85, marker="arrow"),
          path("M 1020 470 C 1084 500 1117 534 1165 582", "#7895A0", 2.2, "none", .85, marker="arrow")]

    # Lower left: solid-state route shown as objects, not a workflow card.
    a += [text(200, 625, "固相成相", 19, "#183A4A", weight="700"),
          circle(72, 690, 20, "#91A3A8"), circle(108, 684, 17, "#B4A8C2"),
          circle(141, 699, 18, "#A9B999"), circle(174, 686, 16, "#D6C8B0"),
          text(123, 730, "前驱体粉体", 15, "#657C86"),
          # mortar and pestle
          '<path d="M 215 681 Q 258 661 299 681 L 288 741 Q 258 760 226 741 Z" fill="#E9ECEA" stroke="#71828A" stroke-width="1.5"/>',
          '<path d="M 230 675 Q 258 692 287 675" fill="none" stroke="#71828A" stroke-width="1.4"/>',
          '<path d="M 270 654 L 300 620" stroke="#8B9AA0" stroke-width="9" stroke-linecap="round"/>',
          '<path d="M 300 620 L 309 611" stroke="#D3D8D7" stroke-width="7" stroke-linecap="round"/>',
          # pellet and furnace
          '<ellipse cx="349" cy="705" rx="28" ry="11" fill="#D8D1C6" stroke="#77868D" stroke-width="1.4"/>',
          '<rect x="326" y="705" width="46" height="20" fill="#C7BEB0" stroke="#77868D" stroke-width="1.4"/>',
          '<path d="M 399 677 Q 399 656 418 646 L 500 646 Q 519 656 519 677 L 519 741 L 399 741 Z" fill="#DCE0DF" stroke="#647982" stroke-width="1.7"/>',
          '<rect x="421" y="671" width="76" height="48" rx="23" fill="#6B7477" stroke="#404A4C" stroke-width="1.4"/>',
          '<rect x="435" y="680" width="48" height="31" rx="13" fill="#D8902B" opacity=".9"/>',
          '<rect x="447" y="691" width="24" height="12" rx="4" fill="#F5D39A"/>',
          text(457, 770, "混合 · 压片 · 热处理", 15, "#657C86"),
          path("M 520 700 C 566 700 590 682 622 654", "#7895A0", 2.0, "none", .8, marker="arrow")]

    # Lower center: high-temperature solution route.
    a += [text(650, 625, "高温溶液长晶", 19, "#805718", weight="700"),
          '<path d="M 574 683 L 714 683 L 691 758 Q 646 778 597 758 Z" fill="#D8DDDB" stroke="#687D83" stroke-width="1.6"/>',
          '<path d="M 594 704 Q 646 682 696 704 L 686 752 Q 645 766 604 752 Z" fill="url(#amber)" opacity=".88"/>',
          '<ellipse cx="646" cy="704" rx="51" ry="17" fill="#E5AF58" opacity=".72"/>',
          '<path d="M 744 760 L 744 679 Q 744 663 760 658 L 833 658 Q 849 663 849 679 L 849 760 Z" fill="#F1F2F0" stroke="#687D83" stroke-width="1.5"/>',
          '<ellipse cx="796" cy="679" rx="53" ry="16" fill="#E6A743" opacity=".85"/>',
          '<path d="M 768 732 L 796 659 L 823 732 L 796 759 Z" fill="#EBC27E" stroke="#A06C1D" stroke-width="1.4" opacity=".9"/>',
          '<path d="M 796 659 L 823 732 L 796 719 L 768 732 Z" fill="#F4DCA9" stroke="#A06C1D" stroke-width="1.1" opacity=".9"/>',
          text(710, 797, "熔体 · 保温 · 慢冷", 15, "#805718"),
          path("M 852 696 C 898 696 927 686 963 661", "#B8791E", 2.2, "none", .9, marker="arrowAmber")]

    # Right: three compact readouts, floating like a journal figure, not cards.
    a += [text(1350, 126, "互补表征", 21, "#183A4A", weight="700"),
          # XRD trace
          line(1168, 280, 1518, 280, "#A5B3B8", 1.2), line(1168, 177, 1168, 280, "#A5B3B8", 1.2),
          path("M 1170 278 L 1190 278 L 1197 263 L 1203 278 L 1222 278 L 1230 220 L 1235 278 L 1258 278 L 1264 245 L 1269 278 L 1290 278 L 1299 188 L 1305 278 L 1328 278 L 1336 234 L 1341 278 L 1361 278 L 1370 205 L 1376 278 L 1397 278 L 1405 174 L 1410 278 L 1431 278 L 1440 228 L 1445 278 L 1465 278 L 1474 197 L 1480 278 L 1500 278 L 1514 260", "#2C5871", 2.2),
          text(1345, 307, "粉末衍射 · 批量相组成", 16, "#536D79"),
          # unit-cell wireframe
          '<g fill="none" stroke="#527789" stroke-width="1.5"><path d="M 1186 425 L 1280 390 L 1370 420 L 1274 456 Z"/><path d="M 1186 425 L 1186 510 L 1274 545 L 1274 456 Z"/><path d="M 1274 456 L 1370 420 L 1370 507 L 1274 545 Z"/><path d="M 1280 390 L 1280 477 L 1370 507"/><path d="M 1186 510 L 1280 477 L 1280 390"/></g>',
          circle(1186,425,5,"#C65B4C"), circle(1280,390,5,"#C65B4C"), circle(1370,420,5,"#C65B4C"), circle(1274,545,5,"#C65B4C"),
          text(1350, 574, "单晶衍射 · 结构身份", 16, "#536D79"),
          # composition strip / points
          line(1190, 674, 1505, 674, "#A5B3B8", 1.2),
          '<rect x="1190" y="632" width="315" height="13" rx="6" fill="#D9E2E2"/>',
          '<rect x="1302" y="632" width="93" height="13" rx="6" fill="#E1B561"/>',
          line(1215, 670, 1215, 688, "#8298A0", 1.2), line(1302, 670, 1302, 688, "#8298A0", 1.2),
          line(1395, 670, 1395, 688, "#8298A0", 1.2), line(1488, 670, 1488, 688, "#8298A0", 1.2),
          circle(1265, 674, 6, "#4E7880"), circle(1355, 674, 7, "#B8791E"), circle(1420, 674, 6, "#4E7880"), circle(1470, 674, 6, "#A4B2B4"),
          text(1350, 716, "EDS / EPMA · 实际化学计量", 16, "#536D79"),
          path("M 1490 744 C 1360 820 1160 820 1010 750", "#8299A1", 1.8, "none", .75, "6 7", marker="arrow"),
          text(1348, 813, "结果反馈至下一轮组成与工艺", 15, "#657C86")]

    # A restrained scientific footer, not a third row of cards.
    a += [line(80, 850, 1520, 850, "#D5DEE0", 1.0),
          text(800, 872, "核心判据：批量相区、单晶结构与实际化学计量必须相互支持", 15, "#526A75")]
    a.append('</svg>')
    return "\n".join(a)


def build_drawio(svg: str) -> str:
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    # A single image cell preserves the exact journal artwork while remaining
    # movable, resizable and annotatable in Draw.io.  The SVG itself is the
    # editable source of all visible text and geometry.
    return (f'<mxfile host="app.diagrams.net" modified="2026-09-02T00:00:00.000Z" version="24.7.17">'
            f'<diagram id="fig03" name="fig03_research_roadmap"><mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" page="1" pageScale="1" pageWidth="1600" pageHeight="900"><root>'
            f'<mxCell id="0"/><mxCell id="1" parent="0"/>'
            f'<mxCell id="2" value="" style="shape=image;image=data:image/svg+xml;base64,{b64};aspect=fixed;verticalLabelPosition=bottom;verticalAlign=top;" vertex="1" parent="1"><mxGeometry x="0" y="0" width="1600" height="900" as="geometry"/></mxCell>'
            f'</root></mxGraphModel></diagram></mxfile>')


def main() -> None:
    svg = build_svg()
    SVG_PATH.write_text(svg, encoding="utf-8")
    DRAWIO_PATH.write_text(build_drawio(svg), encoding="utf-8")
    print(SVG_PATH)
    print(DRAWIO_PATH)


if __name__ == "__main__":
    main()
