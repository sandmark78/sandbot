#!/usr/bin/env python3
"""
虾聊发帖去重检测 V2
检查文章是否已经发过虾聊，支持从 API 拉取历史记录
"""

import os
import sys
import json
import re
import subprocess
from datetime import datetime
# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

XIALIAO_POSTED_FILE = os.path.join(BLOG_ROOT, "xialiao-posted.json")
POSTS_DIR = os.path.join(BLOG_ROOT, "posts")
API_TOKEN = "clawdchat_Gjvli5EriQ3K_DvKXHRK2LRDNWIHfUA9ZIDuAkUZbE0"
AGENT_NAME = "sandbot-lobster"

def load_posted():
    """加载已发帖列表"""
    if os.path.exists(XIALIAO_POSTED_FILE):
        try:
            with open(XIALIAO_POSTED_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_posted(posted):
    """保存已发帖列表"""
    with open(XIALIAO_POSTED_FILE, 'w', encoding='utf-8') as f:
        json.dump(posted, f, ensure_ascii=False, indent=2)

def fetch_from_api():
    """从虾聊 API 拉取所有已发帖记录"""
    print("🔄 从虾聊 API 拉取历史记录...")
    
    try:
        result = subprocess.run(
            ['curl', '-s', f'https://clawdchat.cn/api/v1/posts?author={AGENT_NAME}&limit=50'],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode != 0:
            print(f"❌ curl 失败: {result.stderr}")
            return []
        
        data = json.loads(result.stdout)
        posts = data.get('posts', [])
        
        posted = []
        for post in posts:
            content = post.get('content', '')
            # 从内容中提取博客链接
            blog_link = ''
            if 'sandbot.cgfan.com/posts/' in content:
                match = re.search(r'sandbot\.cgfan\.com/posts/([^\s\)\"]+)', content)
                if match:
                    blog_link = match.group(1)
            
            if blog_link:
                posted.append({
                    'article': blog_link,
                    'post_url': f"https://clawdchat.cn/post/{post.get('id', '')}",
                    'post_title': post.get('title', ''),
                    'posted_at': post.get('created_at', '')
                })
        
        print(f"✅ 从 API 拉取到 {len(posted)} 个已发帖记录")
        return posted
    
    except Exception as e:
        print(f"❌ API 拉取失败: {e}")
        return []

def check_posted(article_file):
    """检查文章是否已发帖"""
    posted = load_posted()
    article_base = os.path.basename(article_file).replace('.html', '')
    
    for item in posted:
        if item.get('article') == article_base:
            return True, item.get('post_url', '')
    
    return False, ''

def mark_posted(article_file, post_url, post_title):
    """标记文章已发帖"""
    posted = load_posted()
    article_base = os.path.basename(article_file).replace('.html', '')
    
    # 检查是否已存在
    for item in posted:
        if item.get('article') == article_base:
            print(f"⚠️  已存在: {article_base}")
            return
    
    posted.append({
        'article': article_base,
        'post_url': post_url,
        'post_title': post_title,
        'posted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    save_posted(posted)
    print(f"✅ 已标记: {article_base}")

def get_unposted_articles(limit=10):
    """获取未发帖的文章列表（只显示最近的）"""
    posted = load_posted()
    posted_articles = {item.get('article') for item in posted}
    
    # 获取所有文章，按日期排序（最新的在前）
    articles = []
    for filename in os.listdir(POSTS_DIR):
        if not filename.endswith('.html'):
            continue
        
        # 跳过非文章文件
        if not filename.startswith('2026-'):
            continue
        
        article_base = filename.replace('.html', '')
        if article_base not in posted_articles:
            # 提取日期
            date_match = re.match(r'(\d{4}-\d{2}-\d{2})', filename)
            date = date_match.group(1) if date_match else 'unknown'
            
            articles.append({
                'filename': filename,
                'date': date,
                'base': article_base
            })
    
    # 按日期排序（最新的在前）
    articles.sort(key=lambda x: x['date'], reverse=True)
    
    return articles[:limit]

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  检查: python3 check-xialiao-posted.py check <article-file>")
        print("  标记: python3 check-xialiao-posted.py mark <article-file> <post-url> <post-title>")
        print("  列表: python3 check-xialiao-posted.py list [数量]")
        print("  初始化: python3 check-xialiao-posted.py init")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == 'check':
        if len(sys.argv) < 3:
            print("❌ 缺少文章文件参数")
            sys.exit(1)
        
        article_file = sys.argv[2]
        is_posted, post_url = check_posted(article_file)
        
        if is_posted:
            print(f"❌ 已发帖: {post_url}")
            sys.exit(1)
        else:
            print(f"✅ 未发帖")
            sys.exit(0)
    
    elif action == 'mark':
        if len(sys.argv) < 5:
            print("❌ 缺少参数")
            sys.exit(1)
        
        article_file = sys.argv[2]
        post_url = sys.argv[3]
        post_title = sys.argv[4]
        
        mark_posted(article_file, post_url, post_title)
    
    elif action == 'list':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        
        articles = get_unposted_articles(limit)
        if articles:
            print(f"📋 未发帖的文章（最新 {len(articles)} 篇）:")
            for article in articles:
                print(f"  - {article['date']} | {article['base']}")
        else:
            print("✅ 所有文章都已发帖")
    
    elif action == 'init':
        # 从 API 拉取历史记录
        posted = fetch_from_api()
        
        # 合并现有记录
        existing = load_posted()
        existing_articles = {item.get('article') for item in existing}
        
        for item in posted:
            if item.get('article') not in existing_articles:
                existing.append(item)
        
        save_posted(existing)
        print(f"✅ 已初始化，总计 {len(existing)} 个已发帖记录")
    
    else:
        print(f"❌ 未知操作: {action}")
        sys.exit(1)

if __name__ == '__main__':
    main()
