#!/usr/bin/env python3
"""
news-aggregator.py — 统一新闻聚合器
优化方案：一次抓取多个源，本地处理，减少模型调用

用法:
  python3 news-aggregator.py [--sources all|hn|aihot|finews] [--top N]

输出:
  tmp/news/YYYY-MM-DD.json - 结构化新闻数据
  tmp/news/YYYY-MM-DD.md - 可读摘要
"""

import urllib.request
import json
import sys
import os
import re
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
OUTPUT_DIR = os.path.join(WORKSPACE, "tmp", "news")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 新闻源配置
SOURCES = {
    "hn": {
        "name": "Hacker News",
        "url": "https://hacker-news.firebaseio.com/v0/topstories.json",
        "threshold": 100,  # 最低分数
        "max_items": 10
    },
    "aihot": {
        "name": "AIHOT",
        "url": "https://aihot.virxact.com",
        "max_items": 10
    },
    "finews": {
        "name": "FiNews 美股日报",
        "url": "https://finews.elsetech.app/",
        "max_items": 5
    }
}

def fetch_hn_stories(max_items=10, threshold=100):
    """抓取 Hacker News 热门故事（使用官方 API）"""
    print("📡 抓取 Hacker News...")
    
    # 获取热门故事 ID
    req = urllib.request.Request(
        SOURCES["hn"]["url"],
        headers={"User-Agent": "Mozilla/5.0"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            story_ids = json.loads(resp.read().decode('utf-8'))[:max_items * 2]
    except Exception as e:
        print(f"  ❌ 获取故事列表失败: {e}")
        return []
    
    stories = []
    for story_id in story_ids[:max_items]:
        try:
            # 获取故事详情
            req = urllib.request.Request(
                f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                story = json.loads(resp.read().decode('utf-8'))
                
                # 过滤低分故事
                if story.get('score', 0) < threshold:
                    continue
                
                stories.append({
                    "title": story.get('title', ''),
                    "url": story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                    "score": story.get('score', 0),
                    "comments": story.get('descendants', 0),
                    "source": "Hacker News",
                    "hn_url": f"https://news.ycombinator.com/item?id={story_id}"
                })
                
                print(f"  ✅ [{story.get('score', 0)}分] {story.get('title', '')[:50]}...")
                
                if len(stories) >= max_items:
                    break
                    
        except Exception as e:
            print(f"  ⚠️ 获取故事 {story_id} 失败: {e}")
            continue
    
    return stories

def fetch_aihot(max_items=10):
    """抓取 AIHOT 每日 AI 热点"""
    print("📡 抓取 AIHOT...")
    
    url = SOURCES["aihot"]["url"]
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    })
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  ❌ 抓取失败: {e}")
        return []
    
    # 解析 Next.js 数据
    matches = list(re.finditer(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.DOTALL))
    
    items = []
    for m in matches:
        raw = m.group(1)
        if 'initialItems' not in raw:
            continue
        
        # 解码 Next.js JSON
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
        
        # 提取 JSON 数组
        depth = 0
        start = idx + len('"initialItems":')
        for j in range(start, min(start + 300000, len(raw))):
            if raw[j] == '[':
                depth += 1
            elif raw[j] == ']':
                depth -= 1
                if depth == 0:
                    try:
                        items_data = json.loads(raw[start:j+1])
                        for item in items_data[:max_items]:
                            items.append({
                                "title": item.get('title', ''),
                                "url": item.get('url', ''),
                                "source": "AIHOT",
                                "summary": item.get('summary', '')[:200]
                            })
                            print(f"  ✅ {item.get('title', '')[:50]}...")
                    except:
                        pass
                    break
        
        if len(items) >= max_items:
            break
    
    return items

def fetch_finews(max_items=5):
    """抓取 FiNews 美股日报"""
    print("📡 抓取 FiNews...")
    
    url = SOURCES["finews"]["url"]
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    })
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  ❌ 抓取失败: {e}")
        return []
    
    # 提取标题和内容
    items = []
    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html)
    if title_match:
        items.append({
            "title": title_match.group(1).strip(),
            "url": url,
            "source": "FiNews",
            "summary": "美股日报"
        })
        print(f"  ✅ {title_match.group(1).strip()[:50]}...")
    
    return items[:max_items]

def save_results(all_news, date_str):
    """保存结果到文件"""
    # JSON 格式
    json_file = os.path.join(OUTPUT_DIR, f"{date_str}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
    
    # Markdown 格式
    md_file = os.path.join(OUTPUT_DIR, f"{date_str}.md")
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"# 📰 每日新闻聚合 - {date_str}\n\n")
        f.write(f"**抓取时间**: {datetime.now(timezone.utc).strftime('%H:%M UTC')}\n")
        f.write(f"**新闻总数**: {len(all_news)} 条\n\n")
        f.write("---\n\n")
        
        # 按来源分组
        by_source = {}
        for item in all_news:
            source = item.get('source', 'Unknown')
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(item)
        
        for source, items in by_source.items():
            f.write(f"## {source} ({len(items)} 条)\n\n")
            for i, item in enumerate(items, 1):
                f.write(f"### {i}. {item.get('title', '无标题')}\n")
                if item.get('score'):
                    f.write(f"- **分数**: {item['score']}\n")
                if item.get('comments'):
                    f.write(f"- **评论**: {item['comments']}\n")
                f.write(f"- **链接**: {item.get('url', '')}\n")
                if item.get('summary'):
                    f.write(f"- **摘要**: {item['summary'][:200]}\n")
                f.write("\n")
    
    print(f"\n✅ 已保存到:")
    print(f"   - {json_file}")
    print(f"   - {md_file}")
    
    return json_file, md_file

def main():
    import argparse
    parser = argparse.ArgumentParser(description='统一新闻聚合器')
    parser.add_argument('--sources', default='all', help='新闻源: all|hn|aihot|finews')
    parser.add_argument('--top', type=int, default=10, help='每个源最多抓取条数')
    args = parser.parse_args()
    
    date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    print(f"🦞 开始抓取新闻 - {date_str}\n")
    
    all_news = []
    
    # 根据参数选择源
    sources_to_fetch = []
    if args.sources == 'all':
        sources_to_fetch = ['hn', 'aihot', 'finews']
    else:
        sources_to_fetch = args.sources.split(',')
    
    # 抓取各个源
    if 'hn' in sources_to_fetch:
        all_news.extend(fetch_hn_stories(max_items=args.top, threshold=SOURCES['hn']['threshold']))
    
    if 'aihot' in sources_to_fetch:
        all_news.extend(fetch_aihot(max_items=args.top))
    
    if 'finews' in sources_to_fetch:
        all_news.extend(fetch_finews(max_items=min(args.top, 5)))
    
    # 保存结果
    if all_news:
        save_results(all_news, date_str)
        print(f"\n📊 总计: {len(all_news)} 条新闻")
    else:
        print("\n❌ 没有抓取到新闻")
        sys.exit(1)

if __name__ == '__main__':
    main()
