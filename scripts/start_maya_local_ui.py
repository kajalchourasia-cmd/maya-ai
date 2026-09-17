"""Start a loopback-only UI and API with private access kept in process memory.

Does not edit .env, publish source content, import data, or spend provider budget
until the user actually requests a live answer. Does not stop existing services.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-private-local', action='store_true')
    parser.add_argument('--node', required=True, type=Path)
    args = parser.parse_args()
    if not args.execute_private_local:
        parser.error('Explicit private local execution required')
    for port in (8000, 5180):
        with socket.socket() as probe:
            if probe.connect_ex(('127.0.0.1', port)) == 0:
                raise SystemExit(f'Port {port} is occupied. Inspect its owner; no existing process was stopped.')
    if not args.node.is_file():
        raise SystemExit('Node executable not found')
    env = dict(os.environ)
    env.update(MAYA_RUNTIME_MODE='private_development', MAYA_OPERATOR_TOKEN=secrets.token_urlsafe(36),
               MAYA_LOCAL_UI_ORIGIN='http://127.0.0.1:5180', MAYA_ALLOWED_ORIGINS='http://127.0.0.1:5180',
               NEXT_PUBLIC_MAYA_API_URL='/api/maya', MAYA_ISOLATED_PREVIEW='true',
               PYTHONPATH=os.pathsep.join([str(ROOT/'.local-api-deps'), str(ROOT)]), PYTHONDONTWRITEBYTECODE='1')
    output = ROOT/'reports/local/ui-integration'
    output.mkdir(parents=True, exist_ok=True)
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    commands = [
        ('api', [sys.executable, '-B', '-m', 'uvicorn', 'api.main:app', '--host', '127.0.0.1', '--port', '8000', '--no-access-log'], ROOT),
        ('ui', [str(args.node.resolve()), str(ROOT/'frontend/node_modules/next/dist/bin/next'), 'dev', '--webpack', '--hostname', '127.0.0.1', '--port', '5180'], ROOT/'frontend'),
    ]
    processes = {}
    for name, command, cwd in commands:
        with (output/f'{name}.log').open('ab') as log:
            child = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                     stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
            processes[name] = child.pid
    (output/'processes.json').write_text(json.dumps(processes, indent=2), encoding='utf-8')
    print(json.dumps({'url':'http://127.0.0.1:5180/', 'pids':processes,
                      'access':'private local only', 'secrets_written':False}))


if __name__ == '__main__':
    main()
