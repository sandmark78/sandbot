#!/usr/bin/env python3
"""
文章 TTS 生成脚本
用法: python3 generate-tts.py <article.html>

自动生成 zh-CN-YunxiNeural 音色的 MP3 音频
"""

import sys
import os
import re
import subprocess

def extract_text(html_file):
    """从 HTML 提取标题+正文（跳过元数据）"""
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 提取 article 标签内容
    match = re.search(r'<article>([\s\S]*?)</article>', html, re.IGNORECASE)
    if match:
        text = match.group(1)
    else:
        text = html
    
    # 提取标题
    title_match = re.search(r'<h1 class="article-title">(.*?)</h1>', text, re.IGNORECASE)
    title = ''
    if title_match:
        title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
    
    # 移除不需要的部分（元数据、速览、来源声明、音频播放器）
    text = re.sub(r'<div class="article-label">[\s\S]*?</div>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<div class="article-meta">[\s\S]*?</div>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<div class="quick-glance">[\s\S]*?</div>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<div class="source-note">[\s\S]*?</div>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<div class="audio-player">[\s\S]*?</div>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<script[\s\S]*?</script>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<style[\s\S]*?</style>', '', text, flags=re.IGNORECASE)
    
    # 处理标题标签（h2, h3）- 添加停顿
    text = re.sub(r'<h2[^>]*>[\s\S]*?</h2>', lambda m: '\n\n' + re.sub(r'<[^>]+>', '', m.group(0)) + '\n', text)
    text = re.sub(r'<h3[^>]*>[\s\S]*?</h3>', lambda m: '\n\n' + re.sub(r'<[^>]+>', '', m.group(0)) + '\n', text)
    
    # 处理列表项
    text = re.sub(r'<li[^>]*>([\s\S]*?)</li>', lambda m: re.sub(r'<[^>]+>', '', m.group(1)).strip() + '。', text)
    
    # 处理段落
    text = re.sub(r'<p[^>]*>([\s\S]*?)</p>', lambda m: re.sub(r'<[^>]+>', '', m.group(1)).strip() + '\n', text)
    
    # 移除剩余 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 解码 HTML 实体
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '和')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('&middot;', '·')
    
    # 清理空白
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()
    
    # 组合：标题 + 正文
    if title:
        result = title + '\n\n' + text
    else:
        result = text
    
    return result

def generate_tts(text_file, output_file, voice='zh-CN-YunxiNeural'):
    """调用 edge-tts 生成音频"""
    cmd = [
        'edge-tts',
        '--voice', voice,
        '--file', text_file,
        '--write-media', output_file
    ]
    
    print(f"🎙️ 音色: {voice}")
    print(f"📝 文本文件: {text_file}")
    print(f"🎵 输出文件: {output_file}")
    print()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ 失败: {result.stderr}")
        sys.exit(1)
    
    size = os.path.getsize(output_file)
    print(f"✅ 音频已生成: {output_file} ({size / 1024:.1f} KB)")

def main():
    if len(sys.argv) < 2:
        print("用法: python3 generate-tts.py <article.html>")
        print("      python3 generate-tts.py <article.html> zh-CN-YunjianNeural")
        print()
        print("可用音色:")
        print("  zh-CN-YunxiNeural    (年轻男性，有活力) ← 默认")
        print("  zh-CN-YunjianNeural  (成熟男性，稳重)")
        print("  zh-CN-XiaoyiNeural   (女性，活泼)")
        print("  zh-CN-YunyangNeural  (男性，新闻播报风)")
        sys.exit(1)
    
    html_file = sys.argv[1]
    voice = sys.argv[2] if len(sys.argv) > 2 else 'zh-CN-YunxiNeural'
    
    if not os.path.exists(html_file):
        print(f"❌ 文件不存在: {html_file}")
        sys.exit(1)
    
    # 提取文本
    text = extract_text(html_file)
    print(f"📝 提取文本: {len(text)} 字符")
    
    # 保存临时文本文件
    text_file = '/tmp/tts-text.txt'
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text)
    
    # 生成输出文件名
    base_name = os.path.splitext(os.path.basename(html_file))[0]
    output_file = os.path.join(os.path.dirname(html_file), f"{base_name}.mp3")
    
    # 生成 TTS
    generate_tts(text_file, output_file, voice)
    
    # 清理
    os.remove(text_file)
    
    print(f"✅ 完成")
    print(f"📎 音频路径: {output_file}")

if __name__ == '__main__':
    main()
