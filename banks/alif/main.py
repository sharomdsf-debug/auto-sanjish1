import requests
import json
import os
import time

# =========================================================
# API KEYS
# =========================================================

FIRECRAWL_API = os.getenv("FIRECRAWL_API")
OPENROUTER_API = os.getenv("OPENROUTER_API")

# =========================================================
# BANK
# =========================================================

BANK = {
    "name": "Алиф Бонк",
    "id": "alif",
    "website": "https://alif.tj/ru"
}

# =========================================================
# MODELS
# =========================================================

MODELS = [
    "openai/gpt-oss-120b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-7b-instruct:free"
]

# =========================================================
# EMPTY JSON
# =========================================================

EMPTY = {
    "USD": {"buy": "0.0000", "sell": "0.0000"},
    "EUR": {"buy": "0.0000", "sell": "0.0000"},
    "RUB": {"buy": "0.0000", "sell": "0.0000"},
    "CNY": {"buy": "0.0000", "sell": "0.0000"},
    "KZT": {"buy": "0.0000", "sell": "0.0000"}
}

# =========================================================
# FIRECRAWL SCRAPE
# =========================================================

def scrape():

    print("=" * 80)
    print(f"SCRAPING: {BANK['website']}")
    print("=" * 80)

    response = requests.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={
            "Authorization": f"Bearer {FIRECRAWL_API}",
            "Content-Type": "application/json"
        },
        json={
            "url": BANK["website"],
            "formats": ["markdown"],
            "onlyMainContent": False,
            "waitFor": 10000
        },
        timeout=180
    )

    print("\nSTATUS:")
    print(response.status_code)

    data = response.json()

    markdown = data.get("data", {}).get("markdown", "")

    print("\nMARKDOWN SIZE:")
    print(len(markdown))

    with open("full_markdown.txt", "w", encoding="utf-8") as f:
        f.write(markdown)

    print("\nFULL WEBSITE SAVED -> full_markdown.txt")

    return markdown

# =========================================================
# PROMPT
# =========================================================

PROMPT = """
Аз ин матни калон танҳо қурби асъорро ёб.

Қоидаҳо:
- Танҳо JSON баргардон
- Ягон шарҳ надеҳ
- Ягон markdown надеҳ
- Ягон ```json надеҳ
- Танҳо рақамҳои воқеиро истифода бар
- Агар асъор набошад -> 0.0000

Формат:

{
  "USD": {"buy":"0.0000","sell":"0.0000"},
  "EUR": {"buy":"0.0000","sell":"0.0000"},
  "RUB": {"buy":"0.0000","sell":"0.0000"},
  "CNY": {"buy":"0.0000","sell":"0.0000"},
  "KZT": {"buy":"0.0000","sell":"0.0000"}
}

МАТН:
"""

# =========================================================
# AI EXTRACT
# =========================================================

def extract(markdown):

    for model in MODELS:

        print("\n" + "=" * 80)
        print(f"MODEL: {model}")
        print("=" * 80)

        for attempt in range(3):

            print(f"\nATTEMPT {attempt+1}/3")

            try:

                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "user",
                                "content": PROMPT + markdown
                            }
                        ],
                        "temperature": 0,
                        "max_tokens": 400
                    },
                    timeout=300
                )

                print("\nSTATUS:")
                print(response.status_code)

                raw = response.text

                print("\nRAW RESPONSE:")
                print(raw[:3000])

                data = response.json()

                if "choices" not in data:
                    print("\nNO CHOICES")
                    continue

                content = data["choices"][0]["message"]["content"]

                if content is None:
                    print("\nCONTENT IS NONE")
                    continue

                print("\nAI CONTENT:")
                print(content)

                content = content.replace("```json", "")
                content = content.replace("```", "")

                start = content.find("{")
                end = content.rfind("}") + 1

                if start == -1:
                    print("\nNO JSON FOUND")
                    continue

                parsed = json.loads(content[start:end])

                return parsed

            except Exception as e:

                print("\nERROR:")
                print(str(e))

            time.sleep(5)

    return EMPTY

# =========================================================
# RUN
# =========================================================

print("\n" + "=" * 80)
print(BANK["name"])
print("=" * 80)

markdown = scrape()

result = extract(markdown)

final = {
    "bank_name": BANK["name"],
    "bank_id": BANK["id"],
    "currencies": result
}

print("\n" + "=" * 80)
print("FINAL RESULT")
print("=" * 80)

print(json.dumps(final, ensure_ascii=False, indent=2))

with open("result.json", "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=2)

print("\nRESULT SAVED -> result.json")
print("\nDONE")
