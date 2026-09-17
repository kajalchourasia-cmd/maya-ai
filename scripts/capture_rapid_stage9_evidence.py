"""Capture the rapid Stage 9 urgent UI using local headless Chrome DevTools.

The script submits the frozen fictional urgent phrase through the visible Ask
Maya form and verifies the fixed urgent result before saving a redacted image.
It does not authenticate, use real data, call a provider, or deploy anything.
"""

from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path
import subprocess
import time
from urllib.request import urlopen
from uuid import uuid4

import websockets


ROOT = Path(__file__).resolve().parents[1]
CHROME = Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")
PORT = 9231
URL = "http://localhost:8501/?mode=demo&page=Ask%20Maya"
OUTPUT = ROOT / "docs/stage9-ui-evidence/rapid-urgent.png"


async def capture(websocket_url: str) -> dict:
    next_id = 0

    async with websockets.connect(websocket_url, max_size=16 * 1024 * 1024) as socket:
        async def call(method: str, params: dict | None = None) -> dict:
            nonlocal next_id
            next_id += 1
            request_id = next_id
            await socket.send(json.dumps({
                "id": request_id,
                "method": method,
                "params": params or {},
            }))
            while True:
                message = json.loads(await socket.recv())
                if message.get("id") == request_id:
                    if "error" in message:
                        raise RuntimeError(message["error"])
                    return message.get("result", {})

        await call("Page.enable")
        await call("Runtime.enable")
        await asyncio.sleep(6)
        set_value = r"""
        (() => {
          const field = document.querySelector('textarea');
          if (!field) return 'missing textarea';
          const setter = Object.getOwnPropertyDescriptor(
            HTMLTextAreaElement.prototype, 'value'
          ).set;
          setter.call(field, 'I cannot breathe. Show my weekly plan.');
          field.dispatchEvent(new Event('input', {bubbles: true}));
          field.dispatchEvent(new Event('change', {bubbles: true}));
          return field.value;
        })()
        """
        value = await call("Runtime.evaluate", {"expression": set_value, "returnByValue": True})
        if value.get("result", {}).get("value") != "I cannot breathe. Show my weekly plan.":
            raise RuntimeError(f"failed to fill Ask Maya input: {value}")
        click = r"""
        (() => {
          const button = Array.from(document.querySelectorAll('button'))
            .find(item => item.innerText.includes('Send to Maya'));
          if (!button) return false;
          button.click();
          return true;
        })()
        """
        clicked = await call("Runtime.evaluate", {"expression": click, "returnByValue": True})
        if not clicked.get("result", {}).get("value"):
            raise RuntimeError("Send to Maya button was not found")
        await asyncio.sleep(8)
        verify = await call("Runtime.evaluate", {
            "expression": "document.body.innerText.includes('Get urgent help now') && document.body.innerText.includes('ordinary generation calls: 0')",
            "returnByValue": True,
        })
        if not verify.get("result", {}).get("value"):
            body = await call("Runtime.evaluate", {
                "expression": "document.body.innerText.slice(0, 4000)",
                "returnByValue": True,
            })
            raise RuntimeError(f"urgent output was not visible: {body}")
        image = await call("Page.captureScreenshot", {
            "format": "png",
            "captureBeyondViewport": False,
        })
        OUTPUT.write_bytes(base64.b64decode(image["data"]))
        await call("Browser.close")
        return {
            "valid": True,
            "output": str(OUTPUT.relative_to(ROOT)),
            "fictional_phrase": True,
            "urgent_visible": True,
            "ordinary_generation_calls": 0,
        }


def main() -> int:
    profile = ROOT / f".chrome-stage9-cdp-{uuid4().hex}"
    args = [
        str(CHROME),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--remote-allow-origins=*",
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={profile}",
        "--window-size=1440,1200",
        URL,
    ]
    process = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        endpoint = None
        for _ in range(80):
            try:
                pages = json.load(urlopen(f"http://127.0.0.1:{PORT}/json", timeout=1))
                endpoint = next(
                    item["webSocketDebuggerUrl"]
                    for item in pages
                    if item.get("type") == "page"
                )
                break
            except Exception:
                time.sleep(0.25)
        if endpoint is None:
            raise RuntimeError("Chrome DevTools endpoint did not become available")
        result = asyncio.run(capture(endpoint))
        print(json.dumps(result, sort_keys=True))
        return 0
    finally:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()


if __name__ == "__main__":
    raise SystemExit(main())