import requests
import json
import os
import time

# ======================================================
# API
# ======================================================

FIRECRAWL_API = os.getenv("FIRECRAWL_API")
OPENROUTER_API = os.getenv("OPENROUTER_API")

# ======================================================
# CONFIG
# ======================================================

URL = "https://alif.tj/ru"

MODEL = "deepseek/deepseek-v4-flash:free"

PROMPT = """
Аз ин матни калон танҳо қурби асъорро пайдо кун.

Фақат ҳамон қисми қурбҳоро навис.

JSON надеҳ.
Шарҳ надеҳ.
"""

# ======================================================
# FIRECRAWL
# ======================================================

print("=" * 80)
print("SCRAPING")
print("=" * 80)

response = requests.post(
    "https://api.firecrawl.dev/v1/scrape",
    headers={
        "Authorization": f"Bearer {FIRECRAWL_API}",
        "Content-Type": "application/json"
    },
    json={
        "url": URL,
        "formats": ["markdown"]
    },
    timeout=300
)

print("STATUS:")
print(response.status_code)

data = response.json()

markdown = data["data"]["markdown"]

print("=" * 80)
print("MARKDOWN SIZE")
print("=" * 80)

print(len(markdown))

# SAVE FULL TEXT
with open("full_markdown.txt", "w", encoding="utf-8") as f:
    f.write(markdown)

print("FULL MARKDOWN SAVED")

# ======================================================
# AI
# ======================================================

print("=" * 80)
print("ASKING AI")
print("=" * 80)

answer = None

# БЕҲАД КӮШИШ МЕКУНАД
for attempt in range(1000):

    print(f"ATTEMPT {attempt + 1}")

    try:

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": PROMPT + "\n\n" + markdown
                    }
                ],
                "temperature": 0
            },
            timeout=300
        )

        print("STATUS:")
        print(response.status_code)

        raw = response.text

        print("=" * 80)
        print("RAW RESPONSE")
        print("=" * 80)

        print(raw[:3000])

        data = json.loads(raw)

        # ==========================================
        # SUCCESS
        # ==========================================

        if "choices" in data:

            answer = data["choices"][0]["message"]["content"]

            print("=" * 80)
            print("AI ANSWER")
            print("=" * 80)

            print(answer)

            with open("answer.txt", "w", encoding="utf-8") as f:
                f.write(answer)

            print("ANSWER SAVED -> answer.txt")

            break

        # ==========================================
        # RATE LIMIT
        # ==========================================

        else:

            print("=" * 80)
            print("NO CHOICES / RATE LIMITED")
            print("=" * 80)

            print(data)

            print("WAITING 30 SECONDS...")

            time.sleep(30)

    except Exception as e:

        print("=" * 80)
        print("ERROR")
        print("=" * 80)

        print(e)

        print("WAITING 30 SECONDS...")

        time.sleep(30)

# ======================================================
# FINAL
# ======================================================

print("=" * 80)
print("DONE")
print("=" * 80)

if answer:
    print(answer)
else:
    print("NO ANSWER")
