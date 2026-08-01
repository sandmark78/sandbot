#!/usr/bin/env python3
"""
多源热点抓取脚本
从 HN、Reddit、AI HOT 等多个来源抓取热点话题
"""
import json
import sys
from datetime import datetime
from pathlib import Path
# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def fetch_hn():
    """抓取 Hacker News 首页"""
    import urllib.request
    try:
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        with urllib.request.urlopen(url, timeout=10) as response:
            ids = json.loads(response.read())[:10]
        
        stories = []
        for story_id in ids[:5]:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            with urllib.request.urlopen(story_url, timeout=5) as resp:
                story = json.loads(resp.read())
                stories.append({
                    'title': story.get('title', ''),
                    'score': story.get('score', 0),
                    'url': story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                    'source': 'HN'
                })
        return stories
    except Exception as e:
        print(f"HN 抓取失败: {e}", file=sys.stderr)
        return []

def main():
    output_file = Path(os.path.join(BLOG_ROOT, "hot-topics-multi.md"))
    
    print("📡 抓取多源热点...")
    
    hn_stories = fetch_hn()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# 多源热点素材 (生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n")
        
        f.write("## Hacker News Top 5\n\n")
        for i, story in enumerate(hn_stories, 1):
            f.write(f"### {i}. {story['title']}\n")
            f.write(f"- 分数: {story['score']}\n")
            f.write(f"- URL: {story['url']}\n")
            f.write(f"- 来源: {story['source']}\n")
            f.write(f"- 图片: none\n\n")
    
    print(f"✅ 已写入 {output_file}")
    print(f"   HN: {len(hn_stories)} 个话题")

if __name__ == "__main__":
    main()
