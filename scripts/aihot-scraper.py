#!/usr/bin/env python3
"""
aihot-scraper.py — 抓取 AIHOT 每日 AI 热点
输出：结构化 JSON + 可读文本摘要
用法: python3 aihot-scraper.py [--format json|text] [--top N]
"""
import urllib.request, re, json, sys, os
from datetime import datetime, timezone

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
OUTPUT_DIR = os.path.join(WORKSPACE, "tmp", "aihot")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def scrape_aihot():
    """Scrape AIHOT main page - parse Next.js initialItems"""
    url = "https://aihot.virxact.com"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    })
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    
    # Find Next.js push containing initialItems
    matches = list(re.finditer(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.DOTALL))
    
    for m in matches:
        raw = m.group(1)
        if 'initialItems' not in raw:
            continue
        
        # Unescape Next.js JSON string
        raw = raw.replace('\\\\', '\x00')
        raw = raw.replace('\\"', '"')
        raw = raw.replace('\\n', '\n')
        raw = raw.replace('\\t', '\t')
        raw = raw.replace('\x00', '\\')
        
        try:
            raw = raw.encode('latin-1').decode('unicode_escape')
        except:
            pass
        
        idx = raw.find('"initialItems":[')
        if idx < 0:
            continue
        
        depth = 0
        start = idx + len('"initialItems":')
        for j in range(start, min(start+300000, len(raw))):
            if raw[j] == '[':
                depth += 1
            elif raw[j] == ']':
                depth -= 1
                if depth == 0:
                    json_str = raw[start:j+1]
                    items = json.loads(json_str)
                    
                    news = []
                    for item in items:
                        news.append({
                            "id": item.get("id", ""),
                            "title": item.get("titleZh", item.get("title", "")),
                            "link": item.get("url", ""),
                            "summary": item.get("summaryZh", ""),
                            "reason": item.get("aiSelectedReason", ""),
                            "score": item.get("qualityScore", 0),
                            "tags": [t.get("tag", "") for t in item.get("aiTags", [])],
                            "source": item.get("source", {}).get("name", ""),
                            "time": item.get("timeLabel", ""),
                            "date": item.get("dateLabel", ""),
                        })
                    
                    return {
                        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                        "total_items": len(news),
                        "items": news,
                    }
    
    return {"error": "Could not parse AIHOT data", "total_items": 0, "items": []}

def format_text(data, top=10):
    """Format as readable text for 虾聊/blog"""
    lines = []
    lines.append(f"🤖 AI 热点日报 — {data['date']}")
    lines.append(f"共 {data['total_items']} 条精选")
    lines.append("")
    
    for i, item in enumerate(data['items'][:top], 1):
        lines.append(f"{i}. **{item['title']}**")
        lines.append(f"   🔗 {item['link']}")
        lines.append(f"   📊 推荐分: {item['score']} | {item['source']} | {item['time']}")
        if item['summary']:
            lines.append(f"   📝 {item['summary'][:120]}")
        if item['reason']:
            lines.append(f"   💡 {item['reason'][:100]}")
        if item['tags']:
            lines.append(f"   🏷️ {', '.join(item['tags'][:3])}")
        lines.append("")
    
    return "\n".join(lines)

def main():
    out_fmt = "json"
    top = 10
    
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--format" and i+1 < len(args):
            out_fmt = args[i+1]
        elif arg == "--top" and i+1 < len(args):
            top = int(args[i+1])
    
    print("🔍 抓取 AIHOT...", file=sys.stderr)
    data = scrape_aihot()
    
    if "error" in data:
        print(f"❌ {data['error']}", file=sys.stderr)
        sys.exit(1)
    
    # Save JSON
    today = data['date']
    json_path = os.path.join(OUTPUT_DIR, f"aihot-{today}.json")
    with open(json_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 已保存: {json_path}", file=sys.stderr)
    
    if out_fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_text(data, top))

if __name__ == "__main__":
    main()
