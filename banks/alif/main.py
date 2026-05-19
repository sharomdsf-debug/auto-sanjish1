import requests
import json
import os
import time
from bs4 import BeautifulSoup

# =========================================================
# API
# =========================================================

OPENROUTER_API = os.getenv("OPENROUTER_API")

# =========================================================
# MODEL
# =========================================================

MODEL = "deepseek/deepseek-v4-flash:free"

# =========================================================
# URL
# =========================================================

URL = "https://alif.tj/ru"

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
# DOWNLOAD WEBSITE
# =========================================================

print("=" * 80)
print("DOWNLOADING WEBSITE")
print("=" * 80)

html = requests.get(
    URL,
    headers={
        "User-Agent": "Mozilla/5.0"
    },
    timeout=120
).text

print("HTML SIZE:")
print(len(html))

# =========================================================
# HTML -> TEXT
# =========================================================

print("=" * 80)
print("CONVERTING HTML TO TEXT")
print("=" * 80)

soup = BeautifulSoup(html, "html.parser")

text = soup.get_text("\n")

text = "\n".join(
    line.strip()
    for line in text.splitlines()
    if line.strip()
)

print("TEXT SIZE:")
print(len(text))

with open("website_text.txt", "w", encoding="utf-8") as f:
    f.write(text)

print("TEXT SAVED -> website_text.txt")

# =========================================================
# ASK AI
# =========================================================

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
                        "content": PROMPT + text
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

        break

    except Exception as e:

        print("ERROR:")
        print(e)

        time.sleep(5)

print("=" * 80)
print("DONE")
print("=" * 80)
