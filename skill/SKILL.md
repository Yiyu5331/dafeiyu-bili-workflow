---
name: dyfish-bili
description: 用 dyfish 流水线给 B 站账号做竖屏口播视频并投稿：DeepSeek 写稿、豆包 Seed Audio 配音、Remotion 渲染手机 UI 模板、自动封面与上传。当用户要「做一条 B 站短视频 / 批量出片 / 定时更新 / 复刻这套工作流」时使用。
---

# dyfish · B 站竖屏口播工作流

## 什么时候用

- 用户要「做一条 B 站视频」「出几条短视频」「每天自动更新」
- 用户要把这套流程搬到自己机器上（装环境、配 key、跑通）
- 用户要改模板画面、换音色、换文案风格

## 前置检查（每次先跑）

```bash
dyfish doctor
```

看四项：DeepSeek key、火山 APP ID/Token、参考音文件、bili/ffmpeg/node 命令。
缺哪个就按 `docs/` 对应文档引导用户去拿，**不要把 key 回显到聊天里**。

## 常用命令

```bash
dyfish script --topic "为什么深夜才想干活"        # 只写稿
dyfish video  --topic "为什么深夜才想干活"        # 一条龙出片
dyfish video  --topic "..." --upload             # 出片并投稿
dyfish batch  --topics topics.txt --limit 3      # 批量
dyfish upload --limit 2                          # 投 out/ 里没投的
```

产出：`out/phone-<hash>/out.mp4`、`cover.jpg`、`script.json`、`投稿信息.txt`。

## 干活顺序

1. `dyfish doctor` → 有问题先解决，别硬跑。
2. 写稿阶段如果选题敏感（医疗、金融、未成年、涉政），先提醒用户，不擅自投。
3. 出片后**先把成片路径和封面给用户看**，等「可以发」再 `--upload`，除非用户已明确要求全自动。
4. 投稿后把 BV 号回报给用户；`bili upload status <BV>` 查审核。

## 硬规矩

- 密钥只从 `secrets/` 读，绝不打印全文。
- 投稿默认带 `--ai-declare`（AI 生成内容声明）与 `--no-reprint`；不要替用户去掉。
- 遇到 `captcha_required`：告诉用户去网页端手动传一条解锁，不要尝试绕过风控。
- 别把用户的 key、cookie、参考音提交进 git（`.gitignore` 已挡 `secrets/`、`*.mp3`）。

## 调参入口

| 想改 | 改哪 |
| --- | --- |
| 文案风格/句数 | `dyfish/script.py` 的 PROMPT |
| 音色 | `~/dyfish-work/assets/ref.mp3`（5–15 秒单人干净人声） |
| 语速 | `config.json` → `voice.speed`（默认 1.25） |
| 音高 | `config.json` → `voice.pitch_target_hz`（锁定参考音 f0） |
| 画面 | `template/remotion/src/Phone.tsx`，`npm run studio` 预览 |
| 出镜形象 | `template/remotion/public/narrator.png`（透明底 PNG） |

## 已知坑

- 逐句合成会让音色每句漂移 → 必须整篇一次合成。
- `deepseek-flash` 写短稿容易返回空 content，用 `deepseek-chat`。
- 表情/形象图必须放 `public/` 子目录，否则 Remotion 报 `Error loading image with src`。
- 变速用 `atempo`（音高不变）；音高对齐要用 `asetrate`+`aresample`+`atempo` 三步，且采样率要用 ffprobe 实测值。
