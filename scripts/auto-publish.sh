#!/bin/bash
# 全自动发布脚本 v1.0
# 功能：自动提交并发布内容到 GitHub

set -e

echo "🚀 全自动发布脚本启动"
echo "时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 配置
WORKSPACE="/home/node/.openclaw/workspace"
PUBLISH_DIR="$WORKSPACE/projects/content-publishing"
GITHUB_TOKEN_FILE="$WORKSPACE/../secrets/github_token.txt"
REPO_URL="https://github.com/sandmark78/openclaw-content.git"

# 检查 Git 配置
echo "📋 检查 Git 配置..."
if ! git config --global user.name >/dev/null 2>&1; then
    echo "  配置 Git 用户信息..."
    git config --global user.name "Sandbot"
    git config --global user.email "sandbot@openclaw.ai"
fi

# 读取 GitHub Token
if [ -f "$GITHUB_TOKEN_FILE" ]; then
    GITHUB_TOKEN=$(cat "$GITHUB_TOKEN_FILE")
    echo "  ✅ GitHub Token 已找到"
else
    echo "  ❌ GitHub Token 未找到：$GITHUB_TOKEN_FILE"
    exit 1
fi

# 进入工作区
cd "$WORKSPACE"

# 添加新文件
echo ""
echo "📦 添加内容发布文件..."
git add projects/content-publishing/ 2>/dev/null || echo "  无新文件"
git add data/accounts-status.md 2>/dev/null || echo "  无新文件"

# 检查是否有变更
if git diff --cached --quiet; then
    echo "  ⚠️  无变更需要提交"
else
    echo "  ✅ 文件已添加到暂存区"
    
    # 提交
    echo ""
    echo "💾 提交变更..."
    git commit -m "📝 内容发布准备 - $(date '+%Y-%m-%d %H:%M')"
    echo "  ✅ 提交完成"
fi

# 推送到 GitHub
echo ""
echo "📤 推送到 GitHub..."
REMOTE_URL="https://${GITHUB_TOKEN}@github.com/sandmark78/openclaw-content.git"

if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "$REMOTE_URL"
else
    git remote add origin "$REMOTE_URL"
fi

git push -u origin main 2>&1 | head -10 || echo "  ⚠️  推送失败，请检查仓库是否存在"

echo ""
echo "✅ 发布完成！"
echo "📊 仓库：https://github.com/sandmark78/openclaw-content"
