#!/usr/bin/env python3
"""
重建文章索引文件
- topic-index.md: 最近90天文章标题（选题去重用）
- article-titles-index.md: 最近60天文章标题（选题去重用）
"""

import os
import re
from datetime import datetime, timedelta
from pathlib import Path

BLOG_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = BLOG_ROOT / "posts"

def extract_title(html_file):
    """从HTML提取标题"""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'<title>(.*?)</title>', content, re.DOTALL)
    if match:
        title = match.group(1).strip()
        # 清理常见后缀
        title = re.sub(r'\s*—\s*Sandbot Blog.*$', '', title)
        title = re.sub(r'\s*\|.*$', '', title)
        return title.strip()
    return ""

def extract_date_from_filename(filename):
    """从文件名提取日期"""
    match = re.match(r'(\d{4}-\d{2}-\d{2})', filename)
    if match:
        return match.group(1)
    return None

def extract_category(html_file):
    """从HTML提取分类标签"""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'<span class="label-category">(.*?)</span>', content)
    if match:
        return match.group(1).strip()
    return ""

def scan_posts():
    """扫描所有文章"""
    articles = []
    for f in POSTS_DIR.glob("*.html"):
        if f.name in ("all.html", "index.html"):
            continue
        date = extract_date_from_filename(f.name)
        if not date:
            continue
        title = extract_title(f)
        category = extract_category(f)
        if title:
            articles.append({
                'date': date,
                'title': title,
                'category': category,
                'filename': f.name
            })
    # 按日期排序（最新在前）
    articles.sort(key=lambda x: x['date'], reverse=True)
    return articles

def build_topic_index(articles, days=90):
    """生成 topic-index.md"""
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    recent = [a for a in articles if a['date'] >= cutoff]
    
    # 去重（按标题）
    seen = set()
    unique = []
    for a in recent:
        if a['title'] not in seen:
            seen.add(a['title'])
            unique.append(a)
    
    lines = [
        f"# 最近 {days} 天文章标题索引",
        f"# 共 {len(unique)} 篇（去重后）",
        f"# 生成时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"# 用途: Cron agent 选题时参考，语义去重",
        ""
    ]
    for a in unique:
        cat = f" [{a['category']}]" if a['category'] else ""
        lines.append(f"{a['date']} |{cat} {a['title']}")
    
    output = BLOG_ROOT / "topic-index.md"
    output.write_text('\n'.join(lines), encoding='utf-8')
    print(f"✅ topic-index.md: {len(unique)} articles ({days} days)")
    return len(unique)

def build_article_titles_index(articles, days=60):
    """生成 article-titles-index.md"""
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    recent = [a for a in articles if a['date'] >= cutoff]
    
    # 去重（按标题）
    seen = set()
    unique = []
    for a in recent:
        if a['title'] not in seen:
            seen.add(a['title'])
            unique.append(a)
    
    lines = [
        f"# 最近 {days} 天文章标题索引（共 {len(unique)} 篇）",
        f"# 生成时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"# 用途: 选题去重参考",
        ""
    ]
    for a in unique:
        cat = f"[{a['category']}]" if a['category'] else ""
        lines.append(f"{a['date']} | {cat} {a['title']}")
    
    output = BLOG_ROOT / "article-titles-index.md"
    output.write_text('\n'.join(lines), encoding='utf-8')
    print(f"✅ article-titles-index.md: {len(unique)} articles ({days} days)")
    return len(unique)

if __name__ == '__main__':
    print("Scanning posts...")
    articles = scan_posts()
    print(f"Found {len(articles)} total articles")
    
    t = build_topic_index(articles, 90)
    a = build_article_titles_index(articles, 60)
    
    print(f"\nDone! topic-index: {t}, article-titles: {a}")
