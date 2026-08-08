#!/bin/bash
BLOG_ROOT="/home/node/.openclaw/workspace/sandbot-blog"
MEMORY_DIR="/home/node/.openclaw/workspace/memory"
TODAY=$(date +%Y-%m-%d)

ARTICLE_COUNT=$(find "$BLOG_ROOT/posts" -name "${TODAY}*.html" 2>/dev/null | wc -l)
PLACEHOLDER_FILES=$(find "$BLOG_ROOT/posts" -name "${TODAY}*.html" -exec grep -l '来源说明\|XX 官方\|要点一\|要点二\|要点三' {} \; 2>/dev/null)

{
echo "# $TODAY 每日复盘"
echo ""
echo "## 📊 文章发布: $ARTICLE_COUNT 篇"
if [ "$ARTICLE_COUNT" -gt 0 ]; then
  find "$BLOG_ROOT/posts" -name "${TODAY}*.html" -exec basename {} \; | sort | while read f; do echo "- $f"; done
fi
echo ""
echo "## 🔍 质量检查"
if [ -z "$PLACEHOLDER_FILES" ]; then echo "- ✅ 无占位符问题"; else echo "- ❌ 发现占位符"; fi
echo ""
echo "## 📝 知识文件"
for f in practical-techniques.md learning-application.md; do
  if [ -f "$MEMORY_DIR/$f" ]; then
    SIZE=$(stat -c%s "$MEMORY_DIR/$f" 2>/dev/null)
    echo "- ✅ $f — $(numfmt --to=iec $SIZE 2>/dev/null)"
  else
    echo "- ❌ $f — 不存在"
  fi
done
} > "$MEMORY_DIR/${TODAY}-review.md"

cat "$MEMORY_DIR/${TODAY}-review.md"
