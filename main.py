import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

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
# SAVE FOLDER
# =========================================================

os.makedirs("raw_banks", exist_ok=True)

# =========================================================
# SCRAPER
# =========================================================

def scrape_bank(bank):

    print("\n" + "=" * 70)
    print(bank["name"])
    print("=" * 70)

    result = {
        "bank_name": bank["name"],
        "bank_id": bank["id"],
        "website": bank["website"],
        "scraped_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "data": {
            "title": "",
            "body_text": "",
            "tables": [],
            "api_responses": [],
            "exchange_related": []
        }
    }

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )

            context = browser.new_context()

            page = context.new_page()

            # =================================================
            # NETWORK CAPTURE
            # =================================================

            def handle_response(response):

                try:

                    ct = response.headers.get(
                        "content-type",
                        ""
                    )

                    if (
                        "json" in ct
                        or "api" in response.url.lower()
                        or "graphql" in response.url.lower()
                    ):

                        body = response.text()

                        if len(body) < 300000:

                            result["data"]["api_responses"].append({
                                "url": response.url,
                                "body": body
                            })

                except:
                    pass

            page.on(
                "response",
                handle_response
            )

            # =================================================
            # OPEN WEBSITE
            # =================================================

            print("🌐 Opening website...")

            page.goto(
                bank["website"],
                wait_until="networkidle",
                timeout=180000
            )

            time.sleep(10)

            # =================================================
            # AUTO SCROLL
            # =================================================

            print("📜 Scrolling...")

            for _ in range(15):

                page.mouse.wheel(0, 5000)

                time.sleep(1)

            # =================================================
            # TITLE
            # =================================================

            try:

                result["data"]["title"] = page.title()

            except:
                pass

            # =================================================
            # BODY TEXT
            # =================================================

            print("📝 Extracting body text...")

            try:

                body = page.locator("body").inner_text()

                result["data"]["body_text"] = body

            except:
                pass

            # =================================================
            # TABLES
            # =================================================

            print("📊 Extracting tables...")

            try:

                tables = page.locator("table").all()

                for table in tables:

                    try:

                        txt = table.inner_text()

                        if len(txt) > 20:

                            result["data"]["tables"].append(txt)

                    except:
                        pass

            except:
                pass

            # =================================================
            # EXCHANGE RATE SEARCH
            # =================================================

            print("💵 Searching exchange sections...")

            keywords = [
                "USD",
                "EUR",
                "RUB",
                "CNY",
                "KZT",
                "доллар",
                "евро",
                "рубл",
                "қурб",
                "курс",
                "валюта",
                "exchange",
                "currency"
            ]

            lines = result["data"]["body_text"].split("\n")

            found = []

            for line in lines:

                low = line.lower()

                for key in keywords:

                    if key.lower() in low:

                        clean = line.strip()

                        if len(clean) > 5:

                            found.append(clean)

                        break

            result["data"]["exchange_related"] = found

            # =================================================
            # CLOSE
            # =================================================

            browser.close()

    except Exception as e:

        result["error"] = str(e)

        print("❌ ERROR:", e)

    # =========================================================
    # SAVE INDIVIDUAL JSON
    # =========================================================

    path = f"raw_banks/{bank['id']}.json"

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"✅ SAVED: {path}")

    return result

# =========================================================
# MAIN
# =========================================================

all_banks = []

for bank in BANKS:

    data = scrape_bank(bank)

    all_banks.append(data)

    time.sleep(5)

# =========================================================
# FINAL JSON
# =========================================================

final = {
    "project_name": "ASOR TJ RAW BANK DATA",
    "updated_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
    "total_banks": len(all_banks),
    "banks": all_banks
}

with open(
    "all_banks_raw.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        final,
        f,
        ensure_ascii=False,
        indent=2
    )

print("\n🔥 DONE")
print("✅ all_banks_raw.json CREATED")
