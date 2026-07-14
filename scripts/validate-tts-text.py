#!/usr/bin/env python3
"""
TTS 文本验证器
在生成音频之前检查文本是否有问题
用法: python3 validate-tts-text.py <input.txt>

检查项目:
1. HTML 标签残留
2. SSML 标签残留
3. 章节标题（不应该被读出）
4. icon-list 内容（带 emoji 的列表）
5. 音频播放器控制文字
6. 文本长度是否合理
"""

import re
import sys

def validate(text):
    issues = []
    
    # 1. HTML 标签
    html_tags = re.findall(r'<[a-z][^>]*>', text)
    if html_tags:
        issues.append(f"❌ HTML 标签残留: {html_tags[:5]}")
    
    # 2. SSML 标签
    ssml_tags = re.findall(r'<speak|<voice|<prosody|<break|<mstts', text)
    if ssml_tags:
        issues.append(f"❌ SSML 标签残留: {ssml_tags[:5]}")
    
    # 3. CSS 样式内容
    css_patterns = re.findall(r'font-family|background:|var\(--|border-radius|display:\s*flex', text)
    if css_patterns:
        issues.append(f"❌ CSS 样式内容: {css_patterns[:5]}")
    
    # 4. JavaScript 内容
    js_patterns = re.findall(r'function\s|document\.|window\.|addEventListener|const\s+\w+\s*=', text)
    if js_patterns:
        issues.append(f"❌ JavaScript 内容: {js_patterns[:5]}")
    
    # 5. 音频播放器控制文字
    audio_controls = re.findall(r'\d+:\d+/\d+:\d+|播放|暂停|进度条', text)
    if audio_controls:
        issues.append(f"❌ 音频控制文字: {audio_controls[:5]}")
    
    # 6. emoji（TTS 会乱读）- 只检测真正的 emoji，不误报中文
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"   # symbols & pictographs
        "\U0001F680-\U0001F6FF"   # transport & map
        "\U0001F1E0-\U0001F1FF"   # flags
        "\U00002702-\U000027B0"
        "\U0001F900-\U0001F9FF"   # supplemental symbols
        "\U00002600-\U000026FF"   # misc symbols
        "]+",
        flags=re.UNICODE
    )
    emojis = emoji_pattern.findall(text)
    if emojis:
        issues.append(f"⚠️ 包含 emoji（TTS 可能乱读）: {emojis[:5]}")
    
    # 7. 文本长度
    if len(text) < 100:
        issues.append(f"⚠️ 文本太短: {len(text)} 字符")
    elif len(text) > 10000:
        issues.append(f"⚠️ 文本太长: {len(text)} 字符（建议 < 8000）")
    
    # 8. 重复标题
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if len(lines) >= 2 and lines[0] == lines[1]:
        issues.append(f"⚠️ 标题重复: {lines[0][:50]}")
    
    return issues

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 validate-tts-text.py <input.txt>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        text = f.read()
    
    issues = validate(text)
    
    if issues:
        print(f"⚠️ 发现 {len(issues)} 个问题：")
        for issue in issues:
            print(f"  {issue}")
        sys.exit(1)
    else:
        print(f"✅ 文本验证通过（{len(text)} 字符）")
        sys.exit(0)
