#!/bin/bash
# 批量重新生成音频（修复SSML问题）
# 用法: ./scripts/regenerate-audio.sh

cd "$(dirname "$0")/.."

echo "🔊 批量重新生成音频（2026-08-01 之后）"
echo ""

# 需要重新生成的音频列表
AUDIO_FILES=(
  "2026-08-01-elevator-algorithm-deep-dive"
  "2026-08-02-diataxis-four-documentation-types"
  "2026-08-02-early-gemma4-13year-xeon"
  "2026-08-02-evening"
  "2026-08-02-noon-ai-financial-advice"
  "2026-08-02-suno-ai-copyright-germany"
  "2026-08-03-airllm-4gb-70b"
  "2026-08-03-early-airllm-4gb-70b"
  "2026-08-03-early-karpathy-pelican"
  "2026-08-03-evening-qwen38-max"
  "2026-08-03-noon-localai-inference-engines"
  "2026-08-04-afternoon-palantir-ai-marxist"
  "2026-08-04-evening-swiftlet"
  "2026-08-04-hot-gpt56-luna-price-cut"
  "2026-08-04-noon-llm-rewards-expertise"
  "2026-08-05-hot-shieldstral"
)

SUCCESS=0
FAILED=0

for base in "${AUDIO_FILES[@]}"; do
  ARTICLE="posts/${base}.html"
  AUDIO="posts/audio/${base}.mp3"
  
  # 检查文章是否存在
  if [ ! -f "$ARTICLE" ]; then
    echo "❌ 文章不存在: $ARTICLE"
    FAILED=$((FAILED+1))
    continue
  fi
  
  echo "📝 处理: $base"
  
  # 提取文本
  python3 scripts/extract-article-text.py "$ARTICLE" /tmp/tts-regen.txt 2>&1 | grep "✅"
  
  # 检查文本长度
  TEXT_LEN=$(wc -c < /tmp/tts-regen.txt)
  if [ "$TEXT_LEN" -lt 100 ]; then
    echo "   ⚠️  文本太短 ($TEXT_LEN 字符)，跳过"
    FAILED=$((FAILED+1))
    continue
  fi
  
  # 生成音频
  python3 scripts/edge-tts-human.py /tmp/tts-regen.txt "$AUDIO" zh-CN-YunxiNeural -10% 2>&1 | grep "✅"
  
  if [ -f "$AUDIO" ]; then
    SIZE=$(ls -lh "$AUDIO" | awk '{print $5}')
    echo "   ✅ 已生成 ($SIZE)"
    SUCCESS=$((SUCCESS+1))
  else
    echo "   ❌ 生成失败"
    FAILED=$((FAILED+1))
  fi
  
  echo ""
done

echo "================================"
echo "✅ 成功: $SUCCESS"
echo "❌ 失败: $FAILED"
echo ""
echo "📦 提交推送..."
git add posts/audio/
git commit -m "🔊 批量重新生成音频（修复SSML问题）"
git push
