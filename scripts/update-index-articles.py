#!/usr/bin/env python3
"""
动态更新首页最新文章列表
从 blog.html 提取最新文章，更新到 index.html
"""

import re
import os

BLOG_HTML = "/tmp/sandbot-gh/blog.html"
INDEX_HTML = "/tmp/sandbot-gh/index.html"

def extract_latest_articles(blog_html, limit=6):
    """从 blog.html 提取最新文章"""
    with open(blog_html, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找 const articles = [...] 部分
    articles_match = re.search(r'const articles = \[(.*?)\];', content, re.DOTALL)
    if not articles_match:
        print("❌ 无法找到 articles 数组")
        return []
    
    articles_str = articles_match.group(1)
    
    # 解析每个文章对象
    articles = []
    article_pattern = r'\{\s*title:\s*"([^"]+)",\s*type:\s*"([^"]+)",\s*typeLabel:\s*"([^"]+)",\s*tag:\s*"([^"]+)",\s*date:\s*"([^"]+)",\s*url:\s*"([^"]+)",\s*excerpt:\s*"([^"]*)",\s*duration:\s*"([^"]+)",\s*access:\s*"([^"]+)"\s*\}'
    
    for match in re.finditer(article_pattern, articles_str):
        title, type_, typeLabel, tag, date, url, excerpt, duration, access = match.groups()
        
        # 清理标题（移除 [热点] 等前缀）
        clean_title = re.sub(r'^\[[^\]]+\]\s*', '', title)
        
        articles.append({
            'title': clean_title,
            'type': type_,
            'tag': tag,
            'date': date,
            'url': url,
            'excerpt': excerpt,
            'duration': duration,
            'access': access
        })
        
        if len(articles) >= limit:
            break
    
    return articles

def generate_article_card(article):
    """生成文章卡片 HTML"""
    tag_class = article['type']
    
    # 映射类型到显示文本
    type_map = {
        'hot': '热点',
        'early': '早鸟',
        'evening': '晚间',
        'noon': '午间',
        'afternoon': '下午'
    }
    tag_text = type_map.get(article['type'], article['tag'])
    
    # 构建 URL
    url = article['url']
    if not url.startswith('http'):
        url = f"/{url}"
    
    html = f'''      <a href="{url}" class="latest-card">
        <span class="card-tag {tag_class}">{tag_text}</span>
        <h3>{article['title']}</h3>
        <p>{article['excerpt']}</p>
        <div class="card-meta">{article['date']} · {article['duration']}</div>
      </a>'''
    
    return html

def update_index_html(index_html, articles):
    """更新 index.html 的最新文章部分"""
    with open(index_html, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 生成新的文章卡片
    new_cards = '\n'.join([generate_article_card(a) for a in articles])
    
    # 查找 latest-articles 开始和结束位置
    start_marker = '<div class="latest-articles">'
    end_marker = '</div>\n  </div>\n\n  <div class="membership-banner">'
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("❌ 未找到 latest-articles 开始标记")
        return False
    
    # 找到结束标记
    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        print("❌ 未找到 latest-articles 结束标记")
        return False
    
    # 构建新内容
    new_section = f'''{start_marker}
{new_cards}
    </div>
  </div>

  <div class="membership-banner">'''
    
    # 替换
    new_content = content[:start_idx] + new_section + content[end_idx + len(end_marker):]
    
    with open(index_html, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    print("🔄 更新首页最新文章...")
    
    # 提取最新文章
    articles = extract_latest_articles(BLOG_HTML, limit=6)
    
    if not articles:
        print("❌ 未找到文章")
        return
    
    print(f"📰 找到 {len(articles)} 篇最新文章：")
    for i, article in enumerate(articles, 1):
        print(f"  {i}. {article['title']} ({article['date']})")
    
    # 更新 index.html
    if update_index_html(INDEX_HTML, articles):
        print("✅ 首页已更新")
    else:
        print("❌ 更新失败")

if __name__ == '__main__':
    main()
