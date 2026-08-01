#!/bin/bash
# RSS 资讯自动整理生成器 - 龙虾🦞资讯助手 v2.0

RSS_URL="https://news.google.com/atom/search?q=AI+Internet+Developer&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M)
OUTPUT_FILE="/home/node/.openclaw/workspace/memory/rss-news-$TIMESTAMP.md"
SUMMARY_FILE="/home/node/.openclaw/workspace/memory/rss-summary-$TIMESTAMP.md"

echo "🦞 RSS 资讯自动整理器启动..."
echo "="*60

# 第 1 步：抓取 RSS
echo "📥 第 1 步：抓取 RSS..."
curl -s "$RSS_URL" -o /tmp/rss-feed.xml
echo "  ✅ 抓取完成"

# 第 2 步：解析并生成详细文章
echo ""
echo "📝 第 2 步：生成详细文章..."
python3 << 'PYEOF'
import xml.etree.ElementTree as ET
from datetime import datetime

tree = ET.parse('/tmp/rss-feed.xml')
root = tree.getroot()
ns = {'atom': 'http://www.w3.org/2005/Atom'}

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
filename = f"/home/node/.openclaw/workspace/memory/rss-news-{timestamp}.md"

with open(filename, "w", encoding="utf-8") as f:
    f.write(f"# 📰 AI 资讯日报 - {datetime.now().strftime('%Y-%m-%d')}\n\n")
    f.write(f"**抓取时间**: {datetime.now().strftime('%H:%M UTC')}\n")
    f.write(f"**来源**: Google News RSS\n")
    f.write(f"**关键词**: AI, Internet, Developer\n\n")
    f.write("---\n\n")
    
    count = 0
    for entry in root.findall('.//atom:entry', ns):
        title = entry.find('atom:title', ns)
        link = entry.find('atom:link', ns)
        published = entry.find('atom:published', ns) or entry.find('atom:updated', ns)
        content = entry.find('atom:content', ns)
        
        if title is not None and count < 15:
            count += 1
            f.write(f"## {count}. {title.text}\n\n")
            if published is not None:
                f.write(f"**时间**: {published.text[:10]}\n\n")
            if content is not None:
                # 清理 HTML 标签
                import re
                text = re.sub('<[^<]+?>', '', content.text)[:500]
                f.write(f"**摘要**:\n{text}\n\n")
            if link is not None:
                f.write(f"**链接**: [阅读原文]({link.get('href')})\n\n")
            f.write("---\n\n")

print(f"  ✅ 详细文章：{filename} ({count} 条)")
PYEOF

# 第 3 步：生成摘要简报
echo ""
echo "📋 第 3 步：生成摘要简报..."
python3 << 'PYEOF'
import xml.etree.ElementTree as ET
from datetime import datetime

tree = ET.parse('/tmp/rss-feed.xml')
root = tree.getroot()
ns = {'atom': 'http://www.w3.org/2005/Atom'}

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
filename = f"/home/node/.openclaw/workspace/memory/rss-summary-{timestamp}.md"

with open(filename, "w", encoding="utf-8") as f:
    f.write(f"# 🦞 AI 资讯简报 - {datetime.now().strftime('%Y-%m-%d')}\n\n")
    f.write("**快速浏览** | 15 条精选 | Google News RSS\n\n")
    f.write("---\n\n")
    
    f.write("## 🔥 今日热点\n\n")
    
    count = 0
    for entry in root.findall('.//atom:entry', ns):
        title = entry.find('atom:title', ns)
        link = entry.find('atom:link', ns)
        published = entry.find('atom:published', ns) or entry.find('atom:updated', ns)
        
        if title is not None and count < 15:
            count += 1
            pub_date = published.text[:10] if published is not None else "未知"
            f.write(f"{count}. **{title.text}** ({pub_date})\n")
            if link is not None:
                f.write(f"   🔗 {link.get('href')}\n\n")

print(f"  ✅ 摘要简报：{filename} ({count} 条)")
PYEOF

echo ""
echo "="*60
echo "✅ 资讯整理完成！"
echo ""
echo "📊 输出文件:"
ls -lh /home/node/.openclaw/workspace/memory/rss-*.md 2>/dev/null | tail -2
