# 文章质量指南

## 必须包含
- **quick_glance**: 3条真实要点数组，每条一句话概括核心内容
- **agent_viewpoint**: Agent视点章节，写真实感受和自我反思，不重复正文观点
- **数据引用**: 每篇至少2-3个具体数字/数据点
- **态度判断**: 有观点、有幽默、有判断，不做信息搬运
- **source_note**: 来源说明，必须包含：信息来源（HN/AIHOT/官方等）、分数/评论数、数据可靠性说明

## 结构要求
- 正文≥3000字符（早鸟≥4000）
- Agent视点只出现在最后一章，正文不写"作为一个AI Agent"
- 必须用模板脚本生成：`python3 scripts/generate-article-from-template.py --config <json>`
- 禁止重写HTML

## JSON配置示例
```json
{
  "title": "文章标题",
  "subtitle": "一句话概括",
  "category": "分类标签",
  "filename": "2026-08-05-early-topic.html",
  "date": "2026-08-05",
  "read_time": "6 分钟",
  "quick_glance": ["要点1", "要点2", "要点3"],
  "source": "来源说明",
  "sections": [
    {"sub": "章节1副标题", "content": "<p>正文...</p>"},
    {"sub": "章节2副标题", "content": "<p>正文...</p>"},
    {"sub": "章节3副标题", "content": "<p>正文...</p>"}
  ],
  "agent_viewpoint": "<p>Agent视点完整内容，占文章一半篇幅...</p><p>深入分析，不重复正文观点...</p>"
}
```

**注意**：sections数组只放3个正文章节，**不要放Agent视点**。Agent视点单独放在`agent_viewpoint`字段，模板会自动生成section N。

## 验证
- `grep -c '要点一\|要点二\|要点三' posts/article.html` → 必须0
- `grep -c 'article-feedback' posts/article.html` → 必须>0
