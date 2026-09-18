"""Manually verify LLM menu-finder responses, one restaurant at a time.

Same idea as manual_verify_menus.py, but for the response CSVs produced by
llm_menu_finder.py under data/runs/<date>/responses/*.csv. Each row there is
one restaurant with columns: prompt, model, batch_index, restaurant_id,
input, answer -- where "input" is the original restaurant record (JSON) and
"answer" is the model's raw answer for that restaurant (JSON, sometimes
wrapped in prose or a ```json fence, sometimes empty if parsing failed
upstream).

For each row, prints the restaurant's id/name (from "input"), the model,
and hasFoundMenu/menuLink (parsed out of "answer"), opens the link in your
browser (if present), and asks you to judge it the same way as
manual_verify_menus.py -- not just whether a menu was there, but whether the
LLM picked the *best available* source for it. Your answer is stored in two
new columns, "manualVerification" (one of "correct" / "suboptimal" /
"incorrect") and "correctMenuLink".

Progress is written to a separate output CSV after every answer, so the
input file is never touched and you can safely stop (Ctrl+C) and resume
later -- already-verified rows are skipped on the next run.

Output defaults to a same-named CSV under a "verified_responses" folder next
to "responses" (e.g. data/runs/<date>/responses/foo.csv ->
data/runs/<date>/verified_responses/foo.csv).

Usage:
    python manual_verify_responses.py data/runs/2026-09-16/responses/prompt_20260910.md__gpt-5.6-terra.csv
    python manual_verify_responses.py data/runs/2026-09-16/responses/prompt_20260910.md__gpt-5.6-terra.csv --output data/runs/2026-09-16/verified_responses/gpt-5.6-terra.csv
    python manual_verify_responses.py data/runs/2026-09-16/responses/*.csv   # process several files in a row

Answering a restaurant:
    c   -> correct: best available menu (or correctly no menu found)
    o   -> suboptimal: real menu, but a better source exists
    i   -> incorrect: no real menu there / missed an existing menu
    s   -> skip for now (leave unverified, ask again next run)
    q   -> save and quit
"""

import argparse
import csv
import json
import re
import sys
import webbrowser
from pathlib import Path

CORRECT_ANSWERS = {"c", "correct"}
SUBOPTIMAL_ANSWERS = {"o", "suboptimal"}
INCORRECT_ANSWERS = {"i", "incorrect"}
SKIP_ANSWERS = {"s", "skip"}
QUIT_ANSWERS = {"q", "quit"}

EXTRA_FIELDS = ["manualVerification", "correctMenuLink"]


def extract_json(text: str) -> dict:
    """Best-effort parse of a CSV cell (raw JSON, fenced, or prose-wrapped) into a dict."""
    text = str(text).strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    i, j = text.find("{"), text.rfind("}")
    if i != -1 and j > i:
        try:
            return json.loads(text[i:j + 1])
        except Exception:
            pass
    return {}


def load_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def default_output_path(input_path: Path) -> Path:
    """<date>/responses/foo.csv -> <date>/verified_responses/foo.csv (a
    sibling of "responses"), or "<name>-verified<suffix>" next to the input
    file if it isn't under a "responses" folder."""
    responses_dir = input_path.parent
    if responses_dir.name == "responses":
        return responses_dir.parent / "verified_responses" / input_path.name
    return input_path.with_name(input_path.stem + "-verified" + input_path.suffix)


def prompt_verification(row: dict) -> str | None:
    """Returns 'quit', 'skip', or None (answer already recorded)."""
    restaurant = extract_json(row.get("input", ""))
    answer = extract_json(row.get("answer", ""))

    print("-" * 70)
    print(f"model:       {row.get('model', '')}")
    print(f"id:          {row.get('restaurant_id', '') or restaurant.get('id', '')}")
    print(f"name:        {restaurant.get('name', '')}")
    print(f"hasFoundMenu:{answer.get('hasFoundMenu', '')}")
    link = answer.get("menuLink") or ""
    print(f"menuLink:    {link}")
    if not answer:
        print(f"(raw answer could not be parsed as JSON: {str(row.get('answer', ''))[:200]!r})")

    if link:
        webbrowser.open(link)
    else:
        print("(no menuLink to open)")

    while True:
        answer_key = input("Verdict? [c=correct / o=suboptimal / i=incorrect / s=skip / q=quit]: ").strip().lower()
        if answer_key in CORRECT_ANSWERS:
            verdict = "correct"
        elif answer_key in SUBOPTIMAL_ANSWERS:
            verdict = "suboptimal"
        elif answer_key in INCORRECT_ANSWERS:
            verdict = "incorrect"
        elif answer_key in SKIP_ANSWERS:
            return "skip"
        elif answer_key in QUIT_ANSWERS:
            return "quit"
        else:
            print("Please answer c, o, i, s (skip) or q (quit).")
            continue

        row["manualVerification"] = verdict
        sys.stdout.flush()
        better_link = input("Better menu link you found (leave blank if the one above was fine / none found): ").strip()
        row["correctMenuLink"] = better_link
        return None


def process_file(input_path: Path, output_path: Path) -> bool:
    """Returns False if the user asked to quit entirely, True otherwise."""
    data = load_csv(input_path)

    if output_path.exists():
        data = load_csv(output_path)

    for field in EXTRA_FIELDS:
        for row in data:
            row.setdefault(field, "")

    total = len(data)
    remaining = sum(1 for r in data if not r.get("manualVerification"))
    print(f"\n=== {input_path.name} -> {output_path.name} ===")
    print(f"{total} restaurants total, {remaining} left to verify.")

    for row in data:
        if row.get("manualVerification"):
            continue

        result = prompt_verification(row)
        save_csv(output_path, data)

        if result == "quit":
            print(f"Saved progress to {output_path}")
            return False

    print(f"Done with {input_path.name}. Saved to {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_files", nargs="+", type=Path, help="Input response CSV file(s) to verify")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV file path (only valid with a single input file). "
        "Defaults to '<input>-verified.csv' next to the input file.",
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
