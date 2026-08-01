#!/usr/bin/env python3
"""Backfill smevals Runs from the SVGs committed to this repository.

Every git revision of each <model>.svg becomes one Run under
runs/pelican/default/<model-slug>/<commit-timestamp>/ containing the
SVG as output.txt plus a run.yaml marked backfilled: true.

Caveats, recorded in each run.yaml: output.txt is the SVG extracted
from the model's response (the raw response was never committed), and
the timestamp is the commit's author date, not the moment the model
was called. Failed attempts (the old script's failures/ directory)
were never committed and cannot be recovered.

Idempotent: existing Run directories are left untouched.
"""
import pathlib
import re
import subprocess
from datetime import datetime, timezone

import yaml

ROOT = pathlib.Path(__file__).parent

# Exact model names from generate-svgs.sh; filenames replaced ':' with '-'
MODELS = [
    "gpt-3.5-turbo",
    "gpt-4o-mini",
    "gpt-4o",
    "o1-preview",
    "o1-mini",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-sonnet-20241022",
    "claude-3-haiku-20240307",
    "claude-3-opus-20240229",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-1.5-pro-001",
    "gemini-1.5-pro-002",
    "gemini-1.5-flash-8b-001",
    "cerebras-llama3.1-8b",
    "cerebras-llama3.1-70b",
    "gemini-exp-1114",
    "gemini-exp-1121",
    "gemini-exp-1206",
    "us.amazon.nova-micro-v1:0",
    "us.amazon.nova-lite-v1:0",
    "us.amazon.nova-pro-v1:0",
]

TASK = {
    "name": "pelican",
    "prompt": "Generate an SVG of a pelican riding a bicycle",
}


def slugify(text):
    # Matches smevals' own slugify
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", text).strip("-")


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout


def main():
    created = skipped = 0
    for model in MODELS:
        filename = model.replace(":", "-") + ".svg"
        if not (ROOT / filename).exists():
            print(f"!! {filename} not found, skipping {model}")
            continue
        history = git(
            "log", "--follow", "--format=%H %aI", "--", filename
        ).strip().splitlines()
        for line in history:
            commit, author_date = line.split()
            started = datetime.fromisoformat(author_date).astimezone(timezone.utc)
            timestamp = started.strftime("%Y-%m-%dT%H-%M-%SZ")
            run_dir = ROOT / "runs" / TASK["name"] / "default" / slugify(model) / timestamp
            if run_dir.exists():
                skipped += 1
                continue
            svg = git("show", f"{commit}:{filename}")
            run_dir.mkdir(parents=True)
            (run_dir / "output.txt").write_text(svg)
            record = {
                "task": TASK,
                "config": {
                    "name": "default",
                    "runner": "run-llm",
                    "model": model,
                },
                "started": started.isoformat(),
                "exit_code": 0,
                "backfilled": True,
                "source_commit": commit,
                "note": (
                    "Backfilled from git history: output.txt is the extracted "
                    "SVG (the raw model response was not preserved) and "
                    "started is the commit's author date."
                ),
            }
            # run.yaml written last: its presence marks a complete Run
            (run_dir / "run.yaml").write_text(yaml.safe_dump(record, sort_keys=False))
            created += 1
            print(f"{run_dir.relative_to(ROOT)}")
    print(f"\n{created} run(s) created, {skipped} already existed")


if __name__ == "__main__":
    main()
