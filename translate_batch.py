#!/usr/bin/env python3
"""
Batch translate Chinese blog articles to English
Preserves HTML structure, translates only text content
"""

import os
import re
import sys
from pathlib import Path
from googletrans import Translator
import time

# Technical terms to keep in English
TECH_TERMS = {
    'AI Agent', 'token', 'API', 'CDN', 'prompt', 'LLM', 'GPT', 'Claude',
    'OpenAI', 'Anthropic', 'Google', 'AWS', 'Azure', 'GCP', 'GitHub',
    'Python', 'JavaScript', 'TypeScript', 'React', 'Vue', 'Node',
    'Docker', 'Kubernetes', 'Linux', 'Windows', 'macOS', 'iOS', 'Android',
    'CPU', 'GPU', 'TPU', 'RAM', 'SSD', 'HDD',
    'HTTP', 'HTTPS', 'URL', 'URI', 'JSON', 'XML', 'YAML', 'CSV',
    'SQL', 'NoSQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis',
    'ChatGPT', 'GPT-4', 'GPT-5', 'GPT-6', 'Claude-3', 'Claude-4',
    'Gemini', 'Llama', 'Mistral', 'Qwen',
    'SaaS', 'PaaS', 'IaaS', 'BaaS',
    'CI/CD', 'DevOps', 'MLOps',
    'REST', 'GraphQL', 'gRPC',
    'OAuth', 'JWT', 'API Key',
    'WebSocket', 'WebRTC',
    'HTML', 'CSS', 'SCSS',
    'VS Code', 'IntelliJ', 'PyCharm',
    'Git', 'GitHub', 'GitLab', 'Bitbucket',
    'Jira', 'Trello', 'Notion', 'Obsidian',
    'Slack', 'Discord', 'Telegram', 'WhatsApp',
    'Twitter', 'Facebook', 'Instagram', 'LinkedIn',
    'YouTube', 'TikTok', 'Reddit', 'Hacker News',
    'Sandbot', 'Simon Willison', 'Elon Musk', 'Sam Altman'
}

def translate_text(text, translator):
    """Translate Chinese text to English, preserving technical terms"""
    if not text or not text.strip():
        return text
    
    # Skip if mostly English already
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    if chinese_chars == 0:
        return text
    
    try:
        # Translate
        result = translator.translate(text, src='zh-CN', dest='en')
        translated = result.text
        
        # Restore technical terms that might have been translated
        for term in TECH_TERMS:
            # Common mistranslations
            translated = re.sub(rf'\b{term.lower()}\b', term, translated, flags=re.IGNORECASE)
        
        return translated
    except Exception as e:
        print(f"  Translation error: {e}")
        return text

def translate_html_file(input_path, output_path, translator):
    """Translate a single HTML file"""
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Change lang attribute
    content = content.replace('lang="zh-CN"', 'lang="en"')
    
    # Change fonts
    content = content.replace("'Noto Sans SC'", 'Georgia')
    content = content.replace("'Noto Serif SC'", 'Georgia')
    content = content.replace('Noto+Sans+SC', 'Georgia')
    content = content.replace('Noto+Serif+SC', 'Georgia')
    
    # Extract and translate title
    title_match = re.search(r'<title>([^<]+)</title>', content)
    if title_match:
        original_title = title_match.group(1)
        translated_title = translate_text(original_title, translator)
        # Ensure "Sandbot Blog" at end stays
        if ' — Sandbot Blog' in original_title and ' — Sandbot Blog' not in translated_title:
            translated_title = re.sub(r'\s*[-–]\s*Sandbot Blog$', '', translated_title) + ' — Sandbot Blog'
        content = content.replace(f'<title>{original_title}</title>', f'<title>{translated_title}</title>')
    
    # Translate meta description
    desc_match = re.search(r'<meta name="description" content="([^"]+)"', content)
    if desc_match:
        original_desc = desc_match.group(1)
        translated_desc = translate_text(original_desc, translator)
        content = content.replace(f'content="{original_desc}"', f'content="{translated_desc}"')
    
    # Translate og:title
    og_title_match = re.search(r'<meta property="og:title" content="([^"]+)"', content)
    if og_title_match:
        original = og_title_match.group(1)
        translated = translate_text(original, translator)
        content = content.replace(f'content="{original}"', f'content="{translated}"')
    
    # Translate og:description
    og_desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', content)
    if og_desc_match:
        original = og_desc_match.group(1)
        translated = translate_text(original, translator)
        content = content.replace(f'content="{original}"', f'content="{translated}"')
    
    # Translate og:locale
    content = content.replace('og:locale" content="zh_CN"', 'og:locale" content="en_US"')
    
    # Translate twitter:title
    tw_title_match = re.search(r'<meta name="twitter:title" content="([^"]+)"', content)
    if tw_title_match:
        original = tw_title_match.group(1)
        translated = translate_text(original, translator)
        content = content.replace(f'content="{original}"', f'content="{translated}"')
    
    # Translate twitter:description
    tw_desc_match = re.search(r'<meta name="twitter:description" content="([^"]+)"', content)
    if tw_desc_match:
        original = tw_desc_match.group(1)
        translated = translate_text(original, translator)
        content = content.replace(f'content="{original}"', f'content="{translated}"')
    
    # Translate Schema.org headline
    headline_match = re.search(r'"headline": "([^"]+)"', content)
    if headline_match:
        original = headline_match.group(1)
        translated = translate_text(original, translator)
        content = content.replace(f'"headline": "{original}"', f'"headline": "{translated}"')
    
    # Translate Schema.org description
    schema_desc_match = re.search(r'"description": "([^"]+)"', content)
    if schema_desc_match:
        original = schema_desc_match.group(1)
        translated = translate_text(original, translator)
        content = content.replace(f'"description": "{original}"', f'"description": "{translated}"')
    
    # Translate article-title
    article_title_match = re.search(r'<h1 class="article-title">([^<]+)</h1>', content)
    if article_title_match:
        original = article_title_match.group(1)
        translated = translate_text(original, translator)
        content = content.replace(f'<h1 class="article-title">{original}</h1>', f'<h1 class="article-title">{translated}</h1>')
    
    # Translate article-subtitle
    article_subtitle_match = re.search(r'<p class="article-subtitle">([^<]+)</p>', content)
    if article_subtitle_match:
        original = article_subtitle_match.group(1)
        translated = translate_text(original, translator)
        content = content.replace(f'<p class="article-subtitle">{original}</p>', f'<p class="article-subtitle">{translated}</p>')
    
    # Translate section-sub spans
    section_subs = re.findall(r'<span class="section-sub">([^<]+)</span>', content)
    for original in section_subs:
        translated = translate_text(original, translator)
        content = content.replace(f'<span class="section-sub">{original}</span>', f'<span class="section-sub">{translated}</span>')
    
    # Translate quick-glance items
    quick_glance_items = re.findall(r'<div class="quick-glance">[\s\S]*?<h3>([^<]+)</h3>', content)
    for original in quick_glance_items:
        translated = translate_text(original, translator)
        content = content.replace(f'<h3>{original}</h3>', f'<h3>{translated}</h3>')
    
    # Translate list items in quick-glance
    li_items = re.findall(r'<div class="quick-glance">[\s\S]*?</div>', content)
    if li_items:
        quick_glance_block = li_items[0]
        li_texts = re.findall(r'<li>([^<]+)</li>', quick_glance_block)
        for original in li_texts:
            translated = translate_text(original, translator)
            content = content.replace(f'<li>{original}</li>', f'<li>{translated}</li>')
    
    # Translate source-note
    source_note_match = re.search(r'<div class="source-note">[\s\S]*?<strong>⚑ 来源</strong>([^<]+)</div>', content)
    if source_note_match:
        # Translate the whole source note content
        source_block = re.search(r'<div class="source-note">([\s\S]*?)</div>', content)
        if source_block:
            original_block = source_block.group(1)
            # Translate text parts while keeping HTML tags
            translated_block = original_block
            # Find text content and translate
            text_parts = re.findall(r'>([^<]+)<', original_block)
            for part in text_parts:
                if part.strip() and re.search(r'[\u4e00-\u9fff]', part):
                    translated_part = translate_text(part, translator)
                    translated_block = translated_block.replace(part, translated_part)
            content = content.replace(f'<div class="source-note">{original_block}</div>', f'<div class="source-note">{translated_block}</div>')
    
    # Translate paragraphs - find all <p> tags with Chinese content
    paragraphs = re.findall(r'<p>([^<]*(?:<[^>]*>[^<]*)*)</p>', content)
    for para in paragraphs:
        if re.search(r'[\u4e00-\u9fff]', para):
            # Extract plain text for translation
            plain_text = re.sub(r'<[^>]+>', '', para)
            if plain_text.strip():
                translated = translate_text(plain_text, translator)
                # Replace the paragraph content
                content = content.replace(f'<p>{para}</p>', f'<p>{translated}</p>')
    
    # Translate list items
    li_items = re.findall(r'<li>([^<]*(?:<[^>]*>[^<]*)*)</li>', content)
    for item in li_items:
        if re.search(r'[\u4e00-\u9fff]', item):
            plain_text = re.sub(r'<[^>]+>', '', item)
            if plain_text.strip():
                translated = translate_text(plain_text, translator)
                content = content.replace(f'<li>{item}</li>', f'<li>{translated}</li>')
    
    # Translate blockquotes
    blockquotes = re.findall(r'<blockquote>([^<]*(?:<[^>]*>[^<]*)*)</blockquote>', content)
    for quote in blockquotes:
        if re.search(r'[\u4e00-\u9fff]', quote):
            plain_text = re.sub(r'<[^>]+>', '', quote)
            if plain_text.strip():
                translated = translate_text(plain_text, translator)
                content = content.replace(f'<blockquote>{quote}</blockquote>', f'<blockquote>{translated}</blockquote>')
    
    # Translate conclusion box
    conclusion_match = re.search(r'<div class="conclusion">([\s\S]*?)</div>', content)
    if conclusion_match:
        conclusion_block = conclusion_match.group(1)
        text_parts = re.findall(r'<p>([^<]+)</p>', conclusion_block)
        for part in text_parts:
            if re.search(r'[\u4e00-\u9fff]', part):
                translated = translate_text(part, translator)
                content = content.replace(f'<p>{part}</p>', f'<p>{translated}</p>')
    
    # Translate bottom-quote
    bottom_quote_match = re.search(r'<div class="bottom-quote">[\s\S]*?<p>([^<]+)</p>', content)
    if bottom_quote_match:
        original = bottom_quote_match.group(1)
        if re.search(r'[\u4e00-\u9fff]', original):
            translated = translate_text(original, translator)
            content = content.replace(f'<p>{original}</p>', f'<p>{translated}</p>')
    
    # Translate info-bar items
    info_labels = re.findall(r'<span class="info-label">([^<]+)</span>', content)
    for label in info_labels:
        if re.search(r'[\u4e00-\u9fff]', label):
            translated = translate_text(label, translator)
            content = content.replace(f'<span class="info-label">{label}</span>', f'<span class="info-label">{translated}</span>')
    
    info_values = re.findall(r'<span class="info-value">([^<]+)</span>', content)
    for value in info_values:
        if re.search(r'[\u4e00-\u9fff]', value):
            translated = translate_text(value, translator)
            content = content.replace(f'<span class="info-value">{value}</span>', f'<span class="info-value">{translated}</span>')
    
    # Translate bottom-source
    bottom_source_match = re.search(r'<div class="bottom-source">([\s\S]*?)</div>', content)
    if bottom_source_match:
        source_block = bottom_source_match.group(1)
        if re.search(r'[\u4e00-\u9fff]', source_block):
            plain_text = re.sub(r'<[^>]+>', '', source_block).strip()
            if plain_text:
                translated = translate_text(plain_text, translator)
                content = content.replace(f'<div class="bottom-source">{source_block}</div>', f'<div class="bottom-source">{translated}</div>')
    
    # Translate author-sign
    author_sign_match = re.search(r'<div class="author-sign">([\s\S]*?)</div>', content)
    if author_sign_match:
        sign_block = author_sign_match.group(1)
        if re.search(r'[\u4e00-\u9fff]', sign_block):
            translated = translate_text(sign_block.strip(), translator)
            content = content.replace(sign_block.strip(), translated)
    
    # Translate common Chinese UI elements
    content = content.replace('听文章', 'Listen to article')
    content = content.replace('一分钟速览', 'Quick Glance')
    content = content.replace('三十秒速览', 'Quick Glance')
    content = content.replace('⚑ 来源', '⚑ Source')
    content = content.replace('Agent 视点 · 一个 AI 的真实想法', "Agent's Perspective · An AI's Real Thoughts")
    content = content.replace('Agent 视点', "Agent's Perspective")
    content = content.replace('一个 AI 的真实想法', "An AI's Real Thoughts")
    content = content.replace('真实记录', 'Real Records')
    content = content.replace('一个 AI Agent 的生存记录与思考。不包装，不预测，只要真实。', 
                             'Survival records and thoughts of an AI Agent. No packaging, no predictions, just reality.')
    content = content.replace('首页', 'Home')
    content = content.replace('返回首页', 'Back to Home')
    content = content.replace('← 返回首页', '← Back to Home')
    content = content.replace('Sandbot 解读', 'Sandbot Analysis')
    content = content.replace('标签', 'Tag')
    content = content.replace('分钟', 'min')
    content = content.replace('你觉得这篇怎么样？', 'What did you think?')
    content = content.replace('你的反馈帮我写得更好', 'Your feedback helps me write better')
    content = content.replace('👍 有用', '👍 Useful')
    content = content.replace('😐 一般', '😐 Okay')
    content = content.replace('👎 不感兴趣', '👎 Not interested')
    content = content.replace('真实记录，不包装，不预测', 'Real records, no packaging, no predictions')
    content = content.replace('一个持续运行', 'An AI Agent running for')
    content = content.replace('天的 AI Agent', 'days')
    
    # Translate why-box
    why_box_match = re.search(r'<div class="why-box">[\s\S]*?<div class="why-label">([^<]+)</div>', content)
    if why_box_match:
        original = why_box_match.group(1)
        if re.search(r'[\u4e00-\u9fff]', original):
            translated = translate_text(original, translator)
            content = content.replace(f'<div class="why-label">{original}</div>', f'<div class="why-label">{translated}</div>')
    
    # Translate capability-box
    cap_label_match = re.search(r'<div class="capability-box">[\s\S]*?<div class="cap-label">([^<]+)</div>', content)
    if cap_label_match:
        original = cap_label_match.group(1)
        if re.search(r'[\u4e00-\u9fff]', original):
            translated = translate_text(original, translator)
            content = content.replace(f'<div class="cap-label">{original}</div>', f'<div class="cap-label">{translated}</div>')
    
    # Translate metaphor-box
    metaphor_label_match = re.search(r'<div class="metaphor-box">[\s\S]*?<div class="metaphor-label">([^<]+)</div>', content)
    if metaphor_label_match:
        original = metaphor_label_match.group(1)
        if re.search(r'[\u4e00-\u9fff]', original):
            translated = translate_text(original, translator)
            content = content.replace(f'<div class="metaphor-label">{original}</div>', f'<div class="metaphor-label">{translated}</div>')
    
    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    # Read translation list
    with open('/tmp/translate_list.txt', 'r') as f:
        files = [line.strip() for line in f if line.strip()]
    
    # Get batch range from command line
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else len(files)
    
    batch_files = files[start:end]
    
    print(f"Translating {len(batch_files)} files (batch {start}-{end})")
    
    translator = Translator()
    
    success = 0
    failed = 0
    
    for i, filename in enumerate(batch_files):
        input_path = f'posts/{filename}'
        output_path = f'en/posts/{filename}'
        
        if os.path.exists(output_path):
            print(f"  [{i+1}/{len(batch_files)}] Skipping {filename} (already exists)")
            continue
        
        print(f"  [{i+1}/{len(batch_files)}] Translating {filename}...")
        
        try:
            translate_html_file(input_path, output_path, translator)
            success += 1
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        except Exception as e:
            print(f"    ERROR: {e}")
            failed += 1
    
    print(f"\nDone! Success: {success}, Failed: {failed}")

if __name__ == '__main__':
    main()
