# 05 · 排错

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `语音合成失败：HTTP 401` | APP ID 与 Token 不配套 | 控制台重新复制两串，注意别把 `APP_ID:` 前缀带进值里 |
| 音色每句都不一样 | 用了逐句合成 | dyfish 默认整篇合成，别自己拆句 |
| 声音不像参考音 | 参考音有 BGM/多人/太长 | 换 5–15 秒单人干净人声，删掉 `work/audio/` 重跑 |
| `captcha_required` | 新号风控 | 网页端手动传一条解锁 |
| `Error loading image with src` | 模板缺 `public/narrator.png` | 放一张透明底 PNG 进去 |
| Remotion 渲染报 ffmpeg 错 | 缺 ffmpeg / 版本旧 | `brew install ffmpeg` |
| 端口被占用 | remotion 内部起服务 | 重跑一次，或 `pkill -f remotion` |
| 稿子太长/太短 | 模型没按格式 | `dyfish script` 多看几版，或调 `script.py` 的提示词 |
