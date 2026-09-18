"""Manually verify scraped menu links, one restaurant at a time.

For each restaurant object in an input JSON file, prints its id, name,
hasFoundMenu and menuLink, opens the link in your browser (if present),
and asks you to judge not just whether a menu was there, but whether the
LLM picked the *best available* source for it (e.g. an official website
menu is better than a Wolt listing). Your answer is stored under a new
"manualVerification" key, one of:

    "correct"    - the link is the best available menu (or, if no menu
                   was found, there really is none available anywhere)
    "suboptimal" - a real menu is at the link, but a better source exists
    "incorrect"  - the link has no real menu (false positive), or no menu
                   was found but one actually exists (false negative)

After every verdict you're also asked for a better menu link you found
during your manual check (if any), stored under "correctMenuLink".
Leave it blank if the link above was already the best one.

Progress is written to a separate output file after every answer, so the
input file is never touched and you can safely stop (Ctrl+C) and resume
later — already-verified entries are skipped on the next run.

Usage:
    python manual_verify_menus.py data/manual_tries_20_only/20260916-claude-1.json
    python manual_verify_menus.py data/manual_tries_20_only/20260916-claude-1.json --output data/manual_tries_20_only/verified/20260916-claude-1.json
    python manual_verify_menus.py data/manual_tries_20_only/*.json   # process several files in a row

Answering a restaurant:
    c   -> correct: best available menu (or correctly no menu found)
    o   -> suboptimal: real menu, but a better source exists
    i   -> incorrect: no real menu there / missed an existing menu
    s   -> skip for now (leave unverified, ask again next run)
    q   -> save and quit
"""

import argparse
import json
import sys
import webbrowser
from pathlib import Path

CORRECT_ANSWERS = {"c", "correct"}
SUBOPTIMAL_ANSWERS = {"o", "suboptimal"}
INCORRECT_ANSWERS = {"i", "incorrect"}
SKIP_ANSWERS = {"s", "skip"}
QUIT_ANSWERS = {"q", "quit"}


def load_json(path: Path) -> list:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def default_output_path(input_path: Path) -> Path:
    return input_path.with_name(input_path.stem + "-verified" + input_path.suffix)


def prompt_verification(restaurant: dict) -> str | None:
    """Returns 'quit', 'skip', or None (answer already recorded)."""
    print("-" * 70)
    print(f"id:          {restaurant.get('id', '')}")
    print(f"name:        {restaurant.get('name', '')}")
    print(f"hasFoundMenu:{restaurant.get('hasFoundMenu', '')}")
    link = restaurant.get("menuLink", "")
    print(f"menuLink:    {link}")

    if link:
        webbrowser.open(link)
    else:
        print("(no menuLink to open)")

    while True:
        answer = input("Verdict? [c=correct / o=suboptimal / i=incorrect / s=skip / q=quit]: ").strip().lower()
        if answer in CORRECT_ANSWERS:
            verdict = "correct"
        elif answer in SUBOPTIMAL_ANSWERS:
            verdict = "suboptimal"
        elif answer in INCORRECT_ANSWERS:
            verdict = "incorrect"
        elif answer in SKIP_ANSWERS:
            return "skip"
        elif answer in QUIT_ANSWERS:
            return "quit"
        else:
            print("Please answer c, o, i, s (skip) or q (quit).")
            continue

        restaurant["manualVerification"] = verdict
        sys.stdout.flush()
        better_link = input("Better menu link you found (leave blank if the one above was fine / none found): ").strip()
        if better_link:
            restaurant["correctMenuLink"] = better_link
        else:
            restaurant.pop("correctMenuLink", None)
        return None


def process_file(input_path: Path, output_path: Path) -> bool:
    """Returns False if the user asked to quit entirely, True otherwise."""
    data = load_json(input_path)

    if output_path.exists():
        data = load_json(output_path)

    total = len(data)
    remaining = sum(1 for r in data if "manualVerification" not in r)
    print(f"\n=== {input_path.name} -> {output_path.name} ===")
    print(f"{total} restaurants total, {remaining} left to verify.")

    for restaurant in data:
        if "manualVerification" in restaurant:
            continue

        result = prompt_verification(restaurant)
        save_json(output_path, data)

        if result == "quit":
            print(f"Saved progress to {output_path}")
            return False

    print(f"Done with {input_path.name}. Saved to {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_files", nargs="+", type=Path, help="Input JSON file(s) to verify")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON file path (only valid with a single input file). "
        "Defaults to '<input>-verified.json' next to the input file.",
    )
    args = parser.parse_args()

    if args.output and len(args.input_files) > 1:
        parser.error("--output can only be used with a single input file")

    for input_path in args.input_files:
        if not input_path.exists():
            print(f"Skipping missing file: {input_path}", file=sys.stderr)
            continue

        output_path = args.output if args.output else default_output_path(input_path)
        keep_going = process_file(input_path, output_path)
        if not keep_going:
            break


if __name__ == "__main__":
    main()
