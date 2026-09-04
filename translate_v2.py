#!/usr/bin/env python3
"""Batch translate Chinese blog posts to English with robust retry and rate limiting."""

import os
import re
import sys
import time
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Comment
from deep_translator import GoogleTranslator

BASE_DIR = Path("/home/node/.openclaw/workspace/sandbot-blog")
POSTS_DIR = BASE_DIR / "posts"
OUT_DIR = BASE_DIR / "en" / "posts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SKIP_TAGS = {'script', 'style', 'code', 'pre', 'svg', 'path', 'button', 'audio', 'source'}

def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def translate_chunk(text, max_retries=5):
    """Translate with exponential backoff retry."""
    if not text or not text.strip() or not has_chinese(text):
        return text
    
    for attempt in range(max_retries):
        try:
            translator = GoogleTranslator(source='zh-CN', target='en')
            result = translator.translate(text)
            if result:
                return result
            # Empty result - retry
            time.sleep(1)
        except Exception as e:
            wait = min(2 ** attempt, 10)
            time.sleep(wait)
    
    # All retries failed
    print(f"    WARN: Failed to translate: {text[:40]}...", flush=True)
    return text

def translate_in_element(element, depth=0):
    """Translate all text nodes within an element tree."""
    if element.name in SKIP_TAGS:
        return
    
    for child in list(element.children):
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            text = str(child)
            if has_chinese(text) and text.strip():
                translated = translate_chunk(text)
                child.replace_with(translated)
                # Rate limit between translations
                time.sleep(0.3)
        elif hasattr(child, 'name') and child.name:
            translate_in_element(child, depth + 1)

def process_html(html_content, filename):
    """Process a single HTML file."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. lang attribute
    html_tag = soup.find('html')
    if html_tag:
        html_tag['lang'] = 'en'
    
    # 2. title
    title = soup.find('title')
    if title and title.string and has_chinese(title.string):
        title.string = translate_chunk(title.string)
        time.sleep(0.3)
    
    # 3. meta tags
    for meta in soup.find_all('meta'):
        content = meta.get('content', '')
        if content and has_chinese(content):
            prop = meta.get('property', '') or meta.get('name', '')
            if prop in ('description', 'og:title', 'og:description',
                       'twitter:title', 'twitter:description'):
                meta['content'] = translate_chunk(content)
                time.sleep(0.3)
    
    # 4. JSON-LD - translate individual fields
    for script in soup.find_all('script', type='application/ld+json'):
        if script.string and has_chinese(script.string):
            # Parse and translate fields individually
            import json
            try:
                data = json.loads(script.string)
                if 'headline' in data and has_chinese(data['headline']):
                    data['headline'] = translate_chunk(data['headline'])
                    time.sleep(0.3)
                if 'description' in data and has_chinese(data['description']):
                    data['description'] = translate_chunk(data['description'])
                    time.sleep(0.3)
                script.string = json.dumps(data, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                # Fallback: translate whole thing
                script.string = translate_chunk(script.string)
                time.sleep(0.3)
    
    # 5. Body content
    body = soup.find('body')
    if body:
        header = body.find('header', class_='site-header')
        if header:
            translate_in_element(header)
        
        for a in body.find_all('a', class_='back-link'):
            translate_in_element(a)
        
        article = body.find('article')
        if article:
            translate_in_element(article)
        
        for fb in body.find_all('div', class_='article-feedback'):
            translate_in_element(fb)
    
    # 6. Footer
    footer = soup.find('footer', class_='site-footer')
    if footer:
        translate_in_element(footer)
    
    # 7. CSS font replacement
    for style in soup.find_all('style'):
        if style.string:
            css = style.string
            css = css.replace("'Noto Serif SC', serif", "Georgia, 'Times New Roman', serif")
            css = css.replace("'Noto Serif SC'", "Georgia")
            css = css.replace("'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif",
                             "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif")
            css = css.replace("'Noto Sans SC'", "system-ui, -apple-system, sans-serif")
            style.string = css
    
    # 8. Remove Google Fonts links
    for link in soup.find_all('link'):
        href = link.get('href', '')
        if 'Noto' in href and ('googleapis' in href or 'gstatic' in href):
            link.decompose()
    for link in soup.find_all('link', rel='preconnect'):
        href = link.get('href', '')
        if 'googleapis' in href or 'gstatic' in href:
            link.decompose()
    
    # 9. og:locale
    for meta in soup.find_all('meta', attrs={'property': 'og:locale'}):
        if meta.get('content', '').startswith('zh'):
            meta['content'] = 'en_US'
    
    return str(soup)


def main():
    with open('/tmp/en-retry1.txt', 'r') as f:
        files = [line.strip() for line in f if line.strip()]
    
    print(f"=== Translating {len(files)} files ===", flush=True)
    
    success = 0
    for i, filename in enumerate(files, 1):
        src_path = POSTS_DIR / filename
        dst_path = OUT_DIR / filename
        
        if not src_path.exists():
            print(f"[{i}/{len(files)}] SKIP: {filename}", flush=True)
            continue
        
        print(f"[{i}/{len(files)}] {filename}", flush=True)
        start_time = time.time()
        
        with open(src_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        translated = process_html(content, filename)
        
        with open(dst_path, 'w', encoding='utf-8') as f:
            f.write(translated)
        
        elapsed = time.time() - start_time
        success += 1
        print(f"  -> OK ({elapsed:.1f}s)", flush=True)
        
        # Pause between files
        if i < len(files):
            time.sleep(1)
    
    print(f"\n=== Done: {success}/{len(files)} files ===", flush=True)


if __name__ == '__main__':
    main()
