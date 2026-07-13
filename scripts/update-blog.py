#!/usr/bin/env python3
"""
更新 blog.html，添加新文章到文章列表
用法: python3 update-blog.py <article-file> <blog-html>
"""

import sys
import re
import os
from datetime import datetime

def extract_article_info(article_file):
    """从文章文件提取信息"""
    with open(article_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取标题
    title_match = re.search(r'<h1 class="article-title">(.*?)</h1>', content)
    title = title_match.group(1) if title_match else "未知标题"
    
    # 提取副标题
    subtitle_match = re.search(r'<p class="article-subtitle">(.*?)</p>', content)
    subtitle = subtitle_match.group(1) if subtitle_match else ""
    
    # 提取文件名
    filename = os.path.basename(article_file)
    
    # 从文件名提取日期和标签
    # 格式: 2026-07-10-morning-gpt-5-6.html
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})-(morning|noon|afternoon|hot|night)', filename)
    if date_match:
        date = date_match.group(1)
        time_type = date_match.group(2)
        tag_map = {
            'morning': '早鸟',
            'noon': '午间',
            'afternoon': '下午',
            'hot': '热点',
            'night': '晚间'
        }
        tag = tag_map.get(time_type, '热点')
    else:
        date = datetime.now().strftime('%Y-%m-%d')
        tag = '热点'
    
    return {
        'title': f'[{tag}] {title}',
        'subtitle': subtitle,
        'filename': filename,
        'date': date,
        'tag': tag
    }

def escape_js_string(text):
    """转义 JavaScript 字符串中的特殊字符"""
    if not text:
        return ""
    # 转义双引号
    text = text.replace('"', '\\"')
    # 转义中文引号（防止被误解析）
    text = text.replace('"', '\u201c')  # 左中文引号 → Unicode 转义
    text = text.replace('"', '\u201d')  # 右中文引号 → Unicode 转义
    # 转义单引号
    text = text.replace("'", "\\'")
    # 转义反斜杠
    text = text.replace('\\', '\\\\')
    # 转义换行
    text = text.replace('\n', '\\n')
    text = text.replace('\r', '\\r')
    return text

def update_blog_html(blog_file, article_info):
    """更新 blog.html"""
    with open(blog_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 转义所有字段
    title_escaped = escape_js_string(article_info['title'])
    subtitle_escaped = escape_js_string(article_info['subtitle'])
    
    # 构建新文章条目
    # Cloudflare Pages: 文件名用 .html，但链接用无后缀格式
    url_filename = article_info['filename'].replace('.html', '')
    
    # 根据标签动态设置 type 和 typeLabel
    type_map = {
        '早鸟': ('early', '早鸟'),
        '午间': ('noon', '午间'),
        '下午': ('afternoon', '下午'),
        '热点': ('hot', '热点'),
        '晚间': ('evening', '晚间')
    }
    article_type, type_label = type_map.get(article_info['tag'], ('hot', '热点'))
    
    new_entry = f'''  {{
    title: "{title_escaped}",
    type: "{article_type}",
    typeLabel: "{type_label}",
    tag: "{article_info['tag']}",
    date: "{article_info['date']}",
    url: "posts/{url_filename}",
    excerpt: "{subtitle_escaped}",
    duration: "6 分钟",
    access: "free"
  }}'''
    
    # 在 articles 数组开头插入
    pattern = r'(const articles = \[\n)'
    replacement = r'\1' + new_entry + ',\n'
    content = re.sub(pattern, replacement, content)
    
    # 同时更新今日精选部分
    # 更新标题
    content = re.sub(
        r'<h2 class="featured-title"><a href="[^"]*">[^<]*</a></h2>',
        f'<h2 class="featured-title"><a href="posts/{url_filename}">{article_info["title"].replace("[热点] ", "").replace("[早鸟] ", "").replace("[晚间] ", "").replace("[下午] ", "")}</a></h2>',
        content
    )
    
    # 更新摘要
    content = re.sub(
        r'<p class="featured-excerpt">[^<]*</p>',
        f'<p class="featured-excerpt">{article_info["subtitle"]}</p>',
        content
    )
    
    # 更新今日精选的日期和时长
    # 找到 featured-meta 部分并更新
    content = re.sub(
        r'(<div class="featured-meta">\s*<span class="tag">[^<]*</span>\s*<span class="dot"></span>\s*)<span>\d{4}-\d{2}-\d{2}</span>',
        rf'\1<span>{article_info["date"]}</span>',
        content
    )
    
    # 写回文件
    with open(blog_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已更新 {blog_file}")
    print(f"   - articles 数组：已添加 {article_info['title']}")
    print(f"   - 今日精选：已更新为 {article_info['title']}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python3 update-blog.py <article-file> <blog-html>")
        sys.exit(1)
    
    article_file = sys.argv[1]
    blog_file = sys.argv[2]
    
    article_info = extract_article_info(article_file)
    update_blog_html(blog_file, article_info)
