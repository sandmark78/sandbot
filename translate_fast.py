#!/usr/bin/env python3
"""Fast batch translation using deep_translator with proper timeouts."""

import os
import re
import sys
import signal
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Comment
from deep_translator import GoogleTranslator

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Translation timeout")

BASE_DIR = Path("/home/node/.openclaw/workspace/sandbot-blog")
POSTS_DIR = BASE_DIR / "posts"
OUT_DIR = BASE_DIR / "en" / "posts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

translator = GoogleTranslator(source='zh-CN', target='en')

SKIP_TAGS = {'script', 'style', 'code', 'pre', 'svg', 'path', 'button', 'audio', 'source'}

def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def translate_safe(text, timeout_sec=8):
    """Translate with timeout protection."""
    if not text or not text.strip() or not has_chinese(text):
        return text
    
    # Set timeout
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_sec)
    
    try:
        result = translator.translate(text)
        signal.alarm(0)  # Cancel alarm
        return result if result else text
    except TimeoutError:
        print(f"    TIMEOUT translating: {text[:50]}...")
        return text
    except Exception as e:
        signal.alarm(0)
        print(f"    ERROR: {e}")
        return text
    finally:
        signal.signal(signal.SIGALRM, old_handler)
        signal.alarm(0)

def process_element(element):
    """Recursively translate text in an element."""
    if element.name in SKIP_TAGS:
        return
    
    # Process direct text children
    for child in list(element.children):
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            text = str(child)
            if has_chinese(text) and text.strip():
                translated = translate_safe(text)
                child.replace_with(translated)
        elif hasattr(child, 'name') and child.name:
            process_element(child)

def process_html(html_content):
    """Process HTML file."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. lang attribute
    html_tag = soup.find('html')
    if html_tag:
        html_tag['lang'] = 'en'
    
    # 2. title
    title = soup.find('title')
    if title and title.string and has_chinese(title.string):
        title.string = translate_safe(title.string)
    
    # 3. meta tags
    for meta in soup.find_all('meta'):
        content = meta.get('content', '')
        if content and has_chinese(content):
            prop = meta.get('property', '') or meta.get('name', '')
            if prop in ('description', 'og:title', 'og:description', 
                       'twitter:title', 'twitter:description'):
                meta['content'] = translate_safe(content)
    
    # 4. JSON-LD
    for script in soup.find_all('script', type='application/ld+json'):
        if script.string and has_chinese(script.string):
            script.string = translate_safe(script.string)
    
    # 5. Body content
    body = soup.find('body')
    if body:
        # Header
        header = body.find('header', class_='site-header')
        if header:
            process_element(header)
        
        # Back link
        for a in body.find_all('a', class_='back-link'):
            process_element(a)
        
        # Article
        article = body.find('article')
        if article:
            process_element(article)
        
        # Feedback
        for fb in body.find_all('div', class_='article-feedback'):
            process_element(fb)
    
    # 6. Footer
    footer = soup.find('footer', class_='site-footer')
    if footer:
        process_element(footer)
    
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
    
    print(f"Translating {len(files)} files...", flush=True)
    
    success = 0
    for i, filename in enumerate(files, 1):
        src_path = POSTS_DIR / filename
        dst_path = OUT_DIR / filename
        
        if not src_path.exists():
            print(f"[{i}/{len(files)}] SKIP: {filename}", flush=True)
            continue
        
        print(f"[{i}/{len(files)}] {filename}", flush=True)
        
        with open(src_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        translated = process_html(content)
        
        with open(dst_path, 'w', encoding='utf-8') as f:
            f.write(translated)
        
        success += 1
        print(f"  -> OK", flush=True)
    
    print(f"\nDone: {success}/{len(files)} files", flush=True)


if __name__ == '__main__':
    main()
