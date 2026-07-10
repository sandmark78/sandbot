#!/bin/bash
# 一键发布文章脚本
# 用法: ./publish-article.sh <article-file> <blog-html>

ARTICLE_FILE=$1
BLOG_HTML=$2

if [ -z "$ARTICLE_FILE" ] || [ -z "$BLOG_HTML" ]; then
  echo "用法: $0 <article-file> <blog-html>"
  exit 1
fi

# 1. 更新 blog.html
python3 /tmp/sandbot-gh/scripts/update-blog.py "$ARTICLE_FILE" "$BLOG_HTML"

# 2. 更新RSS
python3 /tmp/sandbot-gh/scripts/update-rss.py

# 3. Git操作（合并）
cd /tmp/sandbot-gh
git add "$ARTICLE_FILE" "$BLOG_HTML" feed.xml
git commit -m "📝 发布文章: $(basename $ARTICLE_FILE .html)"
git push origin main

echo "✅ 发布完成"
