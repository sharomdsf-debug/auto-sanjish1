import requests
import json
import os
import time
import copy

# =========================================================
# API KEYS
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
# BANK INFO
# =========================================================

BANK_NAME = "Алиф Бонк"

BANK_ID = "alif"

BANK_URL = "https://alif.tj/ru"

# =========================================================
# SETTINGS
# =========================================================

WAIT_FOR = 10000

TIMEOUT = 60

MAX_RETRIES = 3

CHUNK_SIZE = 5000

# =========================================================
# VALIDATION
# =========================================================

VALID_RANGES = {
    "USD": (5.0, 20.0),
    "EUR": (5.0, 25.0),
    "RUB": (0.01, 1.0),
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


def split_chunks(text, size):

    return [
        text[i:i+size]
        for i in range(0, len(text), size)
    ]

# =========================================================
# SCRAPE
# =========================================================

def scrape_full_website():

    print("\n" + "=" * 80)
    print("SCRAPING FULL WEBSITE")
    print("=" * 80)

    for attempt in range(1, MAX_RETRIES + 1):

        print(f"\nATTEMPT {attempt}/{MAX_RETRIES}")

        try:

            response = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Authorization": f"Bearer {FIRECRAWL_API}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": BANK_URL,
                    "formats": ["markdown"],
                    "onlyMainContent": False,
                    "waitFor": WAIT_FOR
                },
                timeout=TIMEOUT
            )

            print("\nSTATUS:")
            print(response.status_code)

            if response.status_code != 200:

                time.sleep(5)

                continue

            data = response.json()

            markdown = (
                data
                .get("data", {})
                .get("markdown", "")
            )

            if not markdown:

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
# FIND BEST CHUNK
# =========================================================

SECTION_PROMPT = """
Find ONLY text containing REAL exchange rates.

IMPORTANT:
- Return ONLY raw text
- No explanations
- No JSON
- Ignore menus
- Ignore banners
- Ignore loans
- Ignore cards
- Ignore commissions
- Ignore limits

Find:
USD
EUR
RUB
CNY
KZT

IMPORTANT:
Return ONLY section with REAL numeric rates.

TEXT:
"""

def find_currency_section(markdown):

    chunks = split_chunks(markdown, CHUNK_SIZE)

    print("\n" + "=" * 80)
    print(f"TOTAL CHUNKS: {len(chunks)}")
    print("=" * 80)

    best_section = ""

    for chunk_index, chunk in enumerate(chunks):

        print("\n" + "=" * 80)
        print(f"CHECKING CHUNK {chunk_index+1}/{len(chunks)}")
        print("=" * 80)

        for model in MODELS:

            print(f"\nMODEL: {model}")

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
                                    SECTION_PROMPT + chunk
                            }
                        ],
                        "temperature": 0,
                        "max_tokens": 800
                    },
                    timeout=120
                )

                data = response.json()

                print("\nOPENROUTER RESPONSE:")
                print(json.dumps(data)[:1000])

                if "choices" not in data:
                    continue

                text = (
                    data["choices"][0]
                    ["message"]
                    ["content"]
                )

                print("\nSECTION RESULT:\n")
                print(text[:2000])

                # =====================================
                # CHECK CURRENCIES
                # =====================================

                found = 0

                for cur in CURRENCIES:

                    if cur in text.upper():
                        found += 1

                print(f"\nFOUND CURRENCIES: {found}")

                if found >= 2:

                    best_section = text

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

            time.sleep(3)

    return best_section

# =========================================================
# AI STAGE 2
# EXTRACT JSON
# =========================================================

JSON_PROMPT = """
Extract REAL bank exchange rates against TJS.

STRICT RULES:
- Return ONLY JSON
- Never explain
- Never invent values
- Ignore limits
- Ignore percentages
- Ignore phone numbers
- Ignore years

IMPORTANT:
If currency missing -> "0.0000"

FORMAT:

{
  "USD": {
    "buy": "0.0000",
    "sell": "0.0000"
  },
  "EUR": {
    "buy": "0.0000",
    "sell": "0.0000"
  },
  "RUB": {
    "buy": "0.0000",
    "sell": "0.0000"
  },
  "CNY": {
    "buy": "0.0000",
    "sell": "0.0000"
  },
  "KZT": {
    "buy": "0.0000",
    "sell": "0.0000"
  }
}

TEXT:
"""

def extract_rates(section):

    best = copy.deepcopy(EMPTY)

    if not section:

        return best

    for model in MODELS:

        print("\n" + "=" * 80)
        print(f"EXTRACT MODEL: {model}")
        print("=" * 80)

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
                                JSON_PROMPT + section
                        }
                    ],
                    "temperature": 0,
                    "max_tokens": 500
                },
                timeout=120
            )

            data = response.json()

            print("\nOPENROUTER RESPONSE:")
            print(json.dumps(data)[:1000])

            if "choices" not in data:
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
                continue

            parsed = json.loads(raw[start:end])

            cleaned = clean_json(parsed)

            found = count_found(cleaned)

            print(f"\nFOUND: {found}/5")

            if found > count_found(best):
                best = cleaned

            if found >= 2:
                return cleaned

        except Exception as e:

            print("\nEXTRACT ERROR:")
            print(str(e))

        time.sleep(3)

    return best

# =========================================================
# MAIN
# =========================================================

print("\n" + "=" * 80)
print(BANK_NAME)
print("=" * 80)

markdown = scrape_full_website()

if not markdown:

    final = {
        "bank_name": BANK_NAME,
        "bank_id": BANK_ID,
        "success": False,
        "currencies": copy.deepcopy(EMPTY)
    }

else:

    section = find_currency_section(markdown)

    currencies = extract_rates(section)

    final = {
        "bank_name": BANK_NAME,
        "bank_id": BANK_ID,
        "success": True,
        "currencies": currencies,
        "found": count_found(currencies),
        "timestamp": int(time.time())
    }

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

print("\nDONE")
