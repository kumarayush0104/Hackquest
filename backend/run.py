from __future__ import annotations

import asyncio
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    from backend.system import run_system
except ModuleNotFoundError:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from backend.system import run_system


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = ROOT / "dashboard"
SHARED_DIR = ROOT / "shared"


class DashboardHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        clean_path = path.split("?", 1)[0].split("#", 1)[0]
        if clean_path.startswith("/shared/"):
            rel = clean_path.replace("/shared/", "")
            return str(SHARED_DIR / rel)
        if clean_path == "/":
            return str(DASHBOARD_DIR / "index.html")
        return str(DASHBOARD_DIR / clean_path.lstrip("/"))

    def guess_type(self, path: str) -> str:
        if path.endswith(".json"):
            return "application/json"
        return super().guess_type(path)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()


async def main() -> None:
    SHARED_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 8000), DashboardHandler)

    loop = asyncio.get_running_loop()
    server_task = loop.run_in_executor(None, server.serve_forever)

    sim_task = asyncio.create_task(run_system())

    await asyncio.gather(server_task, sim_task)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
