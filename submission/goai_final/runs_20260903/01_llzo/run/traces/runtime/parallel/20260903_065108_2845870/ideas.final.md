已完成 `goai-idea-forge` 全流程，产物位于指定 workspace：

三条研究方向：

1. 锂活度/反应路径控制的 cubic Al–LLZO  
   采用 16-cell 分阶段交互设计，控制 Li 前驱体加入顺序、覆盖几何、压片厚度与 Li 保留。

2. 超快烧结后的表面层—界面输运耦合  
   锁定 cubic Li6.25Al0.25La3Zr2O12，使用四类 sister specimens 分别测量烧结前后表面化学、Li 保留、界面阻抗和 CCD。

3. Ta–LLZO 晶界化学与标准化输运  
   以 Bae 2026 Li2CO3/LiOH 结果为复现实验基线，采用匹配密度嵌套设计，并强制 STEM-EDS/EELS 或校准 ToF-SIMS 晶界表征。

核心文件：

- [proposal_li_activity_pathway.md](<HOME>
- [experiment_li_activity_pathway.json](<HOME>
- [proposal_ultrafast_surface_layer.md](<HOME>
- [experiment_ultrafast_surface_layer.json](<HOME>
- [proposal_ta_gb_transport.md](<HOME>
- [experiment_ta_gb_transport.json](<HOME>

审核与引用核查：

- [review_log.md](<HOME>
- [review_round1.md](<HOME>
- [review_round2.md](<HOME>
- [review_round3.md](<HOME>
- [ref_guard_round2.md](<HOME>

结果：首轮 3 个 MAJOR，经过迭代后第三轮为 3 个 provisional PASS；0 blocker、0 major，账本 issue I1–I8 全部关闭。提案引用二次 `verify_entry` 为 16/16 PASS。每条材料方向均调用了 `inorganic_model_status`、`predict_precursor_routes` 和实验方案骨架生成器；所有模型路线均标注“演示数据，非化学结论”，并保留 `chemical_route_verified=false` 与 EHS/NOT FOR LAB USE 限制。

`ideas_reviewed` gate 已通过并写入 loopctl，最终状态为 PASS。