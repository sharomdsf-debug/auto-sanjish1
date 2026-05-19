import requests
import os
import json
import time
import copy

# =========================================================
# API
# =========================================================

FIRECRAWL_API = os.getenv("FIRECRAWL_API")
OPENROUTER_API = os.getenv("OPENROUTER_API")

# =========================================================
# MODELS
# =========================================================

MODELS = [
    "openai/gpt-oss-120b:free",
    "deepseek/deepseek-v3-base:free"
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
    "USD": (5.0, 20.0),
    "EUR": (5.0, 25.0),
    "RUB": (0.01, 2.0),
    "CNY": (0.5, 5.0),
    "KZT": (0.001, 0.5)
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

        num = float(
            str(value)
            .replace(",", ".")
            .replace(" ", "")
        )

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

        print(f"\nATTEMPT {attempt+1}/3")

        try:

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
                    "waitFor": 10000
                },
                timeout=120
            )

            print("\nSTATUS:")
            print(response.status_code)

            if response.status_code != 200:

                print("\nBAD STATUS")

                time.sleep(5)

                continue

            data = response.json()

            markdown = (
                data
                .get("data", {})
                .get("markdown", "")
            )

            if not markdown:

                print("\nEMPTY MARKDOWN")

                time.sleep(5)

                continue

            print("\nSCRAPE SUCCESS")

            print(f"\nMARKDOWN SIZE: {len(markdown)}")

            with open(
                "full_markdown.txt",
                "w",
                encoding="utf-8"
            ) as f:

                f.write(markdown)

            print(
                "\nFULL WEBSITE SAVED -> full_markdown.txt"
            )

            return markdown

        except Exception as e:

            print("\nSCRAPE ERROR:")
            print(str(e))

            time.sleep(5)

    return ""

# =========================================================
# AI STAGE 1
# =========================================================

SECTION_PROMPT = """
You are extracting ONLY the REAL currency exchange section from a bank website.

STRICT RULES:
- Return ONLY raw text
- DO NOT explain
- DO NOT summarize
- DO NOT output JSON

IMPORTANT:
Find REAL exchange rates.

The text MUST contain things like:

| USD | 9.25 | 9.35 |
| RUB | 0.12 | 0.13 |
| EUR | 10.70 | 10.91 |

IGNORE:
- news
- menus
- cards
- loans
- commissions
- limits
- banners

IMPORTANT:
Return ONLY the exchange rate section.

TEXT:
"""

def find_currency_section(markdown):

    # =====================================================
    # VERY IMPORTANT
    # =====================================================

    markdown = markdown[:40000]

    print("\n" + "=" * 80)
    print("SEARCHING CURRENCY SECTION")
    print("=" * 80)

    for model in MODELS:

        print("\n" + "=" * 80)
        print(f"SECTION MODEL: {model}")
        print("=" * 80)

        for attempt in range(3):

            print(f"\nMODEL ATTEMPT {attempt+1}/3")

            try:

                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization":
                            f"Bearer {OPENROUTER_API}",
                        "Content-Type":
                            "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "user",
                                "content":
                                    SECTION_PROMPT
                                    + "\n\n"
                                    + markdown
                            }
                        ],
                        "temperature": 0,
                        "max_tokens": 2000
                    },
                    timeout=180
                )

                data = response.json()

                print("\nOPENROUTER RESPONSE:")
                print(json.dumps(data)[:1500])

                if "choices" not in data:

                    print("\nNO CHOICES")

                    time.sleep(5)

                    continue

                text = (
                    data["choices"][0]
                    ["message"]
                    ["content"]
                )

                print("\nSECTION RESULT:\n")
                print(text[:5000])

                if (
                    "USD" in text
                    or "EUR" in text
                    or "RUB" in text
                ):

                    with open(
                        "currency_section.txt",
                        "w",
                        encoding="utf-8"
                    ) as f:

                        f.write(text)

                    print(
                        "\nSECTION SAVED -> currency_section.txt"
                    )

                    return text

            except Exception as e:

                print("\nSECTION ERROR:")
                print(str(e))

            time.sleep(5)

    # =====================================================
    # FALLBACK
    # =====================================================

    print("\nFALLBACK TO RAW MARKDOWN")

    return markdown[:40000]

# =========================================================
# AI STAGE 2
# =========================================================

JSON_PROMPT = """
Extract REAL bank exchange rates against TJS.

STRICT RULES:
- Return ONLY JSON
- Never explain
- Never invent values
- Ignore years
- Ignore percentages
- Ignore limits
- Ignore commissions
- Ignore phone numbers

IMPORTANT:
Extract ONLY REAL currency table values.

IMPORTANT:
If currency missing -> "0.0000"

OUTPUT FORMAT:

{
  "USD": {
    "buy":"0.0000",
    "sell":"0.0000"
  },
  "EUR": {
    "buy":"0.0000",
    "sell":"0.0000"
  },
  "RUB": {
    "buy":"0.0000",
    "sell":"0.0000"
  },
  "CNY": {
    "buy":"0.0000",
    "sell":"0.0000"
  },
  "KZT": {
    "buy":"0.0000",
    "sell":"0.0000"
  }
}

TEXT:
"""

def extract_rates(text):

    best = copy.deepcopy(EMPTY)

    print("\n" + "=" * 80)
    print("EXTRACTING RATES")
    print("=" * 80)

    for model in MODELS:

        print("\n" + "=" * 80)
        print(f"EXTRACT MODEL: {model}")
        print("=" * 80)

        for attempt in range(3):

            print(f"\nEXTRACT ATTEMPT {attempt+1}/3")

            try:

                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization":
                            f"Bearer {OPENROUTER_API}",
                        "Content-Type":
                            "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "user",
                                "content":
                                    JSON_PROMPT
                                    + "\n\n"
                                    + text
                            }
                        ],
                        "temperature": 0,
                        "max_tokens": 700
                    },
                    timeout=180
                )

                data = response.json()

                print("\nOPENROUTER RESPONSE:")
                print(json.dumps(data)[:1500])

                if "choices" not in data:

                    print("\nNO CHOICES")

                    time.sleep(5)

                    continue

                raw = (
                    data["choices"][0]
                    ["message"]
                    ["content"]
                )

                print("\nRAW AI:\n")
                print(raw)

                raw = raw.replace("```json", "")
                raw = raw.replace("```", "")

                start = raw.find("{")
                end = raw.rfind("}") + 1

                if start == -1:

                    print("\nNO JSON FOUND")

                    continue

                parsed = json.loads(raw[start:end])

                cleaned = clean_json(parsed)

                found = count_found(cleaned)

                print(f"\nFOUND: {found}/5")

                if found > count_found(best):
                    best = cleaned

                if found >= 1:
                    return cleaned

            except Exception as e:

                print("\nEXTRACT ERROR:")
                print(str(e))

            time.sleep(5)

    return best

# =========================================================
# PROCESS BANK
# =========================================================

def process_bank(bank):

    print("\n" + "=" * 80)
    print(bank["name"])
    print("=" * 80)

    markdown = scrape(bank["website"])

    if not markdown:

        return {
            "bank_name": bank["name"],
            "bank_id": bank["id"],
            "success": False,
            "currencies": copy.deepcopy(EMPTY)
        }

    section = find_currency_section(markdown)

    print(f"\nSECTION SIZE: {len(section)}")

    currencies = extract_rates(section)

    print(f"\nFINAL FOUND: {count_found(currencies)}/5")

    return {
        "bank_name": bank["name"],
        "bank_id": bank["id"],
        "success": True,
        "currencies": currencies,
        "found": count_found(currencies)
    }

# =========================================================
# RUN
# =========================================================

final = process_bank(BANK)

# =========================================================
# SAVE RESULT
# =========================================================

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

# =========================================================
# FINAL
# =========================================================

print("\n" + "=" * 80)

print("FINAL RESULT:\n")

print(json.dumps(final, ensure_ascii=False, indent=2))

print("\nRESULT SAVED -> result.json")

print("=" * 80)

print("\nDONE")2000
