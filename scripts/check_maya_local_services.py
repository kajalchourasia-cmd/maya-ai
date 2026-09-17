"""Check local infrastructure health without displaying Supabase credentials."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.maya_local_database import cli, run, verify_loopback, PROJECT, WORK


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def safe_studio_redirect(current: str, location: str) -> str:
    target = urljoin(current, location)
    parsed = urlsplit(target)
    if parsed.scheme != "http" or parsed.netloc != "127.0.0.1:54323" or parsed.username or parsed.password:
        raise ValueError("Refusing a redirect outside local Studio")
    return target


def main():
    status = cli("status", "--output", "json")
    if status.returncode:
        raise RuntimeError("Local Supabase status failed")
    values = json.loads(status.stdout)
    if values.get("API_URL") != "http://127.0.0.1:54321" or values.get("STUDIO_URL") != "http://127.0.0.1:54323":
        raise RuntimeError("Unexpected local endpoints")
    public_key = values.get("PUBLISHABLE_KEY") or values.get("ANON_KEY")
    opener = build_opener(NoRedirect())
    endpoints = [("auth", "http://127.0.0.1:54321/auth/v1/health"),
                 ("rest", "http://127.0.0.1:54321/rest/v1/"),
                 ("studio", "http://127.0.0.1:54323/")]
    health = {}
    redirects = {}
    for name, url in endpoints:
        headers = {"apikey": public_key} if name != "studio" else {}
        redirects[name] = []
        for attempt in range(4):
            try:
                with opener.open(Request(url, headers=headers), timeout=15) as response:
                    health[name] = response.status
                break
            except HTTPError as exc:
                health[name] = exc.code
                if name == "studio" and exc.code in (301, 302, 303, 307, 308) and attempt < 3:
                    redirects[name].append(exc.code)
                    url = safe_studio_redirect(url, exc.headers.get("Location", ""))
                    continue
                break
            except (URLError, TimeoutError, OSError):
                health[name] = "connection_failed"
                break
    containers = []
    for service in ("db", "auth", "rest", "storage", "kong", "pg_meta", "studio"):
        name = f"supabase_{service}_{PROJECT}"
        result = run(["docker", "inspect", name])
        info = json.loads(result.stdout)[0]
        containers.append({"name": name, "running": info["State"]["Running"],
                           "health": info["State"].get("Health", {}).get("Status", "no_healthcheck"),
                           "published_ports": info["NetworkSettings"]["Ports"]})
    loopback = verify_loopback()
    report = {"verified_at_utc": datetime.now(timezone.utc).isoformat(),
              "loopback_only": loopback, "http_statuses": health, "redirect_statuses": redirects, "containers": containers,
              "pass": loopback and all(code == 200 for code in health.values()) and
              all(c["running"] and c["health"] in ("healthy", "no_healthcheck") for c in containers)}
    (WORK / "local-services-verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, KeyError, OSError) as exc:
        print("Local service check failed: " + type(exc).__name__ + "; no credential data printed")
        raise SystemExit(1)
