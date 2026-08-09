#!/usr/bin/env python3
"""
文章质量LLM评分
用法: python3 article-quality-score.py <article-file>
返回: 0=通过(>=70分), 1=不通过(<70分)

评分维度（10个，每个10分，总分100）：
1. 选题价值 2. 标题吸引力 3. 开头质量 4. 结构逻辑 5. 数据支撑
6. Agent视角深度 7. 实操价值 8. 语言质量 9. 结尾质量 10. 整体独特性
"""

import sys
import os
import re
import json
import urllib.request
import urllib.error
from datetime import datetime

RECENT_IMPROVEMENTS_FILE = "/home/node/.openclaw/workspace/sandbot-blog/posts/recent-improvements.json"

def extract_text(filepath):
    """提取文章纯文本（去掉HTML标签、header/footer/nav）"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    article_match = re.search(r'<article[^>]*>(.*?)</article>', content, re.DOTALL)
    article_html = article_match.group(1) if article_match else content
    
    for tag in ['header', 'footer', 'nav', 'audio-player', 'article-feedback', 'tip-jar', 'subscribe-banner']:
        article_html = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', article_html, flags=re.DOTALL)
    
    text = re.sub(r'<[^>]+>', ' ', article_html)
    text = re.sub(r'\s+', ' ', text).strip()
    
    if len(text) > 8000:
        text = text[:8000] + '...'
    
    return text

def call_llm(text, api_key):
    """调用LLM评分"""
    prompt = f"""你是一个严格的文章质量评审员。请对以下AI Agent写的博客文章进行评分。

评分维度（每个10分，总分100）：
1. 选题价值 - 是否切痛点、有观点空间、与AI Agent视角有交集
2. 标题吸引力 - 是否有观点/判断、有悬念/冲突、不是纯新闻标题
3. 开头质量 - 是否用场景切入、能否抓住读者
4. 结构逻辑 - 章节是否清晰、递进是否合理
5. 数据支撑 - 是否有具体数据/案例、不是泛泛而谈
6. Agent视角深度 - 是否有独特视角、不是新闻搬运
7. 实操价值 - 读者能带走什么、有框架/步骤/清单
8. 语言质量 - 是否简洁有力、没有废话/套话
9. 结尾质量 - 是否有金句/判断、不是空洞总结
10. 整体独特性 - 是否有不可替代的价值、不是信息搬运工

评分标准：
- 9-10分：优秀，有深度有洞察
- 7-8分：良好，有亮点但不够深
- 5-6分：一般，及格但无亮点
- 3-4分：较差，明显不足
- 1-2分：很差，严重问题

请输出JSON格式：
{{
  "scores": {{"选题价值": 8, "标题吸引力": 7, "开头质量": 8, "结构逻辑": 9, "数据支撑": 7, "Agent视角深度": 8, "实操价值": 6, "语言质量": 8, "结尾质量": 7, "整体独特性": 8}},
  "total": 73,
  "summary": "一句话总结文章优缺点",
  "improvements": ["改进建议1", "改进建议2"]
}}

文章内容：
{text}"""
    
    url = "https://coding.dashscope.aliyuncs.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "qwen3.7-plus",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1000,
        "enable_thinking": False
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            content = result["choices"][0]["message"]["content"]
            
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return None
    except Exception as e:
        print(f"❌ LLM调用失败: {e}")
        return None

def update_recent_improvements(filepath, result):
    """更新最近改进建议汇总文件"""
    # 读取现有文件
    if os.path.exists(RECENT_IMPROVEMENTS_FILE):
        with open(RECENT_IMPROVEMENTS_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []
    
    # 添加新记录
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "article": os.path.basename(filepath),
        "total": result.get("total", 0),
        "scores": result.get("scores", {}),
        "summary": result.get("summary", ""),
        "improvements": result.get("improvements", [])
    }
    history.append(entry)
    
    # 只保留最近20条
    if len(history) > 20:
        history = history[-20:]
    
    with open(RECENT_IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def main():
    if len(sys.argv) < 2:
        print("用法: python3 article-quality-score.py <article-file>")
        sys.exit(2)
    
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        sys.exit(2)
    
    # 从openclaw.json读取API key
    config_path = os.path.expanduser("~/.openclaw/openclaw.json")
    if not os.path.exists(config_path):
        print("❌ openclaw.json不存在")
        sys.exit(2)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    api_key = None
    providers = config.get('models', {}).get('providers', {})
    for provider in providers.values():
        if 'dashscope' in provider.get('baseUrl', ''):
            api_key = provider.get('apiKey')
            break
    
    if not api_key:
        print("❌ 找不到dashscope API key")
        sys.exit(2)
    
    # 提取文本
    text = extract_text(filepath)
    if len(text) < 500:
        print(f"❌ 文章内容太短: {len(text)}字符")
        sys.exit(1)
    
    # 调用LLM评分
    result = call_llm(text, api_key)
    
    if not result:
        print("❌ 评分失败")
        sys.exit(1)
    
    # 输出结果
    scores = result.get("scores", {})
    total = result.get("total", 0)
    summary = result.get("summary", "")
    improvements = result.get("improvements", [])
    
    print(f"📊 文章质量评分: {total}/100")
    print("")
    
    for dimension, score in scores.items():
        if score >= 9:
            icon = "✅"
        elif score >= 7:
            icon = "⚠️"
        else:
            icon = "❌"
        print(f"   {icon} {dimension}: {score}/10")
    
    print("")
    if summary:
        print(f"📝 {summary}")
        print("")
    
    if improvements:
        print("💡 改进建议:")
        for imp in improvements:
            print(f"   • {imp}")
        print("")
    
    # 保存评分结果到JSON
    result_file = filepath.replace('.html', '.score.json')
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"💾 评分详情已保存: {result_file}")
    
    # 更新最近改进建议汇总
    update_recent_improvements(filepath, result)
    print(f"📋 改进建议已汇总: {RECENT_IMPROVEMENTS_FILE}")
    
    if total >= 70:
        print(f"✅ 通过 (>=70分)")
        sys.exit(0)
    else:
        print(f"❌ 不通过 (<70分)")
        sys.exit(1)

if __name__ == '__main__':
    main()
