"""Prepare and check Maya's isolated local Supabase stack; never link hosted projects.

Generated state lives under ignored reports/local. Original migrations and .env
are not edited. Start output is captured because Supabase prints credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "reports/local/supabase-kajal"
PROJECT = "maya-kajal-local"
NETWORK = "maya-kajal-loopback"


def stop_local_containers() -> None:
    names = [f"supabase_{service}_{PROJECT}" for service in
             ("studio", "pg_meta", "storage", "rest", "auth", "kong", "db")]
    for name in names:
        existing = run(["docker", "inspect", name, "--format", "{{.Name}}"], timeout=30)
        if existing.returncode == 0:
            if existing.stdout.strip() != "/" + name:
                raise RuntimeError("Unexpected container identity")
            stopped = run(["docker", "stop", name], timeout=60)
            if stopped.returncode:
                raise RuntimeError("Could not stop local container " + name)


def verify_loopback() -> bool:
    for service in ("db", "kong", "studio"):
        result = run(["docker", "inspect", f"supabase_{service}_{PROJECT}"])
        if result.returncode:
            return False
        container = json.loads(result.stdout)[0]
        if not container["State"]["Running"] or not bindings_are_loopback(container["NetworkSettings"]["Ports"]):
            return False
    return True


def bindings_are_loopback(ports: dict) -> bool:
    bindings = [item for rows in ports.values() for item in rows or []]
    return bool(bindings) and all(item.get("HostIp") in ("127.0.0.1", "::1") for item in bindings)


def resume_local() -> None:
    # Restart the repaired containers themselves, not newly recreated CLI defaults.
    services = ("db", "auth", "rest", "storage", "kong", "pg_meta", "studio")
    for service in services:
        name = f"supabase_{service}_{PROJECT}"
        result = run(["docker", "inspect", name])
        if result.returncode:
            raise RuntimeError("Missing local container " + name)
        container = json.loads(result.stdout)[0]
        if container["Config"].get("Labels", {}).get("com.supabase.cli.project") != PROJECT:
            raise RuntimeError("Unexpected local container ownership")
        if service in ("db", "kong", "studio") and not bindings_are_loopback(container["HostConfig"]["PortBindings"]):
            raise RuntimeError("Explicit loopback repair required before restarting " + name)
    try:
        for service in services:
            name = f"supabase_{service}_{PROJECT}"
            result = run(["docker", "start", name], timeout=60)
            if result.returncode:
                raise RuntimeError("Could not start " + name)
            print("Started " + name, flush=True)
            if service == "db":
                for _ in range(30):
                    ready = run(["docker", "exec", name, "pg_isready", "-U", "postgres"], timeout=10)
                    if ready.returncode == 0:
                        break
                    time.sleep(1)
                else:
                    raise RuntimeError("Local PostgreSQL did not become ready")
        if not verify_loopback():
            raise RuntimeError("Actual runtime ports are not exclusively loopback")
    except Exception:
        stop_local_containers()
        raise
    print("Actual db/API/Studio port bindings verified: loopback only.")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare() -> dict:
    source = ROOT / "supabase"
    target = WORK / "supabase"
    files = [source / "seed.sql"]
    for directory in ("migrations", "tests", "fixtures"):
        files.extend(sorted((source / directory).rglob("*.sql")))
    checksums = {}
    for original in files:
        relative = original.relative_to(source)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and digest(destination) != digest(original):
            raise RuntimeError(f"Local snapshot differs: {relative}; review before replacing")
        if not destination.exists():
            shutil.copy2(original, destination)
        checksums[str(relative).replace("\\", "/")] = digest(destination)
    config = (source / "config.toml").read_text(encoding="utf-8")
    config = config.replace('project_id = "nestline"', f'project_id = "{PROJECT}"', 1)
    config = config.replace("127.0.0.1:8501", "127.0.0.1:5180").replace("localhost:8501", "localhost:5180")
    destination = target / "config.toml"
    if destination.exists() and destination.read_text(encoding="utf-8") != config:
        raise RuntimeError("Local config differs; review it instead of overwriting")
    if not destination.exists():
        destination.write_text(config, encoding="utf-8")
    manifest = {"project_id": PROJECT, "files": checksums, "hosted_project_linked": False}
    (WORK / "source-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"project_id": PROJECT, "sql_files_verified": len(checksums), "migrations": len(list((target / "migrations").glob("*.sql")))}


def run(command: list[str], timeout: int = 1800) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    for name in ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD", "SUPABASE_PROJECT_ID", "SUPABASE_WORKDIR"):
        env.pop(name, None)
    return subprocess.run(command, cwd=WORK, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def cli(*args: str) -> subprocess.CompletedProcess:
    executable = ROOT / "node_modules/.bin" / ("supabase.cmd" if os.name == "nt" else "supabase")
    return run([str(executable), *args, "--workdir", str(WORK), "--network-id", NETWORK])


def safe_output(value: str) -> str:
    value = re.sub(r"\x1b\[[0-9;]*m", "", value)
    value = re.sub(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[REDACTED-JWT]", value)
    value = re.sub(r"(?:sb_(?:publishable|secret)_|sk-)[A-Za-z0-9_-]+", "[REDACTED-KEY]", value)
    value = re.sub(r"postgres(?:ql)?://[^\s\"']+", "[REDACTED-DB-URL]", value)
    return "\n".join(line for line in value.splitlines()
                     if not re.search(r"(?i)(api.?key|service.?role|secret|password|anon.?key|publishable.?key)", line))


def ensure_network() -> None:
    inspected = run(["docker", "network", "inspect", NETWORK])
    if inspected.returncode:
        created = run(["docker", "network", "create", "-o",
                       "com.docker.network.bridge.host_binding_ipv4=127.0.0.1", NETWORK])
        if created.returncode:
            raise RuntimeError("Could not create localhost-only Docker network")
        inspected = run(["docker", "network", "inspect", NETWORK])
    if json.loads(inspected.stdout)[0].get("Options", {}).get("com.docker.network.bridge.host_binding_ipv4") != "127.0.0.1":
        raise RuntimeError("Docker network is not localhost-only")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "start", "resume", "status", "test", "lint", "profile", "stop"))
    args = parser.parse_args()
    print(json.dumps(prepare()), flush=True)
    if args.action == "prepare":
        return 0
    if args.action == "stop":
        stop_local_containers()
        print("Stopped only Maya's local containers. Containers and volumes retained; no data deleted.")
        return 0
    if args.action == "resume" or (args.action == "start" and (WORK / "loopback-repair.json").exists()):
        resume_local()
        return 0
    if args.action == "start":
        ensure_network()
        result = cli("start",
                     "--exclude", "realtime,imgproxy,mailpit,edge-runtime,logflare,vector,supavisor")
    elif args.action in ("status", "profile"):
        result = cli("status", "--output", "json")
        if result.returncode == 0:
            payload = json.loads(result.stdout)
            if args.action == "profile":
                sys.path.insert(0, str(ROOT))
                from app.services.local_backend_configuration import local_profile
                if payload.get("API_URL") != "http://127.0.0.1:54321":
                    raise RuntimeError("Unexpected local API URL")
                public_key = payload.get("PUBLISHABLE_KEY") or payload.get("ANON_KEY")
                profile = local_profile(public_key)
                profile_path = ROOT / ".env.maya-local"
                if profile_path.exists():
                    raise RuntimeError("Local profile already exists; not overwriting it")
                profile_path.write_text("\n".join(f"{key}={value}" for key, value in profile.items()) + "\n", encoding="utf-8")
                print("Created ignored .env.maya-local; provider secrets remain only in the original .env. Live runtime remains disabled.")
                return 0
            # This report deliberately excludes all keys and database URLs.
            print(json.dumps({name: payload.get(name) for name in ("API_URL", "STUDIO_URL")}, indent=2))
            return 0
    elif args.action == "test":
        result = cli("test", "db", "--local")
    else:
        result = cli("db", "lint", "--local")
    output = safe_output(result.stdout + "\n" + result.stderr)
    (WORK / f"{args.action}-redacted.log").write_text(output, encoding="utf-8")
    print(output[-18000:])
    print(f"exit_code={result.returncode}")
    if args.action == "start" and result.returncode == 0 and not verify_loopback():
        stop_local_containers()
        print("Startup did not bind exclusively to loopback. Maya containers stopped with data retained; resolve binding before restart.")
        return 1
    return result.returncode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"Local database setup failed ({type(exc).__name__}): {safe_output(str(exc))}")
        sys.exit(1)
