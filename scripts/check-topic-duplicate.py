#!/usr/bin/env python3
"""
选题去重检查器（改进版）
用法: python3 check-topic-duplicate.py <关键词1> [关键词2] ...

检查历史文章是否已经写过类似选题
支持两种检查：
1. 关键词匹配（精确匹配）
2. 主题相似度（语义匹配）
"""

import sys
import os
import re
from datetime import datetime, timedelta

POSTS_DIR = "/tmp/sandbot-gh/posts"

# 主题分类映射
TOPIC_CATEGORIES = {
    'ai-coding': ['ai 编程', 'ai 代码', '编程助手', 'coding agent', 'claude code', 'copilot', 'cursor', 'grok', 'opencode'],
    'ai-security': ['ai 安全', '数据安全', '隐私', '泄露', 'security', 'privacy'],
    'ai-agent': ['ai agent', '智能体', 'agent', '自治'],
    'llm': ['llm', '大模型', 'gpt', 'claude', 'gemini', '模型'],
    'open-source': ['开源', 'open source', 'github', '社区'],
}

def get_topic_category(text):
    """识别文本的主题分类"""
    text_lower = text.lower()
    categories = []
    for category, keywords in TOPIC_CATEGORIES.items():
        for keyword in keywords:
            if keyword in text_lower:
                categories.append(category)
                break
    return list(set(categories))

def check_duplicate(keywords, days=7):
    """检查过去 N 天是否写过类似选题"""
    duplicates = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # 获取输入关键词的主题分类
    input_text = ' '.join(keywords)
    input_categories = get_topic_category(input_text)
    
    for filename in os.listdir(POSTS_DIR):
        if not filename.endswith('.html'):
            continue
        
        filepath = os.path.join(POSTS_DIR, filename)
        
        # 检查文件名日期
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            file_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
            if file_date < cutoff_date:
                continue
        
        # 读取文件内容
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        # 提取标题
        title_match = re.search(r'<title>([^<]+)</title>', content)
        title = title_match.group(1) if title_match else ""
        
        # 提取 h1, h2
        headings = re.findall(r'<h[12][^>]*>(.*?)</h[12]>', content, re.DOTALL)
        headings_text = ' '.join(headings)
        
        # 合并检查文本
        check_text = (title + " " + headings_text).lower()
        
        # 检查关键词匹配
        matched_keywords = []
        for keyword in keywords:
            if keyword.lower() in check_text:
                matched_keywords.append(keyword)
        
        # 检查主题相似度
        file_categories = get_topic_category(check_text)
        category_overlap = set(input_categories) & set(file_categories)
        
        # 判断是否重复：
        # 1. 匹配 2 个以上关键词
        # 2. 或者主题分类重叠 2 个以上（说明主题非常接近）
        is_duplicate = len(matched_keywords) >= 2 or len(category_overlap) >= 2
        
        if is_duplicate:
            duplicates.append({
                'file': filename,
                'keywords': matched_keywords,
                'categories': list(category_overlap),
                'title': title[:80]
            })
    
    return duplicates

def main():
    if len(sys.argv) < 2:
        print("用法: python3 check-topic-duplicate.py <关键词1> [关键词2] ...")
        print("\n示例:")
        print("  python3 check-topic-duplicate.py Apple OpenAI 起诉")
        print("  python3 check-topic-duplicate.py GPT 发布")
        sys.exit(1)
    
    keywords = sys.argv[1:]
    
    print(f"🔍 检查选题去重...")
    print(f"   关键词: {', '.join(keywords)}")
    print(f"   检查范围: 过去 7 天")
    print()
    
    duplicates = check_duplicate(keywords, days=7)
    
    if duplicates:
        print(f"❌ 发现 {len(duplicates)} 篇重复选题：")
        for dup in duplicates:
            print(f"\n   📄 {dup['file']}")
            print(f"      标题: {dup['title']}")
            print(f"      匹配关键词: {', '.join(dup['keywords'])}")
        print("\n💡 建议：选择其他话题，或从不同角度切入")
        return False
    else:
        print("✅ 未发现重复选题")
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
