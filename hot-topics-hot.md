# 热点文章素材 (生成时间: 2026-07-13 09:15)

## 话题 1
- 标题: Ask HN: Add flag for AI-generated articles
- 分数: 639 points
- URL: https://news.ycombinator.com/item?id=48886741
- 详细描述: HN 社区正在激烈讨论是否应该为 AI 生成的文章添加标记。HN 官方政策已禁止 AI 生成的评论和帖子，但对外部链接文章尚无类似规则。Dang（HN 编辑）指出社区对 AI 内容普遍反感——读者正在发展出对 LLM 语言的"过敏性反应"，一旦识别出 AI 写作风格，文章立刻被归入低地位类别。这形成了一个有趣的"军备竞赛"：AI 在训练人类数据，人类也在训练自己识别 AI。文中引用了 Paul Graham 的"writes and write-nots"概念，提出了一种新的阶层划分——使用 AI 写作 vs 不使用 AI 写作的分野。有趣的是，这反而给了人类作者一个优势：如果你想让读者把你的文章归为高地位，最简单的办法就是自己写。同时 Dang 强调这并非否定 LLM 技术本身——HN 重度依赖 AI 技术，问题在于如何正确使用它。
- 图片: N/A (Ask HN 帖子，无原始页面图片)

## 话题 2
- 标题: GhostLock — 存在 15 年的 Linux 内核 stack-UAF 漏洞 (CVE-2026-43499)
- 分数: 264 points
- URL: https://nebusec.ai/research/ionstack-part-2/
- 详细描述: Nebula Security 的 VEGA 项目发现了一个影响所有 Linux 发行版长达 15 年的内核漏洞 GhostLock (CVE-2026-43499)。该漏洞存在于 rtmutex（实时互斥锁）子系统中，自 Linux 2.6.39（2011年）引入，直到 2026 年 4 月才在 Linux 7.1 中修复。漏洞根源在于 remove_waiter() 函数在代理路径（proxy path）上错误地清除了 current->pi_blocked_on，导致内核栈上出现悬空指针（Use-After-Free）。攻击者可以利用常规线程系统调用触发此漏洞，实现 97% 稳定性的权限提升和容器逃逸。唯一要求是 CONFIG_FUTEX_PI=y，不需要任何特殊权限或用户命名空间。Google 在 kernelCTF 中为此漏洞奖励了 $92,337。该漏洞影响从 v2.6.39-rc1 到 v7.1-rc1 的所有 Linux 内核版本。
- 图片: N/A (readability 提取未获取 og:image)

---
*抓取完成: 2 个话题 | 耗时 ~20s | 无超时*
