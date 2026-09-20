#!/bin/bash
# 一键写文章脚本（优化版）
# 用法: ./write-article.sh <slot> [topic]
# slot: morning/noon/afternoon/evening/hot
# topic: 可选，指定话题关键词

SLOT=$1
TOPIC=$2

if [ -z "$SLOT" ]; then
  echo "用法: $0 <slot> [topic]"
  echo "slot: morning/noon/afternoon/evening/hot"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOG_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📝 开始写${SLOT}文章..."

# 1. 准备素材（一次性读取）
MATERIAL_FILE="/tmp/article-material-${SLOT}.txt"
cat > "$MATERIAL_FILE" << EOF
=== 素材 ===
$(cat "$BLOG_ROOT/hot-topics-${SLOT}.md" 2>/dev/null || cat "$BLOG_ROOT/tmp/news/$(date +%Y-%m-%d).md" 2>/dev/null || echo "无素材")

=== 模板结构 ===
$(grep -E '<div class="(quick-glance|article-content|data-card|quote|metaphor|icon-list|info-bar|conclusion|bottom-quote|bottom-source)">' "$BLOG_ROOT/post-template-v3.html" | head -20)

=== 要求 ===
- 正文≥3000字符
- Agent视角贯穿全文（第一人称）
- 必须包含：一分钟速览、数据来源、配图、引用金句
- 用 generate-article-from-template.py 生成
EOF

echo "✅ 素材已准备: $MATERIAL_FILE"

# 2. 生成文章（Python 脚本处理）
ARTICLE_FILE="$BLOG_ROOT/posts/$(date +%Y-%m-%d)-${SLOT}.html"

python3 "$SCRIPT_DIR/generate-article-from-template.py" \
  --material "$MATERIAL_FILE" \
  --output "$ARTICLE_FILE" \
  --slot "$SLOT" \
  --topic "$TOPIC"

if [ $? -ne 0 ]; then
  echo "❌ 文章生成失败"
  exit 1
fi

echo "✅ 文章已生成: $ARTICLE_FILE"

# 3. 发布（并行执行）
echo "🚀 开始发布..."

# 并行：生成音频 + 更新博客
(
  python3 "$SCRIPT_DIR/edge-tts-human.py" \
    <(python3 "$SCRIPT_DIR/extract-article-text.py" "$ARTICLE_FILE") \
    "$BLOG_ROOT/posts/audio/$(basename $ARTICLE_FILE .html).mp3" \
    zh-CN-YunxiNeural
) &
AUDIO_PID=$!

(
  python3 "$SCRIPT_DIR/update-blog.py" "$ARTICLE_FILE" "$BLOG_ROOT/blog.html"
  python3 "$SCRIPT_DIR/generate-rss-from-posts.py"
) &
UPDATE_PID=$!

# 等待完成
wait $AUDIO_PID
wait $UPDATE_PID

# 4. 提交
cd "$BLOG_ROOT"
git add posts/ blog.html feed.xml posts/audio/
git commit -m "📝 发布文章: $(basename $ARTICLE_FILE .html)"
git push origin main

echo "✅ 发布完成"
echo "🔗 https://sandbot.cgfan.com/posts/$(basename $ARTICLE_FILE .html)"
