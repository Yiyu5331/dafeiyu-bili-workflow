"""DeepSeek 写口播稿。"""
from __future__ import annotations

import json
import urllib.request

PROMPT = """你是短视频口播编剧。主题：{topic}
写一条 {seconds} 秒左右的知识类口播，规则：
1. 正好 12 句，每句 4-9 个字，口语、短促、有节奏。
2. 第 1-2 句必须是钩子（提问或反常识断言），不要客套。
3. 中间拆机制，第 10-11 句给一个马上能做的动作。
4. 最后一句给"让观众动手/留言"的指令。
5. 不要 emoji，不要书名号，不要分点。
只输出 JSON：{{"title":"标题(18-26字，带钩子)","subtitle":"顶部小标题(4-8字)","tags":["标签1","标签2","标签3"],"lines":["句1", ...共12句]}}"""


def write_script(cfg, topic: str, seconds: int = 16) -> dict:
    key = cfg.secret("deepseek.key")
    base = cfg.get("deepseek.base_url", "https://api.deepseek.com")
    body = {
        "model": cfg.get("deepseek.model", "deepseek-chat"),
        "messages": [{"role": "user", "content": PROMPT.format(topic=topic, seconds=seconds)}],
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
