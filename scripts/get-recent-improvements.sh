#!/bin/bash
# 获取最近5篇文章的改进建议
# 用法: bash get-recent-improvements.sh

cd /home/node/.openclaw/workspace/sandbot-blog/posts

echo "=== 最近文章改进建议 ==="
echo ""

# 找最近的5个.score.json文件
for f in $(ls -t *.score.json 2>/dev/null | head -5); do
    article=$(basename "$f" .score.json)
    improvements=$(python3 -c "
import json
with open('$f') as f:
    data = json.load(f)
imps = data.get('improvements', [])
if imps:
    for imp in imps:
        print(f'  • {imp}')
else:
    print('  (无改进建议)')
")
    
    echo "📄 $article:"
    echo "$improvements"
    echo ""
done
