#!/usr/bin/env python3
"""Compatibility wrapper for the bounded OpenAI fictional benchmark."""

from __future__ import annotations

import sys

from scripts.run_live_provider_benchmark import main


if __name__ == "__main__":
    sys.exit(main(["--provider", "openai", *sys.argv[1:]]))
