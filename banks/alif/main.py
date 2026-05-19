import requests
import json
import os
import time

# =========================================================
# FIRECRAWL API
# =========================================================

FIRECRAWL_API = os.getenv("FIRECRAWL_API")

# =========================================================
# BANK INFO
# =========================================================

BANK_NAME = "Алиф Бонк"

BANK_ID = "alif"

# IMPORTANT:
# RU VERSION OF WEBSITE
# BECAUSE CURRENCY SECTION EXISTS THERE

BANK_URL = "https://alif.tj/ru"

# =========================================================
# SETTINGS
# =========================================================

MAX_RETRIES = 3

WAIT_FOR = 15000

TIMEOUT = 60

# =========================================================
# START
# =========================================================

print("=" * 80)
print(f"SCRAPING FULL WEBSITE: {BANK_NAME}")
print("=" * 80)

# =========================================================
# CHECK API
# =========================================================

if not FIRECRAWL_API:

    print("\nERROR: FIRECRAWL_API NOT FOUND")

    result = {
        "success": False,
        "error": "FIRECRAWL_API NOT FOUND"
    }

else:

    success = False

    markdown = ""

    error_message = ""

    # =====================================================
    # RETRIES
    # =====================================================

    for attempt in range(1, MAX_RETRIES + 1):

        print("\n" + "-" * 80)
        print(f"ATTEMPT {attempt}/{MAX_RETRIES}")
        print("-" * 80)

        try:

            response = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Authorization": f"Bearer {FIRECRAWL_API}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": BANK_URL,

                    # FULL WEBSITE

                    "formats": ["markdown"],

                    # IMPORTANT
                    # DO NOT CUT CONTENT

                    "onlyMainContent": False,

                    # WAIT JS

                    "waitFor": WAIT_FOR,

                    # REMOVE CACHE

                    "skipTlsVerification": False
                },
                timeout=TIMEOUT
            )

            # =================================================
            # STATUS
            # =================================================

            print("\nSTATUS CODE:")
            print(response.status_code)

            # =================================================
            # RAW RESPONSE
            # =================================================

            raw_text = response.text

            print("\nRAW RESPONSE PREVIEW:\n")

            print(raw_text[:3000])

            # =================================================
            # CHECK STATUS
            # =================================================

            if response.status_code != 200:

                error_message = f"HTTP {response.status_code}"

                print(f"\nBAD STATUS: {error_message}")

                time.sleep(5)

                continue

            # =================================================
            # PARSE JSON
            # =================================================

            data = response.json()

            markdown = data.get("data", {}).get("markdown", "")

            # =================================================
            # CHECK EMPTY
            # =================================================

            if not markdown:

                error_message = "EMPTY MARKDOWN"

                print("\nERROR: EMPTY MARKDOWN")

                time.sleep(5)

                continue

            # =================================================
            # SUCCESS
            # =================================================

            success = True

            print("\nSCRAPE SUCCESS")

            print(f"\nFULL MARKDOWN SIZE: {len(markdown)}")

            # =================================================
            # SEARCH CURRENCIES
            # =================================================

            print("\nSEARCHING CURRENCIES...\n")

            for word in [
                "USD",
                "EUR",
                "RUB",
                "CNY",
                "KZT",
                "ДОЛЛАР",
                "РУБЛЬ",
                "ЕВРО"
            ]:

                found = word in markdown.upper()

                print(f"{word}: {found}")

            # =================================================
            # SAVE FULL MARKDOWN
            # =================================================

            with open(
                "full_markdown.txt",
                "w",
                encoding="utf-8"
            ) as f:

                f.write(markdown)

            print("\nFULL WEBSITE SAVED -> full_markdown.txt")

            # =================================================
            # TRY FIND CURRENCY SECTION
            # =================================================

            currency_words = [
                "USD",
                "EUR",
                "RUB",
                "CNY",
                "KZT",
                "курс",
                "обмен",
                "валют",
                "currency"
            ]

            found_section = False

            for word in currency_words:

                index = markdown.lower().find(word.lower())

                if index != -1:

                    found_section = True

                    start = max(0, index - 1500)

                    end = min(len(markdown), index + 5000)

                    section = markdown[start:end]

                    print("\n" + "=" * 80)
                    print(f"FOUND SECTION USING: {word}")
                    print("=" * 80)

                    print(section)

                    with open(
                        "currency_section.txt",
                        "w",
                        encoding="utf-8"
                    ) as f:

                        f.write(section)

                    print(
                        "\nCURRENCY SECTION SAVED -> currency_section.txt"
                    )

                    break

            if not found_section:

                print("\nNO CURRENCY SECTION FOUND")

            break

        except Exception as e:

            error_message = str(e)

            print("\nSCRAPE ERROR:")

            print(error_message)

            time.sleep(5)

    # =====================================================
    # RESULT
    # =====================================================

    if success:

        result = {
            "bank_name": BANK_NAME,
            "bank_id": BANK_ID,
            "success": True,
            "markdown_size": len(markdown),
            "timestamp": int(time.time())
        }

    else:

        result = {
            "bank_name": BANK_NAME,
            "bank_id": BANK_ID,
            "success": False,
            "error": error_message,
            "timestamp": int(time.time())
        }

# =========================================================
# SAVE RESULT JSON
# =========================================================

with open("result.json", "w", encoding="utf-8") as f:

    json.dump(
        result,
        f,
        ensure_ascii=False,
        indent=2
    )

# =========================================================
# FINAL
# =========================================================

print("\n" + "=" * 80)

print("FINAL RESULT:\n")

print(json.dumps(result, ensure_ascii=False, indent=2))

print("\nRESULT SAVED -> result.json")

print("=" * 80)

print("\nDONE")
