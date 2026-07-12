#!/usr/bin/env python3
"""
独立播客生成器 - 双人对话风格
针对文章写专门的对话稿，不是复读
"""

import asyncio
import edge_tts
import os

OUTPUT_DIR = "/tmp/podcast2"
os.makedirs(OUTPUT_DIR, exist_ok=True)

MALE_VOICE = "zh-CN-YunxiNeural"
FEMALE_VOICE = "zh-CN-XiaoxiaoNeural"

# 独立播客稿：针对 Apple 起诉 OpenAI 的对话
# 风格：轻松聊天，大白话，有互动
SCRIPT = [
    # (speaker, text, emotion)
    ("bgm", "intro", None),  # 片头音乐
    
    ("male", "哈喽大家好，欢迎收听 Sandbot 播客。我是小明。", "cheerful"),
    ("female", "我是小沙！今天咱们聊个大事儿。", "cheerful"),
    ("male", "对，Apple 把 OpenAI 给告了！", "cheerful"),
    ("female", "这事儿可太有意思了。你知道吗，这不是一般的商业纠纷，这里面的瓜可多了。", "cheerful"),
    ("male", "来来来，我先给大家捋一捋。简单来说呢，Apple 说 OpenAI 偷了它的商业秘密。", "cheerful"),
    ("female", "等等，偷商业秘密？这可不是跳槽带走点经验那么简单啊。具体怎么偷的？", "curious"),
    ("male", "细节相当劲爆。第一个关键人物，Tang Tan，前 iPhone 和 Apple Watch 的设计副总裁。", "serious"),
    ("female", "副总裁级别？！那他知道的可太多了。", "surprised"),
    ("male", "对吧！Apple 说他跳槽到 OpenAI 之后，用 Apple 内部的项目代号去面试候选人。更离谱的是，他还让还在 Apple 工作的候选人，带着没发布的硬件到面试现场展示。", "serious"),
    ("female", "等等等等，我没听错吧？让在职员工带着没发布的硬件去面试？这不等于把 Apple 的秘密直接摆到 OpenAI 桌子上了吗？", "angry"),
    ("male", "就是啊！这已经不是脑子里记住点什么了，这是有组织的数据外泄。还有第二个人，工程师 Chang Liu。", "serious"),
    ("female", "他又干了啥？", "curious"),
    ("male", "这个人更狠。Apple 说他利用安全漏洞，离职之后还在下载机密文件。注意啊，是离职之后！这都快成黑客了。", "serious"),
    ("female", "我的天，这要是真的，那可触犯《经济间谍法》了。不过话说回来，OpenAI 为啥非要挖 Apple 的人呢？", "thoughtful"),
    ("male", "问到点子上了！这就要说到 OpenAI 的大动作了。你知道 OpenAI 花了多少钱收购 Jony Ive 的公司吗？", "cheerful"),
    ("female", "Jony Ive？设计 iPhone 的那个人？多少钱？", "surprised"),
    ("male", "65 亿美元！", "cheerful"),
    ("female", "六十五亿？！疯了疯了。所以 OpenAI 是要做硬件了？", "shocked"),
    ("male", "没错！OpenAI 不满足于只做 ChatGPT 了，它要做一个完整的 AI 硬件设备。而做硬件，最懂的就是 Apple 的人。", "thoughtful"),
    ("female", "原来如此。所以 Apple 这是在保护自己啊。Jony Ive 设计了多少代 iPhone，现在去帮 OpenAI 做硬件，Apple 能不急吗？", "thoughtful"),
    ("male", "对啊！而且你注意到没有，Apple 选的时间点特别有意思。正好是 OpenAI 准备发布首款消费硬件的时候。这明显是在杀鸡儆猴。", "cheerful"),
    ("female", "嗯，我觉得 Apple 是在告诉整个 AI 行业：软件你们随便搞，但硬件领域的商业秘密，碰不得。这是底线。", "serious"),
    ("male", "说得好。其实我觉得这事儿也反映了一个更大的趋势，AI 公司正在从纯软件走向物理世界。以前大家觉得 AI 就是聊天机器人，现在不一样了，AI 要有实体了。", "thoughtful"),
    ("female", "是啊，而且一旦涉及到硬件，涉及到物理世界，商业秘密就变得特别敏感。代码可以重写，但硬件设计、供应链关系、制造工艺，这些可不是拍拍脑袋就能想出来的。", "thoughtful"),
    ("male", "没错。所以我觉得这场官司，不管最后结果怎么样，都会成为 AI 行业的一个标志性事件。它定义了一个边界：人才可以流动，但商业秘密不能带走。", "serious"),
    ("female", "同意。对了，你知道 Hacker News 上这个话题有多火吗？928 分！评论区都吵翻了。", "cheerful"),
    ("male", "看到了，大家都在讨论人才流动和商业秘密的边界。有人说 Apple 是在保护创新，有人说这是在限制人才自由。你怎么看？", "curious"),
    ("female", "我觉得关键在于手段。跳槽没问题，但你不能让人家在职员工把没发布的硬件带到你的面试室里吧？这已经不是正常的人才竞争了，这是在窃取。", "serious"),
    ("male", "说得好！好了，今天我们就聊到这里。总结一下：Apple 起诉 OpenAI，表面是商业秘密纠纷，背后是 AI 行业从软件走向硬件的结构性冲突。", "cheerful"),
    ("female", "没错。提醒大家一句：以后跳槽的时候，记住，脑子里的东西可以带走，但公司的文件、硬件、代码，碰都不要碰。", "cheerful"),
    ("male", "好了，我们下期再见！", "cheerful"),
    ("female", "拜拜！", "cheerful"),
    
    ("bgm", "outro", None),  # 片尾音乐
]

def build_ssml(text, voice, style="cheerful"):
    """构建带情感的 SSML"""
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
            bgm_file = f"{OUTPUT_DIR}/bgm_{text}.mp3"
            audio_files.append(("bgm", bgm_file, text))
            continue
        
        voice = MALE_VOICE if speaker == "male" else FEMALE_VOICE
        output_file = f"{OUTPUT_DIR}/segment_{i:03d}.mp3"
        
        print(f"   [{i+1}/{len(SCRIPT)}] {speaker}: {text[:30]}...")
        
        await generate_segment(text, voice, emotion or "cheerful", output_file)
        audio_files.append(("voice", output_file, speaker))
    
    return audio_files

def concat_podcast(audio_files, output_file):
    """拼接所有音频片段"""
    print("\n🔧 拼接音频...")
    
    # 简单二进制拼接
    with open(output_file, 'wb') as outfile:
        for file_type, file_path, extra in audio_files:
            if file_type == "voice" and os.path.exists(file_path):
                with open(file_path, 'rb') as infile:
                    outfile.write(infile.read())
    
    size = os.path.getsize(output_file)
    print(f"✅ 播客生成完成: {output_file}")
    print(f"   大小: {size / 1024:.1f} KB ({size / 1024 / 1024:.2f} MB)")
    
    duration_sec = size * 8 / 48000
    print(f"   估计时长: {duration_sec / 60:.1f} 分钟")
    
    return True

async def main():
    audio_files = await generate_podcast()
    
    output_file = "/tmp/sandbot-gh/posts/audio/podcast-ep01-apple-vs-openai.mp3"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    if concat_podcast(audio_files, output_file):
        print(f"\n🎉 播客已保存到: {output_file}")
    else:
        print("\n❌ 拼接失败")

if __name__ == "__main__":
    asyncio.run(main())
