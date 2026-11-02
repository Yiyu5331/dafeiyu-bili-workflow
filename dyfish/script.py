"""DeepSeek 写口播稿。"""
from __future__ import annotations

import json
import urllib.request

# 从爆款拆出来的三种骨架，写稿时按主题自动挑
FORMULAS = {
    "揭秘": "先抛一个反常现象，前半段带观众看细节，用具体数字制造惊讶，最后揭示它其实是什么（营销/心理机制/设计），结尾反问观众。",
    "清单": "开头宣布「有几个」，中间每条一句、只给结论不给论证，最后给一个可执行动作。",
    "仪式": "用一个年份/数字开场，画面感强的短句推进，像在讲一段被误解的历史，结尾落回当下。",
}

PROMPT = """你是短视频口播编剧。主题：{topic}
结构：{formula}
写一条 {seconds} 秒左右的口播，规则：
1. 正好 12 句，每句 4-9 个字，口语、短促、有节奏。
2. 第 1-2 句必须是钩子（提问、反常识断言、或一个具体数字），不要客套。
3. 至少有一句带具体数字（价格、年份、次数），数字是留人点。
4. 中间拆机制，第 10-11 句给一个马上能做的动作。
5. 最后一句给"让观众动手/留言"的指令。
6. 不要 emoji，不要书名号，不要分点。
只输出 JSON：{{"title":"标题(18-26字，带钩子)","subtitle":"顶部小标题(4-8字)","formula":"{formula}","tags":["标签1","标签2","标签3"],"lines":["句1", ...共12句]}}"""


def write_script(cfg, topic: str, seconds: int = 16, formula: str = "揭秘") -> dict:
    key = cfg.secret("deepseek.key")
    base = cfg.get("deepseek.base_url", "https://api.deepseek.com")
    body = {
        "model": cfg.get("deepseek.model", "deepseek-chat"),
        "messages": [{"role": "user", "content": PROMPT.format(
            topic=topic, seconds=seconds, formula=FORMULAS.get(formula, FORMULAS["揭秘"]))}],
        "temperature": 1.0,
        "max_tokens": 1200,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        f"{base.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    d = json.loads(urllib.request.urlopen(req, timeout=180).read().decode())
    sc = json.loads(d["choices"][0]["message"]["content"])
    sc["lines"] = [x.strip() for x in sc["lines"]][:12]
    if len(sc["lines"]) < 8:
        raise SystemExit("DeepSeek 返回的行数太少，换个主题再试")
    sc["topic"] = topic
    return sc
