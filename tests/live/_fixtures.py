"""实测 fixture 生成：判定矩阵条目 + 真实规模稿件工程（供三个闸门工具）。

矩阵条目 = 真实论文 + 人为损坏的混合，期望语义见每条 expect 注释。
"""
from __future__ import annotations

import os
import textwrap

# ---------- verify_entry 判定矩阵 ----------
# expect_verdicts: 可接受裁决集合；expect_issue: 必须出现的 (axis, type)；
# note: 该条构造意图。

RESNET_AUTHORS_OK = "He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian"

MATRIX: list[dict] = [
    {
        "id": "M1_resnet_ok",
        "expect_verdicts": {"PASS"},
        "expect_issues": [],
        "note": "完全正确条目（DOI 路由）",
        "bibtex": textwrap.dedent("""\
            @inproceedings{he2016deep,
              title     = {Deep Residual Learning for Image Recognition},
              author    = {He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
              booktitle = {CVPR},
              year      = {2016},
              doi       = {10.1109/CVPR.2016.90}
            }"""),
    },
    {
        "id": "M2_attention_ok",
        "expect_verdicts": {"PASS"},
        "expect_issues": [],
        "note": "完全正确条目（无 DOI，标题检索路由）",
        "bibtex": textwrap.dedent("""\
            @inproceedings{vaswani2017attention,
              title     = {Attention Is All You Need},
              author    = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and
                           Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N. and
                           Kaiser, Lukasz and Polosukhin, Illia},
              booktitle = {Advances in Neural Information Processing Systems},
              year      = {2017}
            }"""),
    },
    {
        "id": "M3_depthanything2024_ok",
        "expect_verdicts": {"PASS"},
        "expect_issues": [],
        "note": "2024 真实论文（arXiv 路由）",
        "bibtex": textwrap.dedent("""\
            @misc{yang2024depthanything,
              title  = {Depth Anything: Unleashing the Power of Large-Scale Unlabeled Data},
              author = {Yang, Lihe and Kang, Bingyi and Huang, Zilong and Xu, Xiaogang and
                        Feng, Jiashi and Zhao, Hengshuang},
              year   = {2024},
              eprint = {2401.10891}
            }"""),
    },
    {
        "id": "M4_resnet_author_order",
        "expect_verdicts": {"FIX", "MISMATCH"},
        "expect_issues": [("AUTHORS", "order")],
        "note": "作者顺序打乱（前两位互换）",
        "bibtex": textwrap.dedent("""\
            @inproceedings{he2016deep_order,
              title     = {Deep Residual Learning for Image Recognition},
              author    = {Zhang, Xiangyu and He, Kaiming and Ren, Shaoqing and Sun, Jian},
              booktitle = {CVPR},
              year      = {2016},
              doi       = {10.1109/CVPR.2016.90}
            }"""),
    },
    {
        "id": "M5_resnet_fake_author",
        "expect_verdicts": {"MISMATCH"},
        "expect_issues": [("AUTHORS", "extra"), ("AUTHORS", "missing")],
        "note": "第三作者替换成编造名字",
        "bibtex": textwrap.dedent("""\
            @inproceedings{he2016deep_fakeauthor,
              title     = {Deep Residual Learning for Image Recognition},
              author    = {He, Kaiming and Zhang, Xiangyu and Smithers, Johnathan and Sun, Jian},
              booktitle = {CVPR},
              year      = {2016},
              doi       = {10.1109/CVPR.2016.90}
            }"""),
    },
    {
        "id": "M6_adam_year_off_by_one",
        "expect_verdicts": {"FIX"},
        "expect_issues": [("YEAR", "off_by_one")],
        "note": "年份差 1（ICLR 2015 口径 vs arXiv 2014 口径）",
        "bibtex": textwrap.dedent("""\
            @misc{kingma2015adam,
              title  = {Adam: A Method for Stochastic Optimization},
              author = {Kingma, Diederik P. and Ba, Jimmy},
              year   = {2015},
              eprint = {1412.6980}
            }"""),
    },
    {
        "id": "M7_resnet_venue_abbrev",
        "expect_verdicts": {"FIX"},
        "expect_issues": [("VENUE", "drift")],
        "note": "venue 缩写变体（Proc. CVPR，非权威名子串）",
        "bibtex": textwrap.dedent("""\
            @inproceedings{he2016deep_venue,
              title     = {Deep Residual Learning for Image Recognition},
              author    = {He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
              booktitle = {Proc. CVPR},
              year      = {2016},
              doi       = {10.1109/CVPR.2016.90}
            }"""),
    },
    {
        "id": "M8_doi_points_elsewhere",
        # 真标题 + 他篇真论文的 DOI：绝不能 PASS，且应指出 DOI 与标题不一致
        "expect_verdicts": {"MISMATCH"},
        "expect_issues": [("ID", "id_conflict")],
        "note": "标题真实但 DOI 指向另一篇真实论文（ResNet 的 DOI）",
        "bibtex": textwrap.dedent("""\
            @inproceedings{vaswani2017attention_baddoi,
              title     = {Attention Is All You Need},
              author    = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and
                           Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N. and
                           Kaiser, Lukasz and Polosukhin, Illia},
              booktitle = {Advances in Neural Information Processing Systems},
              year      = {2017},
              doi       = {10.1109/CVPR.2016.90}
            }"""),
    },
    {
        "id": "M9_fabricated",
        "expect_verdicts": {"UNVERIFIED"},
        "expect_issues": [],
        "note": "完全编造条目（幻觉引用）",
        "bibtex": textwrap.dedent("""\
            @inproceedings{marlowe2024recursive,
              title     = {Recursive Epistemic Gradient Surgery for Trustworthy Multi-Hop
                           Citation Alignment in Autonomous Survey Agents},
              author    = {Marlowe, Vincent T. and Okafor-Reyes, Damaris},
              booktitle = {Proceedings of the 3rd International Symposium on Verified
                           Knowledge Systems (ISVKS)},
              year      = {2024}
            }"""),
    },
    {
        "id": "M10_resnet_fake_doi",
        # 元数据全对但 DOI 是编造的（解析不出来）：应发现 DOI 不实，FIX 级可自动修正
        "expect_verdicts": {"FIX"},
        "expect_issues": [("ID", "doi_mismatch")],
        "note": "正确元数据 + 编造 DOI（10.1109/CVPR.2016.99999 不存在）",
        "bibtex": textwrap.dedent("""\
            @inproceedings{he2016deep_fakedoi,
              title     = {Deep Residual Learning for Image Recognition},
              author    = {He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
              booktitle = {CVPR},
              year      = {2016},
              doi       = {10.1109/CVPR.2016.99999}
            }"""),
    },
]

# verify_bib_file 用的混合小文件：PASS + MISMATCH + UNVERIFIED 各一
BIBFILE_MEMBERS = ["M1_resnet_ok", "M5_resnet_fake_author", "M9_fabricated"]


def mixed_bib_text() -> str:
    by_id = {m["id"]: m for m in MATRIX}
    return "\n\n".join(by_id[i]["bibtex"] for i in BIBFILE_MEMBERS) + "\n"


# ---------- 真实规模稿件工程（三个闸门工具共用） ----------

GATES_BIB = textwrap.dedent("""\
    @inproceedings{vaswani2017attention,
      title = {Attention Is All You Need},
      author = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki},
      booktitle = {NeurIPS}, year = {2017}
    }
    @inproceedings{he2016deep,
      title = {Deep Residual Learning for Image Recognition},
      author = {He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
      booktitle = {CVPR}, year = {2016}
    }
    @inproceedings{devlin2019bert,
      title = {BERT: Pre-training of Deep Bidirectional Transformers},
      author = {Devlin, Jacob and Chang, Ming-Wei}, booktitle = {NAACL}, year = {2019}
    }
    @inproceedings{brown2020gpt3,
      title = {Language Models are Few-Shot Learners},
      author = {Brown, Tom and Mann, Benjamin}, booktitle = {NeurIPS}, year = {2020}
    }
    @inproceedings{kingma2015adam,
      title = {Adam: A Method for Stochastic Optimization},
      author = {Kingma, Diederik P. and Ba, Jimmy}, booktitle = {ICLR}, year = {2015}
    }
    @inproceedings{dosovitskiy2021vit,
      title = {An Image is Worth 16x16 Words},
      author = {Dosovitskiy, Alexey and Beyer, Lucas}, booktitle = {ICLR}, year = {2021}
    }
    @misc{yang2024depthanything,
      title = {Depth Anything: Unleashing the Power of Large-Scale Unlabeled Data},
      author = {Yang, Lihe and Kang, Bingyi}, year = {2024}, eprint = {2401.10891}
    }
    @inproceedings{liu2024survey,
      title = {A Survey of Retrieval-Augmented Generation Agents},
      author = {Liu, Wei and Chen, Fang}, booktitle = {ACL Findings}, year = {2024}
    }
    @article{park2025hallucination,
      title = {Hallucinated Citations in LLM-Generated Reviews: Measurement and Mitigation},
      author = {Park, Jisoo and Novak, Emil}, journal = {TMLR}, year = {2025}
    }
    @inproceedings{gomez2025gate,
      title = {Deterministic Gates for Multi-Agent Scientific Writing Pipelines},
      author = {Gomez, Aria and Lindqvist, Nora}, booktitle = {AAMAS}, year = {2025}
    }
    @article{shen2026audit,
      title = {Evidence-First Citation Auditing at Scale},
      author = {Shen, Ruolan and Fischer, Tobias}, journal = {Nature Machine Intelligence},
      year = {2026}
    }
    @misc{delgado2026loop,
      title = {Closed-Loop Verification for Autonomous Literature Surveys},
      author = {Delgado, Ines and Watanabe, Kenji}, year = {2026}, eprint = {2601.04455}
    }
    """)

SECTION_INTRO = textwrap.dedent(r"""
    \section{Introduction}\label{sec:intro}
    Large language model agents are increasingly used to draft literature
    surveys end to end, from retrieval to camera-ready prose. The transformer
    architecture \cite{vaswani2017attention} and its scaling into few-shot
    learners \cite{brown2020gpt3} made fluent long-form generation cheap, while
    pretraining recipes such as BERT \cite{devlin2019bert} and visual backbones
    from residual networks \cite{he2016deep} to vision transformers
    \cite{dosovitskiy2021vit} broadened the corpus such systems must summarize.
    Fluency, however, is exactly what makes fabricated evidence dangerous: a
    generated survey can weave a hallucinated reference into an otherwise
    plausible narrative, and readers rarely chase every pointer back to its
    source. Recent measurements show that hallucinated citations survive in a
    non-trivial fraction of LLM-generated reviews \cite{park2025hallucination},
    and that reference lists drift further from ground truth as pipelines chain
    more autonomous steps \cite{delgado2026loop}.

    This survey examines verification-centric designs for multi-agent research
    assistants. Our organizing claim is that citation integrity is a systems
    property: it emerges from deterministic gates placed between retrieval,
    drafting, and revision \cite{gomez2025gate}, not from better prompting
    alone. We review how retrieval-augmented generation agents ground their
    claims \cite{liu2024survey}, how evidence-first auditing scales to full
    bibliographies \cite{shen2026audit}, and how optimization heuristics that
    originated in supervised training, from adaptive optimizers
    \cite{kingma2015adam} to self-supervised depth estimators
    \cite{yang2024depthanything}, migrate into agent tooling. Throughout, we
    contrast fail-open designs, which pass silently on missing evidence, with
    fail-closed designs, which block until every reference resolves to an
    authoritative record.
    """)

SECTION_METHOD = textwrap.dedent(r"""
    \section{Verification Pipelines}\label{sec:method}
    We group existing systems by where verification sits in the loop. The
    first family verifies at retrieval time: every candidate reference enters
    the pool only after resolution against Crossref, OpenAlex, arXiv, or DBLP,
    a discipline inherited from evidence-first auditing frameworks
    \cite{shen2026audit}. The second family verifies at drafting time, where
    each claim-citation pair is checked before a sentence is committed;
    retrieval-augmented agents follow this pattern when they cite from a
    curated bank rather than free-form memory \cite{liu2024survey}. The third
    family verifies post hoc, sweeping a finished manuscript for references
    that fail to resolve, an approach that catches the measurement gap
    documented for generated reviews \cite{park2025hallucination} but wastes
    drafting effort when large sections must be rewritten.

    Architecturally, the gate placement mirrors older debates in training
    pipelines. Just as residual connections \cite{he2016deep} and attention
    \cite{vaswani2017attention} stabilized deep stacks by shortening gradient
    paths, deterministic gates shorten the feedback path between a fabricated
    reference and its detection \cite{gomez2025gate}. Closed-loop systems make
    this explicit by re-running the citation audit after every revision round
    \cite{delgado2026loop}, and the same loop structure appears in
    self-training pipelines for dense prediction \cite{yang2024depthanything}.
    We adopt three comparison axes: coverage of the authoritative sources,
    strictness of the fail-closed policy, and the marginal cost per verified
    citation, reported per thousand words of generated prose. Where papers
    report optimizer-sensitive ablations we normalize to the Adam baseline
    \cite{kingma2015adam}, and where vision-language corpora are involved we
    note the pretraining lineage from BERT \cite{devlin2019bert}, GPT-3
    \cite{brown2020gpt3}, and ViT \cite{dosovitskiy2021vit} to keep
    comparisons commensurable.
    \begin{figure}[t]
      \centering
      \includegraphics[width=0.9\linewidth]{figures/arch}
      \caption{Gate placement in a survey-writing loop.}\label{fig:arch}
    \end{figure}
    As Figure~\ref{fig:arch} shows, the audit gate sits between drafting and
    review, so a failed verdict blocks the round instead of annotating it.
    """)

MAIN_TEX = textwrap.dedent(r"""
    \documentclass{article}
    \title{Verification-Centric Multi-Agent Survey Writing}
    \author{Live Test Harness}
    \begin{document}
    \maketitle
    \input{sections/01_intro}
    \input{sections/02_method}
    See Section~\ref{sec:intro} and Section~\ref{sec:method} for details.
    \end{document}
    """)

# tex_guard 五类问题注入版（TODO 残留 / input 缺失 / 图缺失 / 悬空 ref / 环境未闭合）
MAIN_TEX_BROKEN = textwrap.dedent(r"""
    \documentclass{article}
    \title{TODO: fill in survey title}
    \begin{document}
    \maketitle
    \input{sections/01_intro}
    \input{sections/99_missing}
    \includegraphics{figures/ghost_figure}
    See Section~\ref{sec:nowhere}.
    \begin{itemize}
    \item unclosed list
    \end{document}
    """)

BANK_OK = textwrap.dedent("""\
    # Citation bank — verification-centric survey
    ## S1 Introduction
    - [park2025hallucination] LLM 生成综述中的幻觉引用占比已被系统测量 (strong)
    - [delgado2026loop] 自主流水线链路越长引用漂移越严重 (strong)
    - [liu2024survey] RAG agent 通过受控引用库降低自由记忆引用 (strong)
    ## S2 Pipelines
    - [shen2026audit] 证据优先审计可扩展到整本参考文献 (strong)
    - [gomez2025gate] 确定性闸门是多智能体写作的收敛机制 (strong)
    - [yang2024depthanything] 自训练闭环同样出现在稠密预测任务 (weak)
    - [vaswani2017attention] 注意力机制是这些系统的共同底座 (weak)
    """)

BANK_BAD = textwrap.dedent("""\
    # Citation bank — 带三类违规
    - [ghost2030survey] 库外 key：这条引用不在 references.bib (strong)
    - [gomez2025gate] 缺强度标注的行，应被格式检查拦下
    - [shen2026audit] 短 (weak)
    - [he2016deep] 旧文献拉低近三年占比 (weak)
    - [vaswani2017attention] 旧文献拉低近三年占比 (weak)
    - [kingma2015adam] 旧文献拉低近三年占比 (weak)
    - [devlin2019bert] 旧文献拉低近三年占比 (weak)
    """)


def write_gate_project(root: str) -> dict[str, str]:
    """在 root 下生成真实规模稿件工程，返回关键路径。"""
    paths = {
        "drafts": os.path.join(root, "drafts"),
        "sections": os.path.join(root, "drafts", "sections"),
        "figures": os.path.join(root, "drafts", "figures"),
        "library": os.path.join(root, "library"),
        "notes": os.path.join(root, "notes"),
        "broken": os.path.join(root, "drafts_broken"),
    }
    for p in paths.values():
        os.makedirs(p, exist_ok=True)
    w = {
        "main_tex": (os.path.join(paths["drafts"], "main.tex"), MAIN_TEX),
        "intro": (os.path.join(paths["sections"], "01_intro.tex"), SECTION_INTRO),
        "method": (os.path.join(paths["sections"], "02_method.tex"), SECTION_METHOD),
        "bib": (os.path.join(paths["library"], "references.bib"), GATES_BIB),
        "bank_ok": (os.path.join(paths["notes"], "citation_bank.md"), BANK_OK),
        "bank_bad": (os.path.join(paths["notes"], "citation_bank_bad.md"), BANK_BAD),
        "broken_main": (os.path.join(paths["broken"], "main.tex"), MAIN_TEX_BROKEN),
    }
    out: dict[str, str] = {k: v for k, (v, _) in w.items()}
    for path, content in w.values():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    # 图文件（PDF 占位）与 broken 工程共享的 intro
    open(os.path.join(paths["figures"], "arch.pdf"), "wb").write(b"%PDF-1.4 live-test placeholder\n")
    os.makedirs(os.path.join(paths["broken"], "sections"), exist_ok=True)
    with open(os.path.join(paths["broken"], "sections", "01_intro.tex"), "w",
              encoding="utf-8") as f:
        f.write(SECTION_INTRO)
    out.update({k: p for k, p in paths.items()})
    return out
