#!/usr/bin/env python3
"""Fast parallel translation - each invocation handles one file"""
import os
import re
import sys
from googletrans import Translator

def main():
    filename = sys.argv[1]
    input_path = f'posts/{filename}'
    output_path = f'en/posts/{filename}'
    
    if os.path.exists(output_path):
        sys.exit(0)
    
    translator = Translator()
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Structural changes
    content = content.replace('lang="zh-CN"', 'lang="en"')
    content = content.replace('og:locale" content="zh_CN"', 'og:locale" content="en_US"')
    content = content.replace("'Noto Sans SC'", 'Georgia')
    content = content.replace("'Noto Serif SC'", 'Georgia')
    content = content.replace('Noto+Sans+SC', 'Georgia')
    content = content.replace('Noto+Serif+SC', 'Georgia')
    content = re.sub(
        r'<link href="https://fonts\.googleapis\.com/css2\?family=[^"]*Noto[^"]*"[^>]*>',
        '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">',
        content
    )
    
    # Collect all Chinese text segments
    segments = set()
    for match in re.finditer(r'>([^<]+)<', content):
        text = match.group(1).strip()
        if text and re.search(r'[\u4e00-\u9fff]', text):
            segments.add(text)
    for match in re.finditer(r'content="([^"]+)"', content):
        text = match.group(1).strip()
        if text and re.search(r'[\u4e00-\u9fff]', text) and len(text) > 3:
            segments.add(text)
    
    # Translate all segments
    translations = {}
    for seg in segments:
        try:
            result = translator.translate(seg, src='zh-CN', dest='en')
            translations[seg] = result.text.strip()
        except:
            translations[seg] = seg
    
    # Apply translations (longest first to avoid partial matches)
    for orig, trans in sorted(translations.items(), key=lambda x: -len(x[0])):
        content = content.replace(f'>{orig}<', f'>{trans}<')
        content = content.replace(f'"{orig}"', f'"{trans}"')
    
    # UI text replacements
    ui = {
        '听文章': 'Listen to article', '一分钟速览': 'Quick Glance',
        '三十秒速览': 'Quick Glance', '⚑ 来源': '⚑ Source',
        'Agent 视点 · 一个 AI 的真实想法': "Agent's Perspective · An AI's Real Thoughts",
        'Agent 视点': "Agent's Perspective", '一个 AI 的真实想法': "An AI's Real Thoughts",
        '真实记录': 'Real Records', '首页': 'Home', '返回首页': 'Back to Home',
        '← 返回首页': '← Back to Home', 'Sandbot 解读': 'Sandbot Analysis',
        '标签': 'Tag', '分钟': 'min read', '你觉得这篇怎么样？': 'What did you think?',
        '你的反馈帮我写得更好': 'Your feedback helps me write better',
        '👍 有用': '👍 Useful', '😐 一般': '😐 Okay', '👎 不感兴趣': '👎 Not interested',
        '真实记录，不包装，不预测': 'Real records, no packaging, no predictions',
        '一个持续运行': 'An AI Agent running for', '天的 AI Agent': 'days',
        '核心能力': 'Core Capabilities', '为什么值得看': 'Why It Matters',
    }
    for zh, en in ui.items():
        content = content.replace(zh, en)
    
    # Update URLs
    content = content.replace('href="https://sandbot.cgfan.com/posts/', 'href="https://sandbot.cgfan.com/en/posts/')
    content = content.replace('"mainEntityOfPage": "https://sandbot.cgfan.com/posts/', '"mainEntityOfPage": "https://sandbot.cgfan.com/en/posts/')
    content = content.replace('content="https://sandbot.cgfan.com/posts/', 'content="https://sandbot.cgfan.com/en/posts/')
    content = content.replace('../audio/', '../../audio/')
    content = content.replace('/sandbot/blog.html', '/sandbot/en/blog.html')
    
    os.makedirs('en/posts', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    main()
