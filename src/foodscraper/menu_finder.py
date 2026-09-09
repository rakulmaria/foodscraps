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

load_dotenv()  

def get_client():
    return openai.OpenAI(
        api_key=os.environ["LLMGATEWAY_API_KEY"],
        base_url="https://api.llmgateway.io/v1",
    )

def call_model(client, model, system_prompt, user_content, *, temperature=0):
    return client.chat.completions.create(
        model=model,
        temperature=temperature,          # 0 = as reproducible as the model allows
        messages=[
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        tools=[
            {"type": "web_search"}
        ]
    )

def run(restaurants, models, prompt_name, *, sleep=0.2, temperature=0):
    system_prompt = (PROMPTS_DIR / f"{prompt_name}.md").read_text(encoding="utf-8")
    client = get_client()

    today_dir = DATA_DIR / str(date.today())
    responses_dir = today_dir / "responses"
    raw_responses_dir = today_dir / "raw_responses"
    responses_dir.mkdir(parents=True, exist_ok=True)
    raw_responses_dir.mkdir(parents=True, exist_ok=True)

    for model in models:
        rows, raw = [], []
        
        for r in tqdm(restaurants, desc=model):
            user_content = json.dumps(r, ensure_ascii=False)
            resp = call_model(client, model, system_prompt, user_content,
                              temperature=temperature)

            rows.append({
                "prompt": prompt_name,                       # which prompt produced this
                "model": model,
                "restaurant_id": r["id"],
                "input": user_content,
                "answer": resp.choices[0].message.content,
            })
            raw.append(resp.model_dump(warnings=False))    
            time.sleep(sleep)

        tag = f"{prompt_name}__{model.split('/')[-1]}"
        pd.DataFrame(rows).to_csv(responses_dir / f"{tag}.csv", index=False)

        (raw_responses_dir / f"{tag}.jsonl").write_text(
            "\n".join(json.dumps(x, ensure_ascii=False) for x in raw), encoding="utf-8"
        )

def main():
    # restaurants = json.loads((DATA_DIR / "mini-box_20260311_101610.json").read_text())
    restaurants = json.loads((GOOGLE_MAPS_DATASETS / RESTAURANT_FILE).read_text())

    models = [
        "openai/gpt-5.6-terra", 
        "anthropic/claude-sonnet-5", 
        "google-ai-studio/gemini-3.8-flash"
    ]

    run(restaurants, models, prompt_name="prompt_20260904")

if __name__ == "__main__":
    main()
