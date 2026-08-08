#!/usr/bin/env python3
"""
更新首页 index.html 的"最新文章"部分
用法: python3 update-index.py

修复记录:
- 2026-08-08: 修复分类提取（从JSON配置读取，不从section-sub提取）
- 2026-08-08: 修复正则匹配（避免嵌套div导致HTML结构破坏）
"""

import sys
import os
import re
import json
from datetime import datetime

BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
INDEX_FILE = os.path.join(BLOG_ROOT, "index.html")
POSTS_DIR = os.path.join(BLOG_ROOT, "posts")
TOPICS_DIR = os.path.join(BLOG_ROOT, "topics")

# 分类关键词映射（从标题前缀提取）
CATEGORY_PREFIXES = [
    "行业观察", "AI安全", "技术深度", "端侧AI", "开源治理",
    "思维模型", "AI 社会", "AI 硬件", "AI协作", "产品实测",
    "成长日记", "热点", "早鸟", "午间", "晚间", "下午"
]

def extract_category_from_title(title):
    """从标题前缀提取分类"""
    for prefix in CATEGORY_PREFIXES:
        if title.startswith(prefix):
            return prefix
    return "热点"

def extract_article_info(article_file):
    """从文章HTML和JSON配置提取信息"""
    basename = os.path.basename(article_file)
    base_name = basename.replace('.html', '')
    
    # 日期（从文件名提取）
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})', base_name)
    date = date_match.group(1) if date_match else datetime.now().strftime('%Y-%m-%d')
    
    # 尝试从JSON配置读取分类
    category = None
    json_file = os.path.join(TOPICS_DIR, f"config-{base_name}.json")
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                category = config.get('category')
        except:
            pass
    
    # 读取HTML提取标题和摘要
    with open(article_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 标题
    title_match = re.search(r'<title>([^<]+)</title>', content)
    title = title_match.group(1) if title_match else "未知标题"
    title = title.replace(" — Sandbot Blog", "").strip()
    
    # 如果JSON没有category，从标题前缀提取
    if not category:
        category = extract_category_from_title(title)
    
    # 副标题/摘要
    subtitle_match = re.search(r'<meta name="description" content="([^"]+)"', content)
    subtitle = subtitle_match.group(1) if subtitle_match else ""
    # 清理HTML实体
    subtitle = subtitle.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    
    # 时长（从JSON或估算）
    read_time = None
    if os.path.exists(json_file):
        try:
            read_time = config.get('read_time')
        except:
            pass
    if not read_time:
        word_count = len(re.sub(r'<[^>]+>', '', content))
        read_time = f"{max(3, word_count // 500)} 分钟"
    
    return {
        'title': title,
        'subtitle': subtitle,
        'category': category,
        'basename': base_name,
        'date': date,
        'read_time': read_time
    }

def get_latest_articles(n=4):
    """获取最新的N篇文章"""
    articles = []
    
    for f in os.listdir(POSTS_DIR):
        if f.endswith('.html') and re.match(r'\d{4}-\d{2}-\d{2}', f):
            filepath = os.path.join(POSTS_DIR, f)
            try:
                info = extract_article_info(filepath)
                articles.append(info)
            except Exception as e:
                pass
    
    # 按日期+文件名排序（同一天按时间类型排序）
    articles.sort(key=lambda x: (x['date'], x['basename']), reverse=True)
    return articles[:n]

def get_category_class(category):
    """分类对应的CSS class"""
    mapping = {
        '热点': 'hot',
        '早鸟': 'early',
        '午间': 'noon',
        '晚间': 'evening',
        '下午': 'afternoon',
        '成长日记': 'growth',
        '技术深度': 'tech',
        'AI安全': 'security',
        '端侧AI': 'edge',
        '行业观察': 'industry',
        '开源治理': 'industry',
        '思维模型': 'tech',
        'AI 社会': 'industry',
        'AI 硬件': 'edge',
        'AI协作': 'tech',
        '产品实测': 'tech'
    }
    return mapping.get(category, 'hot')

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
        category_class = get_category_class(article['category'])
        
        # 转义HTML特殊字符
        title_escaped = article['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        subtitle_escaped = article['subtitle'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        
        card = f'''      <a href="/posts/{article['basename']}" class="latest-card">
        <span class="card-tag {category_class}">{article['category']}</span>
        <h3>{title_escaped}</h3>
        <p>{subtitle_escaped}</p>
        <div class="card-meta">{article['date']} · {article['read_time']}</div>
      </a>'''
        new_cards.append(card)
    
    new_cards_html = '\n'.join(new_cards)
    
    # 精确匹配 <div class="latest-articles"> 到对应的 </div>
    # 使用非贪婪匹配，但要确保匹配到正确的闭合标签
    pattern = r'(<div class="latest-articles">)\s*\n(.*?)\n(\s*</div>)'
    
    def replace_func(match):
        return f'{match.group(1)}\n{new_cards_html}\n{match.group(3)}'
    
    new_content = re.sub(pattern, replace_func, content, flags=re.DOTALL, count=1)
    
    if new_content == content:
        print("⚠️  没有匹配到最新文章区域")
        return False
    
    # 写回文件
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ 首页已更新：{len(latest)} 篇文章")
    for article in latest:
        print(f"   - [{article['category']}] {article['title'][:40]}...")
    
    return True

if __name__ == '__main__':
    success = update_index()
    sys.exit(0 if success else 1)
