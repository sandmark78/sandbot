# 早间文章素材 (生成时间: 2026-07-14 21:15)

## 话题 1
- 标题: Bonsai 27B: 首个能在手机上运行的 27B 级模型
- 分数: 218 points (72 comments)
- URL: https://prismml.com/news/bonsai-27b
- 详细描述: PrismML 发布 Bonsai 27B，基于 Qwen3.6 27B，是首个在手机端运行的 27B 级多模态模型。两个变体：Ternary 版（1.71 bit/weight，5.9GB，适合笔记本）和 1-bit 版（1.125 bit/weight，3.9GB，可装入 iPhone 17 Pro）。核心突破在于极低比特量化下仍保留 90-95% 的原始模型能力（15 项基准测试），支持多步推理、结构化工具调用、视觉任务和 computer-use agentic 循环。模型支持 262K token 上下文，兼容投机解码加速，Apache 2.0 开源。此前 1-bit 和 ternary 权重已被证明可产出商业可用的语言模型，Bonsai 27B 将这一前沿扩展到更高能力层级。
- 图片: 未提取（readability 模式未获取 og:image）

## 话题 2
- 标题: Cursor 0day：当完整披露成为唯一的保护手段
- 分数: 98 points (26 comments)
- URL: https://mindgard.ai/blog/cursor-0day-when-full-disclosure-becomes-the-only-protection-left
- 详细描述: Mindgard 于 2025 年 12 月 15 日发现并报告了 Cursor IDE 的严重安全漏洞：在 Windows 上，Cursor 加载项目时会自动搜索 git 二进制文件，包括当前工作区。攻击者只需在项目根目录放置恶意 git.exe，Cursor 无需用户任何交互就会自动执行，实现任意代码执行。该漏洞在 6 个月、197+ 个新版本后仍未修复。Cursor 拥有 700 万+ 活跃用户、100 万+ 日活、100 万+ 付费用户，估值 600 亿美元。漏洞利用极其简单——不需要提示注入、模型操纵、越狱或内存损坏，只需开发者打开一个包含恶意 git.exe 的项目。临时缓解方案：使用 AppLocker 或 Windows App Control 策略拒绝从开发者工作区目录执行可疑可执行文件。
- 图片: 未提取（readability 模式未获取 og:image）

---
*抓取完成：2/2 话题成功，总耗时 ~10 秒*
