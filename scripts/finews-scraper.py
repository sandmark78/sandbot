#!/usr/bin/env python3
"""
finews-scraper.py — 抓取 FiNews 美股日报
来源: https://finews.elsetech.app/
输出: JSON 格式，包含盘后总结和主要新闻
"""
import urllib.request
import re
import json
import sys
import os
from datetime import datetime, timezone

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
OUTPUT_DIR = os.path.join(WORKSPACE, "tmp", "finews")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def scrape_finews():
    """抓取 FiNews 美股日报"""
    url = "https://finews.elsetech.app/"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    })
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    
    result = {
        "source": "FiNews 美股日报",
        "url": url,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "date": None,
        "summary": [],
        "news": []
    }
    
    # 提取日期
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})\s*美股', html)
    if date_match:
        result["date"] = date_match.group(1)
    
    # 提取盘后总结 - 从 summary-text span 中提取
    summary_items = re.findall(r'<span class="summary-text">(.*?)</span>', html, re.DOTALL)
    for item in summary_items:
        clean = re.sub(r'<[^>]+>', '', item).strip()
        if clean:
            result["summary"].append(clean)
    
    # 提取主要新闻 - 从 news-card 中提取
    news_cards = re.findall(r'<a[^>]*class="news-card"[^>]*href="([^"]*)"[^>]*>.*?<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
    for url, title in news_cards:
        clean_title = re.sub(r'<[^>]+>', '', title).strip()
        if clean_title and url.startswith('http'):
            result["news"].append({
                "title": clean_title,
                "url": url
            })
    
    # 备用：如果 news-card 没找到，尝试从普通链接提取
    if not result["news"]:
        news_links = re.findall(r'<a[^>]*href="(https?://[^"]*)"[^>]*>([^<]+)</a>', html)
        for url, title in news_links:
            title = title.strip()
            if title and len(title) > 10 and 'finews' not in url:
                result["news"].append({
                    "title": title,
                    "url": url
                })
    
    return result

def main():
    try:
        data = scrape_finews()
        
        # 保存 JSON
        output_file = os.path.join(OUTPUT_DIR, "latest.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 输出摘要
        print(f"📊 FiNews 美股日报 - {data.get('date', 'unknown')}")
        print(f"📅 抓取时间: {data['scraped_at']}")
        print(f"\n📋 盘后总结 ({len(data['summary'])} 条):")
        for i, item in enumerate(data['summary'][:5], 1):
            print(f"  {i}. {item[:80]}...")
        print(f"\n📰 主要新闻 ({len(data['news'])} 条):")
        for i, item in enumerate(data['news'][:5], 1):
            print(f"  {i}. {item['title'][:60]}...")
        
        print(f"\n✅ 已保存到: {output_file}")
        return 0
        
    except Exception as e:
        print(f"❌ 抓取失败: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
