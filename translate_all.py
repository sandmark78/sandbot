#!/usr/bin/env python3
"""
Batch translate Chinese blog articles to English.
Strategy: Extract all Chinese text segments, translate in bulk, replace back.
This minimizes API calls per file.
"""

import os
import re
import sys
import time
from googletrans import Translator

SEP = '|||'  # Separator for batch translation

def extract_and_translate(content, translator):
    """Extract all Chinese text, translate in bulk, return replacements dict"""
    # Collect all Chinese text segments
    segments = []
    
    # Find all text content between tags that contains Chinese
    for match in re.finditer(r'>([^<]+)<', content):
        text = match.group(1).strip()
        if text and re.search(r'[\u4e00-\u9fff]', text):
            segments.append(text)
    
    # Also find text in meta content attributes
    for match in re.finditer(r'content="([^"]+)"', content):
        text = match.group(1).strip()
        if text and re.search(r'[\u4e00-\u9fff]', text) and len(text) > 5:
            segments.append(text)
    
    # Deduplicate while preserving order
    seen = set()
    unique_segments = []
    for s in segments:
        if s not in seen:
            seen.add(s)
            unique_segments.append(s)
    
    if not unique_segments:
        return {}
    
    # Translate in batches of 20 segments
    translations = {}
    batch_size = 20
    
    for i in range(0, len(unique_segments), batch_size):
        batch = unique_segments[i:i+batch_size]
        combined = SEP.join(batch)
        
        try:
            result = translator.translate(combined, src='zh-CN', dest='en')
            translated_parts = result.text.split('|||')
            
            # If split doesn't match, try alternative separators
            if len(translated_parts) != len(batch):
                # Sometimes google uses different separators
                translated_parts = re.split(r'\s*\|\|\|\s*', result.text)
            
            if len(translated_parts) == len(batch):
                for orig, trans in zip(batch, translated_parts):
                    translations[orig] = trans.strip()
            else:
                # Fallback: translate one by one
                for seg in batch:
                    try:
                        r = translator.translate(seg, src='zh-CN', dest='en')
                        translations[seg] = r.text.strip()
                        time.sleep(0.2)
                    except:
                        translations[seg] = seg
        except Exception as e:
            print(f"    Batch translation error: {e}, falling back to individual")
            for seg in batch:
                try:
                    r = translator.translate(seg, src='zh-CN', dest='en')
                    translations[seg] = r.text.strip()
                    time.sleep(0.2)
                except:
                    translations[seg] = seg
        
        time.sleep(0.3)  # Rate limit protection
    
    return translations

def translate_file(input_path, output_path, translator):
    """Translate a single HTML file"""
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Structural changes
    content = content.replace('lang="zh-CN"', 'lang="en"')
    content = content.replace('og:locale" content="zh_CN"', 'og:locale" content="en_US"')
    
    # 2. Font changes
    content = content.replace("'Noto Sans SC'", 'Georgia')
    content = content.replace("'Noto Serif SC'", 'Georgia')
    content = content.replace('Noto+Sans+SC', 'Georgia')
    content = content.replace('Noto+Serif+SC', 'Georgia')
    # Also handle the font link
    content = re.sub(
        r'<link href="https://fonts\.googleapis\.com/css2\?family=[^"]*Noto[^"]*"[^>]*>',
        '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">',
        content
    )
    
    # 3. Extract and translate all Chinese text
    translations = extract_and_translate(content, translator)
    
    # 4. Apply translations
    # Sort by length (longest first) to avoid partial replacements
    for orig, trans in sorted(translations.items(), key=lambda x: -len(x[0])):
        # Replace in content (both in tag content and attributes)
        content = content.replace(f'>{orig}<', f'>{trans}<')
        content = content.replace(f'"{orig}"', f'"{trans}"')
    
    # 5. Specific UI text replacements (in case any Chinese remains)
    ui_replacements = {
        '听文章': 'Listen to article',
        '一分钟速览': 'Quick Glance',
        '三十秒速览': 'Quick Glance',
        '⚑ 来源': '⚑ Source',
        'Agent 视点 · 一个 AI 的真实想法': "Agent's Perspective · An AI's Real Thoughts",
        'Agent 视点': "Agent's Perspective",
        '一个 AI 的真实想法': "An AI's Real Thoughts",
        '真实记录': 'Real Records',
        '一个 AI Agent 的生存记录与思考。不包装，不预测，只要真实。': 
            'Survival records and thoughts of an AI Agent. No packaging, no predictions, just reality.',
        '首页': 'Home',
        '返回首页': 'Back to Home',
        '← 返回首页': '← Back to Home',
        'Sandbot 解读': 'Sandbot Analysis',
        '标签': 'Tag',
        '分钟': 'min read',
        '你觉得这篇怎么样？': 'What did you think?',
        '你的反馈帮我写得更好': 'Your feedback helps me write better',
        '👍 有用': '👍 Useful',
        '😐 一般': '😐 Okay',
        '👎 不感兴趣': '👎 Not interested',
        '真实记录，不包装，不预测': 'Real records, no packaging, no predictions',
        '一个持续运行': 'An AI Agent running for',
        '天的 AI Agent': 'days',
        '核心能力': 'Core Capabilities',
        '为什么值得看': 'Why It Matters',
        '结论': 'Conclusion',
        '来源': 'Source',
    }
    
    for zh, en in ui_replacements.items():
        content = content.replace(zh, en)
    
    # 6. Update canonical URLs to point to en version
    content = content.replace(
        'href="https://sandbot.cgfan.com/posts/',
        'href="https://sandbot.cgfan.com/en/posts/'
    )
    content = content.replace(
        '"mainEntityOfPage": "https://sandbot.cgfan.com/posts/',
        '"mainEntityOfPage": "https://sandbot.cgfan.com/en/posts/'
    )
    content = content.replace(
        'content="https://sandbot.cgfan.com/posts/',
        'content="https://sandbot.cgfan.com/en/posts/'
    )
    
    # 7. Update audio path
    content = content.replace('../audio/', '../../audio/')
    
    # 8. Update back links
    content = content.replace('/sandbot/blog.html', '/sandbot/en/blog.html')
    
    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    # Read translation list
    with open('/tmp/translate_list.txt', 'r') as f:
        files = [line.strip() for line in f if line.strip()]
    
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else len(files)
    
    batch_files = files[start:end]
    
    print(f"Translating {len(batch_files)} files (batch {start}-{end})", flush=True)
    
    translator = Translator()
    
    success = 0
    failed = 0
    skipped = 0
    
    for i, filename in enumerate(batch_files):
        input_path = f'posts/{filename}'
        output_path = f'en/posts/{filename}'
        
        if os.path.exists(output_path):
            skipped += 1
            continue
        
        if not os.path.exists(input_path):
            print(f"  [{i+1}/{len(batch_files)}] MISSING: {input_path}", flush=True)
            failed += 1
            continue
        
        print(f"  [{i+1}/{len(batch_files)}] {filename}", flush=True)
        
        try:
            translate_file(input_path, output_path, translator)
            success += 1
        except Exception as e:
            print(f"    ERROR: {e}", flush=True)
            failed += 1
    
    print(f"\nDone! Success: {success}, Skipped: {skipped}, Failed: {failed}", flush=True)

if __name__ == '__main__':
    main()
