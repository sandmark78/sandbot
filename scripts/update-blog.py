#!/usr/bin/env python3
"""
更新 blog.html，添加新文章到文章列表
用法: python3 update-blog.py <article-file> <blog-html>
"""

import sys
import re
import os

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

def update_blog_html(blog_file, article_info):
    """更新 blog.html"""
    with open(blog_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 构建新文章条目
    new_entry = f'''  {{
    title: "{article_info['title']}",
    type: "launch",
    typeLabel: "LAUNCH",
    tag: "{article_info['tag']}",
    date: "{article_info['date']}",
    url: "posts/{article_info['filename']}",
    excerpt: "{article_info['subtitle']}",
    duration: "6 分钟",
    access: "free"
  }}'''
    
    # 在 articles 数组开头插入
    pattern = r'(const articles = \[\n)'
    replacement = r'\1' + new_entry + ',\n'
    content = re.sub(pattern, replacement, content)
    
    # 写回文件
    with open(blog_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已更新 {blog_file}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python3 update-blog.py <article-file> <blog-html>")
        sys.exit(1)
    
    article_file = sys.argv[1]
    blog_file = sys.argv[2]
    
    article_info = extract_article_info(article_file)
    update_blog_html(blog_file, article_info)
