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
    
    # 提取标题（支持多种格式）
    title_match = re.search(r'<h1 class="article-title">(.*?)</h1>', content)
    if not title_match:
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content)
    title = title_match.group(1) if title_match else "未知标题"
    title = re.sub(r'<[^>]+>', '', title).strip()  # 清理 HTML 标签
    
    # 提取副标题
    subtitle_match = re.search(r'<p class="article-subtitle">(.*?)</p>', content)
    subtitle = subtitle_match.group(1) if subtitle_match else ""
    
    # 提取文件名
    filename = os.path.basename(article_file)
    
    # 从文件名提取日期和标签
    # 格式: 2026-07-10-morning-gpt-5-6.html 或 2026-08-01-growth-diary-xxx.html
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})-(morning|noon|afternoon|hot|night|growth-diary|early|evening)', filename)
    if date_match:
        date = date_match.group(1)
        time_type = date_match.group(2)
        tag_map = {
            'morning': '早鸟',
            'noon': '午间',
            'afternoon': '下午',
            'hot': '热点',
            'night': '晚间',
            'early': '热点',
            'evening': '晚间',
            'growth-diary': '成长日记'
        }
        tag = tag_map.get(time_type, '热点')
    else:
        # 如果文件名格式不匹配，从文件内容提取日期
        date_from_content = re.search(r'date:\s*["\']?(\d{4}-\d{2}-\d{2})["\']?', content)
        if date_from_content:
            date = date_from_content.group(1)
        else:
            date = datetime.now().strftime('%Y-%m-%d')
        tag = '热点'
    
    # 推断内容分类（P1 分类标签）
    category = infer_category(title, subtitle, content)
    
    return {
        'title': f'[{tag}] {title}',
        'subtitle': subtitle,
        'filename': filename,
        'date': date,
        'tag': tag,
        'category': category
    }

def infer_category(title, subtitle, content):
    """从标题+副标题+内容推断文章分类"""
    text = (title + ' ' + subtitle).lower()
    
    # 产品发布类关键词
    product_keywords = ['发布', '推出', '上线', 'launch', 'release', '开源', 'open source',
                        '模型', 'model', 'api', 'sdk', '框架', 'framework', '工具', 'tool',
                        'app', '应用', '平台', 'platform', '服务', 'service']
    # 深度分析类关键词
    deep_keywords = ['深度', '分析', '解读', '复盘', '拆解', '为什么', 'how', 'why',
                     '机制', '原理', '架构', 'architecture', '对比', '比较', '趋势',
                     '分水岭', '转折', '变革', '影响', '意味着']
    # 工具教程类关键词
    tool_keywords = ['教程', '手把手', '指南', 'guide', 'tutorial', 'how to', '怎么用',
                     '实操', '配置', '部署', '安装', '使用', '技巧', '工作流', 'workflow',
                     '提示词', 'prompt', 'skill', '技能']
    # 研究论文类关键词
    research_keywords = ['论文', 'paper', '研究', 'research', '实验', 'experiment',
                         'benchmark', '评测', '跑分', '数据集', 'dataset', '算法',
                         'arxiv', '学术', '形式化', '证明']
    
    # 计分
    scores = {'产品': 0, '深度': 0, '工具': 0, '研究': 0}
    for kw in product_keywords:
        if kw in text: scores['产品'] += 2
    for kw in deep_keywords:
        if kw in text: scores['深度'] += 2
    for kw in tool_keywords:
        if kw in text: scores['工具'] += 2
    for kw in research_keywords:
        if kw in text: scores['研究'] += 2
    
    # 文件名也提供参考
    filename_lower = content[:500].lower() if content else ''
    if 'launch' in filename_lower or 'product' in filename_lower:
        scores['产品'] += 1
    if 'deep' in filename_lower or 'analysis' in filename_lower:
        scores['深度'] += 1
    
    # 取最高分，默认深度
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return '深度'
    return best

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
    
    category = article_info.get('category', '深度')
    
    new_entry = f'''  {{
    title: "{title_escaped}",
    type: "{article_type}",
    typeLabel: "{type_label}",
    tag: "{article_info['tag']}",
    category: "{category}",
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
