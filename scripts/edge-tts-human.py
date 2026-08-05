#!/usr/bin/env python3
"""
Edge TTS 人味版 - 不使用 SSML
用法: python3 edge-tts-human.py <input.txt> <output.mp3> [voice] [rate]

语音:
  zh-CN-YunxiNeural      男声（阳光、自然）- 默认
  zh-CN-XiaoxiaoNeural   女声（温暖、情感丰富）
  zh-CN-YunjianNeural    男声（新闻播报）
  zh-CN-YunyangNeural    男声（专业可靠）

改进:
  - 段落间加停顿（用换行模拟）
  - 语速可调（默认 -10%）
"""

import sys
import asyncio
import edge_tts

async def text_to_speech(text, output_file, voice='zh-CN-YunxiNeural', rate='-10%'):
    """生成语音（不使用 SSML）"""
    # 直接使用纯文本，不用 SSML
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(output_file)
    return True

def main():
    if len(sys.argv) < 3:
        print("用法: python3 edge-tts-human.py <input.txt> <output.mp3> [voice] [rate]")
        print("\n语音: zh-CN-YunxiNeural (男,默认), zh-CN-XiaoxiaoNeural (女)")
        print("语速: -10% (默认), 可调整为 -20%, +10% 等")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else 'zh-CN-YunxiNeural'
    rate = sys.argv[4] if len(sys.argv) > 4 else '-10%'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    
    print(f"🎙️  生成语音（不使用 SSML）...")
    print(f"   语音: {voice}")
    print(f"   语速: {rate}")
    print(f"   文本: {len(text)} 字符")
    
    asyncio.run(text_to_speech(text, output_file, voice, rate))
    
    import os
    size = os.path.getsize(output_file)
    print(f"✅ 已保存: {output_file}")
    print(f"   大小: {size / 1024:.1f} KB")

if __name__ == '__main__':
    main()
