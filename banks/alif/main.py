import requests
import os
import json
import time
import copy
import re
from datetime import datetime

# =========================================================
# API
# =========================================================

FIRECRAWL_API = os.getenv("FIRECRAWL_API")
OPENROUTER_API = os.getenv("OPENROUTER_API")

# =========================================================
# MODEL
# =========================================================

MODELS = [
    "openai/gpt-oss-120b:free"
]

# =========================================================
# BANK
# =========================================================

BANK = {
    "name": "Алиф Бонк",
    "id": "alif",
    "website": "https://alif.tj/ru"
}

# =========================================================
# VALIDATION
# =========================================================

VALID_RANGES = {
    "USD": (8.0, 12.0),
    "EUR": (8.0, 14.0),
    "RUB": (0.08, 0.25),
    "CNY": (1.0, 2.5),
    "KZT": (0.010, 0.060)
}

CURRENCIES = list(VALID_RANGES.keys())

EMPTY = {
    c: {
        "buy": "0.0000",
        "sell": "0.0000"
    }
    for c in CURRENCIES
}

# =========================================================
# HELPERS
# =========================================================

def validate(currency, value):

    try:

        num = float(str(value).replace(",", "."))

        lo, hi = VALID_RANGES[currency]

        if lo <= num <= hi:
            return f"{num:.4f}"

        return "0.0000"

    except:
        return "0.0000"


def clean_json(data):

    result = copy.deepcopy(EMPTY)

    for cur in CURRENCIES:

        if cur not in data:
            continue

        result[cur]["buy"] = validate(
            cur,
            data[cur].get("buy", "0")
        )

        result[cur]["sell"] = validate(
            cur,
            data[cur].get("sell", "0")
        )

    return result


def count_found(data):

    total = 0

    for cur in CURRENCIES:

        if (
            data[cur]["buy"] != "0.0000"
            or data[cur]["sell"] != "0.0000"
        ):
            total += 1

    return total

# =========================================================
# SCRAPE
# =========================================================

def scrape(url):

    print("\n" + "=" * 80)
    print(f"SCRAPING: {url}")
    print("=" * 80)

    for attempt in range(3):

        try:

            print(f"\nATTEMPT {attempt+1}/3")

            response = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Authorization": f"Bearer {FIRECRAWL_API}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": url,
                    "formats": ["markdown"],
                    "onlyMainContent": False,
                    "waitFor": 15000
                },
                timeout=180
            )

            print("\nSTATUS:")
            print(response.status_code)

            data = response.json()

            markdown = data.get(
                "data",
                {}
            ).get(
                "markdown",
                ""
            )

            if len(markdown) > 1000:

                print("\nSCRAPE SUCCESS")

                print("\nMARKDOWN SIZE:")
                print(len(markdown))

                with open(
                    "full_markdown.txt",
                    "w",
                    encoding="utf-8"
                ) as f:
                    f.write(markdown)

                print("\nFULL WEBSITE SAVED -> full_markdown.txt")

                return markdown

        except Exception as e:

            print("\nSCRAPE ERROR:")
            print(str(e))

        time.sleep(5)

    return ""

# =========================================================
# FIND SECTION
# =========================================================

def find_currency_section(markdown):

    print("\n" + "=" * 80)
    print("SEARCHING CURRENCY SECTION")
    print("=" * 80)

    keywords = [
        "Асъор",
        "Харид",
        "Фурӯш",
        "USD",
        "EUR",
        "RUB",
        "Обмен валют",
        "Курс валют"
    ]

    for keyword in keywords:

        pos = markdown.find(keyword)

        if pos != -1:

            start = max(0, pos - 2000)
            end = min(len(markdown), pos + 6000)

            section = markdown[start:end]

            print("\nFOUND KEYWORD:")
            print(keyword)

            print("\nSECTION SIZE:")
            print(len(section))

            with open(
                "currency_section.txt",
                "w",
                encoding="utf-8"
            ) as f:
                f.write(section)

            print("\nSECTION SAVED -> currency_section.txt")

            return section

    print("\nFALLBACK TO RAW MARKDOWN")

    return markdown

# =========================================================
# REGEX EXTRACT
# =========================================================

def regex_extract(section):

    print("\n" + "=" * 80)
    print("REGEX EXTRACTION")
    print("=" * 80)

    result = copy.deepcopy(EMPTY)

    patterns = {
        "USD": r"USD\s*\|\s*([0-9.,]+)\s*\|\s*([0-9.,]+)",
        "EUR": r"EUR\s*\|\s*([0-9.,]+)\s*\|\s*([0-9.,]+)",
        "RUB": r"RUB\s*\|\s*([0-9.,]+)\s*\|\s*([0-9.,]+)",
        "CNY": r"CNY\s*\|\s*([0-9.,]+)\s*\|\s*([0-9.,]+)",
        "KZT": r"KZT\s*\|\s*([0-9.,]+)\s*\|\s*([0-9.,]+)"
    }

    for currency, pattern in patterns.items():

        match = re.search(
            pattern,
            section,
            re.IGNORECASE
        )

        if match:

            buy = match.group(1)
            sell = match.group(2)

            result[currency]["buy"] = validate(
                currency,
                buy
            )

            result[currency]["sell"] = validate(
                currency,
                sell
            )

            print(f"\nFOUND {currency}")
            print(f"BUY: {buy}")
            print(f"SELL: {sell}")

    return result

# =========================================================
# AI EXTRACT
# =========================================================

JSON_PROMPT = """
Extract REAL exchange rates.

Return ONLY JSON.

{
  "USD": {"buy":"0.0000","sell":"0.0000"},
  "EUR": {"buy":"0.0000","sell":"0.0000"},
  "RUB": {"buy":"0.0000","sell":"0.0000"},
  "CNY": {"buy":"0.0000","sell":"0.0000"},
  "KZT": {"buy":"0.0000","sell":"0.0000"}
}

TEXT:
"""

def ai_extract(section):

    print("\n" + "=" * 80)
    print("AI EXTRACTION")
    print("=" * 80)

    best = copy.deepcopy(EMPTY)

    for model in MODELS:

        print(f"\nMODEL: {model}")

        for attempt in range(3):

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
                                "content": JSON_PROMPT + section
                            }
                        ],
                        "temperature": 0,
                        "max_tokens": 300
                    },
                    timeout=180
                )

                data = response.json()

                print("\nOPENROUTER RESPONSE:")
                print(json.dumps(data)[:1000])

                if "choices" not in data:
                    continue

                raw = data["choices"][0]["message"]["content"]

                if raw is None:
                    continue

                print("\nRAW AI:")
                print(raw)

                raw = raw.replace("```json", "")
                raw = raw.replace("```", "")

                start = raw.find("{")
                end = raw.rfind("}") + 1

                if start == -1:
                    continue

                parsed = json.loads(raw[start:end])

                cleaned = clean_json(parsed)

                found = count_found(cleaned)

                print(f"\nFOUND: {found}/5")

                if found > count_found(best):
                    best = cleaned

                if found >= 3:
                    return cleaned

            except Exception as e:

                print("\nAI ERROR:")
                print(str(e))

            time.sleep(5)

    return best

# =========================================================
# MAIN
# =========================================================

print("\n" + "=" * 80)
print(BANK["name"])
print("=" * 80)

markdown = scrape(BANK["website"])

if not markdown:

    print("\nSCRAPE FAILED")
    exit()

section = find_currency_section(markdown)

print("\nSECTION SIZE:")
print(len(section))

# =========================================================
# TRY REGEX FIRST
# =========================================================

currencies = regex_extract(section)

found = count_found(currencies)

# =========================================================
# IF REGEX FAILED -> AI
# =========================================================

if found < 3:

    print("\nREGEX NOT ENOUGH -> USING AI")

    ai_result = ai_extract(section)

    if count_found(ai_result) > found:
        currencies = ai_result

# =========================================================
# FINAL
# =========================================================

final = {
    "bank_name": BANK["name"],
    "bank_id": BANK["id"],
    "success": True,
    "currencies": currencies,
    "found": count_found(currencies),
    "updated": datetime.now().strftime(
        "%d.%m.%Y %H:%M"
    )
}

with open(
    "result.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        final,
        f,
        ensure_ascii=False,
        indent=2
    )

print("\n" + "=" * 80)
print("FINAL RESULT:")
print("=" * 80)

print(
    json.dumps(
        final,
        ensure_ascii=False,
        indent=2
    )
)

print("\nRESULT SAVED -> result.json")

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
