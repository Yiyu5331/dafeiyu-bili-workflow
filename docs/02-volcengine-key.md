# 02 · 拿火山引擎（豆包语音）的 key

1. 注册 <https://console.volcengine.com/>，完成实名认证（个人认证一小时内过）。
2. 搜索「豆包语音」或「语音技术」，开通 **Seed Audio** 语音合成服务。
3. 在控制台「应用管理」里创建应用，拿到：
   - **APP ID**（一串数字）
   - **Access Token**
4. 存起来：

```bash
cat > ~/dyfish-work/secrets/volc.txt <<'TXT'
APP_ID: 你的appid
ACCESS_TOKEN: 你的token
TXT
chmod 600 ~/dyfish-work/secrets/volc.txt
```

调用细节（写给想改代码的人）：

```
POST https://openspeech.bytedance.com/api/v3/tts/create
X-Api-App-Id: <APP ID>
X-Api-Access-Key: <Access Token>
X-Api-Resource-Id: seed-audio-1.0
Content-Type: application/json

{"model":"seed-audio-1.0",
 "text_prompt":"<人设描述>，只说引号里的这句话：“<正文>”",
 "audio_config":{"format":"mp3","sample_rate":24000,"enable_subtitle":true},
 "references":[{"audio_data":"<参考音 base64>"}]}
```

返回 `data.audio`（base64 mp3）和 `data.subtitle.sentences[].words[]`（字级时间戳，dyfish 用它切逐句时间轴）。

计费：按合成字数，16 秒一条大约 1–3 分钱。
