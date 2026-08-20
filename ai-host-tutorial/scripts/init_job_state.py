#!/usr/bin/env python3
"""Create ai-host-tutorial job-state.json."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any, Dict


def build_state(project: str, aspect: str) -> Dict[str, Any]:
    return {
        "skill": "ai-host-tutorial",
        "project": project,
        "created_at": date.today().isoformat(),
        "aspect": aspect,
        "stage": "intake",
        "loudness": {"target_mean_db": -12, "peak_db": 0},
        "gates": {
            "script": "pending",
            "storyboard": "pending",
            "host_preview": "not_started",
            "host_full": "not_started",
            "screen": "idle",
            "broll": "idle",
            "composite": "pending",
            "precheck": "pending",
        },
        "tracks": {
            "host": {"preview": None, "full": None, "audio": None},
            "screen": {"dir": "inputs/screen", "received": []},
            "broll": {"look_ref": None, "clips": []},
            "composite": {"edl": "outputs/jianying-edl.md"},
        },
        "ids": {
            "voice_id": None,
            "image_asset_id": None,
            "preview_video_id": None,
            "full_video_id": None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="ai-host-tutorial")
    parser.add_argument("--aspect", default="3:4", choices=["3:4", "9:16", "16:9"])
    parser.add_argument("--out", default="work/job-state.json")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists() and not args.force:
        raise SystemExit(f"{out} already exists; pass --force to overwrite")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(build_state(args.project, args.aspect), ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
