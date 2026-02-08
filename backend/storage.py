from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None


class SharedStateStore:
    def __init__(self, shared_dir: Path, redis_url: str | None) -> None:
        self.shared_dir = shared_dir
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        self.redis_url = redis_url
        self._redis = None
        if redis_url and redis:
            self._redis = redis.Redis.from_url(redis_url)

    @property
    def backend(self) -> str:
        if self._redis:
            return "redis"
        return "file"

    def write(self, key: str, payload: Dict[str, Any]) -> None:
        if self._redis:
            self._redis.set(key, json.dumps(payload))
            return
        path = self.shared_dir / f"{key}.json"
        tmp_path = self.shared_dir / f"{key}.json.tmp"
        tmp_path.write_text(json.dumps(payload, indent=2))
        tmp_path.replace(path)

    def read(self, key: str) -> Dict[str, Any]:
        if self._redis:
            raw = self._redis.get(key)
            if not raw:
                return {}
            return json.loads(raw)
        path = self.shared_dir / f"{key}.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text())
