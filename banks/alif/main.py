import requests
import json
import os

# =========================================================
# API FROM GITHUB SECRETS
# =========================================================

FIRECRAWL_API = os.getenv("FIRECRAWL_API")

# =========================================================
# BANK
# =========================================================

BANK_NAME = "Алиф Бонк"

BANK_ID = "alif"

BANK_URL = "https://alif.tj/"

# =========================================================
# SCRAPE
# =========================================================

print("=" * 60)
print(f"SCRAPING: {BANK_NAME}")
print("=" * 60)

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

    data = response.json()

    markdown = data.get("data", {}).get("markdown", "")

    print("\nSCRAPE SUCCESS")
    print(f"MARKDOWN SIZE: {len(markdown)}")

    print("\nFIRST 5000 CHARS:\n")
    print(markdown[:5000])

    result = {
        "bank_name": BANK_NAME,
        "bank_id": BANK_ID,
        "success": True,
        "markdown_size": len(markdown),
        "preview": markdown[:1000]
    }

except Exception as e:

    print("\nSCRAPE ERROR")
    print(e)

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
