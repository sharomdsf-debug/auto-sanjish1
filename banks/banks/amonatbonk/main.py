import os
import json
from playwright.sync_api import sync_playwright

URL = "https://www.amonatbonk.tj/ru/mubodilai_asor/"

def scrape():
    print("🌐 Амонатбонк...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("table", timeout=15000)
        table = page.query_selector("table")
        text = table.inner_text()
        browser.close()
        print("✅ Матн:")
        print(text)
        return text

def save(text):
    os.makedirs("banks/amonatbonk/results", exist_ok=True)
    with open("banks/amonatbonk/results/output.json", "w", encoding="utf-8") as f:
        json.dump({"raw_table": text}, f, ensure_ascii=False, indent=2)
    print("💾 Сабт шуд!")

if __name__ == "__main__":
    text = scrape()
    save(text)
