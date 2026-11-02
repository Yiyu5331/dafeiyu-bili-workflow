# 06 · 一天怎么运营

dyfish 不只出片，它管的是**一天的闭环**：

```
刷 → 拆 → 写 → 做 → 发 → 回 → 看
```

## 一条命令跑完

```bash
dyfish day --topics 2              # 出 2 条，不自动投
dyfish day --topics 2 --upload     # 出完直接投
```

它会：

1. `dyfish scroll` 刷热门 + 推荐（`--unseen` 只留没看过的），记进 `work/seen.json`
2. 从候选里挑标题长度合适的 2 个当选题
3. 逐个出片（写稿 → 配音 → 渲染 → 封面）
4. 可选：投稿
5. `dyfish inbox` 拉新回复 / @ / 赞 / 私信，以及**还没回过的评论**
6. `dyfish stats` 拉数据，写 `out/日报.md`

## 每一步单独用

```bash
dyfish scroll --limit 20 --zone knowledge   # 只刷知识区
dyfish inspect BV1xxxxxxxxx                 # 拆一条爆款：AI 总结/字幕/热评/画面总览
dyfish inbox --limit 20                     # 收件箱
dyfish stats                                # 账号总览 + 30 天趋势 + 稿件数据
dyfish report                               # 写日报
```

`dyfish inspect` 的输出里，每帧画面下方是观众对这个画面的弹幕反应，底部是弹幕密度条——
这是判断「哪一秒留人、哪一秒掉人」最直接的东西，比看后台数据快。

## 一条稳定的日常节奏

| 时间 | 做什么 |
| --- | --- |
| 上午 | `dyfish scroll` 扫一遍热门，挑 2–3 个能讲清楚的点 |
| 中午 | `dyfish video` 出一条，先自己看，再 `--upload` |
| 下午 | `dyfish inbox` 回评论和私信（评论 10 秒一条限流，别刷） |
| 晚上 | 再出一条 + `dyfish report` 看今天的数据 |

自动版：launchd 一天三轮（见 README「定时更新」），每轮 `dyfish batch` 出片 + `dyfish upload`。
但**建议每天人工看一次日报**，标题和封面是唯一需要人判断的地方。

## 回复评论的边界

- 只回**自己视频下面**的评论，别去别人视频下引流
- 私信只发给已经给你发过消息/互关的人（bili-cli 有白名单）
- 遇到敏感话题（医疗、纠纷、未成年），不回，直接告诉用户
