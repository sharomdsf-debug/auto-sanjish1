import requests
import json
import os
import time

# =========================================================
# API KEYS
# =========================================================

FIRECRAWL_API = os.getenv("FIRECRAWL_API")
OPENROUTER_API = os.getenv("OPENROUTER_API")

# =========================================================
# MODEL
# =========================================================

MODEL = "deepseek/deepseek-v4-flash:free"

# =========================================================
# BANK
# =========================================================

BANK = {
    "name": "Алиф Бонк",
    "id": "alif",
    "url": "https://alif.tj/ru"
}

# =========================================================
# PROMPT
# =========================================================

PROMPT = """
Аз ин матни калон танҳо қурби асъорро пайдо кун.

Фақат ҳамон қисми қурбҳоро баргардон.

JSON надеҳ.
Шарҳ надеҳ.

Матн:
"""

# =========================================================
# SCRAPE WEBSITE
# =========================================================

def scrape():

    print("=" * 80)
    print("SCRAPING WEBSITE")
    print("=" * 80)

    response = requests.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={
            "Authorization": f"Bearer {FIRECRAWL_API}",
            "Content-Type": "application/json"
        },
        json={
            "url": BANK["url"],
            "formats": ["markdown"]
        },
        timeout=300
    )

    print("STATUS:")
    print(response.status_code)

    raw = response.text

    print("=" * 80)
    print("RAW FIRECRAWL")
    print("=" * 80)

    print(raw[:3000])

    data = json.loads(raw)

    markdown = data["data"]["markdown"]

    print("=" * 80)
    print("MARKDOWN SIZE")
    print("=" * 80)

    print(len(markdown))

    with open("full_markdown.txt", "w", encoding="utf-8") as f:
        f.write(markdown)

    print("FULL MARKDOWN SAVED -> full_markdown.txt")

    return markdown

# =========================================================
# ASK AI
# =========================================================

def ask_ai(markdown):

    print("=" * 80)
    print("ASKING AI")
    print("=" * 80)

    for attempt in range(3):

        print(f"ATTEMPT {attempt+1}/3")

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
                            "content": PROMPT + markdown
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
            print("RAW AI RESPONSE")
            print("=" * 80)

            print(raw[:5000])

            data = json.loads(raw)

            if "choices" not in data:

                print("NO CHOICES")

                time.sleep(5)

                continue

            answer = data["choices"][0]["message"].get("content", "")

            print("=" * 80)
            print("AI ANSWER")
            print("=" * 80)

            print(answer)

            with open("answer.txt", "w", encoding="utf-8") as f:
                f.write(answer)

            print("ANSWER SAVED -> answer.txt")

            return answer

        except Exception as e:

            print("ERROR:")
            print(e)

        time.sleep(5)

    return ""

# =========================================================
# RUN
# =========================================================

print("\n" + "=" * 80)
print(BANK["name"])
print("=" * 80)

markdown = scrape()

answer = ask_ai(markdown)

print("=" * 80)
print("DONE")
print("=" * 80)
