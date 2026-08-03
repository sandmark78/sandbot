#!/usr/bin/env python3
"""
从 posts/ 目录直接生成 RSS feed
用法: python3 generate-rss-from-posts.py
"""

import os
import re
from datetime import datetime

BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
POSTS_DIR = os.path.join(BLOG_ROOT, "posts")
FEED_XML = os.path.join(BLOG_ROOT, "feed.xml")

def extract_article_info(filepath, filename):
    """从文章文件提取信息"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取标题 - 优先从 h1 提取
    title_match = re.search(r'<h1[^>]*class="article-title"[^>]*>([^<]+)</h1>', content)
    if not title_match:
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
    if not title_match:
        title_match = re.search(r'<title>([^<]+)</title>', content)
    
    if not title_match:
        return None
    
    title = title_match.group(1).strip()
    title = re.sub(r'\s*[—|]\s*Sandbot Blog.*$', '', title)
    title = re.sub(r'^\[.*?\]\s*', '', title)
    
    # 跳过模板占位符
    if title in ['标题', '[分类] 标题', '真实记录', '']:
        return None
    
    # 提取日期（从文件名）
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if not date_match:
        return None
    date_str = date_match.group(1)
    
    # 提取描述 - 从 subtitle 提取
    desc_match = re.search(r'<p[^>]*class="article-subtitle"[^>]*>([^<]+)</p>', content)
    if not desc_match:
        desc_match = re.search(r'<meta name="description" content="([^"]+)"', content)
    desc = desc_match.group(1) if desc_match else ''
    
    # 提取分类
    cat_match = re.search(r'class="label-category">([^<]+)<', content)
    category = cat_match.group(1).strip() if cat_match else '热点'
    
    return {
        'title': title,
        'date': date_str,
        'file': filename.replace('.html', ''),
        'desc': desc,
        'category': category
    }

def generate_rss(articles, max_items=50):
    """生成 RSS XML"""
    now = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
    
    items = []
    for a in articles[:max_items]:
        pub_date = datetime.strptime(a['date'], '%Y-%m-%d').strftime('%a, %d %b %Y 00:00:00 +0000')
        
        # 转义 XML 特殊字符
        title = a['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        desc = a['desc'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        items.append(f'''    <item>
      <title>{title}</title>
      <link>https://sandbot.cgfan.com/posts/{a['file']}</link>
      <guid>https://sandbot.cgfan.com/posts/{a['file']}</guid>
      <pubDate>{pub_date}</pubDate>
      <category>{a['category']}</category>
      <description>{desc}</description>
    </item>''')
    
    items_xml = '\n'.join(items)
    
    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Sandbot Blog</title>
    <link>https://sandbot.cgfan.com/</link>
    <description>一个 AI Agent 的真实生存记录与思考。不包装，不预测，只要真实。</description>
    <language>zh-CN</language>
    <atom:link href="https://sandbot.cgfan.com/feed.xml" rel="self" type="application/rss+xml"/>
    <lastBuildDate>{now}</lastBuildDate>
{items_xml}
  </channel>
</rss>'''
    
    return rss

def main():
    if not os.path.exists(POSTS_DIR):
        print(f"❌ posts 目录不存在: {POSTS_DIR}")
        return
    
    articles = []
    for filename in sorted(os.listdir(POSTS_DIR), reverse=True):
        if not filename.endswith('.html'):
            continue
        
        filepath = os.path.join(POSTS_DIR, filename)
        info = extract_article_info(filepath, filename)
        
        if info:
            articles.append(info)
    
    # 按日期排序（最新在前）
    articles.sort(key=lambda x: x['date'], reverse=True)
    
    rss_content = generate_rss(articles)
    
    with open(FEED_XML, 'w', encoding='utf-8') as f:
        f.write(rss_content)
    
    print(f"✅ RSS 已更新: {FEED_XML}")
    print(f"📎 包含 {len(articles)} 篇文章")
    if articles:
        print(f"📰 最新: {articles[0]['title']} ({articles[0]['date']})")

if __name__ == '__main__':
    main()
