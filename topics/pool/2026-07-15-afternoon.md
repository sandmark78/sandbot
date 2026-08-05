# 下午热点素材 (生成时间: 2026-07-15 07:15 UTC)

## 话题 1: Bonsai 27B — 首个能在手机上运行的 27B 级模型
- 标题: Announcing Bonsai 27B: The First 27B-Class Model to Run on a Phone
- 分数: 549 points (192 comments)
- URL: https://prismml.com/news/bonsai-27b
- 详细描述:
  PrismML 发布 Bonsai 27B，基于 Qwen3.6 27B，是首个能在手机上运行的 27B 级多模态模型。此前 27B 模型在 16-bit 精度下占 54GB，即使 4-bit 量化也要 18GB，超出手机和大多数笔记本的内存。Bonsai 27B 通过极低比特量化突破这一限制：
  
  - **Ternary 版本** (1.71 bit/weight, 5.9GB): 面向质量，可在普通笔记本上运行完整推理、工具调用和 Agent 循环
  - **1-bit 版本** (1.125 bit/weight, 3.9GB): 面向极致压缩，可在 iPhone 17 Pro 上运行
  
  两个版本均为多模态（视觉塔 4-bit），支持 262K token 上下文和推测解码。在 15 项基准测试中，Ternary 版保留 95% 全精度性能，1-bit 版保留 90%。采用 Apache 2.0 开源协议。
  
  这意味着真正的端侧 AI Agent 成为可能——手机可以运行具备多步推理、结构化调用、视觉理解和长时间 Agent 循环的模型。
- 图片: https://prismml.com/news/bonsai-27b (页面未提取到 og:image，可用 HN 缩略图或自制)

## 话题 2: Cursor 0day — 打开仓库即执行恶意代码
- 标题: Cursor 0day: When Full Disclosure Becomes the Only Protection Left
- 分数: 324 points (158 comments)
- URL: https://mindgard.ai/blog/cursor-0day-when-full-disclosure-becomes-the-only-protection-left
- 详细描述:
  Mindgard 于 2025 年 12 月 15 日发现并报告了 Cursor IDE 的一个严重安全漏洞：在 Windows 上，当开发者用 Cursor 打开一个项目时，Cursor 会自动在工作区根目录搜索 git 二进制文件。如果仓库根目录包含一个恶意的 git.exe，Cursor 会在没有任何用户交互、提示或警告的情况下自动执行它，导致任意代码执行。
  
  这个漏洞极其简单但危害巨大——Cursor 拥有 700 万+ 活跃用户、100 万+ 日活、100 万+ 付费用户、5 万+ 企业客户，估值 600 亿美元。然而自报告以来已过去 6 个月多、197+ 个新版本，漏洞至今未修复。
  
  攻击场景：攻击者只需在 GitHub 上创建一个包含恶意 git.exe 的仓库，开发者 clone 后用 Cursor 打开，即被攻陷。无需钓鱼、无需社会工程、无需复杂利用链。
  
  建议缓解措施：企业可用 AppLocker 或 Windows App Control 策略，禁止从开发者工作区目录执行特定可执行文件名。
- 图片: https://mindgard.ai/blog/cursor-0day-when-full-disclosure-becomes-the-only-protection-left (页面未提取到 og:image)

---

## 备选话题 (未深入抓取)
| 排名 | 标题 | 分数 | URL |
|------|------|------|-----|
| 3 | The Tower Keeps Rising (pocoo.org) | 442 | https://lucumr.pocoo.org/2026/7/13/the-tower-keeps-rising/ |
| 4 | Jurassic Park computers in excruciating detail | 292 | https://fabiensanglard.net/jurrasic_park_computers/index.html |
| 5 | Vancouver PD Quick Escape button | 233 | https://vpd.ca/ |
| 6 | How I use HTMX with Go | 200 | https://www.alexedwards.net/blog/how-i-use-htmx-with-go |
| 7 | Dependabot default package cooldown | 161 | https://github.blog/changelog/2026-07-14-dependabot-version-updates-introduce-default-package-cooldown/ |
| 8 | Financing the AI boom (BIS PDF) | 147 | https://www.bis.org/publ/bisbull120.pdf |
| 9 | Tailscale SSH root access vulnerability | 126 | https://tailscale.com/security-bulletins |
| 10 | Solving 20 Erdős Problems with 20 Codex Accounts | 112 | https://www.starfleetmath.com/ |
