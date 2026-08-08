#!/usr/bin/env python3
"""
检查最近7天文章标题，防止重复选题
用法: python3 check-recent-duplicates.py <候选标题>
返回: 0=通过, 1=重复
"""

import sys
import os
import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher

BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(BLOG_ROOT, "posts")

def get_recent_titles(days=7):
    """获取最近N天的文章标题"""
    cutoff_date = datetime.now() - timedelta(days=days)
    titles = []
    
    for filename in os.listdir(POSTS_DIR):
        if not filename.endswith('.html'):
            continue
        
        # 从文件名提取日期
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})', filename)
        if not date_match:
            continue
        
        file_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
        if file_date < cutoff_date:
            continue
        
        # 读取标题
        filepath = os.path.join(POSTS_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        title_match = re.search(r'<title>([^<]+)</title>', content)
        if title_match:
            title = title_match.group(1).strip()
            title = re.sub(r'\s*—\s*Sandbot Blog.*$', '', title)
            titles.append({
                'filename': filename,
                'title': title,
                'date': file_date
            })
    
    return titles

def calculate_similarity(s1, s2):
    """计算两个字符串的相似度 (0-1)"""
    return SequenceMatcher(None, s1, s2).ratio()

def check_duplicate(candidate_title, threshold=0.6):
    """检查候选标题是否与最近文章重复"""
    recent_titles = get_recent_titles(days=7)
    
    if not recent_titles:
        return True, "无最近文章"
    
    # 提取关键词（去掉常见词）
    candidate_keywords = set(re.findall(r'[\w\u4e00-\u9fa5]+', candidate_title.lower()))
    stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
    candidate_keywords -= stop_words
    
    duplicates = []
    for item in recent_titles:
        # 方法1: 字符串相似度
        sim = calculate_similarity(candidate_title, item['title'])
        if sim >= threshold:
            duplicates.append({
                'title': item['title'],
                'similarity': sim,
                'method': '字符串相似度'
            })
            continue
        
        # 方法2: 关键词重叠
        item_keywords = set(re.findall(r'[\w\u4e00-\u9fa5]+', item['title'].lower()))
        item_keywords -= stop_words
        
        if candidate_keywords and item_keywords:
            overlap = len(candidate_keywords & item_keywords)
            overlap_ratio = overlap / min(len(candidate_keywords), len(item_keywords))
            if overlap_ratio >= 0.7:
                duplicates.append({
                    'title': item['title'],
                    'similarity': overlap_ratio,
                    'method': '关键词重叠'
                })
    
    if duplicates:
        return False, duplicates
    else:
        return True, None

def main():
    if len(sys.argv) < 2:
        print("用法: python3 check-recent-duplicates.py <候选标题>")
        sys.exit(2)
    
    candidate_title = sys.argv[1]
    print(f"🔍 检查候选标题: {candidate_title}")
    print(f"📅 检查范围: 最近7天文章")
    
    is_unique, result = check_duplicate(candidate_title)
    
    if is_unique:
        print("✅ 无重复，可以继续")
        sys.exit(0)
    else:
        print("❌ 发现重复选题:")
        for dup in result:
            print(f"   • {dup['title']}")
            print(f"     相似度: {dup['similarity']:.2f} ({dup['method']})")
        print("\n建议: 选择其他话题，或从不同角度切入")
        sys.exit(1)

if __name__ == '__main__':
    main()
