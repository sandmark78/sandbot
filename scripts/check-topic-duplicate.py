#!/usr/bin/env python3
"""
选题去重检查器（改进版）
用法: 
  python3 check-topic-duplicate.py <关键词1> [关键词2] ...
  python3 check-topic-duplicate.py --file <文章文件路径>

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
    'app-vs-web': ['app', '网页', 'web', 'pwa', '原生应用', 'native'],
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

def extract_keywords_from_file(filepath):
    """从文章文件中提取关键词"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取标题
    title_match = re.search(r'<title>([^<]+)</title>', content)
    title = title_match.group(1) if title_match else ""
    
    # 提取 h1, h2
    headings = re.findall(r'<h[12][^>]*>(.*?)</h[12]>', content, re.DOTALL)
    headings_text = ' '.join(headings)
    
    # 合并文本
    full_text = (title + " " + headings_text).lower()
    
    # 提取关键词（基于主题分类）
    keywords = []
    for category, category_keywords in TOPIC_CATEGORIES.items():
        for keyword in category_keywords:
            if keyword in full_text:
                keywords.append(keyword)
    
    # 从标题中提取更具代表性的关键词
    if title:
        # 提取中文词汇（至少2个字符）
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,}', title)
        # 过滤掉常见的无意义词
        stop_words = ['的', '是', '在', '和', '与', '或', '但', '而', '了', '着', '过', '你的', '其实', '可以']
        chinese_words = [w for w in chinese_words if w not in stop_words and len(w) >= 2]
        keywords.extend(chinese_words[:5])
    
    # 去重并限制数量
    unique_keywords = list(set(keywords))
    
    # 优先选择更具体的关键词（长度较长的）
    unique_keywords.sort(key=len, reverse=True)
    
    return unique_keywords[:5]  # 最多返回5个关键词

def check_duplicate(keywords, days=7, exclude_file=None):
    """检查过去 N 天是否写过类似选题"""
    duplicates = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # 获取输入关键词的主题分类
    input_text = ' '.join(keywords)
    input_categories = get_topic_category(input_text)
    
    for filename in os.listdir(POSTS_DIR):
        if not filename.endswith('.html'):
            continue
        
        # 排除当前正在检查的文章
        if exclude_file and filename == os.path.basename(exclude_file):
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
        # 1. 匹配 3 个以上关键词（更严格）
        # 2. 或者主题分类重叠 3 个以上（说明主题非常接近）
        # 3. 特殊处理：如果包含 "app-vs-web" 分类，需要更精确匹配
        is_duplicate = False
        
        if len(matched_keywords) >= 3:
            is_duplicate = True
        elif len(category_overlap) >= 3:
            is_duplicate = True
        elif 'app-vs-web' in input_categories and 'app-vs-web' in file_categories:
            # 对于 app vs web 主题，需要至少匹配2个关键词
            if len(matched_keywords) >= 2:
                is_duplicate = True
        
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
        print("用法:")
        print("  python3 check-topic-duplicate.py <关键词1> [关键词2] ...")
        print("  python3 check-topic-duplicate.py --file <文章文件路径>")
        print("\n示例:")
        print("  python3 check-topic-duplicate.py Apple OpenAI 起诉")
        print("  python3 check-topic-duplicate.py --file posts/2026-07-15-early-app-vs-webpage.html")
        sys.exit(1)
    
    # 检查是否使用 --file 模式
    if sys.argv[1] == '--file':
        if len(sys.argv) < 3:
            print("错误: --file 模式需要提供文章文件路径")
            sys.exit(1)
        
        filepath = sys.argv[2]
        if not os.path.exists(filepath):
            print(f"错误: 文件不存在: {filepath}")
            sys.exit(1)
        
        print(f"🔍 从文章中提取关键词...")
        keywords = extract_keywords_from_file(filepath)
        print(f"   文件: {os.path.basename(filepath)}")
        print(f"   提取的关键词: {', '.join(keywords)}")
        print()
        
        # 检查重复，排除当前文件
        duplicates = check_duplicate(keywords, days=7, exclude_file=filepath)
    else:
        # 关键词模式
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
