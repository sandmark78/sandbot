#!/usr/bin/env python3
"""
生成播客页面数据
扫描音频文件，提取文章标题，生成播客列表
"""

import os
import re
import json
from datetime import datetime

AUDIO_DIR = "/tmp/sandbot-gh/posts/audio"
POSTS_DIR = "/tmp/sandbot-gh/posts"

def extract_title_from_article(filename):
    """从文章文件中提取标题"""
    # 尝试找到对应的文章文件
    base_name = filename.replace('.mp3', '').replace('.md', '')
    
    # 尝试不同的文件名模式
    patterns = [
        f"{base_name}.html",
        f"{base_name.replace('.md', '')}.html",
    ]
    
    for pattern in patterns:
        article_path = os.path.join(POSTS_DIR, pattern)
        if os.path.exists(article_path):
            try:
                with open(article_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取 <title> 标签
                title_match = re.search(r'<title>([^<]+)</title>', content)
                if title_match:
                    title = title_match.group(1).strip()
                    # 移除 " — Sandbot Blog" 后缀
                    title = re.sub(r'\s*—\s*Sandbot Blog.*$', '', title)
                    return title
            except Exception as e:
                pass
    
    return None

def extract_excerpt_from_article(filename):
    """从文章文件中提取摘要"""
    base_name = filename.replace('.mp3', '').replace('.md', '')
    
    patterns = [
        f"{base_name}.html",
        f"{base_name.replace('.md', '')}.html",
    ]
    
    for pattern in patterns:
        article_path = os.path.join(POSTS_DIR, pattern)
        if os.path.exists(article_path):
            try:
                with open(article_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取 article-subtitle
                subtitle_match = re.search(r'<p class="article-subtitle">(.*?)</p>', content, re.DOTALL)
                if subtitle_match:
                    subtitle = subtitle_match.group(1).strip()
                    # 清理 HTML 标签
                    subtitle = re.sub(r'<[^>]+>', '', subtitle)
                    return subtitle[:150]  # 限制长度
                
                # 如果没有 subtitle，尝试提取第一段
                para_match = re.search(r'<article[^>]*>.*?<p>(.*?)</p>', content, re.DOTALL)
                if para_match:
                    para = para_match.group(1).strip()
                    para = re.sub(r'<[^>]+>', '', para)
                    return para[:150]
            except Exception as e:
                pass
    
    return None

def extract_tag_from_filename(filename):
    """从文件名中提取标签"""
    base_name = filename.replace('.mp3', '').replace('.md', '')
    
    # 检查是否包含时段标识
    if '-early-' in base_name or base_name.startswith('early-'):
        return 'early'
    elif '-noon-' in base_name or base_name.startswith('noon-'):
        return 'noon'
    elif '-evening-' in base_name or base_name.startswith('evening-'):
        return 'evening'
    elif '-afternoon-' in base_name or base_name.startswith('afternoon-'):
        return 'afternoon'
    elif '-hot-' in base_name or base_name.startswith('hot-'):
        return 'hot'
    else:
        return 'hot'  # 默认

def extract_date_from_filename(filename):
    """从文件名中提取日期"""
    base_name = filename.replace('.mp3', '').replace('.md', '')
    
    # 尝试匹配日期模式
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', base_name)
    if date_match:
        return date_match.group(1)
    
    # 如果没有日期，使用文件修改时间
    file_path = os.path.join(AUDIO_DIR, filename)
    mtime = os.path.getmtime(file_path)
    return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')

def generate_podcast_list():
    """生成播客列表"""
    podcasts = []
    
    # 扫描音频文件
    for filename in os.listdir(AUDIO_DIR):
        if not filename.endswith('.mp3'):
            continue
        
        # 跳过 podcast-ep 开头的文件（这些是旧版本）
        if filename.startswith('podcast-ep'):
            continue
        
        file_path = os.path.join(AUDIO_DIR, filename)
        file_size = os.path.getsize(file_path)
        
        # 提取信息
        title = extract_title_from_article(filename)
        if not title:
            # 如果找不到文章，使用文件名作为标题
            title = filename.replace('.mp3', '').replace('.md', '').replace('-', ' ').title()
        
        excerpt = extract_excerpt_from_article(filename)
        tag = extract_tag_from_filename(filename)
        date = extract_date_from_filename(filename)
        
        # 构建文章链接
        base_name = filename.replace('.mp3', '').replace('.md', '')
        article_url = f"/sandbot/posts/{base_name}"
        
        # 估算时长（假设 16KB/s 比特率）
        duration_seconds = file_size / 16000
        duration_minutes = max(1, round(duration_seconds / 60))
        
        podcasts.append({
            'date': date,
            'title': title,
            'excerpt': excerpt or '',
            'tag': tag,
            'file': f'posts/audio/{filename}',
            'article': article_url,
            'size': file_size,
            'duration': duration_minutes  # 分钟数
        })
    
    # 按日期排序（最新的在前）
    podcasts.sort(key=lambda x: x['date'], reverse=True)
    
    return podcasts

def main():
    print("🎧 生成播客列表...")
    
    podcasts = generate_podcast_list()
    
    print(f"📊 找到 {len(podcasts)} 个播客")
    
    # 输出 JSON
    output_file = "/tmp/sandbot-gh/podcast-data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(podcasts, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已保存到 {output_file}")
    
    # 显示前 10 个
    print("\n📋 最新 10 个播客：")
    for i, podcast in enumerate(podcasts[:10], 1):
        print(f"{i}. {podcast['date']} | {podcast['title'][:50]}...")

if __name__ == '__main__':
    main()
