"""投稿：调 bili CLI（https://github.com/kukemc/bili-cli）。"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


def bili() -> str:
    exe = os.environ.get("BILI_BIN") or shutil.which("bili") or str(Path.home() / ".local" / "bin" / "bili")
    if not Path(exe).exists() and not shutil.which(exe):
        raise SystemExit("找不到 bili 命令，先 `uv tool install bili-agent`（见 docs/03-bili-login.md）")
    return exe


def upload(cfg, video: Path, title: str, tags: list[str], desc: str = "", cover: Path | None = None) -> dict:
    cmd = [bili(), "upload", "video", str(video), "--title", title,
           "--zone", str(cfg.get("bili.zone", 1010)), "--tid", str(cfg.get("bili.tid", 124)),
           "--desc", desc or title, "--dynamic", cfg.get("outro", "新的一条")]
    if cfg.get("bili.no_reprint", True):
        cmd.append("--no-reprint")
    if cfg.get("bili.ai_declare", True):
        cmd.append("--ai-declare")
    if cover and Path(cover).exists():
        cmd += ["--cover", str(cover)]
    for t in tags[:5]:
        cmd += ["--tag", t]
    p = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        return {"ok": False, "raw": (p.stdout or "")[-500:] + (p.stderr or "")[-500:]}
