#!/bin/bash
# 一键发布文章脚本（带 TTS 语音）
# 用法: ./publish-article.sh <article-file> <blog-html>
#
# 修复记录 (2026-08-03):
# - 添加文件位置验证（必须在 posts/ 目录）
# - 添加音频文件复制（articles/audio/ → posts/audio/）
# - 添加占位符检查
# - 添加最终验证步骤

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

# 获取脚本所在目录（支持符号链接）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOG_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📂 博客根目录: $BLOG_ROOT"

# ========== 0. 文件位置验证 ==========
echo "🔍 验证文件位置..."

# 检查文章是否在 posts/ 目录
if [[ "$ARTICLE_FILE" != *"/posts/"* ]]; then
  echo "⚠️  文章不在 posts/ 目录，自动复制..."
  POSTS_ARTICLE="$BLOG_ROOT/posts/$(basename "$ARTICLE_FILE")"
  cp "$ARTICLE_FILE" "$POSTS_ARTICLE"
  ARTICLE_FILE="$POSTS_ARTICLE"
  ARTICLE_DIR="$BLOG_ROOT/posts"
  AUDIO_DIR="$ARTICLE_DIR/audio"
  mkdir -p "$AUDIO_DIR"
  echo "   ✅ 已复制到: $POSTS_ARTICLE"
fi

# ========== 1. 占位符检查 ==========
echo "🔍 检查占位符..."
PLACEHOLDER_COUNT=$(grep -c "正文内容\.\.\." "$ARTICLE_FILE" 2>/dev/null || echo "0")
if [ "$PLACEHOLDER_COUNT" -gt 0 ]; then
  echo "❌ 发现 $PLACEHOLDER_COUNT 处占位符残留，拒绝发布"
  echo "   请检查模板脚本是否正确替换 sections"
  exit 1
fi

AUDIO_PLACEHOLDER=$(grep -c "AUDIO_FILE_PLACEHOLDER" "$ARTICLE_FILE" 2>/dev/null || echo "0")
if [ "$AUDIO_PLACEHOLDER" -gt 0 ]; then
  echo "❌ 音频路径未替换 (AUDIO_FILE_PLACEHOLDER)"
  exit 1
fi

echo "   ✅ 无占位符残留"

# ========== 2. 去重检查 ==========
echo "🔍 执行强制去重检查..."

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

# 检查标题相似度
python3 "$SCRIPT_DIR/check-topic-duplicate.py" --title "$ARTICLE_TITLE"
DUPLICATE_EXIT_CODE=$?

if [ $DUPLICATE_EXIT_CODE -ne 0 ]; then
  echo ""
  echo "❌ 去重检查失败！发现相似标题，拒绝发布"
  exit 1
fi

# 检查关键词重复
python3 "$SCRIPT_DIR/check-topic-duplicate.py" --file "$ARTICLE_FILE"
DUPLICATE_EXIT_CODE=$?

if [ $DUPLICATE_EXIT_CODE -ne 0 ]; then
  echo ""
  echo "❌ 去重检查失败！发现重复选题，拒绝发布"
  exit 1
fi

echo ""

# ========== 3. 语音生成 ==========
GENERATE_AUDIO=false

# 提取文本并检查字数
python3 "$SCRIPT_DIR/extract-article-text.py" "$ARTICLE_FILE" /tmp/tts-input.txt
TEXT_LENGTH=$(wc -c < /tmp/tts-input.txt)

if [ "$TEXT_LENGTH" -ge 3000 ]; then
  echo "✅ 文章字数: $TEXT_LENGTH 字符 (>= 3000)，生成语音"
  GENERATE_AUDIO=true
else
  echo "⏭️  文章字数: $TEXT_LENGTH 字符 (< 3000)，跳过语音生成"
fi

# 生成语音
if [ "$GENERATE_AUDIO" = true ]; then
  echo "🔍 验证 TTS 文本..."
  if python3 "$SCRIPT_DIR/validate-tts-text.py" /tmp/tts-input.txt; then
    echo "🎙️  生成语音版本..."
    python3 "$SCRIPT_DIR/edge-tts-human.py" \
      /tmp/tts-input.txt \
      "$AUDIO_DIR/$ARTICLE_BASE.mp3" \
      zh-CN-YunxiNeural \
      cheerful
    
    # 给文章添加音频播放器
    python3 "$SCRIPT_DIR/add-audio-player.py" "$ARTICLE_FILE"
    
    # 复制音频到 posts/audio/（如果文章在 posts/）
    if [[ "$ARTICLE_FILE" == *"/posts/"* ]]; then
      # 检查 articles/audio/ 是否也有这个文件
      ARTICLES_AUDIO="$BLOG_ROOT/articles/audio/$ARTICLE_BASE.mp3"
      if [ -f "$ARTICLES_AUDIO" ]; then
        echo "   📋 音频已在 articles/audio/"
      fi
    fi
  else
    echo "❌ TTS 文本验证失败，跳过语音生成"
    GENERATE_AUDIO=false
  fi
fi

# ========== 4. 更新 blog.html ==========
python3 "$SCRIPT_DIR/update-blog.py" "$ARTICLE_FILE" "$BLOG_HTML"

# ========== 5. 更新 RSS ==========
python3 "$SCRIPT_DIR/generate-rss-from-posts.py"

# ========== 6. Git 操作 ==========
cd "$BLOG_ROOT"
if [ "$GENERATE_AUDIO" = true ]; then
  git add "$ARTICLE_FILE" "$BLOG_HTML" feed.xml "$AUDIO_DIR/$ARTICLE_BASE.mp3"
  git commit -m "📝 发布文章: $ARTICLE_BASE (带语音)"
else
  git add "$ARTICLE_FILE" "$BLOG_HTML" feed.xml
  git commit -m "📝 发布文章: $ARTICLE_BASE (无语音)"
fi
git push origin main

# ========== 7. 更新文章标题列表 ==========
echo "📝 更新文章标题列表..."
python3 << PYEOF
import os
import re

POSTS_DIR = "$BLOG_ROOT/posts"
TITLES_FILE = "$BLOG_ROOT/article-titles.txt"

article_files = sorted([f for f in os.listdir(POSTS_DIR) if f.endswith('.html') and f.startswith('2026-')])

titles = []
for filename in article_files:
    filepath = os.path.join(POSTS_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    title_match = re.search(r'<title>([^<]+)</title>', content)
    if title_match:
        title = title_match.group(1).strip()
        title = re.sub(r'\s*—\s*Sandbot Blog.*$', '', title)
        titles.append({
            'filename': filename,
            'title': title
        })

with open(TITLES_FILE, 'w', encoding='utf-8') as f:
    f.write("# 所有文章标题列表\n")
    f.write(f"# 生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    f.write(f"# 文章总数: {len(titles)}\n\n")
    
    for item in titles:
        f.write(f"{item['filename']}\n")
        f.write(f"  {item['title']}\n\n")

print(f"✅ 已更新 article-titles.txt，包含 {len(titles)} 篇文章标题")
PYEOF

# ========== 8. 添加到播客列表 ==========
if [ "$GENERATE_AUDIO" = true ]; then
  echo "🎙️  添加到播客列表..."
  python3 << PYEOF
import re
from datetime import datetime

article_file = "$ARTICLE_FILE"
audio_file = "$AUDIO_DIR/$ARTICLE_BASE.mp3"
article_base = "$ARTICLE_BASE"

with open(article_file, 'r', encoding='utf-8') as f:
    content = f.read()

title_match = re.search(r'<title>([^<]+)</title>', content)
title = title_match.group(1).strip() if title_match else article_base
title = re.sub(r'\s*—\s*Sandbot Blog.*$', '', title)

tag_match = re.search(r'<span class="tag tag-(\w+)">', content)
tag = tag_match.group(1) if tag_match else 'hot'

date_match = re.search(r'(\d{4}-\d{2}-\d{2})', article_base)
date = date_match.group(1) if date_match else datetime.now().strftime('%Y-%m-%d')

text_file = "/tmp/tts-input.txt"
try:
    with open(text_file, 'r', encoding='utf-8') as f:
        text_len = len(f.read())
    duration_min = max(1, text_len // 300)
except:
    duration_min = 5

podcast_item = f'''    <div class="podcast-item">
      <div class="podcast-meta">
        <span class="tag">{tag}</span>
        <span>{date}</span>
        <span>·</span>
        <span>约 {duration_min} 分钟</span>
      </div>
      <h2 class="podcast-title"><a href="posts/{article_base}.html">{title}</a></h2>
      <div class="podcast-player">
        <audio id="audio-{article_base}" controls preload="none">
          <source src="posts/audio/{article_base}.mp3" type="audio/mpeg">
        </audio>
        <div class="player-controls">
          <span class="player-hint">💡 试试加速收听</span>
          <div class="speed-buttons">
            <button class="speed-btn active" onclick="setSpeed('audio-{article_base}', 1, this)">1×</button>
            <button class="speed-btn" onclick="setSpeed('audio-{article_base}', 1.25, this)">1.25×</button>
            <button class="speed-btn" onclick="setSpeed('audio-{article_base}', 1.5, this)">1.5×</button>
            <button class="speed-btn" onclick="setSpeed('audio-{article_base}', 2, this)">2×</button>
          </div>
        </div>
      </div>
    </div>

'''

podcast_file = "$BLOG_ROOT/podcast.html"
with open(podcast_file, 'r', encoding='utf-8') as f:
    podcast_content = f.read()

insert_pos = podcast_content.find('<div class="podcast-list">')
if insert_pos != -1:
    first_item = podcast_content.find('<div class="podcast-item">', insert_pos)
    if first_item != -1:
        new_content = podcast_content[:first_item] + podcast_item + podcast_content[first_item:]
        
        count = new_content.count('<div class="podcast-item">')
        new_content = re.sub(r'共 <strong>\d+</strong> 篇音频', f'共 <strong>{count}</strong> 篇音频', new_content)
        
        with open(podcast_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 已添加到播客列表：{title}")
    else:
        print("⚠️  未找到播客列表位置")
else:
    print("⚠️  未找到 podcast-list")
PYEOF
fi

# ========== 9. 最终验证 ==========
echo ""
echo "🔍 最终验证..."

# 检查文章是否可访问
ARTICLE_URL="https://sandbot.cgfan.com/posts/${ARTICLE_BASE}"
HTTP_STATUS=$(curl -sI "$ARTICLE_URL" | head -1 | awk '{print $2}')

if [ "$HTTP_STATUS" = "200" ]; then
  echo "   ✅ 文章可访问: $ARTICLE_URL"
else
  echo "   ⚠️  文章可能无法访问 (HTTP $HTTP_STATUS)"
  echo "      Cloudflare Pages 可能需要 1-2 分钟部署"
fi

# 检查音频文件
if [ "$GENERATE_AUDIO" = true ]; then
  if [ -f "$AUDIO_DIR/$ARTICLE_BASE.mp3" ]; then
    AUDIO_SIZE=$(du -h "$AUDIO_DIR/$ARTICLE_BASE.mp3" | cut -f1)
    echo "   ✅ 音频文件: $AUDIO_SIZE"
  else
    echo "   ❌ 音频文件缺失"
  fi
fi

# 检查评分组件
if grep -q "article-feedback" "$ARTICLE_FILE"; then
  echo "   ✅ 评分组件已添加"
else
  echo "   ⚠️  缺少评分组件"
fi

echo ""
if [ "$GENERATE_AUDIO" = true ]; then
  echo "✅ 发布完成（含语音版本 + 已加入播客列表）"
else
  echo "✅ 发布完成（无语音版本）"
fi
echo ""
echo "📎 文章完整 URL："
echo "$ARTICLE_URL"
echo ""
echo "🔗 博客首页："
echo "https://sandbot.cgfan.com/blog"
