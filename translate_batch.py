#!/usr/bin/env python3
"""Batch translate Chinese blog posts to English, preserving HTML structure."""

import os
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Comment
from deep_translator import GoogleTranslator

BASE_DIR = Path("/home/node/.openclaw/workspace/sandbot-blog")
POSTS_DIR = BASE_DIR / "posts"
OUT_DIR = BASE_DIR / "en" / "posts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

translator = GoogleTranslator(source='zh-CN', target='en')

# Tags whose text content should be translated
TEXT_TAGS = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'span', 'strong', 
             'em', 'a', 'div', 'blockquote', 'td', 'th', 'figcaption', 'dt', 'dd'}

# Tags to skip entirely
SKIP_TAGS = {'script', 'style', 'code', 'pre', 'svg', 'path', 'button', 'audio', 'source'}

def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def translate_chunk(text, retries=3):
    """Translate a chunk of Chinese text with retries."""
    if not text or not text.strip() or not has_chinese(text):
        return text
    
    for attempt in range(retries):
        try:
            result = translator.translate(text)
            return result if result else text
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"    WARN: Translation failed after {retries} attempts: {e}")
                return text

def translate_element_text(element):
    """Translate the direct text content of an element, preserving child tags."""
    new_children = []
    changed = False
    
    for child in element.children:
        if isinstance(child, Comment):
            new_children.append(child)
            continue
        
        if isinstance(child, NavigableString):
            text = str(child)
            if has_chinese(text) and text.strip():
                translated = translate_chunk(text)
                new_children.append(NavigableString(translated))
                changed = True
            else:
                new_children.append(child)
        else:
            # It's a Tag - recurse into it
            new_children.append(child)
    
    if changed:
        # Clear existing children and add new ones
        element.clear()
        for child in new_children:
            element.append(child)

def process_element(element, depth=0):
    """Recursively process an element and its children."""
    if element.name in SKIP_TAGS:
        return
    
    # Translate direct text nodes of this element
    translate_element_text(element)
    
    # Recurse into child elements
    for child in element.find_all(recursive=False):
        if child.name and child.name not in SKIP_TAGS:
            process_element(child, depth + 1)

def process_html(html_content, filename):
    """Process a single HTML file."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. Change lang attribute
    html_tag = soup.find('html')
    if html_tag:
        html_tag['lang'] = 'en'
    
    # 2. Translate <title>
    title = soup.find('title')
    if title and title.string and has_chinese(title.string):
        title.string = translate_chunk(title.string)
    
    # 3. Translate meta content (description, og:title, og:description, twitter:*)
    for meta in soup.find_all('meta'):
        content = meta.get('content', '')
        if content and has_chinese(content):
            prop = meta.get('property', '') or meta.get('name', '')
            if prop in ('description', 'og:title', 'og:description', 
                       'twitter:title', 'twitter:description'):
                meta['content'] = translate_chunk(content)
    
    # 4. Translate schema.org JSON-LD
    for script in soup.find_all('script', type='application/ld+json'):
        if script.string and has_chinese(script.string):
            script.string = translate_chunk(script.string)
    
    # 5. Translate body text - process the article and header sections
    body = soup.find('body')
    if body:
        # Process header
        header = body.find('header', class_='site-header')
        if header:
            process_element(header)
        
        # Process back-link
        for a in body.find_all('a', class_='back-link'):
            process_element(a)
        
        # Process article
        article = body.find('article')
        if article:
            process_element(article)
        
        # Process feedback section
        for fb in body.find_all('div', class_='article-feedback'):
            process_element(fb)
    
    # 6. Process footer
    footer = soup.find('footer', class_='site-footer')
    if footer:
        process_element(footer)
    
    # 7. Replace fonts in CSS
    for style in soup.find_all('style'):
        if style.string:
            css = style.string
            # Font replacements
            css = css.replace("'Noto Serif SC', serif", "Georgia, 'Times New Roman', serif")
            css = css.replace("'Noto Serif SC'", "Georgia")
            css = css.replace("'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif",
                             "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif")
            css = css.replace("'Noto Sans SC'", "system-ui, -apple-system, sans-serif")
            style.string = css
    
    # 8. Remove Google Fonts preconnect/link for Noto
    for link in soup.find_all('link'):
        href = link.get('href', '')
        if 'Noto' in href and 'googleapis' in href:
            link.decompose()
    for link in soup.find_all('link', rel='preconnect'):
        href = link.get('href', '')
        if 'googleapis' in href or 'gstatic' in href:
            link.decompose()
    
    # 9. Update og:locale
    for meta in soup.find_all('meta', attrs={'property': 'og:locale'}):
        if meta.get('content', '').startswith('zh'):
            meta['content'] = 'en_US'
    
    return str(soup)


def main():
    with open('/tmp/en-retry1.txt', 'r') as f:
        files = [line.strip() for line in f if line.strip()]
    
    print(f"=== Translating {len(files)} files ===\n")
    
    success = 0
    for i, filename in enumerate(files, 1):
        src_path = POSTS_DIR / filename
        dst_path = OUT_DIR / filename
        
        if not src_path.exists():
            print(f"[{i}/{len(files)}] SKIP: {filename} not found")
            continue
        
        print(f"[{i}/{len(files)}] {filename}")
        
        with open(src_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            translated = process_html(content, filename)
            
            with open(dst_path, 'w', encoding='utf-8') as f:
                f.write(translated)
            
            success += 1
            print(f"  -> OK ({len(translated)} bytes)")
        except Exception as e:
            print(f"  -> ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        # Rate limit between files
        if i < len(files):
            time.sleep(1)
    
    print(f"\n=== Done: {success}/{len(files)} files translated ===")


if __name__ == '__main__':
    main()
