#!/usr/bin/env python3
"""
Batch translate Chinese HTML blog posts to English using Qwen API.
"""

import os
import re
import sys
import time
import json
from pathlib import Path
import openai

# Configuration from openclaw.json
API_KEY = "sk-sp-3a3cc83013574bffbbfb707615433d95"
BASE_URL = "https://coding.dashscope.aliyuncs.com/v1"
MODEL = "qwen3.7-plus"

client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)

def translate_html_content(html_content, filename):
    """Translate Chinese HTML to English using Qwen API."""
    
    prompt = f"""You are a professional translator. Translate the following Chinese HTML blog post to English.

RULES:
1. Translate ALL Chinese text to English
2. Keep HTML structure/tags exactly the same
3. Keep technical terms in English: AI Agent, token, reasoning effort, API, CDN, RSS, etc.
4. Keep proper nouns: Nitter, XCancel, Twitter/X, Sandbot, HN, etc.
5. Keep URLs unchangeded
6. Keep code/JavaScript unchanged
7. Change lang="zh-CN" to lang="en"
8. Change 'Noto Serif SC' to Georgia
9. Change 'Noto Sans SC' to -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
10. Change og:locale from zh_CN to en_US
11. Update canonical URLs: /posts/ -> /en/posts/
12. Translate navigation: 首页->Home, RSS->RSS, 关于->About, 文章->Articles, 播客->Podcast
13. Translate UI: 听文章->Listen to article, 一分钟速览->One-Minute Overview, 来源->Source
14. Translate feedback buttons: 有用->Useful, 一般->Okay, 不感兴趣->Not Interested
15. Translate: 你觉得这篇怎么样？->What do you think of this article?
16. Translate: 你的反馈帮我写得更好->Your feedback helps me write better
17. Translate footer: 真实记录，不包装，不预测->Real records, no packaging, no predictions
18. Translate: 返回首页->Back to Home
19. Translate: Sandbot 解读->Sandbot Analysis

HTML content to translate:

{html_content}

Return ONLY the translated HTML, nothing else."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a professional Chinese-to-English translator. You translate HTML content while preserving all HTML tags, attributes, and structure. You only output the translated HTML, nothing else."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=16000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  ❌ API error: {e}")
        return None

def update_html_metadata(html_content):
    """Post-process: ensure metadata is correctly updated."""
    
    # Change lang="zh-CN" to lang="en"
    html_content = re.sub(r'lang="zh-CN"', 'lang="en"', html_content)
    
    # Update fonts
    html_content = re.sub(r"'Noto Serif SC'", "Georgia", html_content)
    html_content = re.sub(r'"Noto Serif SC"', "Georgia", html_content)
    html_content = re.sub(r"'Noto Sans SC'", "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", html_content)
    html_content = re.sub(r'"Noto Sans SC"', "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", html_content)
    
    # Update og:locale
    html_content = re.sub(r'og:locale" content="zh_CN"', 'og:locale" content="en_US"', html_content)
    
    # Update canonical URLs
    html_content = re.sub(
        r'href="https://sandbot\.cgfan\.com/posts/',
        'href="https://sandbot.cgfan.com/en/posts/',
        html_content
    )
    
    return html_content

def process_file(input_path, output_path, index, total):
    """Process a single file."""
    print(f"\n[{index}/{total}] 📄 {input_path.name}")
    
    # Read input
    with open(input_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Translate via API
    print(f"  🔄 Translating...")
    translated = translate_html_content(html_content, input_path.name)
    
    if translated is None:
        print(f"  ❌ Translation failed!")
        return False
    
    # Post-process metadata
    translated = update_html_metadata(translated)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(translated)
    
    print(f"  ✅ Saved: {output_path.name}")
    return True

def main():
    # Read file list
    with open('/tmp/en-batch3.txt', 'r') as f:
        files = [line.strip() for line in f if line.strip()]
    
    print(f"🚀 Translating {len(files)} files...")
    
    base_dir = Path('/home/node/.openclaw/workspace/sandbot-blog')
    input_dir = base_dir / 'posts'
    output_dir = base_dir / 'en' / 'posts'
    
    success = 0
    failed = []
    
    for i, filename in enumerate(files, 1):
        input_path = input_dir / filename
        output_path = output_dir / filename
        
        if not input_path.exists():
            print(f"  ⚠️  Not found: {input_path}")
            failed.append(filename)
            continue
        
        if process_file(input_path, output_path, i, len(files)):
            success += 1
        else:
            failed.append(filename)
        
        # Rate limiting - small delay between requests
        if i < len(files):
            time.sleep(1)
    
    print(f"\n{'='*50}")
    print(f"✅ Translated: {success}/{len(files)}")
    if failed:
        print(f"❌ Failed: {len(failed)}")
        for f in failed:
            print(f"   - {f}")

if __name__ == '__main__':
    main()
