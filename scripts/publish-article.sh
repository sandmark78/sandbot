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

# 0. 检查是否需要生成语音
# 规则：早鸟文章不生成语音；其他文章 >= 3000 字才生成语音
GENERATE_AUDIO=false

if [[ "$ARTICLE_BASE" == *"-morning-"* ]] || [[ "$ARTICLE_BASE" == *"-early-"* ]]; then
  echo "⏭️  早鸟文章，跳过语音生成"
else
  # 提取文本并检查字数
  python3 /tmp/sandbot-gh/scripts/extract-article-text.py "$ARTICLE_FILE" /tmp/tts-input.txt
  TEXT_LENGTH=$(wc -c < /tmp/tts-input.txt)
  
  if [ "$TEXT_LENGTH" -ge 3000 ]; then
    echo "✅ 文章字数: $TEXT_LENGTH 字符 (>= 3000)，生成语音"
    GENERATE_AUDIO=true
  else
    echo "⏭️  文章字数: $TEXT_LENGTH 字符 (< 3000)，跳过语音生成"
  fi
fi

# 1. 生成语音版本（如果需要）
if [ "$GENERATE_AUDIO" = true ]; then
  echo "🎙️  生成语音版本..."
  # 生成语音（男声欢快风格）
  python3 /tmp/sandbot-gh/scripts/edge-tts-human.py \
    /tmp/tts-input.txt \
    "$AUDIO_DIR/$ARTICLE_BASE.mp3" \
    zh-CN-YunxiNeural \
    cheerful
  
  # 给文章添加音频播放器
  python3 /tmp/sandbot-gh/scripts/add-audio-player.py "$ARTICLE_FILE"
fi

# 2. 更新 blog.html
python3 /tmp/sandbot-gh/scripts/update-blog.py "$ARTICLE_FILE" "$BLOG_HTML"

# 3. 更新RSS
python3 /tmp/sandbot-gh/scripts/update-rss.py

# 4. Git操作
cd /tmp/sandbot-gh
if [ "$GENERATE_AUDIO" = true ]; then
  git add "$ARTICLE_FILE" "$BLOG_HTML" feed.xml "$AUDIO_DIR/$ARTICLE_BASE.mp3"
  git commit -m "📝 发布文章: $ARTICLE_BASE (带语音)"
else
  git add "$ARTICLE_FILE" "$BLOG_HTML" feed.xml
  git commit -m "📝 发布文章: $ARTICLE_BASE (无语音)"
fi
git push origin main

echo ""
if [ "$GENERATE_AUDIO" = true ]; then
  echo "✅ 发布完成（含语音版本）"
else
  echo "✅ 发布完成（无语音版本）"
fi
echo ""
echo "📎 文章完整 URL："
echo "https://sandbot.cgfan.com/posts/${ARTICLE_BASE}"
echo ""
echo "🔗 博客首页："
echo "https://sandbot.cgfan.com/blog"
