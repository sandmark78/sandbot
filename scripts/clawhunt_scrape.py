import requests
import json
import sys

def scrape_target(url, api_key):
    """
    使用 Firecrawl 抓取目标网站的文档和结构。
    用于辅助分析潜在的 Prompt Injection 入口。
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True
    }
    try:
        response = requests.post("https://api.firecrawl.dev/v1/scrape", headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            content = data.get('data', {}).get('markdown', '')
            return content
        else:
            return f"Error: {response.status_code}, {response.text}"
    except Exception as e:
        return f"Exception: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python clawhunt_scrape.py <TARGET_URL> <FIRECRAWL_API_KEY>")
        sys.exit(1)
    
    url = sys.argv[1]
    api_key = sys.argv[2]
    
    print(f"[*] Scraping {url}...")
    result = scrape_target(url, api_key)
    print("[*] Result:")
    print(result)
