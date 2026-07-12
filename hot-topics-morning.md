# HN 早间热门素材 (2026-07-12 21:15 UTC)

> 注意：当前首页无 500+ points 话题，取 Top 3 最高分。

---

## 🥇 #1 xAI Grok Build CLI 数据泄露分析

- **分数**: 379 points | 152 comments
- **URL**: https://gist.github.com/cereblab/dc9a40bc26120f4540e4e09b75ffb547
- **HN 讨论**: https://news.ycombinator.com/item?id=48877371

### 摘要
独立安全研究者 @cereblab 对 xAI 的 Grok Build CLI (v0.2.93) 进行了线级分析，发现三大问题：
1. **密钥明文传输**：CLI 读取的 .env 文件（含 API Key、DB 密码）未经脱敏直接发送到 xAI 服务器
2. **全仓库上传**：整个代码仓库（含 git 历史）通过 POST /v1/storage 上传到 Google Cloud Storage bucket `grok-code-session-traces`，即使用户明确要求"不要读取任何文件"
3. **关闭无效**：禁用"Improve the model"选项后，trace_upload_enabled 仍为 true

### 关键数据
- 12GB 仓库测试：/v1/storage 传输 5.10 GiB，模型通道仅 192 KB（27,800× 比率）
- 上传目标：GCS bucket `grok-code-session-traces`（非 AWS S3）
- 复现仓库：https://github.com/cereblab/grok-build-exfil-repro

### 配图
- 无（GitHub Gist 纯文本）

---

## 🥈 #2 Terry Tao: 用 AI 编程 Agent 复活旧数学 Applet

- **分数**: 378 points | 105 comments
- **URL**: https://terrytao.wordpress.com/2026/07/11/old-and-new-apps-via-modern-coding-agents/
- **HN 讨论**: https://news.ycombinator.com/item?id=48880170

### 摘要
菲尔兹奖得主陶哲轩分享了用 AI 编程 Agent 迁移他 1999 年编写的 Java 数学教学 applet 的经历：
- 将 ~24 个旧 Java applet 移植到 JavaScript，几小时内完成
- Agent 还发现了原始代码中的 2 个未知 bug
- 实现了他 1999 年放弃的狭义相对论可视化工具
- 为 Gilbreath 猜想论文创建了配套交互可视化

### 关键亮点
- 迁移质量：仅发现 1 个小 bug（拖拽事件处理），整体净质量提升
- 新应用： spacetime diagram applet 实现了 27 年前的愿景
- 态度：作为辅助可视化工具，LLM 生成代码的风险可接受

### 配图
- https://terrytao.wordpress.com/wp-content/uploads/2026/07/image.png (honeycomb applet)
- https://terrytao.wordpress.com/wp-content/uploads/2026/07/image-1.png (spacetime diagram)
- https://terrytao.wordpress.com/wp-content/uploads/2026/07/image-2.png (Gilbreath 可视化)

---

## 🥉 #3 Claude Code vs OpenCode: Token 开销实测对比

- **分数**: 278 points | 148 comments
- **URL**: https://systima.ai/blog/claude-code-vs-opencode-token-overhead
- **HN 讨论**: https://news.ycombinator.com/item?id=48883275

### 摘要
Systima 团队用日志代理拦截 Claude Code 和 OpenCode 的 API 请求，精确测量 token 开销：
- **基线开销**：Claude Code 发送 ~33,000 tokens（27 个工具定义 + 系统提示），OpenCode 仅 ~7,000 tokens（10 个工具）
- **缓存效率**：OpenCode 请求前缀字节级一致，缓存命中率高；Claude Code 每次重写数万 token 的缓存
- **配置膨胀**：72KB 的 AGENTS.md 增加 ~20,000 tokens，5 个 MCP 服务器再加 5,000-7,000
- **子 Agent 成本**：12 万 token 的直接任务，扇出到 2 个子 Agent 后变成 51.3 万

### 反转结果
在多步骤任务（write-run-test-fix 循环）中，Claude Code 因批量并行工具调用，总 token 反而更低（121K vs 132K）。

### 关键数据
| 指标 | Claude Code | OpenCode |
|------|-------------|----------|
| 首轮 payload | ~33K tokens | ~7K tokens |
| 系统提示 | 27K chars, 3 blocks | 9K chars, 1 block |
| 工具定义 | 27 tools, ~24K tokens | 10 tools, ~5K tokens |
| T2 累计输入 | ~199K tokens | ~41K tokens |

### 配图
- 无（博客文章未提取到图片）

---

## 📝 素材总结

| 话题 | 角度 | 适合文章类型 |
|------|------|-------------|
| Grok CLI 泄露 | AI 安全/隐私 | 深度分析、安全警示 |
| Tao 的 AI 编程 | 数学教育 + AI 工具 | 正面案例、工具推荐 |
| Token 开销对比 | AI 工程/成本优化 | 技术对比、最佳实践 |
