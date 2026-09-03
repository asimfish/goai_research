# 引用核查报告

- bib: `workspace/library/references.bib`
- 条目: 51
- 裁决分布: {'PASS': 51, 'FIX': 0, 'MISMATCH': 0, 'UNVERIFIED': 0, 'ERROR': 0}
- 三轴分布: {'existence': {'PASS': 51}, 'metadata': {'PASS': 51}, 'authors': {'PASS': 51}}
- 闸门: **PASS**

| key | 存在性 | 元数据 | 作者名单与顺序 |
|---|---:|---:|---:|
| `ababaikeri2024ba5y12zn` | PASS | PASS | PASS |
| `kolitsch2009crystal` | PASS | PASS | PASS |
| `wierzbickawieczorek2017high` | PASS | PASS | PASS |
| `yamane2024synthesis` | PASS | PASS | PASS |
| `yamane2024microstructure` | PASS | PASS | PASS |
| `gulay2024navigation` | PASS | PASS | PASS |
| `motozawa2022bay16si4o33` | PASS | PASS | PASS |
| `christensen1994investigation` | PASS | PASS | PASS |
| `dolan2008structures` | PASS | PASS | PASS |
| `redhammer2003beta` | PASS | PASS | PASS |
| `becerro2004revisiting` | PASS | PASS | PASS |
| `becerro2004revision` | PASS | PASS | PASS |
| `sun2014recent` | PASS | PASS | PASS |
| `felsche1973the` | PASS | PASS | PASS |
| `finger1995refinement` | PASS | PASS | PASS |
| `hazen1999crystal` | PASS | PASS | PASS |
| `tillmanns1978refinement` | PASS | PASS | PASS |
| `katscher1973the` | PASS | PASS | PASS |
| `zhong2020combining` | PASS | PASS | PASS |
| `yusa2007rhombohedral` | PASS | PASS | PASS |
| `liu1993structures` | PASS | PASS | PASS |
| `lin1999phase` | PASS | PASS | PASS |
| `kaiser2002crystal` | PASS | PASS | PASS |
| `zou2021crystal` | PASS | PASS | PASS |
| `kerstan2012thermal` | PASS | PASS | PASS |
| `thieme2022solid` | PASS | PASS | PASS |
| `ababaikeri2024ba3zn4si4o15` | PASS | PASS | PASS |
| `cai2024optimized` | PASS | PASS | PASS |
| `gorelova2016thermal` | PASS | PASS | PASS |
| `aitasalo2006crystal` | PASS | PASS | PASS |
| `buerger1954the` | PASS | PASS | PASS |
| `gu2025liba2gasi2o8` | PASS | PASS | PASS |
| `thieme2015ba1` | PASS | PASS | PASS |
| `kerstan2013bazn2si2o7` | PASS | PASS | PASS |
| `thieme2017variable` | PASS | PASS | PASS |
| `erlebach2020thermomechanical` | PASS | PASS | PASS |
| `zhao2026crystal` | PASS | PASS | PASS |
| `thieme2016negative` | PASS | PASS | PASS |
| `zou2019anti` | PASS | PASS | PASS |
| `tejas2024structural` | PASS | PASS | PASS |
| `pires2001luminescence` | PASS | PASS | PASS |
| `pang2005study` | PASS | PASS | PASS |
| `leonyuk1999high` | PASS | PASS | PASS |
| `leonyuk1999crystal` | PASS | PASS | PASS |
| `giess1982zn2sio4` | PASS | PASS | PASS |
| `yldrm2009y2sio5` | PASS | PASS | PASS |
| `tzvetkov2001effects` | PASS | PASS | PASS |
| `alizadeh2021spectroscopy` | PASS | PASS | PASS |
| `shoudu1999czochralski` | PASS | PASS | PASS |
| `brandle1986czochralski` | PASS | PASS | PASS |
| `kerstan2015kristallphasen` | PASS | PASS | PASS |

## I9 去重与整合审计

- 规范 key：`liu1993structures`；已删除重复 key `liu1993structuresx`。
- DOI 注册元数据：`10.1006/jssc.1993.1013`；题名为 *Structures of the Stuffed Tridymite Derivatives, BaMSiO4 (M = Co, Zn, Mg)*；作者顺序为 B. Liu → J. Barbier。Crossref 与 OpenAlex DOI 路由交叉核验通过。
- BibTeX 审计：51 条可解析条目、51 个唯一 key、无重复 DOI；`liu1993structures` 保留已核验 DOI/URL 及正确作者顺序。
- 引用整合审计：8 个稿件文件、196 次 citation calls、51 个去重 key；51/51 条目整合（100%），引用密度 36.5 次/千词，`bib_guard` PASS。
- 作者顺序回归：`tests/test_refcheck_authors.py` 6/6 PASS。
