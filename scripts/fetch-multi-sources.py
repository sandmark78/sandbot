#!/usr/bin/env python3
"""
多源新闻聚合脚本 V2
数据源：HN、AI HOT RSS、Reddit、GitHub Trending
"""

import feedparser
import requests
import json
import re
import os
from datetime import datetime, timedelta
from difflib import SequenceMatcher

OUTPUT_DIR = "/tmp/sandbot-gh"
CACHE_FILE = f"{OUTPUT_DIR}/hot-topics-cache.json"

# 数据源配置
SOURCES = {
    "hn": {
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage?count=30",
        "weight": 1.0
    },
    "aihot": {
        "name": "AI HOT 精选",
        "url": "https://aihot.virxact.com/feed.xml",
        "weight": 1.2
    },
    "aihot_all": {
        "name": "AI HOT 全部",
        "url": "https://aihot.virxact.com/feed/all.xml",
        "weight": 0.8
    },
    "reddit": {
        "name": "Reddit ML",
        "url": "https://www.reddit.com/r/MachineLearning/hot/.rss",
        "weight": 0.9
    }
}

def load_cache():
    """加载缓存（用于去重），只保留 24 小时内的记录"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            
            # 清理超过 24 小时的记录
            cutoff = datetime.now() - timedelta(hours=24)
            cache['seen_urls'] = [
                url for url in cache.get('seen_urls', [])
                if cache.get('timestamps', {}).get(url, 0) > cutoff.timestamp()
            ]
            cache['seen_titles'] = [
                title for title in cache.get('seen_titles', [])
                if cache.get('timestamps', {}).get(title, 0) > cutoff.timestamp()
            ]
            
            return cache
        except:
            return {"seen_urls": [], "seen_titles": [], "timestamps": {}}
    return {"seen_urls": [], "seen_titles": [], "timestamps": {}}

def save_cache(cache):
    """保存缓存"""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def similar(a, b):
    """计算两个字符串的相似度"""
    return SequenceMatcher(None, a, b).ratio()

def fetch_rss(source_key, source_config):
    """抓取 RSS 源"""
    print(f"📡 抓取 {source_config['name']}...")
    
    try:
        feed = feedparser.parse(source_config['url'])
        items = []
        
        for entry in feed.entries[:20]:  # 每个源最多 20 条
            # 提取标题
            title = entry.get('title', '').strip()
            if not title:
                continue
            
            # 提取链接
            link = entry.get('link', '')
            
            # 提取摘要
            summary = entry.get('summary', entry.get('description', ''))
            # 清理 HTML 标签
            summary = re.sub(r'<[^>]+>', '', summary)
            summary = re.sub(r'\s+', ' ', summary).strip()
            if len(summary) > 300:
                summary = summary[:300] + '...'
            
            # 提取发布时间
            published = entry.get('published', '')
            
            # 提取分类
            category = ''
            if 'category' in entry:
                category = entry.category if isinstance(entry.category, str) else entry.category[0]
            
            # 计算热度分数
            score = 0
            if 'score' in entry:
                try:
                    score = int(entry.score)
                except (ValueError, TypeError):
                    score = 0
            elif 'comments' in entry:
                try:
                    score = int(entry.comments)
                except (ValueError, TypeError):
                    score = 0
            
            # 应用权重
            weighted_score = score * source_config['weight']
            
            items.append({
                'title': title,
                'link': link,
                'summary': summary,
                'published': published,
                'category': category,
                'score': score,
                'weighted_score': weighted_score,
                'source': source_config['name'],
                'source_key': source_key
            })
        
        print(f"  ✅ 获取到 {len(items)} 条")
        return items
    
    except Exception as e:
        print(f"  ❌ 抓取失败: {e}")
        return []

def deduplicate(items, cache):
    """去重"""
    unique_items = []
    now = datetime.now().timestamp()
    
    for item in items:
        # URL 去重
        if item['link'] in cache['seen_urls']:
            continue
        
        # 标题相似度去重
        is_duplicate = False
        for seen_title in cache['seen_titles']:
            if similar(item['title'], seen_title) > 0.7:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_items.append(item)
            cache['seen_urls'].append(item['link'])
            cache['seen_titles'].append(item['title'])
            cache['timestamps'][item['link']] = now
            cache['timestamps'][item['title']] = now
    
    return unique_items

def categorize(item):
    """自动分类"""
    title_lower = item['title'].lower()
    summary_lower = item['summary'].lower()
    text = title_lower + ' ' + summary_lower
    
    # 分类规则
    if any(word in text for word in ['发布', 'release', 'launch', '推出', 'new model']):
        return '模型发布'
    elif any(word in text for word in ['开源', 'open source', 'github', 'repo']):
        return '开源项目'
    elif any(word in text for word in ['论文', 'paper', 'research', '研究']):
        return '论文'
    elif any(word in text for word in ['融资', 'funding', '投资', 'acquisition']):
        return '行业动态'
    elif any(word in text for word in ['产品', 'product', 'app', '应用']):
        return '产品发布'
    else:
        return '热点'

def generate_hot_topics(items, limit=15):
    """生成热点文件"""
    # 按加权分数排序
    items.sort(key=lambda x: x['weighted_score'], reverse=True)
    
    # 取前 N 条
    top_items = items[:limit]
    
    # 生成 Markdown
    output = f"# 今日 AI 热点\n\n"
    output += f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    output += f"数据源：{', '.join([s['name'] for s in SOURCES.values()])}\n\n"
    output += "---\n\n"
    
    for i, item in enumerate(top_items, 1):
        category = categorize(item)
        output += f"## {i}. {item['title']}\n\n"
        output += f"**分类**：{category}  \n"
        output += f"**来源**：{item['source']}  \n"
        output += f"**热度**：{item['score']}  \n"
        output += f"**链接**：{item['link']}\n\n"
        
        if item['summary']:
            output += f"**摘要**：{item['summary']}\n\n"
        
        output += "---\n\n"
    
    # 保存文件
    output_file = f"{OUTPUT_DIR}/hot-topics-multi.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"\n✅ 已生成热点文件: {output_file}")
    print(f"📊 共 {len(top_items)} 条热点")
    
    return output_file

def main():
    print("🚀 开始多源新闻聚合...\n")
    
    # 加载缓存
    cache = load_cache()
    
    # 抓取所有源
    all_items = []
    for source_key, source_config in SOURCES.items():
        items = fetch_rss(source_key, source_config)
        all_items.extend(items)
    
    print(f"\n📊 总共获取到 {len(all_items)} 条新闻")
    
    # 去重
    unique_items = deduplicate(all_items, cache)
    print(f"✅ 去重后剩余 {len(unique_items)} 条")
    
    # 生成热点
    output_file = generate_hot_topics(unique_items, limit=15)
    
    # 保存缓存
    save_cache(cache)
    
    print(f"\n🎉 聚合完成！")

if __name__ == '__main__':
    main()
