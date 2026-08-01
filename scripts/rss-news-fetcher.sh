#!/bin/bash
# RSS 资讯抓取器 - 龙虾🦞资讯助手 (简化版)
# 使用 curl + web_fetch 抓取 RSS

RSS_URL="https://news.google.com/atom/search?q=AI+Internet+Developer&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
OUTPUT_FILE="/home/node/.openclaw/workspace/memory/rss-news-$(date +%Y-%m-%d).md"

echo "🦞 RSS 资讯抓取器启动..."
echo "="*60

# 抓取 RSS
echo "正在抓取：$RSS_URL"
curl -s "$RSS_URL" -o /tmp/rss-feed.xml

# 解析并生成文章
python3 << 'PYEOF'
import xml.etree.ElementTree as ET
from datetime import datetime

# 解析 RSS
tree = ET.parse('/tmp/rss-feed.xml')
root = tree.getroot()

# 命名空间
ns = {'atom': 'http://www.w3.org/2005/Atom'}

# 生成文章
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
filename = f"/home/node/.openclaw/workspace/memory/rss-news-{timestamp}.md"

with open(filename, "w", encoding="utf-8") as f:
    f.write(f"# 📰 AI 资讯日报 - {datetime.now().strftime('%Y-%m-%d')}\n\n")
    f.write(f"**抓取时间**: {datetime.now().strftime('%H:%M UTC')}\n")
    f.write(f"**来源**: Google News RSS\n\n")
    f.write("---\n\n")
    
    count = 0
    for entry in root.findall('.//atom:entry', ns):
        title = entry.find('atom:title', ns)
        link = entry.find('atom:link', ns)
        published = entry.find('atom:published', ns) or entry.find('atom:updated', ns)
        content = entry.find('atom:content', ns)
        
        if title is not None:
            count += 1
            f.write(f"## {count}. {title.text}\n\n")
            if published is not None:
                f.write(f"**时间**: {published.text}\n\n")
            if content is not None:
                f.write(f"**摘要**:\n{content.text[:500]}\n\n")
            if link is not None:
                f.write(f"**链接**: [阅读原文]({link.get('href')})\n\n")
            f.write("---\n\n")
        
        if count >= 15:
            break

print(f"✅ 文章已生成：{filename}")
print(f"📊 抓取条目：{count}")
PYEOF

echo ""
echo "="*60
echo "✅ RSS 抓取完成！"
