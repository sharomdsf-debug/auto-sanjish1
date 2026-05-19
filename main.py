import os
import json
import time
import copy
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# =========================================================
# API
# =========================================================

OPENROUTER_API = os.getenv("OPENROUTER_API")

# =========================================================
# AI MODELS
# =========================================================

MODELS = [
    "openai/gpt-oss-120b:free",
    "deepseek/deepseek-v3-base:free",
    "qwen/qwen3-coder:free"
]

# =========================================================
# BANKS
# =========================================================

BANKS = [
    {"name": "Бонки Миллии Тоҷикистон", "id": "nbt", "website": "https://nbt.tj/"},
    {"name": "Амонатбонк", "id": "amonatbonk", "website": "https://amonatbonk.tj/"},
    {"name": "Ориёнбонк", "id": "oriyonbank", "website": "https://oriyonbonk.tj/"},
    {"name": "Тавҳидбонк", "id": "tawhid", "website": "https://www.tawhidbank.tj/"},
    {"name": "Бонки Эсхата", "id": "eskhata", "website": "https://eskhata.com/"},
    {"name": "Коммерсбонк", "id": "commerce", "website": "https://cbt.tj/"},
    {"name": "Тиҷорат Бонк", "id": "tijorat", "website": "https://tejaratbank.tj/"},
    {"name": "Спитамен Бонк", "id": "spitamen", "website": "https://spitamenbank.tj/"},
    {"name": "Имон Интернешнл Банк", "id": "imon", "website": "https://imon.tj/"},
    {"name": "Душанбе Сити", "id": "dushanbe_city", "website": "https://dc.tj/"},
    {"name": "Алиф Бонк", "id": "alif", "website": "https://alif.tj/"},
    {"name": "Саноатсодиротбонк", "id": "ssb", "website": "https://ssb.tj/"},
    {"name": "IBT", "id": "ibt", "website": "https://ibt.tj/"},
    {"name": "ICB", "id": "icb", "website": "https://icb.tj/"},
    {"name": "Микрофинансбонк", "id": "mfb", "website": "https://mfb.tj/"},
    {"name": "Бонки рушди Тоҷикистон", "id": "sdb", "website": "https://brt.tj/"},
    {"name": "Ҳумо", "id": "humo", "website": "https://humo.tj/"},
    {"name": "Арванд", "id": "arvand", "website": "https://arvand.tj/"},
    {"name": "FINCA", "id": "finca", "website": "https://finca.tj/"},
    {"name": "Фридом Бонк Тоҷикистон", "id": "freedom", "website": "https://freedombank.tj/"},
    {"name": "Васл Бонк", "id": "vasl", "website": "https://vasl.tj/"},
    {"name": "Актив Бонк", "id": "aktiv", "website": "https://aktivbank.tj/"},
    {"name": "Азизи-Молия", "id": "azizi", "website": "https://azizimoliya.tj/"},
    {"name": "Матин", "id": "matin", "website": "https://matin.tj/"}
]

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
    c: {"buy": "0.0000", "sell": "0.0000"}
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

# =========================================================
# PLAYWRIGHT SCRAPER
# =========================================================

def scrape_everything(url):

    print(f"\n🌐 OPENING: {url}")

    raw_data = {
        "html": "",
        "text": "",
        "tables": [],
        "api_responses": []
    }

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )

            context = browser.new_context()

            page = context.new_page()

            # =====================================
            # CAPTURE NETWORK
            # =====================================

            def handle_response(response):

                try:

                    ct = response.headers.get("content-type", "")

                    if (
                        "json" in ct
                        or "api" in response.url
                        or "graphql" in response.url
                    ):

                        body = response.text()

                        if len(body) < 200000:

                            raw_data["api_responses"].append({
                                "url": response.url,
                                "body": body
                            })

                except:
                    pass

            page.on("response", handle_response)

            # =====================================
            # LOAD WEBSITE
            # =====================================

            page.goto(
                url,
                wait_until="networkidle",
                timeout=120000
            )

            time.sleep(10)

            # =====================================
            # AUTO SCROLL
            # =====================================

            for i in range(10):

                page.mouse.wheel(0, 3000)

                time.sleep(1)

            # =====================================
            # GET HTML
            # =====================================

            raw_data["html"] = page.content()

            # =====================================
            # GET TEXT
            # =====================================

            raw_data["text"] = page.locator("body").inner_text()

            # =====================================
            # GET TABLES
            # =====================================

            tables = page.locator("table").all()

            for table in tables:

                try:

                    txt = table.inner_text()

                    if len(txt) > 20:

                        raw_data["tables"].append(txt)

                except:
                    pass

            browser.close()

    except Exception as e:

        print("SCRAPE ERROR:", e)

    return raw_data

# =========================================================
# AI EXTRACTOR
# =========================================================

PROMPT = """
You are a professional AI currency extraction system.

Extract REAL exchange rates against TJS.

SUPPORTED:
USD
EUR
RUB
CNY
KZT

IMPORTANT:

1. Return ONLY VALID JSON.
2. No markdown.
3. No explanations.
4. No comments.
5. Never invent values.

6. If currency not found:
buy = "0.0000"
sell = "0.0000"

7. If only one rate exists:
buy = real value
sell = "0.0000"

OUTPUT:

{
  "USD": {"buy":"0.0000","sell":"0.0000"},
  "EUR": {"buy":"0.0000","sell":"0.0000"},
  "RUB": {"buy":"0.0000","sell":"0.0000"},
  "CNY": {"buy":"0.0000","sell":"0.0000"},
  "KZT": {"buy":"0.0000","sell":"0.0000"}
}

RAW WEBSITE DATA:
"""

def extract_with_ai(raw):

    best = copy.deepcopy(EMPTY)

    combined = json.dumps(raw, ensure_ascii=False)

    combined = combined[:120000]

    for model in MODELS:

        print(f"\n🤖 MODEL: {model}")

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
                            "content": PROMPT + combined
                        }
                    ],
                    "temperature": 0,
                    "max_tokens": 500
                },
                timeout=180
            )

            data = response.json()

            if "choices" not in data:
                continue

            content = data["choices"][0]["message"]["content"]

            content = content.replace("```json", "")
            content = content.replace("```", "")

            start = content.find("{")
            end = content.rfind("}") + 1

            if start == -1:
                continue

            parsed = json.loads(content[start:end])

            cleaned = clean_json(parsed)

            return cleaned

        except Exception as e:

            print("AI ERROR:", e)

    return best

# =========================================================
# MAIN LOOP
# =========================================================

all_rates = []

for bank in BANKS:

    print("\n" + "="*70)
    print(bank["name"])
    print("="*70)

    raw = scrape_everything(
        bank["website"]
    )

    # =====================================
    # SAVE RAW
    # =====================================

    os.makedirs("raw", exist_ok=True)

    with open(
        f"raw/{bank['id']}.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            raw,
            f,
            ensure_ascii=False,
            indent=2
        )

    # =====================================
    # AI EXTRACTION
    # =====================================

    currencies = extract_with_ai(raw)

    item = {
        "bank_name": bank["name"],
        "bank_id": bank["id"],
        "currencies": currencies
    }

    all_rates.append(item)

    time.sleep(5)

# =========================================================
# FINAL JSON
# =========================================================

final = {
    "project_name": "ASOR TJ",
    "last_updated": "🤖 " + datetime.now().strftime("%d.%m.%Y %H:%M"),
    "base_currency": "TJS",
    "status": "success",
    "rates": all_rates
}

with open(
    "new.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        final,
        f,
        ensure_ascii=False,
        indent=2
    )

print("\n✅ DONE")
print(json.dumps(final, ensure_ascii=False, indent=2))
