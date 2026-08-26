#!/usr/bin/env python3
"""loopctl —— 多 agent 回环账本（单一状态源，所有 agent 只通过它交接）。

账本文件：<workspace>/state/ledger.json
用法：
  loopctl.py init --topic "扩散模型综述" [--max-rounds 5]
  loopctl.py status [--json]
  loopctl.py advance --to lit_search
  loopctl.py gate --name lit_coverage --status PASS --detail "12 子主题全覆盖"
  loopctl.py issue add --from-agent reviewer --target writing --severity major --text "..."
  loopctl.py issue close --id I3 [--note "已改"]
  loopctl.py issue list [--open]
  loopctl.py log --stage writing --agent survey-writer --event draft --detail "sec3 v2"
  loopctl.py next-round
  loopctl.py check-done        # 全 gate PASS 且无 open issue → exit 0
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

STAGES = ["intake", "scoping", "lit_search", "ref_gate", "taxonomy",
          "figures", "ideas", "writing", "review", "final"]


def _ws() -> str:
    return os.environ.get("GOAI_WORKSPACE", "workspace")


def _path() -> str:
    return os.path.join(_ws(), "state", "ledger.json")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load() -> dict:
    with open(_path(), encoding="utf-8") as f:
        return json.load(f)


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
        "stage": "intake", "stages": STAGES,
        "gates": {}, "issues": [], "next_issue_id": 1, "log": [],
    }
    save(ledger)
    print(f"已初始化回环账本: {_path()}  topic={args.topic}")


def cmd_status(args) -> None:
    lg = load()
    open_issues = [i for i in lg["issues"] if i["status"] == "open"]
    if args.json:
        print(json.dumps({**lg, "open_issue_count": len(open_issues)},
                         ensure_ascii=False, indent=2))
        return
    print(f"topic     : {lg['topic']}")
    print(f"round     : {lg['round']}/{lg['max_rounds']}   stage: {lg['stage']}")
    print("gates     :")
    for name, g in lg["gates"].items():
        print(f"  - {name}: {g['status']}  ({g.get('detail', '')})")
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
    lg["gates"][args.name] = {"status": args.status, "detail": args.detail,
                              "round": lg["round"], "at": _now()}
    lg["log"].append({"ts": _now(), "round": lg["round"], "event": "gate",
                      "gate": args.name, "status": args.status,
                      "detail": args.detail})
    save(lg)
    print(f"gate {args.name} = {args.status}")


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
    open_issues = [i for i in lg["issues"] if i["status"] == "open"]
    failing = {k: v for k, v in lg["gates"].items() if v["status"] != "PASS"}
    if not open_issues and not failing and lg["gates"]:
        print("DONE: 全部 gate PASS 且无 open issue")
        sys.exit(0)
    print(json.dumps({"done": False,
                      "failing_gates": failing,
                      "open_issues": [i["id"] for i in open_issues]},
                     ensure_ascii=False))
    sys.exit(1)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init")
    sp.add_argument("--topic", required=True)
    sp.add_argument("--max-rounds", type=int, default=5)
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
    sp.add_argument("--status", required=True, choices=["PASS", "FAIL", "WARN"])
    sp.add_argument("--detail", default="")
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
    args.fn(args)


if __name__ == "__main__":
    main()
