#!/usr/bin/env python3
"""
Edge TTS 人味版 - SSML 模式
用法: python3 edge-tts-human.py <input.txt> <output.mp3> [voice] [style]

语音:
  zh-CN-YunxiNeural      男声（阳光、自然）- 默认
  zh-CN-XiaoxiaoNeural   女声（温暖、情感丰富）
  zh-CN-YunjianNeural    男声（新闻播报）
  zh-CN-YunyangNeural    男声（专业可靠）

风格:
  cheerful    欢快（默认）
  sad         悲伤
  angry       生气
  fearful     害怕
  enthusiastic 热情
  gentle      温柔
  lively      活泼
  serious     严肃

改进:
  - 段落间加 500ms 停顿
  - 句子间加 200ms 停顿
  - 语速 -15%（更自然）
  - 使用指定风格（更生动）
"""

import sys
import asyncio
import re
import edge_tts

def escape_xml(text):
    """转义 XML 特殊字符"""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    return text

def text_to_ssml(text, voice='zh-CN-YunxiNeural', style='cheerful'):
    """将纯文本转换为 SSML，添加停顿和情感"""
    # 转义 XML 特殊字符
    text = escape_xml(text)
    
    # 按段落分割
    paragraphs = re.split(r'\n\s*\n', text.strip())
    
    # 构建 SSML
    ssml_parts = [
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" ',
        'xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="zh-CN">',
        f'<voice name="{voice}">',
        f'<mstts:express-as style="{style}" styledegree="1.5">'
    ]
    
    for i, para in enumerate(paragraphs):
        if not para.strip():
            continue
        
        # 按句子分割（中文句号、问号、感叹号）
        sentences = re.split(r'([。！？])', para)
        
        # 重组句子
        sentence_list = []
        for j in range(0, len(sentences) - 1, 2):
            if j + 1 < len(sentences):
                sentence = sentences[j] + sentences[j + 1]
            else:
                sentence = sentences[j]
            if sentence.strip():
                sentence_list.append(sentence.strip())
        
        # 处理最后一个片段（可能没有标点）
        if len(sentences) % 2 == 0 and sentences[-1].strip():
            sentence_list.append(sentences[-1].strip())
        
        # 添加句子，句间加 200ms 停顿
        for j, sentence in enumerate(sentence_list):
            ssml_parts.append(sentence)
            if j < len(sentence_list) - 1:
                ssml_parts.append('<break time="200ms"/>')
        
        # 段落间加 500ms 停顿
        if i < len(paragraphs) - 1:
            ssml_parts.append('<break time="500ms"/>')
    
    ssml_parts.append('</mstts:express-as>')
    ssml_parts.append('</voice>')
    ssml_parts.append('</speak>')
    
    return ''.join(ssml_parts)

async def text_to_speech(text, output_file, voice='zh-CN-YunxiNeural', style='cheerful'):
    """生成语音（SSML 模式）"""
    # 转换为 SSML
    ssml = text_to_ssml(text, voice, style)
    
    # 使用 SSML 生成语音
    communicate = edge_tts.Communicate(ssml, voice=voice, rate='-15%')
    await communicate.save(output_file)
    return True

def main():
    if len(sys.argv) < 3:
        print("用法: python3 edge-tts-human.py <input.txt> <output.mp3> [voice] [style]")
        print("\n语音: zh-CN-YunxiNeural (男,默认), zh-CN-XiaoxiaoNeural (女)")
        print("风格: cheerful, sad, angry, fearful, enthusiastic, gentle, lively, serious")
        print("\n改进: 段落停顿 500ms, 句间停顿 200ms, 语速 -15%, 指定风格")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else 'zh-CN-YunxiNeural'
    style = sys.argv[4] if len(sys.argv) > 4 else 'cheerful'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    
    print(f"🎙️  生成人味语音（SSML 模式）...")
    print(f"   语音: {voice}")
    print(f"   风格: {style}")
    print(f"   文本: {len(text)} 字符")
    print(f"   改进: 段落停顿 500ms, 句间停顿 200ms, 语速 -15%")
    
    asyncio.run(text_to_speech(text, output_file, voice, style))
    
    import os
    size = os.path.getsize(output_file)
    print(f"✅ 已保存: {output_file}")
    print(f"   大小: {size / 1024:.1f} KB")

if __name__ == '__main__':
    main()
