#!/bin/bash
# 自动评分+Git提交脚本
# 用途：文章生成后自动触发评分，然后git提交
# 调用方式：./scripts/auto-score-and-commit.sh [文章路径]

set -e
cd /home/node/.openclaw/workspace/sandbot-blog

echo "=== 自动评分+提交 $(date -u +%Y-%m-%d_%H:%M) ==="

# 1. 评分：找所有无评分的文章
echo "📊 检查缺失评分..."
MISSING=0
SCORED=0

for f in posts/2026-*.html; do
    base=$(basename "$f" .html)
    if [ ! -f "posts/${base}.score.json" ] && [ ! -f "${base}.score.json" ]; then
        echo "  缺评分: $base"
        python3 scripts/article-quality-score.py "$f" 2>&1 | tail -2
        MISSING=$((MISSING + 1))
    else
        SCORED=$((SCORED + 1))
    fi
done

echo "  已有评分: $SCORED 篇"
echo "  新评分: $MISSING 篇"

# 2. Git提交
echo ""
echo "📤 Git提交..."
git add -A

# 检查是否有变更
if git diff --cached --quiet; then
    echo "  无变更，跳过提交"
else
    # 统计变更
    CHANGED=$(git diff --cached --name-only | wc -l)
    NEW_ARTICLES=$(git diff --cached --name-only | grep "^posts/2026-" | grep ".html$" | wc -l)
    NEW_SCORES=$(git diff --cached --name-only | grep ".score.json$" | wc -l)
    
    # 构建commit message
    MSG="🤖 自动提交 $(date -u +%Y-%m-%d_%H:%M) UTC"
    [ "$NEW_ARTICLES" -gt 0 ] && MSG="$MSG | ${NEW_ARTICLES}篇新文章"
    [ "$NEW_SCORES" -gt 0 ] && MSG="$MSG | ${NEW_SCORES}个评分"
    [ "$CHANGED" -gt "$((NEW_ARTICLES + NEW_SCORES))" ] && MSG="$MSG | 其他${CHANGED}文件"
    
    git commit -m "$MSG"
    git push origin main 2>&1 | tail -3
    echo "  ✅ 已提交并推送"
fi

echo ""
echo "=== 完成 ==="
