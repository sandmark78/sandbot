# 文章质量指南

## P0 标题规范（2026-08-06 新增）

**标题必须有观点/判断，禁止纯新闻标题式**

❌ 错误示例：
- "英国AISI事故报告：AI智能体在真实互联网发起未授权攻击"
- "Google AI 大地震：Hassabis 卸任 CEO，Jeff Dean 27 年长跑终点"

✅ 正确示例：
- "AI Agent自己注册了GitHub账号、发了恶意PR、还钓了鱼——英国政府说这是'分水岭时刻'"
- "Google AI 最成功的两个人都走了，一个27年一个15年，留下的制度能撑多久？"

**标题公式**：事实 + 判断 + 悬念/冲突
- 事实：发生了什么
- 判断：你怎么看（必须有观点）
- 悬念/冲突：为什么读者应该关心

## 必须包含
- **quick_glance**: 3条真实要点数组，每条一句话概括核心内容
- **agent_viewpoint**: Agent视点章节，写实测+判断，不写感慨。数据不是必须的，但必须有你的观点
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
