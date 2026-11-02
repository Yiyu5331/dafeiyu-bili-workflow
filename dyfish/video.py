"""Remotion 模板渲染：写 timeline.ts → npx remotion render。"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = PKG_ROOT / "template" / "remotion"


def ensure_template(cfg) -> Path:
    dst = cfg.workspace / "template" / "remotion"
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(TEMPLATE, dst)
    if not (dst / "node_modules").exists():
        print("首次使用，安装 Remotion 依赖（~1 分钟）…")
        subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=dst, check=True)
    return dst


def write_timeline(proj: Path, tl: dict, lines: list[str]) -> None:
    L = tl["lines"]
    n = len(L)
    dur = tl["total"]
    algo_start = max(0.4, L[5]["start"] - 0.15) if n > 6 else dur * 0.4
    swipe_a = max(algo_start + 0.8, L[6]["start"] - 0.1) if n > 7 else algo_start + 1.2
    swipe_b = (L[8]["end"] + 0.2) if n > 9 else swipe_a + 2.4
    clock_start = max(swipe_b + 0.3, L[n - 2]["start"] - 0.15)
    flip_start = min(max(clock_start + 1.0, L[n - 1]["start"] - 0.25), dur + 0.6 - 0.8)
    total = dur + 0.6

    out = ["// 由 dyfish 自动生成，不要手改", "export type TL = {",
           "  total: number;", "  lines: Array<{ s: number; e: number; text: string }>;",
           "  hookEnd: number; algoStart: number; algoDur: number; swipeA: number; swipeB: number;",
           "  clockStart: number; clockDur: number; flipStart: number;", "};", "", "export const TL: TL = {",
           f"  total: {total:.3f},", "  lines: ["]
    for ln in L:
        out.append(f"    {{ s: {ln['start']:.3f}, e: {ln['end']:.3f}, text: {json.dumps(ln['text'], ensure_ascii=False)} }},")
    out += ["  ],",
            f"  hookEnd: {max(1.2, L[5]['start'] - 0.3):.2f}, algoStart: {algo_start:.2f}, "
            f"algoDur: {max(swipe_a - algo_start, 0.8):.2f},",
            f"  swipeA: {swipe_a:.2f}, swipeB: {swipe_b:.2f},",
            f"  clockStart: {clock_start:.2f}, clockDur: {max(flip_start - clock_start, 0.8):.2f}, "
            f"flipStart: {flip_start:.2f},", "};", ""]
    (proj / "src" / "timeline.ts").write_text("\n".join(out), encoding="utf-8")


def render(cfg, voice: Path, out_mp4: Path, concurrency: int | None = None) -> None:
    proj = ensure_template(cfg)
    shutil.copyfile(voice, proj / "public" / "voice_v6.mp3")
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "PhoneUI", str(out_mp4),
                    f"--concurrency={concurrency or cfg.get('video.concurrency', 4)}"], cwd=proj, check=True)
