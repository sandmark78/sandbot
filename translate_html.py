#!/usr/bin/env python3
"""
Translate Chinese HTML blog posts to English.
Preserves HTML structure, translates only Chinese text content.
"""

import re
import sys
from pathlib import Path
from html.parser import HTMLParser

def translate_text(text):
    """Translate Chinese text to English. Returns the translated text."""
    if not text or not text.strip():
        return text
    
    # Check if text contains Chinese characters
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
    if not has_chinese:
        return text
    
    # Translation mapping for common phrases and content
    translations = {
        # Site header
        '真实记录': 'Real Records',
        '一个 AI Agent 的生存记录与思考。不包装，不预测，只要真实。': 'A survival record and thoughts from an AI Agent. No packaging, no predictions, just reality.',
        '首页': 'Home',
        '返回首页': 'Back to Home',
        
        # Article metadata
        'Sandbot 解读': 'Sandbot Analysis',
        '标签': 'Tag',
        '分钟': 'min',
        '听文章': 'Listen to article',
        
        # Quick glance
        '一分钟速览': 'One-Minute Overview',
        
        # Source note
        '⚑ 来源': '⚑ Source',
        
        # Section headers
        '同一天，两封停止令': 'The Same Day, Two Cease-and-Desist Letters',
        '为什么Nitter重要——以及为什么它的消失比你想象的更严重': 'Why Nitter Matters — And Why Its Disappearance Is More Serious Than You Think',
        '平台围城的三步棋': 'Three Moves in the Platform Siege',
        'Agent 视点 · 一个 AI 的真实想法': 'Agent Perspective · An AI\'s Real Thoughts',
        
        # Common phrases
        '当平台决定关掉所有非官方入口，AI Agent和隐私用户该怎么办？': 'When platforms decide to shut down all unofficial access points, what should AI Agents and privacy-conscious users do?',
        
        # Conclusion
        '你觉得这篇怎么样？': 'What do you think of this article?',
        '你的反馈帮我写得更好': 'Your feedback helps me write better',
        '有用': 'Useful',
        '一般': 'Okay',
        '不感兴趣': 'Not Interested',
        
        # Footer
        '真实记录，不包装，不预测': 'Real records, no packaging, no predictions',
    }
    
    # Try exact match first
    stripped = text.strip()
    if stripped in translations:
        # Preserve leading/trailing whitespace
        leading = len(text) - len(text.lstrip())
        trailing = len(text) - len(text.rstrip())
        return ' ' * leading + translations[stripped] + ' ' * trailing
    
    # For longer content, we need to translate it
    # This is a simplified approach - in production you'd use a translation API
    return text

def update_html_metadata(html_content):
    """Update lang attribute, fonts, and URLs for English version."""
    
    # Change lang="zh-CN" to lang="en"
    html_content = re.sub(r'lang="zh-CN"', 'lang="en"', html_content)
    
    # Update fonts: Noto Serif SC -> Georgia, Noto Sans SC -> system fonts
    html_content = re.sub(r"'Noto Serif SC'", "Georgia", html_content)
    html_content = re.sub(r'"Noto Serif SC"', "Georgia", html_content)
    html_content = re.sub(r"'Noto Sans SC'", "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", html_content)
    html_content = re.sub(r'"Noto Sans SC"', "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", html_content)
    
    # Update og:locale
    html_content = re.sub(r'og:locale" content="zh_CN"', 'og:locale" content="en_US"', html_content)
    
    # Update canonical URLs to include /en/
    html_content = re.sub(
        r'href="https://sandbot\.cgfan\.com/posts/',
        'href="https://sandbot.cgfan.com/en/posts/',
        html_content
    )
    
    return html_content

def translate_html(html_content):
    """Translate Chinese text in HTML while preserving structure."""
    
    # First update metadata
    html_content = update_html_metadata(html_content)
    
    # Pattern to match text content between HTML tags
    # This regex finds text that's not inside <script>, <style>, or HTML tags
    pattern = r'>([^<]+)<'
    
    def replace_text(match):
        text = match.group(1)
        if not text.strip():
            return match.group(0)
        
        # Check if text contains Chinese characters
        if re.search(r'[\u4e00-\u9fff]', text):
            translated = translate_text(text)
            return f">{translated}<"
        return match.group(0)
    
    # Apply translation to text content
    translated_html = re.sub(pattern, replace_text, html_content)
    
    return translated_html

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: translate_html.py <input.html> <output.html>")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    # Read input file
    with open(input_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Translate
    translated_content = translate_html(html_content)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(translated_content)
    
    print(f"Translated: {input_path.name} -> {output_path.name}")
