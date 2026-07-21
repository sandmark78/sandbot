#!/usr/bin/env python3
"""
更新首页最新文章列表
从 blog.html 的文章数组中提取最新 6 篇文章，更新到 index.html
"""

import re
import json

def extract_latest_articles(blog_html_path, count=6):
    """从 blog.html 提取最新文章"""
    with open(blog_html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 articles 数组
    match = re.search(r'const articles = \[(.*?)\];', content, re.DOTALL)
    if not match:
        print("❌ 无法找到 articles 数组")
        return []
    
    articles_str = match.group(1)
    
    # 解析每个文章对象
    articles = []
    article_pattern = r'\{\s*title:\s*"([^"]+)",\s*type:\s*"([^"]+)",\s*typeLabel:\s*"([^"]+)",\s*tag:\s*"([^"]+)",\s*date:\s*"([^"]+)",\s*url:\s*"([^"]+)",\s*excerpt:\s*"([^"]*)",\s*duration:\s*"([^"]+)",\s*access:\s*"([^"]+)"\s*\}'
    
    for m in re.finditer(article_pattern, articles_str, re.DOTALL):
        title, type_, typeLabel, tag, date, url, excerpt, duration, access = m.groups()
        
        # 去掉标题前的标签（如 [热点]）
        clean_title = re.sub(r'^\[[^\]]+\]\s*', '', title)
        
        articles.append({
            'title': clean_title,
            'type': type_,
            'tag': tag,
            'date': date,
            'url': url,
            'excerpt': excerpt,
            'duration': duration
        })
    
    return articles[:count]

def generate_article_card(article):
    """生成文章卡片 HTML"""
    tag_class = article['type']
    if tag_class == 'hot':
        tag_text = '热点'
    elif tag_class == 'early':
        tag_text = '早鸟'
    elif tag_class == 'evening':
        tag_text = '晚间'
    elif tag_class == 'noon':
        tag_text = '午间'
    elif tag_class == 'afternoon':
        tag_text = '下午'
    else:
        tag_text = article['tag']
    
    # 处理 URL（去掉 posts/ 前缀）
    url = article['url'].replace('posts/', '/posts/')
    
    html = f'''      <a href="{url}" class="latest-card">
        <span class="card-tag {tag_class}">{tag_text}</span>
        <h3>{article['title']}</h3>
        <p>{article['excerpt']}</p>
        <div class="card-meta">{article['date']} · {article['duration']}</div>
      </a>'''
    
    return html

def update_index_html(index_html_path, articles):
    """更新 index.html 的最新文章部分"""
    with open(index_html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 生成新的文章卡片
    cards_html = '\n'.join([generate_article_card(a) for a in articles])
    
    # 替换 latest-articles 部分
    pattern = r'<div class="latest-articles">(.*?)</div>\s*</div>\s*<div class="membership-banner">'
    replacement = f'<div class="latest-articles">\n{cards_html}\n    </div>\n  </div>\n\n  <div class="membership-banner">'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(index_html_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ 已更新 index.html，包含 {len(articles)} 篇最新文章")

if __name__ == '__main__':
    blog_html = '/tmp/sandbot-gh/blog.html'
    index_html = '/tmp/sandbot-gh/index.html'
    
    articles = extract_latest_articles(blog_html, count=6)
    if articles:
        print(f"📝 提取到 {len(articles)} 篇最新文章：")
        for a in articles:
            print(f"   - {a['date']} | {a['title'][:50]}...")
        
        update_index_html(index_html, articles)
    else:
        print("❌ 未找到文章")
