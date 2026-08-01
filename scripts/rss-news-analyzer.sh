#!/bin/bash
# RSS 资讯分析器 - Sandbot

GOOGLE_NEWS_RSS="https://news.google.com/atom/search?q=AI+Developer&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
OUTPUT_FILE="/home/node/.openclaw/workspace/memory/rss-daily-brief-$(date +%Y-%m-%d).md"

echo "🦞 RSS 资讯分析开始..."

# 抓取 Google News
curl -s "$GOOGLE_NEWS_RSS" -o /tmp/google-news.xml

# 解析并生成简报
python3 << 'PYEOF'
import xml.etree.ElementTree as ET
from datetime import datetime

tree = ET.parse('/tmp/google-news.xml')
root = tree.getroot()
ns = {'atom': 'http://www.w3.org/2005/Atom'}

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
filename = f"/home/node/.openclaw/workspace/memory/rss-daily-brief-{datetime.now().strftime('%Y-%m-%d')}.md"

with open(filename, "w", encoding="utf-8") as f:
    f.write(f"# 📰 AI 开发者资讯简报\n\n")
    f.write(f"**时间**: {timestamp}\n")
    f.write(f"**来源**: Google News RSS\n\n")
    f.write("---\n\n")
    
    f.write("## 🔥 今日热点\n\n")
    
    count = 0
    for entry in root.findall('.//atom:entry', ns):
        title = entry.find('atom:title', ns)
        link = entry.find('atom:link', ns)
        published = entry.find('atom:published', ns) or entry.find('atom:updated', ns)
        source = entry.find('atom:source/atom:name', ns)
        
        if title is not None and count < 15:
            count += 1
            pub_date = published.text[:10] if published is not None else "未知"
            source_name = source.text if source is not None else "未知"
            
            f.write(f"{count}. **{title.text}**\n")
            f.write(f"   - 来源：{source_name}\n")
            f.write(f"   - 时间：{pub_date}\n")
            if link is not None:
                f.write(f"   - 链接：[{link.get('href')}]\n")
            f.write("\n")

print(f"✅ 资讯简报已生成：{filename}")
print(f"📊 共 {count} 条热点")
PYEOF

echo ""
echo "✅ RSS 资讯分析完成！"
