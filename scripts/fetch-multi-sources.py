#!/usr/bin/env python3
"""
多源热点抓取脚本
从 HN、Reddit、AI HOT 等多个来源抓取热点话题
"""
import json
import sys
from datetime import datetime
from pathlib import Path
# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# AI/科技关键词（用于加权筛选）
AI_TECH_KEYWORDS = [
    'ai', 'artificial intelligence', 'machine learning', 'deep learning', 'llm', 'gpt', 'claude',
    'openai', 'anthropic', 'google ai', 'meta ai', 'microsoft ai', 'nvidia', 'amd', 'intel',
    'transformer', 'neural network', 'model', 'training', 'inference', 'gpu', 'tpu',
    'autonomous', 'agent', 'robotics', 'self-driving', 'chip', 'semiconductor',
    'cloud', 'aws', 'azure', 'gcp', 'kubernetes', 'docker', 'serverless',
    'blockchain', 'crypto', 'bitcoin', 'ethereum', 'web3',
    'cybersecurity', 'security', 'privacy', 'encryption', 'vulnerability',
    'startup', 'funding', 'acquisition', 'ipo', 'valuation',
    '开源', '人工智能', '机器学习', '深度学习', '大模型', '芯片', '半导体'
]

# 科技大佬关键词（最高优先级）
TECH_LEADER_KEYWORDS = [
    # 英文名
    'elon musk', 'musk', 'tesla', 'spacex', 'twitter', 'x.com',
    'jensen huang', 'nvidia ceo', '黄仁勋',
    'sam altman', 'openai ceo',
    'dario amodei', 'anthropic ceo',
    'mark zuckerberg', 'zuckerberg', 'meta ceo', 'facebook ceo',
    'satya nadella', 'microsoft ceo',
    'sundar pichai', 'google ceo', 'alphabet ceo',
    'tim cook', 'apple ceo',
    'sundar pichai', 'google ceo',
    'jeff bezos', 'bezos', 'amazon ceo',
    'andy jassy', 'amazon ceo',
    'pat gelsinger', 'intel ceo',
    'lisa su', 'amd ceo',
    'demis hassabis', 'google deepmind',
    'ylecun', 'yan lecun', 'meta ai chief',
    # 中文名
    '马斯克', '黄仁勋', '扎克伯格', '纳德拉', '皮查伊', '库克', '贝佐斯',
    '李彦宏', '马云', '马化腾', '雷军', '刘强东', '张一鸣',
    '梁汝波', '杨元庆', '余承东'
]

def is_ai_tech_related(title):
    """判断标题是否与AI/科技相关"""
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in AI_TECH_KEYWORDS)

def is_leader_related(title):
    """判断标题是否涉及科技大佬"""
    title_lower = title.lower()
    return any(keyword.lower() in title_lower for keyword in TECH_LEADER_KEYWORDS)

def fetch_hn():
    """抓取 Hacker News 首页，优先大佬 > AI/科技 > 其他"""
    import urllib.request
    try:
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        with urllib.request.urlopen(url, timeout=10) as response:
            ids = json.loads(response.read())[:30]  # 抓取更多候选
        
        leader_stories = []
        ai_tech_stories = []
        other_stories = []
        
        for story_id in ids[:20]:  # 检查前20条
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            with urllib.request.urlopen(story_url, timeout=5) as resp:
                story = json.loads(resp.read())
                story_data = {
                    'title': story.get('title', ''),
                    'score': story.get('score', 0),
                    'url': story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                    'source': 'HN'
                }
                
                # 三级分类：大佬 > AI/科技 > 其他
                if is_leader_related(story_data['title']):
                    leader_stories.append(story_data)
                elif is_ai_tech_related(story_data['title']):
                    ai_tech_stories.append(story_data)
                else:
                    other_stories.append(story_data)
        
        # 优先级：大佬动态至少2条，AI/科技至少3条，不足再用其他补充
        result = leader_stories[:2]
        result.extend(ai_tech_stories[:3])
        if len(result) < 5:
            result.extend(other_stories[:5-len(result)])
        
        return result
    except Exception as e:
        print(f"HN 抓取失败: {e}", file=sys.stderr)
        return []

def main():
    output_file = Path(os.path.join(BLOG_ROOT, "hot-topics-multi.md"))
    
    print("📡 抓取多源热点...")
    
    hn_stories = fetch_hn()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# 多源热点素材 (生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n")
        
        f.write("## Hacker News Top 5\n\n")
        for i, story in enumerate(hn_stories, 1):
            f.write(f"### {i}. {story['title']}\n")
            f.write(f"- 分数: {story['score']}\n")
            f.write(f"- URL: {story['url']}\n")
            f.write(f"- 来源: {story['source']}\n")
            f.write(f"- 图片: none\n\n")
    
    print(f"✅ 已写入 {output_file}")
    print(f"   HN: {len(hn_stories)} 个话题")

if __name__ == "__main__":
    main()
