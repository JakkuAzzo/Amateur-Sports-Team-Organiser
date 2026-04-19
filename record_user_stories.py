#!/usr/bin/env python3
"""Record separate MP4 videos for key user stories with Playwright."""

import asyncio
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from playwright.async_api import Browser, Page, async_playwright

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "docs" / "media"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://127.0.0.1:5000"
DB_URL = "sqlite:///app_demo.db"
SERVER_PORT = 5123

MANAGER_EMAIL = "manager@example.com"
MANAGER_PASSWORD = "Manager123"
DEMO_TEAM_ID: int | None = None

REGISTER_EMAIL = f"demo_user_{int(time.time())}@example.com"
REGISTER_PASSWORD = "DemoPass123"


def _server_env() -> dict:
    env = os.environ.copy()
    env["DATABASE_URL"] = DB_URL
    env["FLASK_APP"] = "wsgi.py"
    env["FLASK_DEBUG"] = "0"
    env["PYTHONUNBUFFERED"] = "1"
    return env


def wait_for_port(host: str, port: int, timeout_seconds: int = 30) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.5)
    return False


def setup_demo_data() -> None:
    env = _server_env()
    subprocess.run(
        [sys.executable, "-c", "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all()"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run([sys.executable, "-m", "flask", "seed-demo"], cwd=ROOT, env=env, check=True)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from app import create_app, db; from app.models import Team; "
            "app=create_app(); app.app_context().push(); "
            "team=db.session.execute(db.select(Team).filter_by(name='Demo United')).scalar_one_or_none(); "
            "print(team.id if team else '')",
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    global DEMO_TEAM_ID
    team_id_text = result.stdout.strip()
    DEMO_TEAM_ID = int(team_id_text) if team_id_text else None


def kill_existing_servers() -> None:
    subprocess.run(["pkill", "-f", "flask run"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-f", "wsgi.py"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)


def wait_for_http(url: str, timeout_seconds: int = 30) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as response:  # nosec B310
                if 200 <= response.status < 400:
                    return True
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(0.5)
    return False


def start_server() -> subprocess.Popen:
    env = _server_env()
    kill_existing_servers()
    log_file = open(ROOT / "flask_server.log", "w", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, "-m", "flask", "run", "--host", "127.0.0.1", "--port", str(SERVER_PORT), "--no-debugger", "--no-reload"],
        cwd=ROOT,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
    )
    if not wait_for_port("127.0.0.1", SERVER_PORT, timeout_seconds=30):
        process.terminate()
        raise RuntimeError(f"Flask server did not start on 127.0.0.1:{SERVER_PORT}")
    if not wait_for_http(f"http://127.0.0.1:{SERVER_PORT}/auth/login", timeout_seconds=30):
        process.terminate()
        raise RuntimeError("Flask server did not become HTTP-ready on /auth/login")
    return process


def stop_server(process: subprocess.Popen) -> None:
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except Exception:
        pass


def convert_to_mp4(webm_path: Path, mp4_path: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(webm_path),
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        str(mp4_path),
    ]
    subprocess.run(cmd, check=True)


async def login(page: Page, email: str, password: str) -> None:
    await page.goto(f"{BASE_URL}/auth/login", wait_until="domcontentloaded")
    await page.locator('input[name="email"]').fill(email)
    await page.locator('input[name="password"]').fill(password)
    await page.get_by_role("button", name="Log In").click()
    await page.wait_for_timeout(1200)


async def logout(page: Page) -> None:
    await page.get_by_role("link", name="Logout").click()
    await page.wait_for_timeout(800)


async def story_registration_and_login(page: Page) -> None:
    await page.goto(f"{BASE_URL}/auth/register", wait_until="domcontentloaded")
    await page.locator('input[name="name"]').fill("Story User")
    await page.locator('input[name="email"]').fill(REGISTER_EMAIL)
    await page.locator('input[name="password"]').fill(REGISTER_PASSWORD)
    await page.locator('input[name="confirm"]').fill(REGISTER_PASSWORD)
    await page.get_by_role("button", name="Create Account").click()
    await page.wait_for_timeout(1000)

    await page.locator('input[name="email"]').fill(REGISTER_EMAIL)
    await page.locator('input[name="password"]').fill(REGISTER_PASSWORD)
    await page.get_by_role("button", name="Log In").click()
    await page.wait_for_url("**/dashboard")
    await page.wait_for_timeout(1200)

    await logout(page)
    await login(page, REGISTER_EMAIL, REGISTER_PASSWORD)
    await page.wait_for_timeout(1200)


async def story_dashboard_and_navigation(page: Page) -> None:
    await login(page, MANAGER_EMAIL, MANAGER_PASSWORD)
    await page.get_by_role("link", name="Dashboard").click()
    await page.wait_for_timeout(1000)
    await page.get_by_role("link", name="Teams").click()
    await page.wait_for_timeout(1000)
    await page.get_by_role("link", name="Open Sessions").click()
    await page.wait_for_timeout(1000)
    await page.get_by_role("link", name="Notifications").click()
    await page.wait_for_timeout(1000)


async def story_create_team(page: Page) -> None:
    await login(page, MANAGER_EMAIL, MANAGER_PASSWORD)
    await page.goto(f"{BASE_URL}/teams", wait_until="domcontentloaded")
    await page.get_by_role("link", name="New Team").click()
    await page.locator('input[name="name"]').fill(f"Story Team {int(time.time())}")
    await page.locator('input[name="sport"]').fill("Football")
    await page.get_by_role("button", name="Save Team").click()
    await page.wait_for_timeout(1400)


async def story_create_event(page: Page) -> None:
    if DEMO_TEAM_ID is None:
        raise RuntimeError("Demo team id not available")
    await login(page, MANAGER_EMAIL, MANAGER_PASSWORD)
    await page.goto(f"{BASE_URL}/teams/{DEMO_TEAM_ID}/events/create", wait_until="domcontentloaded")

    start_time = (datetime.now() + timedelta(days=2)).replace(second=0, microsecond=0)
    await page.locator('input[name="title"]').fill(f"Story Match {int(time.time())}")
    await page.locator('select[name="event_type"]').select_option("match")
    await page.locator('input[name="opponent"]').fill("Friendly XI")
    await page.locator('input[name="location"]').fill("Central Arena")
    await page.locator('input[name="start_time"]').fill(start_time.strftime("%Y-%m-%dT%H:%M"))
    await page.locator('input[name="capacity"]').fill("30")
    await page.locator('input[name="is_open"]').check()
    await page.get_by_role("button", name="Create Event").click()
    await page.wait_for_timeout(1600)


async def story_view_events_and_details(page: Page) -> None:
    await login(page, MANAGER_EMAIL, MANAGER_PASSWORD)
    await page.goto(f"{BASE_URL}/dashboard", wait_until="domcontentloaded")
    await page.locator("a.link-sport").first.click(timeout=10000)
    await page.wait_for_timeout(1000)
    await page.locator('select[name="status"]').select_option("yes")
    await page.get_by_role("button", name="Update").click()
    await page.wait_for_timeout(1200)


async def story_notifications(page: Page) -> None:
    await login(page, MANAGER_EMAIL, MANAGER_PASSWORD)
    await page.goto(f"{BASE_URL}/notifications", wait_until="domcontentloaded")
    await page.wait_for_timeout(1200)
    mark_read = page.get_by_role("button", name="Mark read")
    if await mark_read.count() > 0:
        await mark_read.first.click()
        await page.wait_for_timeout(800)


class Recorder:
    def __init__(self) -> None:
        self.playwright = None
        self.browser: Browser | None = None

    async def start(self) -> None:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)

    async def stop(self) -> None:
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def record(self, filename_base: str, story_coro) -> None:
        assert self.browser is not None
        context = await self.browser.new_context(
            viewport={"width": 1366, "height": 768},
            record_video_dir=str(OUTPUT_DIR),
            record_video_size={"width": 1366, "height": 768},
        )
        page = await context.new_page()

        webm_target = OUTPUT_DIR / f"{filename_base}.webm"
        mp4_target = OUTPUT_DIR / f"{filename_base}.mp4"

        success = False
        failure_reason: Exception | None = None
        try:
            await page.goto(f"{BASE_URL}/auth/login", wait_until="domcontentloaded")
            await page.locator('input[name="email"]').wait_for(timeout=10000)
            await story_coro(page)
            success = True
        except Exception as exc:
            failure_reason = exc
        finally:
            video = page.video
            await context.close()
            raw_video_path = Path(await video.path())
            if webm_target.exists():
                webm_target.unlink()
            if not success:
                raw_video_path.unlink(missing_ok=True)
                mp4_target.unlink(missing_ok=True)
                raise RuntimeError(f"Story failed before export: {filename_base} ({failure_reason})")

            shutil.move(str(raw_video_path), str(webm_target))
            convert_to_mp4(webm_target, mp4_target)
            webm_target.unlink(missing_ok=True)
            print(f"Created {mp4_target}")


async def run_recordings() -> None:
    recorder = Recorder()
    await recorder.start()
    try:
        stories = [
            ("story_01_registration_login", story_registration_and_login),
            ("story_02_dashboard_navigation", story_dashboard_and_navigation),
            ("story_03_create_team", story_create_team),
            ("story_04_create_event", story_create_event),
            ("story_05_view_event_details", story_view_events_and_details),
            ("story_06_notifications", story_notifications),
        ]
        for name, func in stories:
            print(f"Recording {name}...")
            try:
                await recorder.record(name, func)
            except Exception as exc:
                print(f"Skipped {name}: {exc}")
    finally:
        await recorder.stop()


def main() -> None:
    global BASE_URL
    BASE_URL = f"http://127.0.0.1:{SERVER_PORT}"
    setup_demo_data()
    server = start_server()
    try:
        asyncio.run(run_recordings())
    finally:
        stop_server(server)


if __name__ == "__main__":
    main()
