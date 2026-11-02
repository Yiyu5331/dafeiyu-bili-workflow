# 03 · 登录 B 站并投稿

安装命令行：

```bash
uv tool install bili-agent     # 或 pipx install bili-agent
bili --version
```

扫码登录（一次，登录态会保存在本地）：

```bash
bili auth login --qr-out /tmp/bili_qr.png
open /tmp/bili_qr.png
bili auth status --wait 180
```

看自己是谁：

```bash
bili me show
```

投稿：

```bash
dyfish video --topic "为什么一停下来就焦虑" --upload
```

或手动：

```bash
bili upload video out/phone-xxx/out.mp4 \
  --title "一停下来就焦虑？不是你懒" \
  --zone 1010 --tid 124 \
  --cover out/phone-xxx/cover.jpg \
  --tag 心理 --tag 焦虑 --tag 深夜 \
  --ai-declare --no-reprint \
  --desc "完整版在评论区"
```

分区：知识 = `1010`，科普子分区 `tid 124`。其他分区 `bili upload zones` 可以查。

**风控**：新号/新设备第一次用 API 投稿大概率返回 `captcha_required`，到 <https://member.bilibili.com/platform/upload/video/frame> 网页传一条就能解锁，之后持续用 API。

**审核状态**：

```bash
bili upload status <BV号>
```
