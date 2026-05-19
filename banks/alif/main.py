import requests
import json
import os

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

print("=" * 70)
print(f"SCRAPING: {BANK_NAME}")
print("=" * 70)

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
                "waitFor": 20000
            },
            timeout=240
        )

        # =================================================
        # DEBUG
        # =================================================

        print("\nSTATUS CODE:")
        print(response.status_code)

        print("\nRAW RESPONSE:")
        print(response.text)

        # =================================================
        # JSON
        # =================================================

        data = response.json()

        markdown = data.get("data", {}).get("markdown", "")

        # =================================================
        # RESULT
        # =================================================

        print("\nSCRAPE SUCCESS")

        print(f"\nMARKDOWN SIZE: {len(markdown)}")

        print("\nFIRST 3000 CHARS:\n")

        print(markdown[:3000])

        result = {
            "bank_name": BANK_NAME,
            "bank_id": BANK_ID,
            "success": True,
            "markdown_size": len(markdown),
            "preview": markdown[:1000]
        }

    except Exception as e:

        print("\nSCRAPE ERROR:")
        print(str(e))

        result = {
            "bank_name": BANK_NAME,
            "bank_id": BANK_ID,
            "success": False,
            "error": str(e)
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

print("\nRESULT SAVED -> result.json")

print("\nDONE")
