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
            # TEST FOUND URLS
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

                            # IMPORTANT
                            # GET HTML INSTEAD OF MARKDOWN

                            "formats": ["html"],

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

                    # =========================================
                    # GET HTML
                    # =========================================

                    html = (
                        sub_data
                        .get("data", {})
                        .get("html", "")
                    )

                    if not html:
                        continue

                    print("\nHTML SIZE:")
                    print(len(html))

                    # =========================================
                    # SAVE HTML
                    # =========================================

                    with open(
                        "currency_page.html",
                        "w",
                        encoding="utf-8"
                    ) as f:

                        f.write(html)

                    print(
                        "\nHTML SAVED -> currency_page.html"
                    )

                    # =========================================
                    # SEARCH API ENDPOINTS
                    # =========================================

                    print("\n" + "=" * 80)
                    print("SEARCHING API ENDPOINTS")
                    print("=" * 80)

                    api_patterns = [

                        r'https://[^"\']+',

                        r'/api/[^"\']+',

                        r'/graphql[^"\']*',

                        r'graphql',

                        r'api',

                        r'rates',

                        r'exchange',

                        r'currency',

                        r'fetch\([^)]+\)',

                        r'axios\([^)]+\)',

                        r'__NEXT_DATA__'
                    ]

                    found_api = []

                    for pattern in api_patterns:

                        try:

                            matches = re.findall(
                                pattern,
                                html,
                                re.IGNORECASE
                            )

                            for item in matches:

                                if item not in found_api:

                                    found_api.append(item)

                        except:
                            pass

                    # =========================================
                    # PRINT FOUND API
                    # =========================================

                    for item in found_api[:200]:

                        print("\nFOUND:")
                        print(item)

                    # =========================================
                    # SAVE API SEARCH
                    # =========================================

                    with open(
                        "found_api.txt",
                        "w",
                        encoding="utf-8"
                    ) as f:

                        for item in found_api:

                            f.write(item + "\n\n")

                    print(
                        "\nFOUND API SAVED -> found_api.txt"
                    )

                    # =========================================
                    # SEARCH LIVE CURRENCIES
                    # =========================================

                    print("\n" + "=" * 80)
                    print("SEARCHING LIVE RATES")
                    print("=" * 80)

                    currency_patterns = [

                        r'USD.{0,100}',

                        r'EUR.{0,100}',

                        r'RUB.{0,100}',

                        r'KZT.{0,100}',

                        r'CNY.{0,100}',

                        r'\d+\.\d+',

                        r'\d+,\d+'
                    ]

                    found_currency = []

                    for pattern in currency_patterns:

                        try:

                            matches = re.findall(
                                pattern,
                                html,
                                re.IGNORECASE
                            )

                            for item in matches:

                                if item not in found_currency:

                                    found_currency.append(item)

                        except:
                            pass

                    # =========================================
                    # PRINT CURRENCY RESULTS
                    # =========================================

                    for item in found_currency[:100]:

                        print("\nCURRENCY MATCH:")
                        print(item)

                    # =========================================
                    # SAVE CURRENCY SEARCH
                    # =========================================

                    with open(
                        "currency_matches.txt",
                        "w",
                        encoding="utf-8"
                    ) as f:

                        for item in found_currency:

                            f.write(item + "\n\n")

                    print(
                        "\nCURRENCY MATCHES SAVED -> currency_matches.txt"
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
