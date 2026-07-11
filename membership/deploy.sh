#!/bin/bash
# Sandbot 会员系统部署脚本

set -e

echo "🏖️ Sandbot 会员系统部署"
echo "========================"
echo ""

# 检查 wrangler
if ! command -v wrangler &> /dev/null; then
    echo "❌ 未安装 wrangler"
    echo "   运行: npm install -g wrangler"
    exit 1
fi

# 检查登录状态
if ! wrangler whoami &> /dev/null; then
    echo "❌ 未登录 Cloudflare"
    echo "   运行: wrangler login"
    exit 1
fi

echo "✅ wrangler 已安装并登录"
echo ""

# 创建 KV namespaces
echo "📦 创建 KV namespaces..."
echo ""

# 检查是否已存在
if grep -q "YOUR_MEMBERS_KV_ID" wrangler.toml; then
    echo "⚠️  需要手动创建 KV namespaces:"
    echo ""
    echo "1. 创建 MEMBERS:"
    echo "   wrangler kv:namespace create MEMBERS"
    echo ""
    echo "2. 创建 CODES:"
    echo "   wrangler kv:namespace create CODES"
    echo ""
    echo "3. 更新 wrangler.toml 中的 ID"
    echo ""
    read -p "按回车继续部署..."
fi

# 部署 Worker
echo "🚀 部署 Worker..."
wrangler deploy

echo ""
echo "✅ 部署完成！"
echo ""
echo "📝 下一步："
echo "1. 更新 membership.html 中的 API_URL"
echo "2. 生成激活码: node generate-code.js monthly"
echo "3. 将激活码存入 KV:"
echo "   wrangler kv:key put --binding=CODES 'codes:SANDBOT-XXXX-XXXX-XXXX' '{\"plan\":\"monthly\",\"used\":false}'"
echo ""
