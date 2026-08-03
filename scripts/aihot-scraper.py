#!/usr/bin/env python3
"""
aihot-scraper.py — 通过 API 抓取 AIHOT 每日 AI 热点
输出：结构化 JSON + 可读文本摘要
用法: python3 aihot-scraper.py [--format json|text] [--top N]
"""
import urllib.request, json, sys, os
from datetime import datetime, timezone

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
OUTPUT_DIR = os.path.join(WORKSPACE, "tmp", "aihot")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_aihot_api(limit=20):
    """通过 API 获取 AIHOT 数据"""
    url = f"https://aihot.virxact.com/api/v1/items?mode=selected&window=24h&limit={limit}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Accept": "application/json"
    })
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        items = data.get('items', [])
        news = []
        for item in items:
            news.append({
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "title_en": item.get("title_en", ""),
                "link": item.get("url", ""),
                "summary": item.get("summary", ""),
                "source": item.get("source", ""),
                "published": item.get("publishedAt", ""),
                "discovered": item.get("discoveredAt", ""),
            })
        
        return {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "total_items": len(news),
            "items": news,
        }
    except Exception as e:
        print(f"❌ API 请求失败: {e}", file=sys.stderr)
        return None

def format_text(data, top_n=None):
    """格式化为可读文本"""
    if not data:
        return "无数据"
    
    items = data['items']
    if top_n:
        items = items[:top_n]
    
    lines = [
        f"# AIHOT 每日热点 - {data['date']}",
        f"抓取时间: {data['scraped_at']}",
        f"共 {data['total_items']} 条",
        ""
    ]
    
    for i, item in enumerate(items, 1):
        lines.extend([
            f"## {i}. {item['title']}",
            f"来源: {item['source']}",
            f"链接: {item['link']}",
            f"发布: {item['published']}",
            "",
            item['summary'],
            ""
        ])
    
    return "\n".join(lines)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--format', choices=['json', 'text'], default='text')
    parser.add_argument('--top', type=int, help='只显示前N条')
    args = parser.parse_args()
    
    print("🔍 通过 API 抓取 AIHOT...", file=sys.stderr)
    data = fetch_aihot_api(limit=50)
    
    if not data:
        sys.exit(1)
    
    # 保存 JSON
    json_file = os.path.join(OUTPUT_DIR, f"{data['date']}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存: {json_file}", file=sys.stderr)
    
    # 输出
    if args.format == 'json':
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_text(data, args.top))

if __name__ == '__main__':
    main()
