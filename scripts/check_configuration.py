"""Print a secret-free local configuration report."""

from __future__ import annotations

import argparse
import json
import os

from dotenv import load_dotenv

from app.services.configuration import ApplicationMode, validate_configuration


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("demo", "personal"), required=True)
    parser.add_argument("--env-file")
    args = parser.parse_args()
    if args.env_file:
        load_dotenv(args.env_file, override=False)
    report = validate_configuration(os.environ, mode=ApplicationMode(args.mode))
    print(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True))
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
