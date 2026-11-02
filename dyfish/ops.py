"""运营侧：刷、拆、回、看数据。全部走 bili CLI 的 JSON 输出。"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .upload import bili


def _run(args: list[str], timeout: int = 180) -> dict:
    p = subprocess.run([bili(), *args], capture_output=True, text=True, timeout=timeout)
    out = (p.stdout or "").strip().splitlines()
    for line in reversed(out):
        try:
            return json.loads(line)
        except Exception:  # noqa: BLE001
            continue
    return {"ok": False, "error": {"code": "parse_failed", "message": (p.stderr or p.stdout or "")[-300:]}}


def _cards(data) -> list[dict]:
    """bili 返回的列表结构不统一，这里抠出 [{title, bvid, ...}]。"""
    if isinstance(data, dict):
        for k in ("items", "list", "videos", "data"):
            if isinstance(data.get(k), list):
                return data[k]
        return [data]
    if isinstance(data, list):
        return data
    return []


def scroll(cfg, limit: int = 12, zone: str | None = None) -> list[dict]:
    """刷：热门 + 推荐，挑出还没看过的候选选题。"""
    seen = Path(cfg.workspace) / "work" / "seen.json"
    seen_set = set(json.loads(seen.read_text(encoding="utf-8"))) if seen.exists() else set()
    out: list[dict] = []

    calls = [["hot", "popular", "--size", str(min(limit, 50)), "--unseen"],
             ["hot", "rank", "--limit", str(min(limit, 100)), "--unseen"],
             ["feed", "recommend", "-n", str(min(limit, 30)), "--unseen"]]
    if zone:
        calls[1] = ["hot", "rank", "--zone", zone, "--limit", str(min(limit, 100)), "--unseen"]
    for args in calls:
        r = _run(args)
        for it in _cards(r.get("data") if r.get("ok") else {}):
            bv = it.get("bvid") or it.get("bv") or ""
            if not bv or bv in seen_set:
                continue
            author = it.get("author") or it.get("owner") or {}
            stat = it.get("stat") or {}
            out.append({"bvid": bv, "title": it.get("title", ""),
                        "owner": author.get("name") if isinstance(author, dict) else author,
                        "views": stat.get("view") or it.get("view") or it.get("play"),
                        "duration": it.get("duration"),
                        "from": " ".join(args[:2])})
            seen_set.add(bv)
    seen.parent.mkdir(parents=True, exist_ok=True)
    seen.write_text(json.dumps(sorted(seen_set)[-800:], ensure_ascii=False), encoding="utf-8")
    return out[: limit * 2]


def inspect(bv: str) -> dict:
    """拆：一条命令拿全（AI 总结/字幕/热评/画面总览/弹幕亮点）。"""
    r = _run(["video", "watch", bv, "--frames", "9", "--comments", "5"], timeout=300)
    return r


def inbox(limit: int = 10) -> dict:
    """回：收件箱 + 还没回的评论。"""
    return {"feed": _run(["feed", "inbox"]), "unreplied": _run(["comment", "list", "--unreplied", "--size", str(limit)])}


def reply(bv: str, comment_id: str, text: str, reply_to: str | None = None) -> dict:
    args = ["comment", "reply", bv, comment_id, text]
    if reply_to:
        args += ["--root", reply_to]
    return _run(args)


def dm(uid: str, text: str) -> dict:
    return _run(["dm", "send", uid, text])


def stats() -> dict:
    """看：账号总览 + 30 天趋势 + 稿件数据。"""
    return {
        "overview": _run(["data", "overview"]),
        "trend": _run(["data", "trend"]),
        "videos": _run(["data", "videos"]),
    }


def pick_topics(candidates: list[dict], n: int = 2) -> list[str]:
    """从候选里挑标题最像「可以讲清楚的一个点」的，去掉太长太短的。"""
    good = [c for c in candidates if 6 <= len(c.get("title", "")) <= 40]
    return [c["title"] for c in good[:n]]


def report(ws: Path) -> Path:
    """把当天运营情况写一份 md 日报。"""
    s = stats()
    lines = ["# 运营日报", ""]
    for key, r in s.items():
        lines.append(f"## {key}")
        lines.append("```json")
        lines.append(json.dumps(r.get("data") if r.get("ok") else r.get("error"), ensure_ascii=False, indent=2)[:2000])
        lines.append("```")
        lines.append("")
    p = ws / "out" / "日报.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines), encoding="utf-8")
    return p
