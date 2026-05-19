import requests
import json
import os
import time
import re

# =========================================================
# FIRECRAWL API
# =========================================================

FIRECRAWL_API = os.getenv("FIRECRAWL_API")

# =========================================================
# BANK INFO
# =========================================================

BANK_NAME = "Алиф Бонк"

BANK_ID = "alif"

BANK_URL = "https://alif.tj/ru"

# =========================================================
# SETTINGS
# =========================================================

MAX_RETRIES = 3

WAIT_FOR = 10000

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

    found_urls = []

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
                    "formats": ["markdown"],
                    "onlyMainContent": False,
                    "waitFor": WAIT_FOR
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

            print("\nRAW RESPONSE PREVIEW:\n")

            print(response.text[:2000])

            # =================================================
            # CHECK STATUS
            # =================================================

            if response.status_code != 200:

                error_message = f"HTTP {response.status_code}"

                print(f"\nBAD STATUS: {error_message}")

                time.sleep(5)

                continue

            # =================================================
            # JSON
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
            # FIND URLS
            # =================================================

            print("\n" + "=" * 80)
            print("SEARCHING IMPORTANT URLS")
            print("=" * 80)

            urls = re.findall(
                r'https://[^\s\)\"]+',
                markdown
            )

            unique_urls = list(set(urls))

            keywords = [
                "currency",
                "exchange",
                "rate",
                "rates",
                "api",
                "json",
                "kurs",
                "kursi",
                "valuta",
                "usd",
                "eur",
                "rub"
            ]

            for url in unique_urls:

                lower = url.lower()

                if any(word in lower for word in keywords):

                    found_urls.append(url)

                    print("\nFOUND URL:")
                    print(url)

            # =================================================
            # SAVE FOUND URLS
            # =================================================

            with open(
                "found_urls.json",
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    found_urls,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            print("\nFOUND URLS SAVED -> found_urls.json")

            # =================================================
            # TRY SCRAPING FOUND URLS
            # =================================================

            for link in found_urls:

                print("\n" + "=" * 80)
                print("TESTING URL:")
                print(link)
                print("=" * 80)

                try:

                    sub_response = requests.post(
                        "https://api.firecrawl.dev/v1/scrape",
                        headers={
                            "Authorization": f"Bearer {FIRECRAWL_API}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "url": link,
                            "formats": ["markdown"],
                            "onlyMainContent": False,
                            "waitFor": WAIT_FOR
                        },
                        timeout=TIMEOUT
                    )

                    print("\nSUB STATUS:")
                    print(sub_response.status_code)

                    if sub_response.status_code != 200:
                        continue

                    sub_data = sub_response.json()

                    sub_markdown = (
                        sub_data
                        .get("data", {})
                        .get("markdown", "")
                    )

                    if not sub_markdown:
                        continue

                    print("\nSUB PAGE SIZE:")
                    print(len(sub_markdown))

                    # =========================================
                    # SEARCH CURRENCIES
                    # =========================================

                    currency_found = any(
                        x in sub_markdown.upper()
                        for x in [
                            "USD",
                            "EUR",
                            "RUB",
                            "CNY",
                            "KZT"
                        ]
                    )

                    print("\nHAS CURRENCIES:")
                    print(currency_found)

                    if currency_found:

                        print("\nFOUND CURRENCY PAGE!")

                        print("\nFIRST 5000 CHARS:\n")

                        print(sub_markdown[:5000])

                        with open(
                            "currency_page.txt",
                            "w",
                            encoding="utf-8"
                        ) as f:

                            f.write(sub_markdown)

                        print(
                            "\nCURRENCY PAGE SAVED -> currency_page.txt"
                        )

                        break

                except Exception as e:

                    print("\nSUB PAGE ERROR:")
                    print(str(e))

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
            "found_urls": len(found_urls),
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
# SAVE RESULT
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
