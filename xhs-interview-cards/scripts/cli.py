#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from compose_cards import compose_from_json  # noqa: E402
from extract_frame import extract_frame  # noqa: E402
from fetch_transcript import fetch_transcript  # noqa: E402
from fetch_video import fetch_video  # noqa: E402
from ledger import (  # noqa: E402
    colliding_quotes,
    content_root,
    load_config,
    load_ledger,
    make_output_dir,
    on_cooldown,
    record_entry,
)


def cfg() -> dict:
    return load_config(SKILL_DIR)


def cmd_status(_: argparse.Namespace) -> None:
    config = cfg()
    ledger = load_ledger(config)
    entries = ledger.get("entries") or []
    print(f"content_root={content_root(config)}")
    print(f"entries={len(entries)} cooldown_days={ledger.get('cooldown_days')}")
    print("seed_people_are_examples_not_a_closed_list=true")
    if not entries:
        return
    print("\nrecent:")
    for entry in entries[-8:]:
        print(
            f"- {entry.get('date')} [{entry.get('account')}] "
            f"{entry.get('person')} | {entry.get('title')}"
        )


def cmd_cooldown(args: argparse.Namespace) -> None:
    cool = on_cooldown(load_ledger(cfg()), args.account, args.person)
    if not cool:
        print("ok")
        return
    print(json.dumps(cool, ensure_ascii=False, indent=2))
    raise SystemExit(2)


def cmd_check_quotes(args: argparse.Namespace) -> None:
    quotes = json.loads(Path(args.quotes).read_text(encoding="utf-8"))
    if isinstance(quotes, dict):
        quotes = quotes.get("quotes") or []
    hits = colliding_quotes(quotes, load_ledger(cfg()))
    if not hits:
        print("ok")
        return
    print(json.dumps(hits, ensure_ascii=False, indent=2))
    raise SystemExit(2)


def cmd_fetch(args: argparse.Namespace) -> None:
    print(fetch_video(args.url, Path(args.out)))


def cmd_transcript(args: argparse.Namespace) -> None:
    source = args.url or args.video
    if not source:
        raise SystemExit("需要 --url 或 --video")
    info = fetch_transcript(source, Path(args.out_dir), cfg())
    print(json.dumps(info, ensure_ascii=False, indent=2))


def cmd_frame(args: argparse.Namespace) -> None:
    print(extract_frame(Path(args.video), Path(args.out), args.time, args.percent))


def cmd_compose(args: argparse.Namespace) -> None:
    config = cfg()
    canvas = tuple(config.get("canvas") or [1080, 1440])
    paths = compose_from_json(
        Path(args.frame),
        Path(args.cards),
        Path(args.out_dir),
        canvas=canvas,
        hero_ratio=float(config.get("hero_ratio") or 0.36),
    )
    for path in paths:
        print(path)


def cmd_prepare_dir(args: argparse.Namespace) -> None:
    path = make_output_dir(cfg(), args.account, args.date, args.person, args.title)
    print(path)


def cmd_record(args: argparse.Namespace) -> None:
    entry = json.loads(Path(args.entry).read_text(encoding="utf-8"))
    saved = record_entry(cfg(), entry)
    print(json.dumps(saved, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xhs-interview-cards")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")

    p = sub.add_parser("cooldown")
    p.add_argument("--account", required=True)
    p.add_argument("--person", required=True)

    p = sub.add_parser("check-quotes")
    p.add_argument("--quotes", required=True)

    p = sub.add_parser("fetch-video")
    p.add_argument("--url", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("transcript")
    p.add_argument("--url", default=None)
    p.add_argument("--video", default=None)
    p.add_argument("--out-dir", required=True)

    p = sub.add_parser("extract-frame")
    p.add_argument("--video", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--time", default=None)
    p.add_argument("--percent", type=float, default=0.2)

    p = sub.add_parser("compose")
    p.add_argument("--frame", required=True)
    p.add_argument("--cards", required=True)
    p.add_argument("--out-dir", required=True)

    p = sub.add_parser("prepare-dir")
    p.add_argument("--account", required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--person", required=True)
    p.add_argument("--title", required=True)

    p = sub.add_parser("record")
    p.add_argument("--entry", required=True)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    {
        "status": cmd_status,
        "cooldown": cmd_cooldown,
        "check-quotes": cmd_check_quotes,
        "fetch-video": cmd_fetch,
        "transcript": cmd_transcript,
        "extract-frame": cmd_frame,
        "compose": cmd_compose,
        "prepare-dir": cmd_prepare_dir,
        "record": cmd_record,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
