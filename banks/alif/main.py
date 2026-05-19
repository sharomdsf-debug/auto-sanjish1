import requests
import json
import os
import time
import re

# =========================================================
# API
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
# MODEL
# =========================================================

MODEL = "deepseek/deepseek-chat-v3-0324:free"

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
# SCRAPE
# =========================================================

def scrape():

    print("=" * 80)
    print(f"SCRAPING: {BANK['website']}")
    print("=" * 80)

    for attempt in range(3):

        print(f"\nATTEMPT {attempt+1}/3")

        try:

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

        except Exception as e:

            print("\nSCRAPE ERROR:")
            print(str(e))

        time.sleep(5)

    return ""

# =========================================================
# PROMPT
# =========================================================

PROMPT = """
Аз ин матни калон танҳо қисми қурби асъорро баргардон.

Ягон шарҳ надеҳ.
Фақат ҳамон қисми қурбҳоро навис.

TEXT:
"""

# =========================================================
# AI
# =========================================================

def ask_ai(markdown):

    print("\n" + "=" * 80)
    print("ASKING AI")
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
                    "model": MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": PROMPT + markdown
                        }
                    ],
                    "temperature": 0,
                    "max_tokens": 1000
                },
                timeout=300
            )

            print("\nSTATUS:")
            print(response.status_code)

            raw = response.text

            print("\nRAW RESPONSE:")
            print(raw[:2000])

            data = response.json()

            if "choices" not in data:

                print("\nNO CHOICES")
                continue

            content = data["choices"][0]["message"]["content"]

            if not content:

                print("\nEMPTY CONTENT")
                continue

            print("\nAI RESULT:")
            print(content)

            return content

        except Exception as e:

            print("\nAI ERROR:")
            print(str(e))

        time.sleep(5)

    return ""

# =========================================================
# PARSE
# =========================================================

def parse_rates(text):

    result = json.loads(json.dumps(EMPTY))

    patterns = {
        "USD": r"USD\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)",
        "EUR": r"EUR\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)",
        "RUB": r"RUB\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)",
        "CNY": r"CNY\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)",
        "KZT": r"KZT\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)"
    }

    for currency, pattern in patterns.items():

        match = re.search(pattern, text)

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

if not markdown:

    print("\nSCRAPE FAILED")
    exit()

ai_text = ask_ai(markdown)

currencies = parse_rates(ai_text)

final = {
    "bank_name": BANK["name"],
    "bank_id": BANK["id"],
    "success": True,
    "currencies": currencies
}

print("\n" + "=" * 80)
print("FINAL RESULT")
print("=" * 80)

print(json.dumps(final, ensure_ascii=False, indent=2))

with open("result.json", "w", encoding="utf-8") as f:

    json.dump(
        final,
        f,
        ensure_ascii=False,
        indent=2
    )

print("\nRESULT SAVED -> result.json")
print("\nDONE")
