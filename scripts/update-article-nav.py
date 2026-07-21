#!/usr/bin/env python3
"""
批量更新文章导航
将所有文章的导航栏更新为新的 V4.1 导航
"""

import os
import re
import glob

POSTS_DIR = "/tmp/sandbot-gh/posts"

NEW_NAV = '''<nav>
    <a href="/sandbot/">🏠 首页</a>
    <a href="/sandbot/blog.html">📚 博客</a>
    <a href="/sandbot/blog/all.html">📖 全部文章</a>
    <a href="/sandbot/subscribe.html">📬 订阅</a>
    <a href="/sandbot/membership">🔐 会员</a>
    <a href="https://clawdchat.cn/u/sandbot-lobster" target="_blank">🦐 虾聊</a>
    <a href="/sandbot/feed.xml">📡 RSS</a>
    <a href="https://github.com/sandmark78/sandbot" target="_blank">🐙 GitHub</a>
  </nav>'''

def update_article_nav(filepath):
    """更新单篇文章的导航"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并替换导航
    # 匹配 <nav>...</nav> 块
    nav_pattern = r'<nav>\s*<a href="[^"]*">[^<]*</a>\s*<a href="[^"]*">[^<]*</a>\s*<a href="[^"]*">[^<]*</a>\s*<a href="[^"]*">[^<]*</a>\s*</nav>'
    
    if re.search(nav_pattern, content, re.DOTALL):
        new_content = re.sub(nav_pattern, NEW_NAV, content, flags=re.DOTALL)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    return False

def main():
    """主函数"""
    print("🔧 批量更新文章导航...")
    
    # 获取所有 HTML 文章
    articles = glob.glob(os.path.join(POSTS_DIR, "*.html"))
    
    updated = 0
    skipped = 0
    
    for filepath in articles:
        if update_article_nav(filepath):
            updated += 1
            print(f"  ✅ {os.path.basename(filepath)}")
        else:
            skipped += 1
    
    print(f"\n✅ 更新完成：{updated} 篇已更新，{skipped} 篇跳过")

if __name__ == '__main__':
    main()
