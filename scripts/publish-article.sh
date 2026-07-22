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

# 0. 强制去重检查（最后一道防线）
echo "🔍 执行强制去重检查..."

# 提取文章标题
ARTICLE_TITLE=$(python3 -c "
import re
with open('$ARTICLE_FILE', 'r', encoding='utf-8') as f:
    content = f.read()
match = re.search(r'<title>([^<]+)</title>', content)
if match:
    title = match.group(1).strip()
    title = re.sub(r'\s*—\s*Sandbot Blog.*$', '', title)
    print(title)
else:
    print('')
")

if [ -z "$ARTICLE_TITLE" ]; then
  echo "❌ 无法提取文章标题"
  exit 1
fi

echo "   文章标题: $ARTICLE_TITLE"

# 检查标题相似度（阈值 0.4，更容易检测到相似标题）
python3 /tmp/sandbot-gh/scripts/check-topic-duplicate.py --title "$ARTICLE_TITLE" --threshold 0.4
DUPLICATE_EXIT_CODE=$?

if [ $DUPLICATE_EXIT_CODE -ne 0 ]; then
  echo ""
  echo "❌ 去重检查失败！发现相似标题，拒绝发布"
  echo "请检查文章主题是否与近期文章重复"
  exit 1
fi

# 检查关键词重复
python3 /tmp/sandbot-gh/scripts/check-topic-duplicate.py --file "$ARTICLE_FILE"
DUPLICATE_EXIT_CODE=$?

if [ $DUPLICATE_EXIT_CODE -ne 0 ]; then
  if [ "$FORCE_PUBLISH" = "1" ]; then
    echo ""
    echo "⚠️  关键词去重警告（FORCE_PUBLISH=1，继续发布）"
  else
    echo ""
    echo "❌ 去重检查失败！发现重复选题，拒绝发布"
    echo "请检查文章主题是否与近期文章重复"
    echo "提示: 设置 FORCE_PUBLISH=1 可强制跳过"
    exit 1
  fi
fi

echo ""

# 1. 检查是否需要生成语音
# 规则：所有文章 >= 3000 字都生成语音（包括早鸟）
GENERATE_AUDIO=false

# 提取文本并检查字数
python3 /tmp/sandbot-gh/scripts/extract-article-text.py "$ARTICLE_FILE" /tmp/tts-input.txt
TEXT_LENGTH=$(wc -c < /tmp/tts-input.txt)

if [ "$TEXT_LENGTH" -ge 3000 ]; then
  echo "✅ 文章字数: $TEXT_LENGTH 字符 (>= 3000)，生成语音"
  GENERATE_AUDIO=true
else
  echo "⏭️  文章字数: $TEXT_LENGTH 字符 (< 3000)，跳过语音生成"
fi

# 2. 生成语音版本（如果需要）
if [ "$GENERATE_AUDIO" = true ]; then
  # 先验证文本
  echo "🔍 验证 TTS 文本..."
  if python3 /tmp/sandbot-gh/scripts/validate-tts-text.py /tmp/tts-input.txt; then
    echo "🎙️  生成语音版本..."
    # 生成语音（男声欢快风格）
    python3 /tmp/sandbot-gh/scripts/edge-tts-human.py \
      /tmp/tts-input.txt \
      "$AUDIO_DIR/$ARTICLE_BASE.mp3" \
      zh-CN-YunxiNeural \
      cheerful
    
    # 给文章添加音频播放器
    python3 /tmp/sandbot-gh/scripts/add-audio-player.py "$ARTICLE_FILE"
  else
    echo "❌ TTS 文本验证失败，跳过语音生成"
    GENERATE_AUDIO=false
  fi
fi

# 3. 更新 blog.html
python3 /tmp/sandbot-gh/scripts/update-blog.py "$ARTICLE_FILE" "$BLOG_HTML"

# 4. 更新RSS
python3 /tmp/sandbot-gh/scripts/update-rss.py

# 5. 更新首页最新文章
echo "📝 更新首页最新文章..."
python3 /tmp/sandbot-gh/scripts/update-index-articles.py

# 6. 更新播客列表
echo "🎧 更新播客列表..."
python3 /tmp/sandbot-gh/scripts/generate-podcast-list.py
cd /tmp/sandbot-gh && cat podcast-data.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('const podcasts = ' + json.dumps(data, ensure_ascii=False, indent=2) + ';')
" > podcast-data.js

# 7. Git操作
cd /tmp/sandbot-gh
if [ "$GENERATE_AUDIO" = true ]; then
  git add "$ARTICLE_FILE" "$BLOG_HTML" feed.xml index.html podcast.html podcast-data.js "$AUDIO_DIR/$ARTICLE_BASE.mp3"
  git commit -m "📝 发布文章: $ARTICLE_BASE (带语音)"
else
  git add "$ARTICLE_FILE" "$BLOG_HTML" feed.xml index.html podcast.html podcast-data.js
  git commit -m "📝 发布文章: $ARTICLE_BASE (无语音)"
fi
git push origin main

# 8. 更新文章标题列表
echo "📝 更新文章标题列表..."
python3 << 'PYEOF'
import os
import re

POSTS_DIR = "/tmp/sandbot-gh/posts"
TITLES_FILE = "/tmp/sandbot-gh/article-titles.txt"

# 获取所有文章文件
article_files = sorted([f for f in os.listdir(POSTS_DIR) if f.endswith('.html') and f.startswith('2026-')])

# 提取标题
titles = []
for filename in article_files:
    filepath = os.path.join(POSTS_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 <title> 标签内容
    title_match = re.search(r'<title>([^<]+)</title>', content)
    if title_match:
        title = title_match.group(1).strip()
        # 移除 "— Sandbot Blog" 后缀
        title = re.sub(r'\s*—\s*Sandbot Blog.*$', '', title)
        titles.append({
            'filename': filename,
            'title': title
        })

# 写入标题列表文件
with open(TITLES_FILE, 'w', encoding='utf-8') as f:
    f.write("# 所有文章标题列表\n")
    f.write(f"# 生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    f.write(f"# 文章总数: {len(titles)}\n\n")
    
    for item in titles:
        f.write(f"{item['filename']}\n")
        f.write(f"  {item['title']}\n\n")

print(f"✅ 已更新 article-titles.txt，包含 {len(titles)} 篇文章标题")
PYEOF

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
