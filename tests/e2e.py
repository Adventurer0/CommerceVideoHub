"""Local browser E2E + mocked outage. No platform accounts or external pages."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="cvh-e2e-") as directory:
        env = os.environ | {"CVH_RUNTIME_DIR": directory, "PYTHONUTF8": "1"}
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT, env=env, check=True)
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        url = f"http://127.0.0.1:{port}"
        with open(Path(directory) / "server.log", "w", encoding="utf-8") as log:
            stop_file = Path(directory) / "stop.flag"
            server = subprocess.Popen([sys.executable, "-m", "app.backend.serve", "--port", str(port), "--stop-file", str(stop_file)], cwd=ROOT, env=env, stdout=log, stderr=log)
            try:
                for _ in range(100):
                    if server.poll() is not None:
                        raise RuntimeError("E2E server exited")
                    try:
                        with urlopen(url + "/api/health", timeout=1) as response:
                            assert json.load(response)["publishing_enabled"] is False
                        break
                    except OSError:
                        time.sleep(.1)
                else:
                    raise RuntimeError("E2E server did not become healthy")
                with sync_playwright() as p:
                    browser = p.chromium.launch(channel="chrome", headless=True)
                    try:
                        page = browser.new_page(viewport={"width": 1280, "height": 800})
                        errors = []
                        page.on("pageerror", lambda error: errors.append(str(error)))
                        page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(url + "/") else route.abort())
                        page.goto(url)
                        expect(page.get_by_text("本地服务正常", exact=True)).to_be_visible()
                        for label in ("视频仓库", "商品仓库", "店铺账号", "发布中心", "发布记录", "设置"):
                            page.get_by_role("menuitem", name=label).click()
                            expect(page.get_by_role("heading", name=label, exact=True)).to_be_visible()
                            page.reload()
                            expect(page.get_by_role("heading", name=label, exact=True)).to_be_visible()
                        assert page.get_by_role("button", name="发布", exact=True).count() == 0
                        page.screenshot(path=str(ROOT / "docs" / "UI_SMOKE.png"), full_page=True)
                        # Simulate a failed API response; UI must not show healthy.
                        page.route("**/api/health", lambda route: route.fulfill(status=503, content_type="application/json", body='{"detail":"mock outage"}'))
                        page.reload()
                        expect(page.get_by_text("本地服务不可用", exact=True)).to_be_visible()
                        expect(page.get_by_text("无法连接本地服务", exact=True)).to_be_visible()
                        assert not errors, errors
                        print(json.dumps({"live_health": "passed", "six_menus_and_reload": "passed",
                            "no_publish_action": "passed", "mock_api_outage": "passed",
                            "browser_console_errors": errors, "browser": browser.version,
                            "real_platform_tests": "not_run"}, ensure_ascii=False, indent=2))
                    finally:
                        browser.close()
            finally:
                stop_file.touch()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    if os.name == "nt":
                        subprocess.run(["taskkill.exe", "/PID", str(server.pid), "/T", "/F"], capture_output=True, check=True)
                    else:
                        server.terminate()
                    server.wait(timeout=10)
                    raise AssertionError("Graceful shutdown timed out")


if __name__ == "__main__":
    main()
