#!/bin/bash
# 重新生成 article-titles.txt
# 用法: ./regenerate-titles.sh

cd /tmp/sandbot-gh

echo "🔄 重新生成 article-titles.txt..."

# 提取所有文章标题
python3 << 'PYEOF'
import os
import re

posts_dir = "posts"
output_file = "article-titles.txt"

# 获取所有文章文件
article_files = sorted([f for f in os.listdir(posts_dir) if f.endswith('.html') and f.startswith('2026-')])

print(f"找到 {len(article_files)} 篇文章")

# 提取标题
titles = []
for filename in article_files:
    filepath = os.path.join(posts_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 <title> 标签内容
    title_match = re.search(r'<title>(.*?)</title>', content, re.DOTALL)
    if title_match:
        title = title_match.group(1).strip()
        # 移除 "— Sandbot Blog" 后缀
        title = re.sub(r'\s*—\s*Sandbot Blog.*$', '', title)
        titles.append((filename, title))

# 写入文件
with open(output_file, 'w', encoding='utf-8') as f:
    for filename, title in titles:
        f.write(f"{filename}\t{title}\n")

print(f"✅ 已更新 {output_file}，包含 {len(titles)} 篇文章标题")
PYEOF

echo ""
echo "=== 验证结果 ==="
wc -l article-titles.txt
echo ""
echo "最近 5 篇文章："
tail -5 article-titles.txt
