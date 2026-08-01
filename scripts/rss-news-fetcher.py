#!/usr/bin/env python3
"""
RSS 资讯抓取器 - 龙虾🦞资讯助手
功能：抓取 Google News RSS，整理生成文章
"""

import feedparser
import json
from datetime import datetime
from pathlib import Path

# RSS 源配置
RSS_FEEDS = {
    "google_news_ai": "https://news.google.com/atom/search?q=AI+Internet+Developer&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "tophub_news": "https://tophub.today/c/news",
}

def fetch_rss(url, max_entries=20):
    """抓取 RSS 源"""
    print(f"🦞 正在抓取：{url[:50]}...")
    feed = feedparser.parse(url)
    
    entries = []
    for entry in feed.entries[:max_entries]:
        item = {
            "title": entry.get("title", "无标题"),
            "link": entry.get("link", ""),
            "published": entry.get("published", entry.get("updated", "未知时间")),
            "author": entry.get("author", "未知作者"),
            "summary": entry.get("summary", entry.get("description", ""))[:500],
        }
        entries.append(item)
        print(f"  ✅ {item['title'][:40]}...")
    
    return entries

def generate_article(entries, output_dir="memory"):
    """生成文章"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{output_dir}/rss-news-{timestamp}.md"
    
    Path(output_dir).mkdir(exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 📰 AI 资讯日报 - {datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write(f"**抓取时间**: {datetime.now().strftime('%H:%M UTC')}\n")
        f.write(f"**来源**: Google News RSS\n\n")
        f.write("---\n\n")
        
        for i, entry in enumerate(entries, 1):
            f.write(f"## {i}. {entry['title']}\n\n")
            f.write(f"**来源**: {entry['author']}\n\n")
            f.write(f"**时间**: {entry['published']}\n\n")
            f.write(f"**摘要**:\n{entry['summary']}\n\n")
            f.write(f"**链接**: [阅读原文]({entry['link']})\n\n")
            f.write("---\n\n")
    
    print(f"\n✅ 文章已生成：{filename}")
    return filename

def main():
    print("🦞 RSS 资讯抓取器启动...")
    print("="*60)
    
    # 抓取 Google News
    entries = fetch_rss(RSS_FEEDS["google_news_ai"], max_entries=15)
    
    if entries:
        # 生成文章
        filename = generate_article(entries)
        print(f"\n📊 统计:")
        print(f"  抓取条目：{len(entries)}")
        print(f"  输出文件：{filename}")
    else:
        print("❌ 未抓取到任何内容")

if __name__ == "__main__":
    main()
