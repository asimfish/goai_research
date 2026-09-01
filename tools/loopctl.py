#!/usr/bin/env python3
"""loopctl —— 多 agent 回环账本（单一状态源，所有 agent 只通过它交接）。

账本文件：<workspace>/state/ledger.json
并发安全：所有命令在 ledger.json.lock 排它锁内执行读-改-写，多 agent 并发调用不丢更新。

用法：
  loopctl.py init --topic "扩散模型综述" [--max-rounds 5] [--effort balanced]
                  [--strictness normal] [--auto-proceed true]
  loopctl.py status [--json]
  loopctl.py advance --to lit_search
  loopctl.py gate --name lit_coverage --status PASS --detail "12 子主题全覆盖" \
                  [--receipt "model=<审稿模型>;trace=<存档路径>"] \
                  [--inputs workspace/library/references.bib,workspace/drafts/main.tex]
  loopctl.py issue add --from-agent reviewer --target writing --severity major --text "..."
  loopctl.py issue close --id I3 [--note "已改"]
  loopctl.py issue list [--open]
  loopctl.py log --stage writing --agent survey-writer --event draft --detail "sec3 v2"
  loopctl.py next-round
  loopctl.py check-done   # 必需 gate 全部已记录且为 PASS/WARN、无 open blocker/major
                          # → exit 0；gate 带 --inputs 指纹的会先重算，上游产物变更即
                          # 置回 PENDING（stale）；review_pass 的回执 trace 必须真实存在

gate 状态语义：
  PASS    通过；PASS 前建议带 --inputs 记录产物指纹；review_pass 记 PASS
          **必须**带 --receipt "model=<审稿模型>;trace=<存档路径>"，且 trace 文件
          存在且非占位（无回执/空 trace 的审稿等于没审，命令直接拒绝）
  FAIL    未通过，阻塞 check-done
  WARN    合规跳过/带保留通过（如 ideas 支线跳过），不阻塞 check-done
  PENDING 待复审（级联失效重置用），阻塞 check-done

必需 gate（check-done 要求每一个都已记录，缺任何一个 = 该阶段从未执行 = 未完成；
跳过要显式记 WARN，禁止静默跳过）：
  scope_confirmed lit_coverage style_bank_ready ref_integrity taxonomy_ready
  figures_ready ideas_reviewed draft_complete review_pass
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone

STAGES = ["intake", "scoping", "lit_search", "ref_gate", "taxonomy",
          "figures", "ideas", "writing", "review", "final"]
# 全流程必需闸门：check-done 只认「全部已记录」，防止账本停在半路就宣告完成
REQUIRED_GATES = ["scope_confirmed", "lit_coverage", "style_bank_ready",
                  "ref_integrity", "taxonomy_ready", "figures_ready",
                  "ideas_reviewed", "draft_complete", "review_pass"]
# 记 PASS 必须带审稿回执的闸门
RECEIPT_GATES = {"review_pass"}
# 回执 trace 的最小体量：完整的审稿提问+回复不可能低于此，低于即视为占位文件
RECEIPT_TRACE_MIN_BYTES = 512


def _parse_receipt(raw: str) -> dict[str, str]:
    """解析 "model=<x>;trace=<path>" 形态的回执。"""
    out: dict[str, str] = {}
    for part in (raw or "").split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def _receipt_problem(raw: str) -> str | None:
    """回执不合规时返回原因；合规返回 None。"""
    r = _parse_receipt(raw)
    if not r.get("model") or not r.get("trace"):
        return ('缺回执或格式不对，需 --receipt "model=<审稿模型>;trace=<存档路径>"'
                '（无回执的审稿等于没审）')
    trace = r["trace"]
    if not os.path.isfile(trace):
        return f"回执 trace 文件不存在: {trace}（先落盘审稿原始问答再置 gate）"
    if os.path.getsize(trace) < RECEIPT_TRACE_MIN_BYTES:
        return (f"回执 trace 疑似占位文件（{os.path.getsize(trace)} B < "
                f"{RECEIPT_TRACE_MIN_BYTES} B）: {trace}")
    return None


def _ws() -> str:
    return os.environ.get("GOAI_WORKSPACE", "workspace")


def _path() -> str:
    return os.path.join(_ws(), "state", "ledger.json")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: str) -> str:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return "MISSING"


@contextmanager
def _locked():
    """命令全周期排它锁：读-改-写序列互斥，防止并发覆盖丢更新。"""
    os.makedirs(os.path.dirname(_path()), exist_ok=True)
    with open(_path() + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lk, fcntl.LOCK_UN)


def load() -> dict:
    """读账本；缺失/损坏时给可执行的提示，而不是 12 行 Python traceback。

    多 agent 通过本工具交接，调用方（含 LLM agent）只看 stderr 尾行，
    裸 FileNotFoundError 无法区分「忘了 init」与「GOAI_WORKSPACE 指错」。
    """
    try:
        with open(_path(), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        sys.exit(f"账本不存在: {_path()}\n"
                 '请先初始化: loopctl.py init --topic "<研究主题>"；'
                 f"若已初始化过，检查 GOAI_WORKSPACE 是否指向正确工作区"
                 f"（当前 = {_ws()}）")
    except json.JSONDecodeError as e:
        sys.exit(f"账本 JSON 已损坏: {_path()}（{e}）\n"
                 "请人工修复该文件，或用 init --force 重建（会丢失回环历史）")


def save(ledger: dict) -> None:
    os.makedirs(os.path.dirname(_path()), exist_ok=True)
    tmp = _path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _path())


def cmd_init(args) -> None:
    if os.path.exists(_path()) and not args.force:
        sys.exit(f"账本已存在: {_path()}（--force 覆盖）")
    ledger = {
        "topic": args.topic, "created": _now(),
        "round": 1, "max_rounds": args.max_rounds,
        "effort": args.effort, "strictness": args.strictness,
        "auto_proceed": args.auto_proceed == "true",
        "stage": "intake", "stages": STAGES,
        "gates": {}, "issues": [], "next_issue_id": 1, "log": [],
    }
    save(ledger)
    print(f"已初始化回环账本: {_path()}  topic={args.topic}  "
          f"effort={args.effort} strictness={args.strictness} "
          f"auto_proceed={args.auto_proceed}")


def cmd_status(args) -> None:
    lg = load()
    open_issues = [i for i in lg["issues"] if i["status"] == "open"]
    if args.json:
        print(json.dumps({**lg, "open_issue_count": len(open_issues)},
                         ensure_ascii=False, indent=2))
        return
    print(f"topic     : {lg['topic']}")
    print(f"round     : {lg['round']}/{lg['max_rounds']}   stage: {lg['stage']}")
    print(f"mode      : effort={lg.get('effort', 'balanced')} "
          f"strictness={lg.get('strictness', 'normal')} "
          f"auto_proceed={lg.get('auto_proceed', True)}")
    print("gates     :")
    for name, g in lg["gates"].items():
        extra = "  [有回执]" if g.get("receipt") else ""
        print(f"  - {name}: {g['status']}  ({g.get('detail', '')}){extra}")
    missing = [g for g in REQUIRED_GATES if g not in lg["gates"]]
    if missing:
        print(f"  未记录的必需 gate（check-done 前须全部落账）: {', '.join(missing)}")
    print(f"open issue: {len(open_issues)}")
    for i in open_issues:
        print(f"  - [{i['id']}][{i['severity']}] {i['from']} → {i['target']}: "
              f"{i['text'][:80]}")


def cmd_advance(args) -> None:
    lg = load()
    if args.to not in lg["stages"]:
        sys.exit(f"未知 stage『{args.to}』，可选: {lg['stages']}")
    lg["log"].append({"ts": _now(), "round": lg["round"], "event": "advance",
                      "from": lg["stage"], "to": args.to})
    lg["stage"] = args.to
    save(lg)
    print(f"round {lg['round']} → stage {args.to}")


def cmd_gate(args) -> None:
    lg = load()
    if args.name in RECEIPT_GATES and args.status == "PASS":
        problem = _receipt_problem(args.receipt)
        if problem:
            sys.exit(f"拒绝: gate {args.name} 记 PASS —— {problem}")
    if args.name not in REQUIRED_GATES:
        # 自造 gate 名（ref_audit / review_round1 …）不计入必需集，账本会
        # 「看起来全 PASS」却过不了 check-done——当场提醒，别等收尾才发现
        print(f"警告: 『{args.name}』不是协议 gate 名，不计入 check-done 必需集。"
              f"协议名: {', '.join(REQUIRED_GATES)}（辅助 gate 可保留，但对应"
              "阶段仍须用协议名落账）", file=sys.stderr)
    entry = {"status": args.status, "detail": args.detail,
             "round": lg["round"], "at": _now()}
    if args.receipt:
        entry["receipt"] = args.receipt
    if args.inputs:
        entry["inputs"] = [{"path": p.strip(), "sha256": _sha256(p.strip())}
                           for p in args.inputs.split(",") if p.strip()]
    lg["gates"][args.name] = entry
    lg["log"].append({"ts": _now(), "round": lg["round"], "event": "gate",
                      "gate": args.name, "status": args.status,
                      "detail": args.detail})
    save(lg)
    missing = [fp["path"] for fp in entry.get("inputs", [])
               if fp["sha256"] == "MISSING"]
    print(f"gate {args.name} = {args.status}")
    if missing:
        print(f"警告: --inputs 中文件不存在: {missing}")


def cmd_issue(args) -> None:
    lg = load()
    if args.action == "add":
        iid = f"I{lg['next_issue_id']}"
        lg["next_issue_id"] += 1
        lg["issues"].append({
            "id": iid, "from": args.from_agent, "target": args.target,
            "severity": args.severity, "text": args.text,
            "status": "open", "round_opened": lg["round"]})
        save(lg)
        print(f"新 issue {iid} → {args.target}")
    elif args.action == "close":
        for i in lg["issues"]:
            if i["id"] == args.id:
                i["status"] = "closed"
                i["round_closed"] = lg["round"]
                if args.note:
                    i["close_note"] = args.note
                save(lg)
                print(f"issue {args.id} 已关闭")
                return
        sys.exit(f"找不到 issue {args.id}")
    else:  # list
        for i in lg["issues"]:
            if args.open and i["status"] != "open":
                continue
            print(f"[{i['id']}][{i['status']}][{i['severity']}] "
                  f"{i['from']} → {i['target']}: {i['text']}")


def cmd_log(args) -> None:
    lg = load()
    lg["log"].append({"ts": _now(), "round": lg["round"], "stage": args.stage,
                      "agent": args.agent, "event": args.event,
                      "detail": args.detail})
    save(lg)
    print("logged")


def cmd_next_round(_args) -> None:
    lg = load()
    if lg["round"] >= lg["max_rounds"]:
        sys.exit(f"已达最大回合 {lg['max_rounds']}；如需继续请提高 max_rounds "
                 "或人工收敛（回环不允许无限迭代）")
    lg["round"] += 1
    lg["log"].append({"ts": _now(), "round": lg["round"], "event": "next_round"})
    save(lg)
    print(f"进入 round {lg['round']}")


def cmd_check_done(_args) -> None:
    lg = load()

    # stale 检测：gate 带 inputs 指纹的重算一遍，上游产物变更 → 置回 PENDING。
    # 旧审计不得当新审计用，级联失效不依赖编排者记性。
    stale = []
    for name, g in lg["gates"].items():
        if g["status"] != "PASS":
            continue
        for fp in g.get("inputs", []):
            if _sha256(fp["path"]) != fp["sha256"]:
                stale.append(name)
                break
    if stale:
        for name in stale:
            lg["gates"][name]["status"] = "PENDING"
            lg["gates"][name]["detail"] = (
                lg["gates"][name].get("detail", "")
                + " [stale: 上游产物已变更，需复审]").strip()
            lg["log"].append({"ts": _now(), "round": lg["round"],
                              "event": "gate_stale", "gate": name})
        save(lg)

    # 放行语义：WARN=合规跳过不阻塞；open minor 移交 final 阶段清理、不阻塞
    blocking_issues = [i for i in lg["issues"]
                       if i["status"] == "open"
                       and i["severity"] in ("blocker", "major")]
    minor_open = [i["id"] for i in lg["issues"]
                  if i["status"] == "open" and i["severity"] == "minor"]
    failing = {k: v for k, v in lg["gates"].items()
               if v["status"] not in ("PASS", "WARN")}
    # 必需 gate 缺席 = 该阶段从未执行（账本停在半路不得宣告完成）
    missing = [g for g in REQUIRED_GATES if g not in lg["gates"]]
    # 审稿回执再核一遍：账本可能被非本工具写入，trace 也可能事后被删
    bad_receipts = {}
    for name in RECEIPT_GATES:
        g = lg["gates"].get(name)
        if g and g["status"] == "PASS":
            problem = _receipt_problem(g.get("receipt", ""))
            if problem:
                bad_receipts[name] = problem
    if not blocking_issues and not failing and not missing and not bad_receipts:
        msg = "DONE: 必需 gate 全部记录且 PASS/WARN，无 open blocker/major"
        if minor_open:
            msg += f"（open minor {minor_open} 移交 final 阶段清理后逐条 close）"
        print(msg)
        sys.exit(0)
    print(json.dumps({"done": False,
                      "failing_gates": failing,
                      "missing_required_gates": missing,
                      "invalid_receipts": bad_receipts,
                      "stale_gates": stale,
                      "open_blocking_issues": [i["id"] for i in blocking_issues],
                      "open_minor_issues": minor_open},
                     ensure_ascii=False))
    sys.exit(1)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init")
    sp.add_argument("--topic", required=True)
    sp.add_argument("--max-rounds", type=int, default=5)
    sp.add_argument("--effort", default="balanced",
                    choices=["lite", "balanced", "max"])
    sp.add_argument("--strictness", default="normal",
                    choices=["normal", "strict"])
    sp.add_argument("--auto-proceed", dest="auto_proceed", default="true",
                    choices=["true", "false"])
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(fn=cmd_init)

    sp = sub.add_parser("status")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_status)

    sp = sub.add_parser("advance")
    sp.add_argument("--to", required=True)
    sp.set_defaults(fn=cmd_advance)

    sp = sub.add_parser("gate")
    sp.add_argument("--name", required=True)
    sp.add_argument("--status", required=True,
                    choices=["PASS", "FAIL", "WARN", "PENDING"])
    sp.add_argument("--detail", default="")
    sp.add_argument("--receipt", default="",
                    help="审稿回执：模型名/会话标识/trace 存档路径")
    sp.add_argument("--inputs", default="",
                    help="逗号分隔的产物文件列表，记录 sha256 指纹供 stale 检测")
    sp.set_defaults(fn=cmd_gate)

    sp = sub.add_parser("issue")
    sp.add_argument("action", choices=["add", "close", "list"])
    sp.add_argument("--from-agent", default="reviewer")
    sp.add_argument("--target", default="writing")
    sp.add_argument("--severity", default="major",
                    choices=["blocker", "major", "minor"])
    sp.add_argument("--text", default="")
    sp.add_argument("--id", default="")
    sp.add_argument("--note", default="")
    sp.add_argument("--open", action="store_true")
    sp.set_defaults(fn=cmd_issue)

    sp = sub.add_parser("log")
    sp.add_argument("--stage", required=True)
    sp.add_argument("--agent", required=True)
    sp.add_argument("--event", required=True)
    sp.add_argument("--detail", default="")
    sp.set_defaults(fn=cmd_log)

    sp = sub.add_parser("next-round")
    sp.set_defaults(fn=cmd_next_round)

    sp = sub.add_parser("check-done")
    sp.set_defaults(fn=cmd_check_done)

    args = p.parse_args()
    with _locked():
        args.fn(args)


if __name__ == "__main__":
    main()
