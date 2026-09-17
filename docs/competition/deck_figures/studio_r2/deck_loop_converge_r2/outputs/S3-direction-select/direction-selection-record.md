# S3-DIRECTION-SELECT (round 2) — deck_loop_converge_r2

## issue ledger（逐候选，语义与视觉分开记）
### C01
- [medium] (semantic) 「写不进去」「不收敛」两条线从 loopctl 指向 升级人类（应分别指向账本写入口、出自回环）
- [none] (visual) 大回环 + 2×2 互搏卡（角色成对）+ 四张轮次卡 4/7/0/=0，信息最完整
### C02
- [high] (semantic) 编排器角色出现在「路由返工」段；loopctl 被串进主流程；结尾的 Done! 庆祝偏娱乐
- [none] (visual) 角色表现力强
### C03
- [high] (semantic) 气泡方向与发言人不符（"第 1 轮：7 项 issue" 应由审稿人发出）
- [none] (visual) 对话式回环最像 ARIS 的 auto-review hero：轮次即叙事，机械闸门在右侧成列
### C04
- [medium] (visual) 收敛阶梯与下方轮次卡重复表达同一组数字
- [none] (visual) 阶梯上的角色让"4→7→0"一眼可读

## S2 exploration aggregate
- high 级问题共 2 条，全部是语义类（并行画成串行、成员漂移、弧线起止点错）——表面风格已达标，问题出在生图模型不守拓扑。

## direction selection
- selected_direction: C01 的构图（本轮产物 → 2×2 互搏卡 → 路由返工 → 大回环；机械放行在右；底部四张轮次卡）为主方向；C03 的对话式回环留作备选构图
- user_preferred_first_round_candidate_ids: 无（作者尚未点名）
- S5 避免: loopctl 串进主流程；升级人类接回回环；庆祝式装饰
- S5 转化: 语义由条件线框锁死：绿色 0 blocker/major 直通 check-done；橙色 U 形回环 级联失效→本轮产物；红色虚线 不收敛→升级人类
- 方法变更：S5 改为「条件线框锁语义」的 bake；可编辑交付件 = 线框（原生对象）+ 素材表裁出的插画。
