import requests
import json
import os

FIRECRAWL_API = os.getenv("FIRECRAWL_API")
OPENROUTER_API = os.getenv("OPENROUTER_API")

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

data = response.json()

markdown = data["data"]["markdown"]

print("MARKDOWN SIZE:")
print(len(markdown))

with open("full_markdown.txt", "w", encoding="utf-8") as f:
    f.write(markdown)

print("FULL MARKDOWN SAVED")

# ======================================================
# AI
# ======================================================

print("=" * 80)
print("ASKING AI")
print("=" * 80)

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
        ]
    },
    timeout=300
)

print("STATUS:")
print(response.status_code)

raw = response.text

print("=" * 80)
print("RAW RESPONSE")
print("=" * 80)

print(raw[:5000])

data = json.loads(raw)

answer = data["choices"][0]["message"]["content"]

print("=" * 80)
print("AI ANSWER")
print("=" * 80)

print(answer)

with open("answer.txt", "w", encoding="utf-8") as f:
    f.write(answer)

print("ANSWER SAVED -> answer.txt")

print("=" * 80)
print("DONE")
print("=" * 80)
