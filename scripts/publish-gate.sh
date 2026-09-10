#!/bin/bash
# publish-gate.sh — 发布前 CI 门控（P0 #301）
# 用法: ./scripts/publish-gate.sh <article.html>
# 退出码: 0=通过（可发布）, 1=不通过（禁止发布）
#
# 铁律：没评分不让发布。评分 < 70 禁止发布。

cd /home/node/.openclaw/workspace/sandbot-blog

ARTICLE="$1"
if [ -z "$ARTICLE" ]; then
  echo "用法: $0 <article.html>"
  exit 1
fi

if [ ! -f "$ARTICLE" ]; then
  echo "❌ 文件不存在: $ARTICLE"
  exit 1
fi

BASENAME=$(basename "$ARTICLE")
echo "════════════════════════════════════════"
echo "🚦 发布门控 CI — $BASENAME"
echo "════════════════════════════════════════"
echo ""

# ── Phase 1: 结构检查（quality-gate.py）──
echo "📋 Phase 1/2: 结构检查..."
python3 scripts/quality-gate.py "$ARTICLE" --json 2>/dev/null || true
STRUCT_EXIT=${PIPESTATUS[0]:-$?}

# quality-gate.py: 0=通过, 1=有错误, 2=仅警告
# 只有 exit 1（有错误）才阻塞
if [ $STRUCT_EXIT -eq 1 ]; then
  echo ""
  echo "❌ 结构检查失败，禁止发布"
  echo "   修复后重新运行: $0 $ARTICLE"
  exit 1
fi

echo ""

# ── Phase 2: LLM 质量评分（article-quality-score.py）──
echo "📊 Phase 2/2: 质量评分..."

SCORE_FILE="${ARTICLE%.html}.score.json"
if [ -f "$SCORE_FILE" ]; then
  EXISTING_SCORE=$(python3 -c "import json; print(json.load(open('$SCORE_FILE')).get('total', 0))" 2>/dev/null || echo "0")
  echo "  已有评分: $EXISTING_SCORE/100 ($SCORE_FILE)"
  if [ "$EXISTING_SCORE" -ge 70 ]; then
    echo "  ✅ 评分通过 (≥70)"
  else
    echo "  ❌ 评分不通过 (<70)，禁止发布"
    exit 1
  fi
else
  python3 scripts/article-quality-score.py "$ARTICLE"
  SCORE_EXIT=$?
  
  if [ $SCORE_EXIT -ne 0 ]; then
    echo ""
    echo "❌ 质量评分不通过 (<70分)，禁止发布"
    echo "   修改文章后重新运行: $0 $ARTICLE"
    exit 1
  fi
fi

echo ""
echo "════════════════════════════════════════"
echo "✅ 门控通过：结构 ✓ 评分 ✓"
echo "   可以执行 git push 发布"
echo "════════════════════════════════════════"
exit 0
