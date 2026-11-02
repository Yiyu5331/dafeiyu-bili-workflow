"""dyfish 命令行。"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from . import cover as cover_mod
from . import ops
from .config import CONFIG_PATH, Config
from .script import write_script
from .tts import make_voice
from .upload import upload as do_upload
from .video import render, write_timeline


def _need(*bins):
    miss = [b for b in bins if not shutil.which(b)]
    if miss:
        print(f"！缺少命令：{', '.join(miss)}")


def cmd_init(a):
    cfg = Config.create_default(a.workspace)
    for d in ["secrets", "assets", "work", "out"]:
        (cfg.workspace / d).mkdir(parents=True, exist_ok=True)
    print(f"配置写到 {CONFIG_PATH}")
    print(f"工作区 {cfg.workspace}")
    print("下一步：把三份密钥放进 secrets/，参考音放 assets/ref.mp3，再跑 dyfish doctor")


def cmd_doctor(a):
    cfg = Config.load()
    print(f"配置：{cfg.path}")
    print(f"工作区：{cfg.workspace}")
    for name, key in [("DeepSeek key", "deepseek.key"), ("火山 APP ID", "volc.app_id"),
                      ("火山 Access Token", "volc.access_token")]:
        try:
            v = cfg.secret(key)
            print(f"  {name}: {v[:4]}…{v[-4:]}（{len(v)} 位）")
        except SystemExit as e:
            print(f"  {name}: ✗ {e}")
    ref = cfg.p("voice.reference_audio")
    print(f"  参考音：{ref} {'✓' if ref.exists() else '✗ 缺失'}")
    print(f"  bili: {shutil.which('bili') or '✗ 未安装'}")
    print(f"  ffmpeg: {shutil.which('ffmpeg') or '✗ 未安装'}")
    print(f"  node: {shutil.which('node') or '✗ 未安装'}")
    print("\n参考音建议 5-15 秒、单人、无背景音乐；种子选好后音色会一直被它锚住。")


def cmd_script(a):
    cfg = Config.load()
    sc = write_script(cfg, a.topic, a.seconds)
    print(json.dumps(sc, ensure_ascii=False, indent=2))


def _produce(cfg, topic, slug, skip_upload=False):
    import hashlib

    slug = slug or hashlib.md5(topic.encode()).hexdigest()[:8]
    out = cfg.workspace / "out" / f"phone-{slug}"
    out.mkdir(parents=True, exist_ok=True)

    print("① 写稿…")
    sc = write_script(cfg, topic)
    lines = sc["lines"]
    (out / "script.json").write_text(json.dumps(sc, ensure_ascii=False, indent=2), encoding="utf-8")
    print("   ", sc["title"])

    print("② 配音（整篇一次）…")
    work = cfg.workspace / "work" / "audio"
    tl = make_voice(cfg, lines, work)

    print("③ 时间轴…")
    from .video import ensure_template
    proj = ensure_template(cfg)
    write_timeline(proj, tl, lines)
    shutil.copyfile(work / "voice.mp3", proj / "public" / "voice_v6.mp3")

    print("④ 渲染…")
    render(cfg, work / "voice.mp3", out / "out.mp4")

    print("⑤ 封面…")
    frame = cover_mod.grab_frame(out / "out.mp4", out / "cover_frame.jpg")
    cover_mod.make_cover(frame, sc["title"], sc.get("subtitle", ""), out / "cover.jpg")

    (out / "投稿信息.txt").write_text(
        f"标题：{sc['title']}\n分区：知识 {cfg.get('bili.zone')} / tid {cfg.get('bili.tid')}\n"
        f"标签：{'、'.join(sc.get('tags', []))}\n时长：{tl['total']}s\nAI 声明：是\n", encoding="utf-8")
    print("完成：", out)

    if a_upload(a):
        r = do_upload(cfg, out / "out.mp4", sc["title"], sc.get("tags", []), sc.get("subtitle", ""), out / "cover.jpg")
        print("投稿：", r)
    return out


def a_upload(a):
    return getattr(a, "upload", False)


def cmd_video(a):
    cfg = Config.load()
    _produce(cfg, a.topic, a.slug)


def cmd_batch(a):
    cfg = Config.load()
    topics = [t.strip() for t in Path(a.topics).read_text(encoding="utf-8").splitlines()
              if t.strip() and not t.strip().startswith("#")]
    for t in topics[: a.limit]:
        try:
            _produce(cfg, t, None)
        except SystemExit as e:
            print(f"！{t} 失败：{e}")


def cmd_upload(a):
    cfg = Config.load()
    done = 0
    for d in sorted((cfg.workspace / "out").glob("*")):
        if done >= a.limit:
            break
        sc_p, up_p = d / "script.json", d / "uploaded.json"
        if not (sc_p.exists() or (d / "result.json").exists()) or up_p.exists() or not (d / "out.mp4").exists():
            continue
        sc = json.loads((sc_p if sc_p.exists() else d / "result.json").read_text(encoding="utf-8"))
        r = do_upload(cfg, d / "out.mp4", sc.get("title", d.name), sc.get("tags", []),
                      sc.get("subtitle", ""), d / "cover.jpg" if (d / "cover.jpg").exists() else None)
        print(d.name, "->", r.get("ok"), (r.get("data") or {}).get("bvid") or (r.get("error") or {}).get("code"))
        if r.get("ok"):
            up_p.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
            done += 1
        elif (r.get("error") or {}).get("code") == "captcha_required":
            print("被风控了：网页端手动传一条解锁后再跑")
            break


def cmd_scroll(a):
    cfg = Config.load()
    cands = ops.scroll(cfg, a.limit, a.zone)
    for c in cands:
        print(f"{c['bvid']}  {c.get('views') or '?':>10}  {c['title']}")
    if not cands:
        print("没刷到新东西（都看过了？）")
    print("\n挑一个标题丢给：dyfish video --topic \"…\"")


def cmd_inspect(a):
    r = ops.inspect(a.bv)
    print(json.dumps(r.get("data") if r.get("ok") else r.get("error"), ensure_ascii=False, indent=2)[:4000])


def cmd_inbox(a):
    r = ops.inbox(a.limit)
    for k, v in r.items():
        print(f"== {k}")
        print(json.dumps(v.get("data") if v.get("ok") else v.get("error"), ensure_ascii=False, indent=2)[:1500])


def cmd_stats(a):
    r = ops.stats()
    for k, v in r.items():
        print(f"== {k}")
        print(json.dumps(v.get("data") if v.get("ok") else v.get("error"), ensure_ascii=False, indent=2)[:1800])


def cmd_report(a):
    cfg = Config.load()
    p = ops.report(cfg.workspace)
    print("日报写好了：", p)


def cmd_day(a):
    """一天的全流程：刷 → 挑 → 出片 →（投）→ 回 → 复盘。"""
    cfg = Config.load()
    print("① 刷热门找选题…")
    cands = ops.scroll(cfg, a.limit * 6, a.zone)
    print(f"   刷到 {len(cands)} 条没看过的")
    topics = ops.pick_topics(cands, a.topics)
    for t in topics:
        print("   选：", t)
    if not topics:
        print("没挑到合适的选题，先停了")
        return
    for t in topics:
        try:
            _produce(cfg, t, None)
        except SystemExit as e:
            print(f"！{t} 失败：{e}")
    if a.upload:
        print("② 投稿…")
        a.limit = len(topics)
        cmd_upload(a)
    print("③ 收件箱…")
    cmd_inbox(type("A", (), {"limit": 5})())
    print("④ 复盘…")
    p = ops.report(cfg.workspace)
    print("   日报：", p)


def main(argv=None):
    ap = argparse.ArgumentParser("dyfish", description="大肥鱼 B 站出片流水线")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="生成默认配置")
    p.add_argument("--workspace")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("doctor", help="自检：密钥/命令/参考音")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("script", help="只写稿")
    p.add_argument("--topic", required=True)
    p.add_argument("--seconds", type=int, default=16)
    p.set_defaults(func=cmd_script)

    p = sub.add_parser("video", help="一条龙出片")
    p.add_argument("--topic", required=True)
    p.add_argument("--slug")
    p.add_argument("--upload", action="store_true", help="出片后立刻投稿")
    p.set_defaults(func=cmd_video)

    p = sub.add_parser("batch", help="按主题清单批量出片")
    p.add_argument("--topics", required=True, help="每行一个主题的文本文件")
    p.add_argument("--limit", type=int, default=3)
    p.set_defaults(func=cmd_batch)

    p = sub.add_parser("upload", help="把 out/ 下没投的传上去")
    p.add_argument("--limit", type=int, default=2)
    p.set_defaults(func=cmd_upload)

    p = sub.add_parser("scroll", help="刷热门/推荐，挑选题")
    p.add_argument("--limit", type=int, default=12)
    p.add_argument("--zone")
    p.set_defaults(func=cmd_scroll)

    p = sub.add_parser("inspect", help="拆一条视频（AI 总结/字幕/热评/画面）")
    p.add_argument("bv")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("inbox", help="收件箱 + 没回的评论")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_inbox)

    p = sub.add_parser("stats", help="账号数据与稿件数据")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("report", help="写一份运营日报")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("day", help="一天全流程：刷→挑→出片→（投）→回→复盘")
    p.add_argument("--topics", type=int, default=2, help="出几条")
    p.add_argument("--limit", type=int, default=8, help="刷多少条候选")
    p.add_argument("--zone")
    p.add_argument("--upload", action="store_true")
    p.set_defaults(func=cmd_day)

    a = ap.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
