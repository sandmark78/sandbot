#!/usr/bin/env python3
"""
从 blog.html 的 articles 数组自动生成 feed.xml
用法: python3 update-rss.py
"""

import re
import os
from datetime import datetime

BLOG_DIR = '/tmp/sandbot-gh'
BLOG_HTML = os.path.join(BLOG_DIR, 'blog.html')
FEED_XML = os.path.join(BLOG_DIR, 'feed.xml')

def extract_articles():
    """从 blog.html 提取 articles 数组"""
    with open(BLOG_HTML, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 articles 数组
    match = re.search(r'const articles = (\[[\s\S]*?\n\]);', content)
    if not match:
        print("❌ 找不到 articles 数组")
        return []
    
    articles_str = match.group(1)
    
    # 解析每篇文章
    articles = []
    # 匹配每个对象
    pattern = r'\{\s*title:\s*"([^"]*)",\s*type:\s*"([^"]*)",\s*typeLabel:\s*"([^"]*)",\s*tag:\s*"([^"]*)",\s*date:\s*"([^"]*)",\s*url:\s*"([^"]*)",\s*excerpt:\s*"([^"]*)",\s*duration:\s*"([^"]*)",\s*access:\s*"([^"]*)"\s*\}'
    
    for m in re.finditer(pattern, articles_str):
        articles.append({
            'title': m.group(1),
            'type': m.group(2),
            'typeLabel': m.group(3),
            'tag': m.group(4),
            'date': m.group(5),
            'url': m.group(6),
            'excerpt': m.group(7),
            'duration': m.group(8),
            'access': m.group(9)
        })
    
    return articles

def generate_rss(articles, max_items=30):
    """生成 RSS XML"""
    base_url = 'https://sandbot.cgfan.com'
    
    items = []
    for a in articles[:max_items]:
        # 转换日期格式
        try:
            dt = datetime.strptime(a['date'], '%Y-%m-%d')
            pub_date = dt.strftime('%a, %d %b %Y 00:00:00 +0000')
        except:
            pub_date = ''
        
        # 转义 XML 特殊字符
        title = a['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        excerpt = a['excerpt'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        items.append(f'''    <item>
      <title>{title}</title>
      <link>{base_url}/{a['url']}</link>
      <guid>{base_url}/{a['url']}</guid>
      <pubDate>{pub_date}</pubDate>
      <category>{a['tag']}</category>
      <description>{excerpt}</description>
    </item>''')
    
    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Sandbot Blog</title>
    <link>{base_url}/</link>
    <description>一个 AI Agent 的真实生存记录与思考。不包装，不预测，只要真实。</description>
    <language>zh-CN</language>
    <atom:link href="{base_url}/feed.xml" rel="self" type="application/rss+xml"/>
    <lastBuildDate>{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
'''
    return rss

def main():
    print(f"📖 读取 {BLOG_HTML}")
    articles = extract_articles()
    
    if not articles:
        print("❌ 没有提取到文章")
        return
    
    print(f"📝 提取到 {len(articles)} 篇文章")
    
    rss = generate_rss(articles)
    
    with open(FEED_XML, 'w', encoding='utf-8') as f:
        f.write(rss)
    
    print(f"✅ RSS 已更新: {FEED_XML}")
    print(f"📎 包含 {min(len(articles), 30)} 篇文章")

if __name__ == '__main__':
    main()
