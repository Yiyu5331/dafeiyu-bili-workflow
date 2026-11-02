"""豆包（火山引擎）Seed Audio 语音合成 + 音高对齐。"""
from __future__ import annotations

import base64
import json
import subprocess
import time
import urllib.request
import uuid
from pathlib import Path


def _ref_b64(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"找不到参考音 {path}，放一段你想模仿的 5-15 秒人声（mp3/wav）")
    return base64.b64encode(path.read_bytes()).decode()


def synth_whole(cfg, text: str) -> dict:
    app = cfg.secret("volc.app_id")
    tok = cfg.secret("volc.access_token")
    persona = cfg.get("voice.persona")
    tmpl = cfg.get("voice.template")
    body = {
        "model": cfg.get("volc.resource_id", "seed-audio-1.0"),
        "text_prompt": tmpl.format(persona=persona, text=text),
        "audio_config": {"format": "mp3", "sample_rate": 24000, "enable_subtitle": True},
        "references": [{"audio_data": _ref_b64(cfg.p("voice.reference_audio"))}],
    }
    headers = {
        "X-Api-App-Id": app,
        "X-Api-Access-Key": tok,
        "X-Api-Resource-Id": cfg.get("volc.resource_id", "seed-audio-1.0"),
        "X-Api-Request-Id": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(cfg.get("volc.api"), data=json.dumps(body, ensure_ascii=False).encode(),
                                         headers=headers, method="POST")
            return json.loads(urllib.request.urlopen(req, timeout=300).read().decode())
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 + attempt * 3)
    raise SystemExit(f"语音合成失败：{last}")


def f0_median(path: Path) -> float:
    import numpy as np

    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    fr, hop, res = 1600, 400, []
    for i in range(0, len(x) - fr, hop):
        seg = x[i:i + fr]
        if (seg ** 2).mean() ** 0.5 < 0.01:
            continue
        seg = seg - seg.mean()
        c = np.correlate(seg, seg, "full")[fr - 1:]
        lo, hi = int(16000 / 400), int(16000 / 80)
        k = lo + int(np.argmax(c[lo:hi]))
        if c[k] > 0.3 * c[0]:
            res.append(16000 / k)
    return float(np.median(res)) if res else 0.0


def _dur(p: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout.strip() or 0)


def make_voice(cfg, lines: list[str], out_dir: Path, speed: float | None = None) -> dict:
    """整篇一次合成 → 变速 → 音高对齐 → 音量归一。返回 timeline。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    speed = speed or float(cfg.get("voice.speed", 1.25))
    data = synth_whole(cfg, "\n".join(lines))
    raw = out_dir / "raw.mp3"
    raw.write_bytes(base64.b64decode(data["audio"]))

    # 逐句时间轴（来自接口返回的字级字幕，取每句首尾）
    sents = (data.get("subtitle") or {}).get("sentences") or []
    words = [w for s in sents for w in (s.get("words") or [])]
    text_of = lambda w: (w.get("text") or w.get("word") or "")  # noqa: E731

    # 把字级序列按行切分（去掉标点与空白再累加比对）
    clean = lambda s: "".join(ch for ch in s if ch not in " \n\t，。！？、；：“”‘’…—")  # noqa: E731
    cursor, timeline_lines = 0, []
    joined = clean("".join(text_of(w) for w in words))
    for line in lines:
        target = clean(line)
        start_idx = joined.find(target, cursor)
        if start_idx < 0:
            timeline_lines.append({"text": line, "start": 0.0, "end": 0.0})
            continue
        # 换算成音频时间：按字符比例
        total_chars = max(len(joined), 1)
        dur = _dur(raw)
        s = start_idx / total_chars * dur
        e = (start_idx + len(target)) / total_chars * dur
        timeline_lines.append({"text": line, "start": s, "end": e})
        cursor = start_idx + len(target)

    voice_raw = out_dir / "voice_raw.mp3"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", f"atempo={speed}", str(voice_raw)], check=True)
    sped_total = _dur(voice_raw)

    # 变速后时间同步折算
    for ln in timeline_lines:
        ln["start"] = round(min(ln["start"] / speed, sped_total), 3)
        ln["end"] = round(min(ln["end"] / speed, sped_total), 3)

    # 音高对齐（可选）
    target = cfg.get("voice.pitch_target_hz")
    ref = cfg.p("voice.reference_audio")
    final = out_dir / "voice.mp3"
    src_f0 = f0_median(voice_raw)
    goal = float(target) if target else f0_median(ref)
    ratio = 1.0
    if src_f0 > 0 and goal > 0:
        ratio = max(0.88, min(1.12, goal / src_f0))
    sr = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate",
                             "-of", "csv=p=0", str(voice_raw)], capture_output=True, text=True).stdout.strip() or 48000)
    af = f"asetrate={sr}*{ratio:.4f},aresample={sr},atempo={1/ratio:.5f},loudnorm=I=-16:TP=-1.5:LRA=11"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(voice_raw), "-af", af, "-ar", "48000", "-ac", "1", str(final)],
                   check=True)

    tl = {"total": round(_dur(final), 3), "speed": speed, "lines": timeline_lines,
          "pitch_ratio": round(ratio, 4), "f0_raw": round(src_f0, 1), "f0_goal": round(goal, 1)}
    (out_dir / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=2), encoding="utf-8")
    return tl
