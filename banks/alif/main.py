import os
import json
import requests
from playwright.sync_api import sync_playwright

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
URL = os.environ.get("WEBSITE_URL", "https://alif.tj")

def scrape_website(url):
    print("🌐 Браузер кушода мешавад...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"📄 Саҳифа бор мешавад: {url}")
        page.goto(url, wait_until="networkidle")
        
        print("⏳ Ҷадвал интизор...")
        page.wait_for_selector("table", timeout=15000)
        
        table = page.query_selector("table")
        text = table.inner_text()
        
        browser.close()
        
        print("✅ Матн гирифта шуд:")
        print(text)
        
        return text

def extract_prices(text):
    print("🤖 DeepSeek таҳлил мекунад...")
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "deepseek/deepseek-v4-flash:free",
            "messages": [
                {
                    "role": "user",
                    "content": f"Аз ин матн қурби асъорро ҷудо кун:\n\n{text}"
                }
            ],
            "temperature": 0,
            "max_tokens": 500
        },
        timeout=60
    )
    
    data = response.json()
    return data["choices"][0]["message"]["content"]

def save_results(text, answer):
    os.makedirs("results", exist_ok=True)
    
    result = {
        "raw_table": text,
        "ai_answer": answer
    }
    
    with open("results/output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("💾 Натиҷа сабт шуд!")

if __name__ == "__main__":
    text = scrape_website(URL)
    answer = extract_prices(text)
    
    print("=" * 50)
    print("НАТИҶА:")
    print(answer)
    
    save_results(text, answer)
