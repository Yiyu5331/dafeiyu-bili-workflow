# 04 · 出片流程与调参

一条片子的六个阶段（`dyfish video` 全自动）：

1. **写稿** `script.py`：DeepSeek 按「12 句、每句 4–9 字、口语、不解释道理」出稿，返回 `{title, subtitle, lines, tags}`。
2. **配音** `tts.py`：整篇一次合成（不是逐句！逐句会音色漂移），拿字级字幕算每句起止 → `ffmpeg atempo` 变速到 1.25 倍 → 音高对齐 → `loudnorm -16 LUFS`。
3. **时间轴** `video.py`：把句子时间写进 `template/remotion/src/timeline.ts`，模板按时间切镜头。
4. **渲染** Remotion：`npx remotion render src/index.ts PhoneUI out.mp4`。
5. **封面** `cover.py`：从成片 55% 处抽一帧，压一层黑渐变 + 大字标题（自动缩字号，最多 3 行）。
6. **投稿** `upload.py`：调 `bili upload video`，默认带 AI 声明与禁止转载。

常用配置（`~/.config/dyfish/config.json`）：

```json
{
  "voice": {"speed": 1.25, "pitch_target_hz": 254.0},
  "deepseek": {"model": "deepseek-chat"},
  "bili": {"zone": 1010, "tid": 124, "ai_declare": true},
  "video": {"concurrency": 4}
}
```

想改画面：编辑 `template/remotion/src/Phone.tsx`，`npm run studio` 实时预览。
想换出镜形象：把透明底 PNG 放成 `template/remotion/public/narrator.png`。
