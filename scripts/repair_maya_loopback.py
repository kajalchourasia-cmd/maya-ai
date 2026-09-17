"""One-time Windows Docker Desktop repair of Maya's three published bindings.

Preserves container configuration in memory, mounted volumes, and runtime config
files. Original stopped containers remain as backups. No keys are printed/saved.
No Docker daemon, firewall, hosted service or unrelated container is changed.
"""
from __future__ import annotations

import copy
import hashlib
import http.client
import io
import json
from pathlib import Path
import subprocess
import tarfile
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
PROJECT = "maya-kajal-local"
NETWORK = "maya-kajal-loopback"
PIPE = r"\\.\pipe\dockerDesktopLinuxEngine"
PREFIX = "/v1.52"
TARGETS = {
    "db": [("/etc/postgresql-custom", "/etc"), ("/etc/postgresql", "/etc")],
    "kong": [("/home/kong", "/home")],
    "studio": [],
}


def api(method: str, path: str, body=None, content_type="application/json", allowed=(200, 201, 204)):
    data = json.dumps(body).encode() if isinstance(body, dict) else body or b""
    with open(PIPE, "r+b", buffering=0) as pipe:
        headers = (f"{method} {PREFIX}{path} HTTP/1.1\r\nHost: localhost\r\n"
                   f"Content-Type: {content_type}\r\nContent-Length: {len(data)}\r\nConnection: close\r\n\r\n").encode()
        packet = memoryview(headers + data)
        while packet:
            written = pipe.write(packet)
            if not written:
                raise RuntimeError("Local Docker pipe write failed")
            packet = packet[written:]
        socket = type("PipeSocket", (), {"makefile": lambda self, *a, **kw: pipe})()
        response = http.client.HTTPResponse(socket)
        response.begin()
        raw = response.read(16 * 1024 * 1024 + 1)
        if response.status not in allowed:
            raise RuntimeError(f"Docker {method} failed with HTTP {response.status}; response withheld")
        if len(raw) > 16 * 1024 * 1024:
            raise RuntimeError("Docker response exceeds local repair limit")
        return raw


def inspect(name: str) -> dict:
    return json.loads(api("GET", f"/containers/{quote(name)}/json"))


def archive_fingerprints(raw: bytes) -> dict:
    # No extraction to the host filesystem. Include symlink destinations.
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        return {item.name: hashlib.sha256(archive.extractfile(item).read()).hexdigest()
                if item.isfile() else item.linkname for item in archive if item.isfile() or item.issym()}


def create_payload(original: dict) -> dict:
    if original["State"]["Running"]:
        raise ValueError("Stop the scoped Maya services before repair")
    labels = original["Config"].get("Labels", {})
    if labels.get("com.supabase.cli.project") != PROJECT:
        raise ValueError("Refusing a container outside this Maya project")
    if original["HostConfig"]["NetworkMode"] != NETWORK:
        raise ValueError("Unexpected network; refusing automatic repair")
    payload = copy.deepcopy(original["Config"])
    host = copy.deepcopy(original["HostConfig"])
    for bindings in host["PortBindings"].values():
        for binding in bindings or []:
            binding["HostIp"] = "127.0.0.1"
    endpoint = original["NetworkSettings"]["Networks"][NETWORK]
    payload["HostConfig"] = host
    payload["NetworkingConfig"] = {"EndpointsConfig": {NETWORK: {"Aliases": endpoint.get("Aliases") or []}}}
    return payload


def main() -> None:
    context = subprocess.run(["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"],
                             capture_output=True, text=True, check=True).stdout.strip()
    if context != "npipe:////./pipe/dockerDesktopLinuxEngine":
        raise RuntimeError("Expected local Docker Desktop Linux context; refusing another daemon")
    records = []
    # Preflight all targets before making any change.
    prepared = []
    for service, paths in TARGETS.items():
        name = f"supabase_{service}_{PROJECT}"
        original = inspect(name)
        backup = name + "-before-loopback"
        existing = json.loads(api("GET", "/containers/json?all=true"))
        if any("/" + backup in c.get("Names", []) for c in existing):
            raise RuntimeError("Repair backup already exists; inspect previous repair instead of repeating")
        payload = create_payload(original)
        archives = [(source, dest, api("GET", f"/containers/{original['Id']}/archive?path={quote(source)}"))
                    for source, dest in paths]
        prepared.append((name, backup, original, payload, archives))
    for name, backup, original, payload, archives in prepared:
        old_id = original["Id"]
        new_id = None
        api("POST", f"/containers/{old_id}/rename?name={quote(backup)}")
        try:
            api("POST", f"/networks/{NETWORK}/disconnect", {"Container": old_id, "Force": True})
            created = json.loads(api("POST", f"/containers/create?name={quote(name)}", payload))
            new_id = created["Id"]
            for source, destination, archive in archives:
                api("PUT", f"/containers/{new_id}/archive?path={quote(destination)}", archive, "application/x-tar")
                copied = api("GET", f"/containers/{new_id}/archive?path={quote(source)}")
                if archive_fingerprints(archive) != archive_fingerprints(copied):
                    raise RuntimeError("Runtime configuration copy verification failed")
            current = inspect(new_id)
            if current["HostConfig"]["PortBindings"] != payload["HostConfig"]["PortBindings"]:
                raise RuntimeError("Explicit loopback binding was not retained")
            before_mounts = {(m["Type"], m["Source"], m["Destination"]) for m in original["Mounts"]}
            after_mounts = {(m["Type"], m["Source"], m["Destination"]) for m in current["Mounts"]}
            if before_mounts != after_mounts:
                raise RuntimeError("Mount identity changed; refusing replacement")
            records.append({"name": name, "backup": backup, "host_ip": "127.0.0.1",
                            "mounts_preserved": True, "runtime_config_archives_verified": len(archives),
                            "started": False})
            print(json.dumps(records[-1]), flush=True)
        except Exception:
            # Delete only the new unstarted replacement, without deleting volumes.
            if new_id:
                api("DELETE", f"/containers/{new_id}?v=false")
            api("POST", f"/containers/{old_id}/rename?name={quote(name)}")
            endpoint = payload["NetworkingConfig"]["EndpointsConfig"][NETWORK]
            api("POST", f"/networks/{NETWORK}/connect", {"Container": old_id, "EndpointConfig": endpoint})
            raise
    report = ROOT / "reports/local/supabase-kajal/loopback-repair.json"
    report.write_text(json.dumps({"project": PROJECT, "containers": records,
                                 "originals_retained_stopped": True, "secrets_in_report": False}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # No raw Docker inspect payload, archive data or exception body is logged.
        print(f"Local binding repair stopped: {type(exc).__name__}. Inspect scoped state before retrying.")
        raise SystemExit(1)
