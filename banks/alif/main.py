import requests
import json
import re
import os
import time

# =========================================================
# API
# =========================================================

OPENROUTER_API = os.getenv("OPENROUTER_API")

# =========================================================
# MODEL
# =========================================================

MODEL = "deepseek/deepseek-v4-flash:free"

# =========================================================
# BANK
# =========================================================

BANK = {
    "name": "Алиф Бонк",
    "id": "alif",
    "url": "https://alif.tj/ru"
}

# =========================================================
# EMPTY
# =========================================================

EMPTY = {
    "USD": {"buy": "0.0000", "sell": "0.0000"},
    "EUR": {"buy": "0.0000", "sell": "0.0000"},
    "RUB": {"buy": "0.0000", "sell": "0.0000"},
    "CNY": {"buy": "0.0000", "sell": "0.0000"},
    "KZT": {"buy": "0.0000", "sell": "0.0000"}
}

# =========================================================
# PROMPT
# =========================================================

PROMPT = """
Аз ин матни калон танҳо қурби асъорро пайдо кун.

Танҳо ҳамон қисми қурбҳоро баргардон.

JSON лозим нест.
Шарҳ надеҳ.

Матн:
"""

# =========================================================
# SCRAPE
# =========================================================

def scrape():

    print("=" * 80)
    print("SCRAPING:", BANK["url"])
    print("=" * 80)

    response = requests.get(
        BANK["url"],
        timeout=120,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    print("STATUS:")
    print(response.status_code)

    html = response.text

    print("HTML SIZE:")
    print(len(html))

    with open("full_markdown.txt", "w", encoding="utf-8") as f:
        f.write(html)

    print("FULL WEBSITE SAVED -> full_markdown.txt")

    return html

# =========================================================
# ASK AI
# =========================================================

def ask_ai(markdown):

    print("=" * 80)
    print("ASKING AI")
    print("=" * 80)

    for attempt in range(3):

        print(f"ATTEMPT {attempt+1}/3")

        try:

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": PROMPT + markdown
                        }
                    ],
                    "temperature": 0
                },
                timeout=300
            )

            print("STATUS:")
            print(response.status_code)

            data = response.json()

            print("RAW RESPONSE:")
            print(json.dumps(data, ensure_ascii=False)[:2000])

            if "choices" not in data:
                print("NO CHOICES")
                time.sleep(5)
                continue

            content = data["choices"][0]["message"]["content"]

            if not content:
                print("EMPTY CONTENT")
                time.sleep(5)
                continue

            print("=" * 80)
            print("AI FOUND THIS:")
            print("=" * 80)

            print(content)

            return content

        except Exception as e:

            print("ERROR:")
            print(e)

        time.sleep(5)

    return ""

# =========================================================
# EXTRACT RATES
# =========================================================

def extract_rates(text):

    result = json.loads(json.dumps(EMPTY))

    patterns = {
        "USD": r"USD.*?(\d+\.\d+).*?(\d+\.\d+)",
        "EUR": r"EUR.*?(\d+\.\d+).*?(\d+\.\d+)",
        "RUB": r"RUB.*?(\d+\.\d+).*?(\d+\.\d+)",
        "CNY": r"CNY.*?(\d+\.\d+).*?(\d+\.\d+)",
        "KZT": r"KZT.*?(\d+\.\d+).*?(\d+\.\d+)"
    }

    for currency, pattern in patterns.items():

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.DOTALL
        )

        if match:

            result[currency]["buy"] = match.group(1)
            result[currency]["sell"] = match.group(2)

    return result

# =========================================================
# RUN
# =========================================================

print("\n" + "=" * 80)
print(BANK["name"])
print("=" * 80)

markdown = scrape()

ai_text = ask_ai(markdown)

currencies = extract_rates(ai_text)

final = {
    "bank_name": BANK["name"],
    "bank_id": BANK["id"],
    "success": True,
    "currencies": currencies
}

print("=" * 80)
print("FINAL RESULT")
print("=" * 80)

print(json.dumps(
    final,
    ensure_ascii=False,
    indent=2
))

with open("result.json", "w", encoding="utf-8") as f:

    json.dump(
        final,
        f,
        ensure_ascii=False,
        indent=2
    )

print("RESULT SAVED -> result.json")

print("DONE")
