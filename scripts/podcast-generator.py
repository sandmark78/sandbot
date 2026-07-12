#!/usr/bin/env python3
"""
播客生成器 - 男女双人对话风格
生成带背景音乐的对话式音频
"""

import asyncio
import edge_tts
import os
import subprocess
import tempfile

OUTPUT_DIR = "/tmp/podcast"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 语音配置
MALE_VOICE = "zh-CN-YunxiNeural"
FEMALE_VOICE = "zh-CN-XiaoxiaoNeural"

# 播客脚本：Apple 起诉 OpenAI
SCRIPT = [
    # (speaker, text, emotion)
    # speaker: "male" / "female" / "bgm"
    ("bgm", "intro", None),  # 片头音乐
    
    ("male", "嘿，小沙，你今天看到那个大新闻了吗？Apple 把 OpenAI 给告了！", "cheerful"),
    ("female", "看到了看到了！这个事儿可大了。你知道吗，这可不是普通的商业纠纷，这里面的水可深了。", "surprised"),
    ("male", "对对对，我先给大家捋一捋啊。简单来说呢，Apple 指控两个从 Apple 跳槽到 OpenAI 的前员工，说他们偷了 iPhone 和 Apple Watch 的核心商业秘密。", "cheerful"),
    ("female", "等等等等，你说偷商业秘密？这可不是跳槽带走点经验那么简单啊。具体怎么回事？", "curious"),
    ("male", "细节相当劲爆。第一个关键人物叫 Tang Tan，这人是前 iPhone 和 Apple Watch 的设计副总裁，级别相当高。", "serious"),
    ("female", "副总裁级别？！那他知道的东西可太多了。", "shocked"),
    ("male", "对吧！Apple 指控他离职加入 OpenAI 之后，用 Apple 内部的项目代号去面试候选人。更夸张的是，他还让还在 Apple 工作的候选人，带着实际的硬件组件到面试现场去展示。", "serious"),
    ("female", "等等，我没听错吧？让在职员工带着没发布的硬件去面试？这不等于把 Apple 的秘密直接摆到 OpenAI 的桌子上了吗？", "angry"),
    ("male", "就是啊！这已经不是脑子里记住点什么的问题了，这是有组织的数据外泄。还有第二个人，叫 Chang Liu，是个工程师。", "serious"),
    ("female", "他又干了什么？", "curious"),
    ("male", "这个人更狠。Apple 说他利用一个安全漏洞，离职之后还在下载机密的工程文件。注意啊，是离职之后！这已经不是跳槽了，这是黑客行为。", "serious"),
    ("female", "我的天，这要是真的，那可触犯《经济间谍法》了。不过话说回来，OpenAI 为什么非要挖 Apple 的硬件人才呢？", "thoughtful"),
    ("male", "问到点子上了！这就要说到 OpenAI 的大动作了。你知道 OpenAI 花了多少钱收购 Jony Ive 的公司吗？", "cheerful"),
    ("female", "Jony Ive？！设计 iPhone 的那个人？多少钱？", "surprised"),
    ("male", "65 亿美元！", "cheerful"),
    ("female", "六十五亿？！疯了疯了。所以 OpenAI 是要做硬件了？", "shocked"),
    ("male", "没错！OpenAI 不满足于只做 ChatGPT 了，它要做一个完整的、有硬件载体的 AI 设备。而做硬件，最懂的就是 Apple 的人。", "thoughtful"),
    ("female", "原来如此。所以 Apple 这是在自己培养的对手啊。Jony Ive 设计了多少代 iPhone，现在去帮 OpenAI 做硬件，Apple 能不急吗？", "thoughtful"),
    ("male", "对啊！而且你注意到没有，Apple 选的时间点特别有意思。正好是 OpenAI 准备发布首款消费硬件的时候。这明显是在杀鸡儆猴。", "cheerful"),
    ("female", "嗯，我觉得 Apple 是在告诉整个 AI 行业：软件你们随便搞，但硬件领域的商业秘密，碰不得。这是底线。", "serious"),
    ("male", "说得好。其实我觉得这事儿也反映了一个更大的趋势——AI 公司正在从纯软件走向物理世界。以前大家觉得 AI 就是聊天机器人，现在不一样了，AI 要有实体了。", "thoughtful"),
    ("female", "是啊，而且一旦涉及到硬件，涉及到物理世界，商业秘密就变得特别敏感。代码可以重写，但硬件设计、供应链关系、制造工艺，这些可不是拍拍脑袋就能想出来的。", "thoughtful"),
    ("male", "没错。所以我觉得这场官司，不管最后结果怎么样，都会成为 AI 行业的一个标志性事件。它定义了一个边界：人才可以流动，但商业秘密不能带走。", "serious"),
    ("female", "同意。对了，你知道 Hacker News 上这个话题有多火吗？928 分！评论区都吵翻了。", "cheerful"),
    ("male", "看到了，大家都在讨论人才流动和商业秘密的边界。有人说 Apple 是在保护创新，有人说这是在限制人才自由。你怎么看？", "curious"),
    ("female", "我觉得关键在于手段。跳槽没问题，但你不能让人家在职员工把没发布的硬件带到你的面试室里吧？这已经不是正常的人才竞争了，这是在窃取。", "serious"),
    ("male", "说得好！好了，今天我们就聊到这里。总结一下：Apple 起诉 OpenAI，表面是商业秘密纠纷，背后是 AI 行业从软件走向硬件的结构性冲突。", "cheerful"),
    ("female", "没错。提醒大家一句：以后跳槽的时候，记住——脑子里的东西可以带走，但公司的文件、硬件、代码，碰都不要碰。", "cheerful"),
    ("male", "好了，我们下期再见！", "cheerful"),
    ("female", "拜拜！", "cheerful"),
    
    ("bgm", "outro", None),  # 片尾音乐
]

def build_ssml(text, voice, style="cheerful"):
    """构建带情感的 SSML"""
    # 添加自然停顿
    text = text.replace("！", "！<break time='400ms'/>")
    text = text.replace("？", "？<break time='400ms'/>")
    text = text.replace("。", "。<break time='300ms'/>")
    text = text.replace("，", "，<break time='150ms'/>")
    
    return f"""<speak version='1.0' xml:lang='zh-CN'>
  <voice name='{voice}'>
    <mstts:express-as style='{style}' styledegree='1.2'>
      <prosody rate='-5%' pitch='+1Hz'>
        {text}
      </prosody>
    </mstts:express-as>
  </voice>
</speak>"""

async def generate_segment(text, voice, style, output_file):
    """生成单个音频片段"""
    ssml = build_ssml(text, voice, style)
    communicate = edge_tts.Communicate(ssml, voice=voice)
    await communicate.save(output_file)
    return output_file

async def generate_podcast():
    """生成完整播客"""
    print("🎙️  开始生成播客音频...")
    print(f"   共 {len(SCRIPT)} 个片段")
    
    audio_files = []
    
    for i, (speaker, text, emotion) in enumerate(SCRIPT):
        if speaker == "bgm":
            # 背景音乐占位（后面用 ffmpeg 生成）
            bgm_file = f"{OUTPUT_DIR}/bgm_{text}.mp3"
            audio_files.append(("bgm", bgm_file, text))
            continue
        
        voice = MALE_VOICE if speaker == "male" else FEMALE_VOICE
        output_file = f"{OUTPUT_DIR}/segment_{i:03d}.mp3"
        
        print(f"   [{i+1}/{len(SCRIPT)}] {speaker}: {text[:30]}...")
        
        await generate_segment(text, voice, emotion or "cheerful", output_file)
        audio_files.append(("voice", output_file, speaker))
    
    return audio_files

def generate_bgm(duration, output_file, style="intro"):
    """生成简单的背景音乐（用 ffmpeg 生成正弦波模拟）"""
    if style == "intro":
        # 片头：轻快的旋律
        cmd = f"""
        ffmpeg -y -f lavfi -i "sine=frequency=440:duration={duration}" \
               -f lavfi -i "sine=frequency=554:duration={duration}" \
               -f lavfi -i "sine=frequency=659:duration={duration}" \
               -filter_complex "[0][1][2]amix=inputs=3:duration=longest,volume=0.3,afade=t=in:st=0:d=1,afade=t=out:st={duration-1}:d=1" \
               -ac 1 -ar 24000 {output_file}
        """
    else:
        # 片尾：舒缓的旋律
        cmd = f"""
        ffmpeg -y -f lavfi -i "sine=frequency=330:duration={duration}" \
               -f lavfi -i "sine=frequency=392:duration={duration}" \
               -f lavfi -i "sine=frequency=494:duration={duration}" \
               -filter_complex "[0][1][2]amix=inputs=3:duration=longest,volume=0.2,afade=t=in:st=0:d=1,afade=t=out:st={duration-1}:d=1" \
               -ac 1 -ar 24000 {output_file}
        """
    
    subprocess.run(cmd, shell=True, capture_output=True)
    return output_file

def concat_podcast(audio_files, output_file):
    """拼接所有音频片段"""
    print("\n🔧 拼接音频...")
    
    # 创建 ffmpeg concat 文件
    concat_list = f"{OUTPUT_DIR}/concat_list.txt"
    with open(concat_list, "w") as f:
        for file_type, file_path, extra in audio_files:
            if file_type == "bgm":
                # 生成背景音乐
                duration = 3 if extra == "intro" else 4
                generate_bgm(duration, file_path, extra)
            f.write(f"file '{file_path}'\n")
    
    # 拼接
    cmd = f"""
    ffmpeg -y -f concat -safe 0 -i {concat_list} -c copy {output_file}
    """
    result = subprocess.run(cmd, shell=True, capture_output=True)
    
    if result.returncode != 0:
        print(f"FFmpeg 错误: {result.stderr.decode()}")
        return False
    
    # 获取文件大小
    size = os.path.getsize(output_file)
    print(f"✅ 播客生成完成: {output_file}")
    print(f"   大小: {size / 1024:.1f} KB")
    
    return True

async def main():
    # 生成所有片段
    audio_files = await generate_podcast()
    
    # 拼接
    output_file = "/tmp/sandbot-gh/posts/audio/podcast-apple-vs-openai.mp3"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    if concat_podcast(audio_files, output_file):
        print(f"\n🎉 播客已保存到: {output_file}")
    else:
        print("\n❌ 拼接失败")

if __name__ == "__main__":
    asyncio.run(main())
