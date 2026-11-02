# 大肥鱼 B 站运营工作流（dyfish）

一句话：**给一个主题，它自己写稿、配音、出竖屏视频、做封面、投稿到 B 站。**

全流程只有三样东西要你自己准备：DeepSeek 的 key、火山引擎（豆包语音）的 key、一段 5–15 秒的人声参考。
其余交给 `dyfish` 一条命令。

```bash
dyfish video --topic "为什么一停下来就焦虑"
# → out/phone-xxxxxxxx/out.mp4  +  cover.jpg  +  投稿信息.txt
```

---

## 0. 它长什么样

16 秒左右的竖屏口播短片，形式是「手机屏幕实演」：

- 开场 01:29 的锁屏／信息流，直接把观众丢进深夜刷手机的场景
- 中段逐条大字幕推进，配手机 UI 动画（信息流滑动、点赞爆散、算法节点图、时钟加速）
- 结尾手机倒扣「屏幕朝下 明天再说」，字幕留一句钩子
- 音轨：整篇一次合成的中文女声（豆包 Seed Audio）+ 轻 BGM + 提示音

模板是 Remotion 写的，`template/remotion/src/Phone.tsx` 可以随便改配色、文案位置、加镜头。

| 开头钩子 | 信息流实演 | 结尾收束 |
| --- | --- | --- |
| ![](docs/preview/01-hook.jpg) | ![](docs/preview/02-ui.jpg) | ![](docs/preview/03-outro.jpg) |

---

## 1. 安装

需要：macOS / Linux、Python ≥ 3.10、Node ≥ 18、ffmpeg。

```bash
# ffmpeg
brew install ffmpeg          # macOS
# sudo apt install ffmpeg    # Ubuntu

# dyfish 本体
git clone https://github.com/Yiyu5331/dafeiyu-bili-workflow
cd dafeiyu-bili-workflow
pip install -e .

# B 站命令行（投稿用，第三方项目）
uv tool install bili-agent   # 或 pipx install bili-agent
bili --version
```

初始化工作区：

```bash
dyfish init --workspace ~/dyfish-work
```

它会建出：

```
~/dyfish-work/
├── secrets/        # 三份密钥（不进 git）
├── assets/ref.mp3  # 参考音，自己放
├── work/audio/     # 每次合成的音频与时间轴
└── out/            # 成片、封面、投稿信息
```

---

## 2. 准备三把钥匙

### 2.1 DeepSeek key（写稿）

1. 打开 <https://platform.deepseek.com/api_keys>
2. 「创建 API key」，复制 `sk-...`（只显示一次）
3. 存成文件：

```bash
echo "sk-你的key" > ~/dyfish-work/secrets/deepseek.txt
```

模型默认 `deepseek-chat`。**别用 deepseek-flash 写短句稿**：它是推理模型，容易把 token 花在思考上，`content` 可能为空。要改模型见 `~/.config/dyfish/config.json` 的 `deepseek.model`。

### 2.2 火山引擎（豆包语音）key

1. 注册 <https://console.volcengine.com/>，实名认证
2. 进入「语音技术 / 豆包语音 / Seed Audio」，开通服务
3. 在控制台拿到 **APP ID** 和 **Access Token**（有的版本叫 Access Key）
4. 存文件：

```bash
printf '%s\n' "APP_ID: 1234567890" "ACCESS_TOKEN: 你的token" > ~/dyfish-work/secrets/volc.txt
```

调用的是 `https://openspeech.bytedance.com/api/v3/tts/create`，`X-Api-Resource-Id: seed-audio-1.0`，按字收费（一条 16 秒片约 1–3 分钱）。

### 2.3 参考音（决定音色）

准备一段 **5–15 秒、单人、无背景音乐** 的普通话人声（自己录、或你喜欢的样音），存成：

```bash
cp 你的样音.mp3 ~/dyfish-work/assets/ref.mp3
```

`dyfish` 每次合成都把它作为 `references` 参考喂给模型，并用 **音高中位数对齐**（`asetrate` + `atempo`）把输出拉到参考音的音高，所以音色不会一条一个样。

自检：

```bash
dyfish doctor
```

它会把每个 key 打码显示后 4 位，检查 ffmpeg / node / bili / 参考音是否就位。

---

## 3. B 站登录（扫码一次就行）

```bash
bili auth login --qr-out /tmp/bili_qr.png
open /tmp/bili_qr.png      # 手机 B 站扫
bili auth status --wait 180
```

登录态存在 `~/.config/bili-cli/`，之后 `dyfish upload` 直接可用。

第一次投稿有可能触发风控（`captcha_required`）：去 <https://member.bilibili.com/platform/upload/video/frame> 网页手动传一条，解锁后用命令就能连续投。

---

## 4. 出片

```bash
# 只写稿，看看文案
dyfish script --topic "为什么深夜才想干活"

# 一条龙：写稿 → 配音 → 渲染 → 封面
dyfish video --topic "为什么深夜才想干活"

# 出片并直接投稿
dyfish video --topic "为什么深夜才想干活" --upload

# 批量：主题清单一行一个
dyfish batch --topics topics.txt --limit 3

# 把 out/ 里没投的都投了
dyfish upload --limit 2
```

产出在 `out/phone-<hash>/`：`out.mp4`、`cover.jpg`、`script.json`、`投稿信息.txt`。

---

## 5. 定时更新（可选）

macOS 用 launchd，一天三轮：

```bash
# ~/Library/LaunchAgents/com.dyfish.daily.plist
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.dyfish.daily</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>-lc</string>
    <string>cd ~/dafeiyu-bili-workflow && dyfish batch --topics topics.txt --limit 2 && dyfish upload --limit 2</string></array>
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Hour</key><integer>11</integer><key>Minute</key><integer>30</integer></dict>
    <dict><key>Hour</key><integer>16</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Hour</key><integer>20</integer><key>Minute</key><integer>30</integer></dict>
  </array>
  <key>StandardOutPath</key><string>/tmp/dyfish.log</string>
  <key>StandardErrorPath</key><string>/tmp/dyfish.err</string>
</dict></plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.dyfish.daily.plist
```

---

## 6. 目录结构

```
dyfish/
  cli.py       # init / doctor / script / video / batch / upload
  config.py    # ~/.config/dyfish/config.json
  script.py    # DeepSeek 写 12 句短稿
  tts.py       # 豆包 Seed Audio 整篇合成 + 音高对齐 + 时间轴
  video.py     # 写 timeline.ts、调 remotion render
  cover.py     # 抽帧 + 大字标题压黑
  upload.py    # 包 bili CLI
template/remotion/   # 竖屏手机 UI 模板（可改）
docs/                # 分步图文教程
skill/SKILL.md       # 给 AI Agent 用的技能描述（Claude Code / DSH / Cursor 等）
```

---

## 7. 常见问题

**声音不像参考音？**
① 参考音要单人、干净、5–15 秒；② 换参考音后删掉 `work/audio/` 重跑；③ 音高对齐默认开启，配置里 `voice.pitch_target_hz` 可手动钉死目标音高。

**投稿报 `captcha_required`？**
网页端手动传一条解风控，再跑 `dyfish upload`。

**Remotion 首次渲染很慢？**
第一次会自动 `npm install`（约 1 分钟），之后单条 16 秒片在 M 系列芯片上约 40–60 秒。

**能不能换成别的模型 / 别的 TTS？**
`config.json` 里改 `deepseek.model`；TTS 在 `dyfish/tts.py` 里换掉 `synth_whole` 即可，只要返回同样的 `{audio, subtitle}` 结构。

---

## 8. 声明

- 模板、脚本、流水线代码 MIT。
- 语音合成走火山引擎，B 站投稿走 [bili-cli](https://github.com/kukemc/bili-cli)，请自行遵守两家平台的服务条款。
- 用 AI 生成的内容投稿时请勾选 B 站「AI 生成内容」声明（dyfish 默认带上 `--ai-declare`）。
