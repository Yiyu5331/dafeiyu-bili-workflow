"""dyfish 命令行。"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from . import cover as cover_mod
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

    a = ap.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
