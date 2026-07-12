#!/usr/bin/env python3
"""
从文章 HTML 提取纯正文（用于 TTS）
只提取正文内容，过滤掉导航、元数据、付费提示等
"""

import re
import sys

def extract_article_text(html_file):
    """提取文章正文"""
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 1. 提取文章主标题
    title_match = re.search(r'<h1 class="article-title">(.*?)</h1>', html, re.DOTALL)
    if not title_match:
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else ""
    
    # 2. 提取 article 标签内的内容
    article_match = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)
    if article_match:
        article_html = article_match.group(1)
    else:
        article_html = html
    
    # 3. 移除不需要的区块
    article_html = re.sub(r'<div class="article-meta">.*?</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="quick-glance">.*?</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="source-note">.*?</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="article-img">.*?</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="why-box">.*?</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="paywall.*?".*?</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<!-- PAYWALL.*?-->', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="article-label">.*?</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<p class="article-subtitle">.*?</p>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<nav.*?</nav>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<footer.*?</footer>', '', article_html, flags=re.DOTALL)
    
    # 移除音频播放器
    article_html = re.sub(r'<div class="audio-player">.*?</div>\s*</div>\s*</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="audio-player">.*?</audio>\s*</div>', '', article_html, flags=re.DOTALL)
    
    # 移除 UI 元素（打赏、订阅横幅、作者签名等）
    article_html = re.sub(r'<div class="tip-jar">.*?</div>\s*</div>\s*</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="subscribe-banner">.*?</div>\s*</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="author-sign">.*?</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="back-link">.*?</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="bottom-quote">.*?</div>\s*</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="bottom-source">.*?</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="data-cards">.*?</div>\s*</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="compare-box">.*?</div>\s*</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="capability-box">.*?</div>\s*</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="metaphor-box">.*?</div>\s*</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="conclusion">.*?</div>', '', article_html, flags=re.DOTALL)
    article_html = re.sub(r'<div class="info-bar">.*?</div>\s*</div>', '', article_html, flags=re.DOTALL)
    
    # 4. 提取正文元素
    paragraphs = []
    
    # 提取段落
    for p_match in re.finditer(r'<p[^>]*>(.*?)</p>', article_html, re.DOTALL):
        text = re.sub(r'<[^>]+>', '', p_match.group(1)).strip()
        # 过滤掉付费提示、元数据等
        if text and len(text) > 10:
            skip_words = ['升级会员', '只买这篇', '已是会员', '登录', '购买', '分钟', 
                         '免费部分', '墙内还有', '这是会员专属', '后面约', 'MEMBERS ONLY',
                         '约 5 分钟', '数据卡片', 'Agent 视点']
            if not any(x in text for x in skip_words):
                paragraphs.append(text)
    
    # 提取标题（h2, h3）
    for h_match in re.finditer(r'<h([23])[^>]*>(.*?)</h\1>', article_html, re.DOTALL):
        level = h_match.group(1)
        text = re.sub(r'<[^>]+>', '', h_match.group(2)).strip()
        # 清理标题中的数字标记
        text = re.sub(r'^\d+\s*·\s*', '', text)
        # 过滤掉不需要的标题
        skip_titles = ['速览', '来源', '会员专属', '后面约', 'MEMBERS', '深层', '信号', 'Agent 视点']
        if text and not any(x in text for x in skip_titles):
            paragraphs.append(f"\n{text}\n")
    
    # 提取列表项（只提取正文中的列表）
    for li_match in re.finditer(r'<li[^>]*>(.*?)</li>', article_html, re.DOTALL):
        text = re.sub(r'<[^>]+>', '', li_match.group(1)).strip()
        if text and len(text) > 15:
            if not any(x in text for x in ['升级', '登录', '购买', '会员']):
                paragraphs.append(f"· {text}")
    
    # 5. 组合
    text = '\n\n'.join(paragraphs)
    
    # 6. 清理残留
    text = re.sub(r'🔒.*', '', text)
    text = re.sub(r'MEMBERS ONLY.*', '', text)
    text = re.sub(r'本文发布 \d+ 天后免费开放全文。', '', text)
    text = re.sub(r'诉讼 · 到底发生了什么$', '', text)  # 去掉末尾重复标题
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()
    
    # 7. 组合标题和正文
    if title:
        full_text = f"{title}\n\n{text}"
    else:
        full_text = text
    
    # 8. 限制长度（约 8000 字符 ≈ 5-6 分钟音频）
    if len(full_text) > 8000:
        full_text = full_text[:8000] + "\n\n今天就聊到这里。"
    
    return full_text

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 extract-article-text.py <article.html>")
        sys.exit(1)
    
    text = extract_article_text(sys.argv[1])
    
    # 输出到文件或标准输出
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"✅ 提取完成: {sys.argv[2]}")
        print(f"   长度: {len(text)} 字符")
    else:
        print(text)
