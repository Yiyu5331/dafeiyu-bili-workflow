"""配置读写。默认落在 ~/.config/dyfish/config.json。"""
from __future__ import annotations

import json
import os
from pathlib import Path

CONFIG_PATH = Path(os.environ.get("DYFISH_CONFIG", Path.home() / ".config" / "dyfish" / "config.json"))

DEFAULTS = {
    "workspace": str(Path.home() / "dafeiyu"),
    "deepseek": {"key_file": "secrets/deepseek.txt", "model": "deepseek-chat", "base_url": "https://api.deepseek.com"},
    "volc": {
        "app_id_file": "secrets/volc.txt",
        "access_token_file": "secrets/volc.txt",
        "resource_id": "seed-audio-1.0",
        "api": "https://openspeech.bytedance.com/api/v3/tts/create",
    },
    "voice": {
        "reference_audio": "assets/ref.mp3",
        "persona": "普通女生日常说话，音色偏中低，不刻意可爱",
        "template": "{persona}，用很自然的口语说，只说引号里的这句话，一字不差：“{text}”",
        "speed": 1.25,
        "pitch_target_hz": None,
    },
    "video": {"template": "phone", "concurrency": 4, "width": 1080, "height": 1920, "fps": 30},
    "outro": "新的一条",
    "bili": {"zone": 1010, "tid": 124, "ai_declare": True, "no_reprint": True},
}


def _norm(s: str) -> str:
    """把小写、下划线、空格、中划线统统去掉，方便匹配 APP ID / APP_ID / app-id。"""
    return "".join(ch for ch in s.lower() if ch.isalnum())


def _merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


class Config:
    def __init__(self, data: dict, path: Path = CONFIG_PATH):
        self.data = data
        self.path = path
        self.workspace = Path(os.path.expanduser(data["workspace"]))

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "Config":
        if not path.exists():
            raise SystemExit(f"找不到配置 {path}，先跑 `dyfish init`")
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        return cls(_merge(DEFAULTS, raw), path)

    @classmethod
    def create_default(cls, workspace: str | None = None, path: Path = CONFIG_PATH) -> "Config":
        data = _merge(DEFAULTS, {})
        if workspace:
            data["workspace"] = workspace
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return cls(data, path)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- 便捷取值 ---
    def p(self, key: str) -> Path:
        """把配置里的相对路径解析到 workspace 下。"""
        v = self.data
        for part in key.split("."):
            v = v[part]
        p = Path(os.path.expanduser(str(v)))
        return p if p.is_absolute() else self.workspace / p

    def get(self, key: str, default=None):
        v = self.data
        for part in key.split("."):
            if not isinstance(v, dict) or part not in v:
                return default
            v = v[part]
        return v

    def secret(self, key: str) -> str:
        """优先从 *_file 读密钥（支持单行，或 `APP_ID: xxx` 这种键值行），其次读字符串字段。"""
        file_key = key + "_file"
        try:
            f = self.p(file_key)
            if f.exists():
                lines = [x.strip() for x in f.read_text(encoding="utf-8-sig").splitlines() if x.strip()]
                want = _norm(key.split(".")[-1])
                for line in lines:
                    name, sep, val = line.replace("：", ":").partition(":")
                    if sep and _norm(name) == want:
                        return val.strip().strip('"').strip("'")
                return lines[0] if lines else ""
        except (KeyError, IndexError):
            pass
        val = self.get(key)
        if not val:
            raise SystemExit(f"缺少 {key}（配置文件里填字符串，或放一个只含密钥的单行文件到 {file_key}）")
        return str(val)
