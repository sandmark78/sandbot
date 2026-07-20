#!/usr/bin/env python3
"""
素材抓取脚本 - 自动抓取 HN 热点并进行去重检查
用法: python3 fetch-hot-topics.py <output-file> [--hours 24]

功能:
1. 抓取 HN 热门文章
2. 检查最近 3 天的文章标题
3. 过滤重复话题
4. 保存素材文件
"""

import sys
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
import re

def fetch_hn_top_stories(limit=30):
    """抓取 HN 热门文章"""
    try:
        with urllib.request.urlopen('https://hacker-news.firebaseio.com/v0/topstories.json', timeout=5) as response:
            ids = json.loads(response.read().decode())[:limit]
        
        stories = []
        for id in ids:
            try:
                url = f'https://hacker-news.firebaseio.com/v0/item/{id}.json'
                with urllib.request.urlopen(url, timeout=2) as response:
                    item = json.loads(response.read().decode())
                if item and item.get('score', 0) > 200:
                    stories.append({
                        'title': item.get('title', ''),
                        'score': item.get('score', 0),
                        'url': item.get('url', ''),
                        'hn_url': f"https://news.ycombinator.com/item?id={id}",
                        'comments': item.get('descendants', 0)
                    })
            except:
                pass
        
        return stories
    except Exception as e:
        print(f"❌ 抓取 HN 失败: {e}")
        return []

def get_recent_articles(days=3):
    """获取最近 N 天的文章标题"""
    posts_dir = '/tmp/sandbot-gh/posts'
    if not os.path.exists(posts_dir):
        return []
    
    cutoff = datetime.now() - timedelta(days=days)
    articles = []
    
    for filename in os.listdir(posts_dir):
        if not filename.endswith('.html'):
            continue
        
        # 检查文件名日期
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            file_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
            if file_date < cutoff:
                continue
        
        # 提取标题
        filepath = os.path.join(posts_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            title_match = re.search(r'<title>([^<]+)</title>', content)
            if title_match:
                title = title_match.group(1).strip()
                # 移除 "— Sandbot Blog" 后缀
                title = re.sub(r'\s*—\s*Sandbot Blog.*$', '', title)
                articles.append({
                    'filename': filename,
                    'title': title,
                    'date': file_date.strftime('%Y-%m-%d')
                })
        except:
            pass
    
    return articles

def check_similarity(title1, title2, threshold=0.5):
    """检查两个标题的相似度"""
    # 提取关键词
    words1 = set(re.findall(r'\w+', title1.lower()))
    words2 = set(re.findall(r'\w+', title2.lower()))
    
    if not words1 or not words2:
        return 0.0
    
    # 计算 Jaccard 相似度
    intersection = words1 & words2
    union = words1 | words2
    similarity = len(intersection) / len(union)
    
    return similarity

def filter_duplicates(stories, recent_articles, threshold=0.5):
    """过滤重复话题"""
    filtered = []
    
    for story in stories:
        is_duplicate = False
        
        for article in recent_articles:
            similarity = check_similarity(story['title'], article['title'], threshold)
            if similarity >= threshold:
                print(f"⚠️ 跳过重复话题: {story['title']}")
                print(f"   与 {article['date']} 的文章相似 (相似度: {similarity:.2f})")
                is_duplicate = True
                break
        
        if not is_duplicate:
            filtered.append(story)
    
    return filtered

def save_materials(stories, output_file):
    """保存素材文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# 热点素材 (生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')})\n\n")
        f.write(f"共 {len(stories)} 个话题（已过滤重复）\n\n")
        
        for i, story in enumerate(stories[:10], 1):
            f.write(f"## 话题 {i}: {story['title']}\n")
            f.write(f"- **分数**: {story['score']} points\n")
            f.write(f"- **评论**: {story['comments']} comments\n")
            f.write(f"- **URL**: {story['url']}\n")
            f.write(f"- **HN**: {story['hn_url']}\n\n")
    
    print(f"✅ 已保存素材到 {output_file}")

def main():
    if len(sys.argv) < 2:
        print("用法: python3 fetch-hot-topics.py <output-file> [--hours 24]")
        sys.exit(1)
    
    output_file = sys.argv[1]
    
    print("=== 素材抓取脚本 ===")
    print()
    
    # 1. 抓取 HN 热点
    print("1. 抓取 HN 热门文章...")
    stories = fetch_hn_top_stories(30)
    print(f"   找到 {len(stories)} 个热门话题")
    print()
    
    # 2. 获取最近文章
    print("2. 获取最近 3 天的文章...")
    recent_articles = get_recent_articles(3)
    print(f"   找到 {len(recent_articles)} 篇文章")
    print()
    
    # 3. 过滤重复
    print("3. 过滤重复话题...")
    filtered_stories = filter_duplicates(stories, recent_articles, threshold=0.5)
    print(f"   过滤后剩余 {len(filtered_stories)} 个话题")
    print()
    
    # 4. 保存素材
    print("4. 保存素材文件...")
    save_materials(filtered_stories, output_file)
    print()
    
    print("✅ 完成")

if __name__ == '__main__':
    main()
