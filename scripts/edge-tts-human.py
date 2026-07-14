#!/usr/bin/env python3
"""
Edge TTS 人味版 - 纯文本模式
用法: python3 edge-tts-human.py <input.txt> <output.mp3> [voice] [style]

语音:
  zh-CN-YunxiNeural      男声（阳光、自然）
  zh-CN-XiaoxiaoNeural   女声（温暖、情感丰富）
  zh-CN-YunjianNeural    男声（新闻播报）

风格:
  cheerful    欢快（默认）
  sad         悲伤
  angry       生气
  fearful     害怕
  enthusiastic 热情
  gentle      温柔
  lively      活泼
  serious     严肃
"""

import sys
import asyncio
import edge_tts

async def text_to_speech(text, output_file, voice='zh-CN-YunxiNeural', style='cheerful'):
    """生成语音（纯文本模式，不使用 SSML）"""
    # 直接使用纯文本，不添加 SSML 标签
    communicate = edge_tts.Communicate(text, voice=voice, rate='-10%', pitch='+2Hz')
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
    
    print(f"🎙️  生成人味语音...")
    print(f"   语音: {voice}")
    print(f"   风格: {style}")
    print(f"   文本: {len(text)} 字符")
    
    asyncio.run(text_to_speech(text, output_file, voice, style))
    
    import os
    size = os.path.getsize(output_file)
    print(f"✅ 已保存: {output_file}")
    print(f"   大小: {size / 1024:.1f} KB")

if __name__ == '__main__':
    main()
