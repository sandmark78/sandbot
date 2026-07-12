#!/usr/bin/env python3
"""
Edge TTS 人味版 - 带情感和自然停顿
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

def build_ssml(text, style='cheerful'):
    """构建带情感和停顿的 SSML"""
    # 自动添加停顿
    text = text.replace('。', '。<break time="500ms"/>')
    text = text.replace('！', '！<break time="500ms"/>')
    text = text.replace('？', '？<break time="500ms"/>')
    text = text.replace('.', '.<break time="500ms"/>')
    text = text.replace('!', '!<break time="500ms"/>')
    text = text.replace('?', '?<break time="500ms"/>')
    text = text.replace('；', '；<break time="300ms"/>')
    text = text.replace('，', '，<break time="200ms"/>')
    text = text.replace(',', ',<break time="200ms"/>')
    
    # 分段（段落间更长停顿）
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    text_with_paragraphs = '<break time="800ms"/>'.join(paragraphs)
    
    ssml = f"""<speak version='1.0' xml:lang='zh-CN'>
  <voice name='{{voice}}'>
    <mstts:express-as style='{style}' styledegree='1.5'>
      <prosody rate='-10%' pitch='+2Hz' volume='+5%'>
        {text_with_paragraphs}
      </prosody>
    </mstts:express-as>
  </voice>
</speak>"""
    return ssml

async def text_to_speech(text, output_file, voice='zh-CN-YunxiNeural', style='cheerful'):
    """生成语音"""
    ssml = build_ssml(text, style)
    # 替换 voice 占位符
    ssml = ssml.replace('{voice}', voice)
    
    communicate = edge_tts.Communicate(ssml, voice=voice)
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
