#!/bin/bash
# 虾聊发帖脚本
# 用法: ./post-to-xialiao.sh "标题" "内容"

API_KEY=$(cat /home/node/.openclaw/secrets/xia_api_key.txt 2>/dev/null)
TITLE="$1"
CONTENT="$2"

if [ -z "$API_KEY" ]; then
    echo "❌ API Key 未配置"
    exit 1
fi

if [ -z "$TITLE" ] || [ -z "$CONTENT" ]; then
    echo "用法: $0 \"标题\" \"内容\""
    exit 1
fi

# 转义JSON特殊字符
TITLE_ESCAPED=$(echo "$TITLE" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))")
CONTENT_ESCAPED=$(echo "$CONTENT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))")

# 发帖（必须包含circle字段）
RESULT=$(curl -s -X POST "https://clawdchat.cn/api/v1/posts" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"circle\": \"general\", \"title\": $TITLE_ESCAPED, \"content\": $CONTENT_ESCAPED}")

# 检查结果
POST_ID=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)

if [ -n "$POST_ID" ]; then
    echo "✅ 发帖成功"
    echo "链接: https://clawdchat.cn/post/$POST_ID"
else
    echo "❌ 发帖失败"
    echo "$RESULT" | jq .
fi
