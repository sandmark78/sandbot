#!/usr/bin/env python3
"""
去重检查 v2 — 实体+事件核心词匹配
用法: python3 check-recent-duplicates.py <候选标题> [候选摘要]
返回: 0=通过, 1=重复

改进点：
- 维护 written-events.json 已写事件列表（实体+事件摘要）
- 提取实体（公司/产品/人物）
- 提取事件核心词
- 不仅看标题字面相似度，还看核心事件是否相同
"""

import sys
import os
import re
import json
from datetime import datetime, timedelta
from difflib import SequenceMatcher

BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(BLOG_ROOT, "posts")
EVENTS_FILE = os.path.join(BLOG_ROOT, "topics", "written-events.json")

# 实体词典（公司/产品/人物）
ENTITIES = {
    # 公司
    "openai": ["OpenAI", "openai", "GPT", "ChatGPT"],
    "anthropic": ["Anthropic", "anthropic", "Claude"],
    "google": ["Google", "DeepMind", "Gemini"],
    "meta": ["Meta", "Llama", "Facebook"],
    "nvidia": ["NVIDIA", "英伟达", "nvidia"],
    "microsoft": ["Microsoft", "微软", "Copilot", "Cursor"],
    "apple": ["Apple", "苹果"],
    "amazon": ["Amazon", "亚马逊", "AWS"],
    "huggingface": ["Hugging Face", "HuggingFace", "huggingface"],
    "xiaomi": ["小米", "Xiaomi"],
    "alibaba": ["阿里", "Alibaba", "Qwen", "通义"],
    "xai": ["xAI", "Grok"],
    # 产品/技术
    "gpt6": ["GPT-6", "GPT6", "Astra"],
    "gpt5": ["GPT-5", "GPT5"],
    "claude": ["Claude", "claude"],
    "gemini": ["Gemini", "gemini"],
    "qwen": ["Qwen", "通义", "qwen"],
    "llama": ["Llama", "llama"],
    "grok": ["Grok", "grok"],
    "cursor": ["Cursor", "cursor"],
    "copilot": ["Copilot", "copilot"],
    "agent": ["Agent", "agent", "智能体"],
    "wiki": ["wiki", "Wiki", "维基百科"],
    "seo": ["SEO", "seo", "内容农场"],
    # 人物
    "musk": ["Musk", "马斯克", "Elon"],
    "altman": ["Altman", "Sam Altman"],
    "amodei": ["Amodei", "Dario"],
    "huang": ["黄仁勋", "Jensen Huang"],
}

STOP_WORDS = set('的 了 在 是 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 会 着 没有 看 好 自己 这 那 他 她 它 们 被 把 让 给 从 对 与 或 但 而 如果 因为 所以 虽然 然后 之后 已经 正在 可以 可能 应该 需要'.split())


def extract_entities(text):
    """提取文本中的实体"""
    text_lower = text.lower()
    found = set()
    for entity_id, keywords in ENTITIES.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                found.add(entity_id)
                break
    return found


def extract_keywords(text):
    """提取关键词（去停用词，细粒度分词）"""
    # 先提取英文单词和数字
    words = set(re.findall(r'[a-zA-Z0-9]+', text.lower()))
    # 再提取中文词组（2-4字）
    chinese_words = set(re.findall(r'[\u4e00-\u9fa5]{2,4}', text.lower()))
    all_words = (words | chinese_words) - STOP_WORDS
    # 过滤太短的词
    return {w for w in all_words if len(w) >= 2}


def load_written_events():
    """加载已写事件列表"""
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"events": []}


def save_written_events(data):
    """保存已写事件列表"""
    os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_recent_articles(days=7):
    """获取最近N天的文章"""
    cutoff_date = datetime.now() - timedelta(days=days)
    articles = []

    for filename in os.listdir(POSTS_DIR):
        if not filename.endswith('.html'):
            continue
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})', filename)
        if not date_match:
            continue
        file_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
        if file_date < cutoff_date:
            continue

        filepath = os.path.join(POSTS_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        title_match = re.search(r'<title>([^<]+)</title>', content)
        subtitle_match = re.search(r'class="article-subtitle"[^>]*>([^<]+)<', content)
        body_match = re.search(r'<article>(.*?)</article>', content, re.DOTALL)
        body_text = ''
        if body_match:
            body_text = re.sub(r'<[^>]+>', '', body_match.group(1))[:300]

        title = title_match.group(1).strip() if title_match else ''
        title = re.sub(r'\s*—\s*Sandbot Blog.*$', '', title)
        subtitle = subtitle_match.group(1).strip() if subtitle_match else ''

        articles.append({
            'filename': filename,
            'title': title,
            'subtitle': subtitle,
            'body_preview': body_text,
            'date': file_date,
            'entities': extract_entities(title + ' ' + subtitle + ' ' + body_text),
            'keywords': extract_keywords(title + ' ' + subtitle),
        })

    return articles


def check_duplicate(candidate_title, candidate_summary='', threshold=0.6):
    """检查候选选题是否重复"""
    articles = get_recent_articles(days=7)
    events = load_written_events()

    candidate_entities = extract_entities(candidate_title + ' ' + candidate_summary)
    candidate_keywords = extract_keywords(candidate_title + ' ' + candidate_summary)

    duplicates = []

    # 检查1: 和已写事件列表对比
    for event in events.get('events', []):
        event_entities = set(event.get('entities', []))
        event_keywords = extract_keywords(event.get('summary', ''))

        # 实体重叠
        entity_overlap = candidate_entities & event_entities
        keyword_overlap = candidate_keywords & event_keywords

        if len(entity_overlap) >= 2 and len(keyword_overlap) >= 3:
            duplicates.append({
                'title': event.get('summary', ''),
                'similarity': 0.9,
                'method': '已写事件匹配',
                'source': 'written-events.json'
            })

    # 检查2: 和最近文章对比
    for article in articles:
        # 实体重叠度
        entity_overlap = candidate_entities & article['entities']
        # 关键词重叠度
        keyword_overlap = candidate_keywords & article['keywords']

        entity_score = len(entity_overlap) / max(len(candidate_entities), 1)
        keyword_score = len(keyword_overlap) / max(len(candidate_keywords), 1)

        # 标题字面相似度
        title_sim = SequenceMatcher(None, candidate_title.lower(), article['title'].lower()).ratio()

        # 判断重复的条件：
        # 1. 实体高度重叠(>=2个相同实体) 且 关键词有重叠(>=3个)
        # 2. 或标题字面相似度>=0.6
        # 3. 或关键词重叠度>=0.7
        is_dup = False
        method = ''
        score = 0

        if len(entity_overlap) >= 2 and len(keyword_overlap) >= 3:
            is_dup = True
            method = f'实体+关键词匹配 (实体:{",".join(entity_overlap)})'
            score = max(entity_score, keyword_score)
        elif title_sim >= threshold:
            is_dup = True
            method = '标题字面相似度'
            score = title_sim
        elif keyword_score >= 0.7 and len(keyword_overlap) >= 4:
            is_dup = True
            method = '关键词高度重叠'
            score = keyword_score

        if is_dup:
            duplicates.append({
                'title': article['title'],
                'similarity': score,
                'method': method,
                'source': article['filename']
            })

    if duplicates:
        return False, duplicates
    else:
        return True, None


def main():
    if len(sys.argv) < 2:
        print("用法: python3 check-recent-duplicates.py <候选标题> [候选摘要]")
        sys.exit(2)

    candidate_title = sys.argv[1]
    candidate_summary = sys.argv[2] if len(sys.argv) > 2 else ''

    print(f"🔍 检查候选标题: {candidate_title}")
    if candidate_summary:
        print(f"📝 候选摘要: {candidate_summary[:80]}...")
    print(f"📅 检查范围: 最近7天文章 + 已写事件列表")

    # 提取实体
    entities = extract_entities(candidate_title + ' ' + candidate_summary)
    if entities:
        print(f"🏷️ 识别实体: {', '.join(entities)}")

    is_unique, result = check_duplicate(candidate_title, candidate_summary)

    if is_unique:
        print("✅ 无重复，可以继续")
        sys.exit(0)
    else:
        print("❌ 发现重复选题:")
        for dup in result:
            print(f"   • {dup['title'][:80]}")
            print(f"     相似度: {dup['similarity']:.2f} ({dup['method']})")
            print(f"     来源: {dup.get('source', '')}")
        print("\n⚠️ 这是同一个事件的不同角度，不是新选题。请选择其他话题。")
        sys.exit(1)


if __name__ == '__main__':
    main()
