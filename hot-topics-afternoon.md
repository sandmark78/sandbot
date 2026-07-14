# 下午热点素材 (生成时间: 2026-07-13 07:15)

## 话题 1: Claude Code 每次请求发送 33k tokens，而 OpenCode 只发 7k

- **标题**: Claude Code sends 33k tokens before reading the prompt; OpenCode sends 7k
- **分数**: 549 points | 310 comments
- **HN 链接**: https://news.ycombinator.com/item?id=48883275
- **原始 URL**: https://systima.ai (原文已 404，Cloudflare 拦截镜像站)
- **图片**: N/A (原始站点不可访问)

### 详细描述

Systima 团队在 agentic coding 工具（Claude Code 和 OpenCode）与 Anthropic API 端点之间加入了日志记录，捕获了所有请求及返回的 usage 数据。

**核心发现**：
- **Claude Code** 在读取用户 prompt 之前就发送约 **33,000 tokens** 的系统开销（包括 subagent 配置、MCP 工具定义、缓存重写、指令文件等）
- **OpenCode** 同样场景下只发送约 **7,000 tokens**
- Claude Code 的缓存策略和 harness token 使用效率远低于 OpenCode

**社区讨论热点**（310 条评论）：
- 企业用户应该记录和监控 AI 编码工具的实际 token 消耗
- Subagent、MCP 工具链和指令文件会让 token 开销成倍增长
- 这直接影响企业的 AI 编码工具账单成本
- 对 Anthropic 的缓存定价模型提出质疑

**写作角度建议**：
- "AI 编码工具的隐形成本：你付的钱有多少花在了系统 prompt 上？"
- 对比分析各 AI 编码工具的 token 效率
- 企业如何优化 AI 编码工具的成本

---

## 话题 2: GhostLock — 潜伏在所有 Linux 发行版 15 年的内核漏洞

- **标题**: GhostLock, a stack-UAF that has existed in all Linux distributions for 15 years
- **分数**: 226 points | 83 comments
- **HN 链接**: https://news.ycombinator.com/ (首页第 2 位)
- **原始 URL**: https://nebusec.ai/research/ionstack-part-2/
- **图片**: N/A (站点无公开 og:image)

### 详细描述

**GhostLock (CVE-2026-43499)** 是 Nebula Security 的 VEGA 团队发现的 Linux 内核漏洞，存在于自 2011 年以来的每个主要 Linux 发行版中。

**漏洞影响**：
- 无需特殊内核配置或权限即可触发
- 可实现 **97% 稳定性的权限提升和容器逃逸**
- Google 在 kernelCTF 中为此漏洞奖励了 **$92,337**

**技术细节**：
- 漏洞类型：Stack Use-After-Free (stack-UAF)
- 引入版本：Linux 2.6.39 (rtmutex 重构)
- 修复版本：Linux 7.1
- 影响范围：v2.6.39-rc1 到 v7.1-rc1
- 唯一前提条件：`CONFIG_FUTEX_PI=y`（大多数发行版默认开启）

**攻击链**：
1. 通过常规 threading syscalls 获取指向内核栈内存的悬空指针
2. 向几乎任意地址写入指针
3. 劫持函数表实现控制流劫持，最终获取 root 权限

**根本原因**：`remove_waiter()` 在 `kernel/locking/rtmutex.c` 中清除 `current->pi_blocked_on`，在正常慢速路径上是正确的，但在代理路径（proxy path）上是错误的——`rt_mutex_start_proxy_lock()` 代表另一个任务入队 rt_mutex_waiter，此时 current 是重排队者而非实际拥有者。

**写作角度建议**：
- "一个 15 年的 Linux 内核漏洞如何影响你所有的服务器"
- 容器安全：Docker/K8s 环境下的容器逃逸风险
- 开源安全审计的重要性：为什么代码审查不能只靠社区

---

## 其他值得关注的话题

| 排名 | 话题 | 分数 | 评论数 |
|------|------|------|--------|
| #6 | Ask HN: Add flag for AI-generated articles | 496 | 256 |
| #28 | What xAI's Grok CLI sends to xAI: wire-level analysis | 457 | 169 |
| #10 | How to read more books | 309 | 168 |
| #23 | Vint Cerf, "father of the Internet", is retiring | 302 | 177 |
| #18 | LARP – Revenue infrastructure for serious founders | 220 | 46 |
| #16 | Migrating production AI agent to GPT-5.6: 2.2x faster, 27% cheaper | 193 | 76 |
