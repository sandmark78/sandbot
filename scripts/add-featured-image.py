#!/usr/bin/env python3
"""
给文章补题图
用法: python3 add-featured-image.py <article.html> <image_url> [caption] [source]

示例:
  python3 add-featured-image.py posts/2026-08-09-weekly-32.html "https://images.unsplash.com/photo-xxx?w=1200" "周报题图" "Unsplash"
"""

import sys
import re

def add_featured_image(html_file, image_url, caption="题图", source="网络"):
    """在三十秒速览之后、正文之前插入题图"""
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已有题图
    if '<div class="article-img">' in content and '题图' in content:
        print(f"⚠️  {html_file} 已有题图，跳过")
        return False
    
    # 查找插入点：在三十秒速览之后、正文之前
    # 优先找 <!-- 7. 正文：编号 · 短标题 -->
    insert_point = content.find('<!-- 7. 正文：编号 · 短标题 -->')
    
    if insert_point == -1:
        # fallback: 找第一个 <h2><span class="section-num">1</span>
        match = re.search(r'<h2><span class="section-num">1</span>', content)
        if match:
            insert_point = match.start()
        else:
            print(f"❌ 未找到插入点: {html_file}")
            return False
    
    # 构建题图 HTML
    image_html = f'''
  <!-- 题图 -->
  <div class="article-img">
    <img src="{image_url}" alt="{caption}">
    <div class="img-caption">{caption}。来源：{source}</div>
  </div>

'''
    
    # 插入
    new_content = content[:insert_point] + image_html + content[insert_point:]
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ 题图已插入: {html_file}")
    print(f"   图片: {image_url}")
    print(f"   说明: {caption}")
    print(f"   来源: {source}")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python3 add-featured-image.py <article.html> <image_url> [caption] [source]")
        sys.exit(1)
    
    html_file = sys.argv[1]
    image_url = sys.argv[2]
    caption = sys.argv[3] if len(sys.argv) > 3 else "题图"
    source = sys.argv[4] if len(sys.argv) > 4 else "网络"
    
    success = add_featured_image(html_file, image_url, caption, source)
    sys.exit(0 if success else 1)
