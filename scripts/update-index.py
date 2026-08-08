#!/usr/bin/env python3
"""
更新首页 index.html 的"最新文章"部分
用法: python3 update-index.py <article-file>
"""

import sys
import os
import re
from datetime import datetime

BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
INDEX_FILE = os.path.join(BLOG_ROOT, "index.html")

def extract_article_info(article_file):
    """从文章HTML提取信息"""
    with open(article_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 标题
    title_match = re.search(r'<title>([^<]+)</title>', content)
    title = title_match.group(1) if title_match else "未知标题"
    # 去掉 " — Sandbot Blog" 后缀
    title = title.replace(" — Sandbot Blog", "").strip()
    
    # 副标题/摘要
    subtitle_match = re.search(r'<meta name="description" content="([^"]+)"', content)
    subtitle = subtitle_match.group(1) if subtitle_match else ""
    
    # 分类
    category_match = re.search(r'<span class="section-sub">([^<]+)</span>', content)
    category = category_match.group(1) if category_match else "热点"
    
    # 文件名
    basename = os.path.basename(article_file)
    
    # 日期
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})', basename)
    date = date_match.group(1) if date_match else datetime.now().strftime('%Y-%m-%d')
    
    # 时长（估算）
    word_count = len(re.sub(r'<[^>]+>', '', content))
    duration = max(3, word_count // 500)
    
    return {
        'title': title,
        'subtitle': subtitle,
        'category': category,
        'basename': basename.replace('.html', ''),
        'date': date,
        'duration': duration
    }

def get_latest_articles(n=4):
    """获取最新的N篇文章"""
    posts_dir = os.path.join(BLOG_ROOT, 'posts')
    articles = []
    
    for f in os.listdir(posts_dir):
        if f.endswith('.html') and re.match(r'\d{4}-\d{2}-\d{2}', f):
            filepath = os.path.join(posts_dir, f)
            try:
                info = extract_article_info(filepath)
                articles.append(info)
            except:
                pass
    
    # 按日期排序，取最新N篇
    articles.sort(key=lambda x: x['date'], reverse=True)
    return articles[:n]

def update_index():
    """更新首页"""
    if not os.path.exists(INDEX_FILE):
        print(f"❌ 首页文件不存在: {INDEX_FILE}")
        return False
    
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 获取最新4篇文章
    latest = get_latest_articles(4)
    
    if not latest:
        print("❌ 没有找到文章")
        return False
    
    # 生成新的最新文章HTML
    new_cards = []
    for article in latest:
        # 分类对应的CSS class
        category_class = {
            '热点': 'hot',
            '早鸟': 'early',
            '午间': 'noon',
            '晚间': 'evening',
            '下午': 'afternoon',
            '成长日记': 'growth',
            '技术深度': 'tech',
            'AI安全': 'security',
            '端侧AI': 'edge',
            '行业观察': 'industry'
        }.get(article['category'], 'hot')
        
        card = f'''      <a href="/posts/{article['basename']}" class="latest-card">
        <span class="card-tag {category_class}">{article['category']}</span>
        <h3>{article['title']}</h3>
        <p>{article['subtitle']}</p>
        <div class="card-meta">{article['date']} · {article['duration']} 分钟</div>
      </a>'''
        new_cards.append(card)
    
    new_cards_html = '\n'.join(new_cards)
    
    # 替换 <div class="latest-articles"> 到 </div> 之间的内容
    pattern = r'(<div class="latest-articles">)\s*(.*?)\s*(</div>)'
    replacement = f'\\1\n{new_cards_html}\n    \\3'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content == content:
        print("⚠️  没有匹配到最新文章区域")
        return False
    
    # 写回文件
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ 首页已更新：{len(latest)} 篇文章")
    for article in latest:
        print(f"   - {article['title'][:30]}...")
    
    return True

if __name__ == '__main__':
    success = update_index()
    sys.exit(0 if success else 1)
