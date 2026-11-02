# 01 · 拿 DeepSeek 的 key

1. 打开 <https://platform.deepseek.com/api_keys>，登录（手机号即可）。
2. 点「创建 API key」，名字随便写，比如 `dyfish`。
3. 复制弹出的 `sk-...`（**只显示一次**，关掉就看不到了）。
4. 存起来：

```bash
mkdir -p ~/dyfish-work/secrets
echo "sk-你的key" > ~/dyfish-work/secrets/deepseek.txt
chmod 600 ~/dyfish-work/secrets/deepseek.txt
```

5. 充点钱（10 块钱能写几百条稿）。

验证：

```bash
dyfish doctor
#   DeepSeek key: sk-a…f9（35 位）
```

模型选择：默认 `deepseek-chat`。写短视频稿不要用 `deepseek-flash`——它把 token 花在推理上，短输出容易得到空 `content`。
