已完成独立中文综述返工。

- 按`skills/goai-survey-writer/SKILL.md`执行，并先运行`python3 tools/loopctl.py status`。
- 逐节通读并润色全部指定章节，重点调整：
  - 引言改为“研究目标与材料体系→同类体系已有发现→论文结构”；
  - 条件矩阵前先总结前人实验结论；
  - 全文改用短句、主动语态和无机材料学术语；
  - 删除中英文、数字周围手工空格；
  - 四个未来方向均补充前驱体、工艺，并标注“模型预测，待实验验证”；
  - 结论明确下一步优先实验为目标组成附近的小步长局部相图。
- 在[revision_log.md](/home/gaojing/goai_cold_full_byzso_m2gfJJ/workspace/drafts/revision_log.md)记录了各文件的代表性改写、保留的证据边界和终检结果。
- 未修改`references.bib`、figspec、图文件、taxonomy或证据审计；未设置任何 gate。

最终检查结果：

- `academic_language_guard`: PASS
- `bib_guard`: PASS；整合率100%，引用密度41.3次/千词
- `tex_guard`: PASS
- 所有声明产物均已保存且非空。