#!/bin/bash
# 一键发布文章脚本（带 TTS 语音）
# 用法: ./publish-article.sh <article-file> <blog-html>

ARTICLE_FILE=$1
BLOG_HTML=$2

if [ -z "$ARTICLE_FILE" ] || [ -z "$BLOG_HTML" ]; then
  echo "用法: $0 <article-file> <blog-html>"
  exit 1
fi

ARTICLE_BASE=$(basename "$ARTICLE_FILE" .html)
ARTICLE_DIR=$(dirname "$ARTICLE_FILE")
AUDIO_DIR="$ARTICLE_DIR/audio"
mkdir -p "$AUDIO_DIR"

# 0. 生成语音版本（人味 Edge TTS）
echo "🎙️  生成语音版本..."
# 提取纯正文（过滤导航、按钮、会员提示等）
python3 /tmp/sandbot-gh/scripts/extract-article-text.py "$ARTICLE_FILE" /tmp/tts-input.txt

# 生成语音（男声欢快风格）
python3 /tmp/sandbot-gh/scripts/edge-tts-human.py \
  /tmp/tts-input.txt \
  "$AUDIO_DIR/$ARTICLE_BASE.mp3" \
  zh-CN-YunxiNeural \
  cheerful

# 1. 更新 blog.html（添加音频播放器）
python3 /tmp/sandbot-gh/scripts/update-blog.py "$ARTICLE_FILE" "$BLOG_HTML"

# 2. 更新RSS
python3 /tmp/sandbot-gh/scripts/update-rss.py

# 3. Git操作（合并）
cd /tmp/sandbot-gh
git add "$ARTICLE_FILE" "$BLOG_HTML" feed.xml "$AUDIO_DIR/$ARTICLE_BASE.mp3"
git commit -m "📝 发布文章: $ARTICLE_BASE (带语音)"
git push origin main

echo "✅ 发布完成（含语音版本）"
