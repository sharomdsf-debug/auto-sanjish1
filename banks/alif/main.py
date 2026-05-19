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

BANK_URL = "https://alif.tj/"

# =========================================================
# START
# =========================================================

print("=" * 80)
print(f"SCRAPING: {BANK_NAME}")
print("=" * 80)

# =========================================================
# CHECK API
# =========================================================

if not FIRECRAWL_API:

    print("\nERROR: FIRECRAWL_API NOT FOUND")

    result = {
        "bank_name": BANK_NAME,
        "bank_id": BANK_ID,
        "success": False,
        "error": "FIRECRAWL_API NOT FOUND"
    }

else:

    success = False

    markdown = ""

    error_message = ""

    # =====================================================
    # RETRY SYSTEM
    # =====================================================

    for attempt in range(1, 4):

        print("\n" + "-" * 80)
        print(f"ATTEMPT: {attempt}/3")
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
                    "waitFor": 10000
                },
                timeout=60
            )

            # =================================================
            # DEBUG
            # =================================================

            print("\nSTATUS CODE:")
            print(response.status_code)

            print("\nRAW RESPONSE:\n")
            print(response.text[:3000])

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
            # CHECK MARKDOWN
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

            print(f"\nMARKDOWN SIZE: {len(markdown)}")

            print("\nFIRST 5000 CHARS:\n")

            print(markdown[:5000])

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
            "preview": markdown[:2000],
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
# PRINT RESULT
# =========================================================

print("\n" + "=" * 80)

print("FINAL RESULT:\n")

print(json.dumps(result, ensure_ascii=False, indent=2))

print("\nRESULT SAVED -> result.json")

print("=" * 80)

print("\nDONE")
