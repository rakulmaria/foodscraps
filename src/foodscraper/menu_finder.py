import json
import time
import pandas as pd
from tqdm import tqdm
from datetime import date
from foodscraper.config import *
import os
import openai
from dotenv import load_dotenv

RESTAURANT_FILE = "mini-box-input.json"
PROMPT = "prompt_20260910.md"
BATCH_SIZE = 20

load_dotenv()


def get_client():
    return openai.OpenAI(
        api_key=os.environ["LLMGATEWAY_API_KEY"],
        base_url="https://api.llmgateway.io/v1",
    )


def build_system_message(system_prompt, model):
    if model.startswith("anthropic/"):      # ensure caching with Anthropic (not default)
        return {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral", "ttl": "1h"},
                }
            ],
        }
    return {"role": "system", "content": system_prompt}


def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield i // n, seq[i:i + n]


def call_batch(client, model, system_msg, batch, *, temperature=0):
    """Send the cached instructions plus one batch of restaurants."""
    return client.chat.completions.create(
        model=model,
        temperature=temperature,               # 0 = as reproducible as the model allows
        messages=[
            system_msg,                        # cached instructions
            {"role": "user", "content": json.dumps(batch, ensure_ascii=False)},
        ],
        tools=[
            {"type": "web_search"}
        ],
    )


def parse_list(text):
    """Best-effort parse of the model's answer into a list of dicts, or None."""
    text = str(text).strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            text = text[text.find("\n") + 1:]
    try:
        data = json.loads(text)
    except Exception:
        i, j = text.find("["), text.rfind("]")
        if i == -1 or j <= i:
            return None
        try:
            data = json.loads(text[i:j + 1])
        except Exception:
            return None
    if isinstance(data, dict):
        data = [data]
    return data if isinstance(data, list) else None


def parse_restaurants(path):
    df = pd.read_json(path)

    if "displayName" in df.columns:
        df["name"] = df["displayName"].apply(lambda d: d["text"] if isinstance(d, dict) else d)

    df = df.reindex(columns=["id", "name", "formattedAddress", "websiteUri"])
    return df.to_dict(orient="records")


def run(restaurants, models, *, batch_size=BATCH_SIZE, sleep=0.2, temperature=0):
    system_prompt = (PROMPTS_DIR / PROMPT).read_text(encoding="utf-8")
    client = get_client()

    today_dir = RUNS_DIR / str(date.today())
    responses_dir = today_dir / "responses"
    raw_responses_dir = today_dir / "raw_responses"
    responses_dir.mkdir(parents=True, exist_ok=True)
    raw_responses_dir.mkdir(parents=True, exist_ok=True)

    batches = list(chunked(restaurants, batch_size))

    for model in models:
        tag = f"{PROMPT}__{model.split('/')[-1]}"
        csv_path = responses_dir / f"{tag}.csv"
        raw_path = raw_responses_dir / f"{tag}.jsonl"
        csv_path.unlink(missing_ok=True)      # fresh run -- drop any earlier output for this tag
        raw_path.unlink(missing_ok=True)

        system_msg = build_system_message(system_prompt, model)

        header_written = False
        for batch_index, batch in tqdm(batches, desc=model):
            resp = call_batch(client, model, system_msg, batch,
                              temperature=temperature)
            answer = resp.choices[0].message.content

            parsed = parse_list(answer)
            by_id = {}
            if parsed is not None:
                for obj in parsed:
                    if isinstance(obj, dict) and "id" in obj:
                        by_id[obj["id"]] = json.dumps(obj, ensure_ascii=False)

            if parsed is None:
                tqdm.write(f"  batch {batch_index}: no JSON list found; storing raw answer on every row")
            else:
                missing = [r["id"] for r in batch if r["id"] not in by_id]
                if missing:
                    tqdm.write(f"  batch {batch_index}: {len(missing)}/{len(batch)} ids missing from response")

            rows = [
                {
                    "prompt": PROMPT,               # which prompt produced this
                    "model": model,
                    "batch_index": batch_index,
                    "restaurant_id": r["id"],
                    "input": json.dumps(r, ensure_ascii=False),
                    "answer": by_id.get(r["id"], "" if parsed is not None else answer),
                }
                for r in batch
            ]
            pd.DataFrame(rows).to_csv(csv_path, mode="a", header=not header_written, index=False)
            header_written = True

            rec = resp.model_dump(warnings=False)
            rec["batch_index"] = batch_index
            with raw_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

            time.sleep(sleep)


def main():
    restaurants = parse_restaurants(GOOGLE_MAPS_DIR / RESTAURANT_FILE)

    models = [
        "openai/gpt-5.6-terra",
        "anthropic/claude-sonnet-5",
        "google-ai-studio/gemini-3.8-flash",
    ]

    run(restaurants, models)


if __name__ == "__main__":
    main()
