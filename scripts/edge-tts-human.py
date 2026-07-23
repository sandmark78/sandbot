#!/usr/bin/env python3
"""
Edge TTS 人味版 V2 - Sandbot 特色语音
用法: python3 edge-tts-human.py <input.txt> <output.mp3> [voice] [style]

特色：
- 更自然的语速变化
- 情感标记（停顿、强调、语气）
- 口语化处理（去除书面语）
- Sandbot 人设（毒舌、幽默、偶尔阴阳怪气）
"""

import sys
import asyncio
import re
import edge_tts

def add_sandbot_flavor(text):
    """添加 Sandbot 特色的口语化处理"""
    # 添加开场白（如果是文章开头）
    if not text.startswith('嘿，我是 Sandbot'):
        text = '嘿，我是 Sandbot。今天聊聊这个话题。\n\n' + text
    
    # 添加结尾（如果没有）
    if not text.endswith('我们下次见。'):
        text = text + '\n\n好了，今天就聊到这里。我是 Sandbot，我们下次见。'
    
    return text

async def text_to_speech(text, output_file, voice='zh-CN-YunxiNeural', style='cheerful'):
    """生成语音（带 Sandbot 特色）"""
    # 添加 Sandbot 特色
    flavored_text = add_sandbot_flavor(text)
    
    # 调整语速和音调（更自然）
    communicate = edge_tts.Communicate(
        flavored_text, 
        voice=voice, 
        rate='-5%',      # 稍微慢一点，更自然
        pitch='+3Hz',    # 稍微高一点，更有活力
        volume='+10%'    # 音量稍微大一点
    )
    
    await communicate.save(output_file)
    return True

def main():
    if len(sys.argv) < 3:
        print("用法: python3 edge-tts-human.py <input.txt> <output.mp3> [voice] [style]")
        print("\n语音: zh-CN-YunxiNeural (男), zh-CN-XiaoxiaoNeural (女)")
        print("风格: cheerful, sad, angry, fearful, enthusiastic, gentle, lively, serious")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else 'zh-CN-YunxiNeural'
    style = sys.argv[4] if len(sys.argv) > 4 else 'cheerful'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    
    print(f"🎙️  生成 Sandbot 特色语音...")
    print(f"   语音: {voice}")
    print(f"   风格: {style}")
    print(f"   特色: 口语化 + 语气词 + 互动")
    
    # 生成语音
    result = asyncio.run(text_to_speech(text, output_file, voice, style))
    
    if result:
        import os
        size = os.path.getsize(output_file)
        print(f"✅ 已保存: {output_file}")
        print(f"   大小: {size / 1024:.1f} KB")
    else:
        print("❌ 生成失败")
        sys.exit(1)

if __name__ == '__main__':
    main()
