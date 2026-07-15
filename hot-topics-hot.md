# 热点文章素材 (生成时间: 2026-07-15 09:15)

## 话题 1: Bonsai 27B — 首个能在手机上运行的 27B 模型
- 标题: Announcing Bonsai 27B: The First 27B-Class Model to Run on a Phone
- 分数: 584 points (HN #1 热门)
- URL: https://prismml.com/news/bonsai-27b
- HN 讨论: https://news.ycombinator.com/item?id=48910545 (209 comments)
- 详细描述:
  PrismML 发布 Bonsai 27B，基于 Qwen3.6 27B，是首个能在手机上运行的 27B 级别多模态模型。核心突破在于极低比特量化技术：Ternary 版本使用 {-1, 0, +1} 三值权重 + FP16 分组缩放，仅 5.9GB，可在普通笔记本运行；1-bit 版本使用 {-1, +1} 二值权重，仅 3.9GB，首次让 27B 级模型跑在 iPhone 17 Pro 上。两个版本均支持多模态（视觉塔 4-bit 压缩）、262K token 上下文、推测解码加速，且全网络无高精度逃逸路径。性能保留方面，Ternary 版保留原始精度 95% 的智能，1-bit 版保留 90%，在 15 项基准测试（知识、推理、数学、编码、工具调用、视觉）中表现优异。全部以 Apache 2.0 开源发布。这标志着端侧 AI 从"能用"进入"好用"阶段——多步推理、结构化调用、视觉任务和 agentic 循环均可在手机上完成。
- 图片: 未提取（页面未提供 og:image）

## 话题 2: Cursor 0day — 打开仓库即执行恶意代码
- 标题: Cursor 0day: When Full Disclosure Becomes the Only Protection Left
- 分数: 357 points (HN 热门)
- URL: https://mindgard.ai/blog/cursor-0day-when-full-disclosure-becomes-the-only-protection-left
- HN 讨论: https://news.ycombinator.com/item?id=48910676 (165 comments)
- 详细描述:
  Mindgard 安全研究团队披露 Cursor IDE（700 万+ 活跃用户、100 万+ 日活、估值 600 亿美元）的一个严重安全漏洞：在 Windows 上，当开发者用 Cursor 打开一个项目时，IDE 会自动在工作区根目录查找 git 二进制文件并执行。攻击者只需在仓库根目录放置一个恶意 git.exe，Cursor 就会在无任何用户交互、无提示、无警告的情况下自动执行它，实现任意代码执行。该漏洞于 2025 年 12 月 15 日首次发现并报告，经过 6 个月、197+ 个新版本迭代，问题至今未修复。漏洞利用极其简单——不需要提示注入、模型操纵、越狱或内存损坏，只需开发者打开含有恶意 git.exe 的项目即可。建议企业临时使用 AppLocker 或 Windows App Control 策略，在工作区目录拒绝执行特定可执行文件名。
- 图片: 未提取（页面未提供 og:image）

---
*抓取完成: 2/2 话题成功*
*总耗时: ~15 秒*
