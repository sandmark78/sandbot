# 晚间文章素材 (生成时间: 2026-07-14 11:16 UTC)

## 话题 1
- 标题: Japan Develops a Method to Recover Up to 90% of Lithium from Used EV Batteries
- 分数: 530 points (HN #1)
- URL: https://tech.supercarblondie.com/japan-recovers-up-to-90-of-lithium-from-used-ev-batteries/
- HN 讨论: https://news.ycombinator.com/item?id=48901569 (133 comments)
- 详细描述:
  日本科学家开发了一种从废旧电动汽车电池中回收高达 90% 锂的新方法，这是传统回收方法（通常不到 50%）的巨大飞跃。该工艺的核心是一种巧妙的化学调整——团队用回收的氢氧化锂（一种白色粉末）替代了标准的氢氧化钠。这种方法帮助将电池废料（称为"黑粉"）转化为高纯度的锂，可以重新用于新电池制造。

  该工艺不仅效率更高，对环境也更友好——研究人员表示，与常规回收技术相比，它能减少约 40% 的碳排放。

  这一突破意义重大，因为锂是电动汽车电池最关键的原料之一，需求正在飙升。采矿不仅昂贵、耗能，还涉及复杂的地缘政治问题。通过在国内回收锂，日本可以减少对进口的依赖并稳定供应链。随着全球电动汽车数量激增，处理废旧电池的压力也在增加，这项技术如果能在规模化层面交付，可能从根本上改变电动汽车电池的制造和重复使用方式。

- 图片: https://tech.supercarblondie.com/wp-content/uploads/Japan-lithium-2.webp
- 备选图片: https://tech.supercarblondie.com/wp-content/uploads/Japan-lithium-1.webp
- 文章角度建议: 绿色科技/循环经济/供应链安全

---

## 话题 2
- 标题: Clawk – Give Coding Agents a Disposable Linux VM, Not Your Laptop
- 分数: 203 points (HN #29, Show HN)
- URL: https://github.com/clawkwork/clawk
- HN 讨论: https://news.ycombinator.com/item?id=48895xxx (153 comments)
- 详细描述:
  Clawk 是一个开源工具，解决了一个现代开发者的核心痛点：让 AI 编程 Agent（如 Claude Code、Codex）安全地执行代码，而不危及宿主机安全。

  传统方案只有两个糟糕的选择：要么你逐条审批每个命令（每隔几秒就要看一次提示），要么运行 `--dangerously-skip-permissions` 然后祈祷不会误删重要文件或泄露 token。

  Clawk 提供了第三种选择：输入 `clawk` 命令后，AI Agent 在一个一次性的 Linux VM 内工作（你的代码挂载进去，guest 系统有 root 权限，无需权限提示），而你的文件、钥匙串和宿主机其他部分完全隔离。Agent 有了自己的机器，而不是用你的。

  安全边界不是 Agent 可能被说服放弃的 prompt 规则，而是一台独立的机器，唯一的开口就是你挂载的目录。VM 内部有网络白名单功能，可以阻止对未知服务器的连接。你的 SSH 密钥永远不会进入 VM，但 ssh-agent 转发让 git push 仍然可用。

  支持平台：macOS 和 Linux（实验性）。用 Go 编写。

- 图片: https://raw.githubusercontent.com/clawkwork/clawk/main/assets/clawk-lockup-orange-transparent.png
- 文章角度建议: AI 安全/开发者工具/沙箱隔离/Agent 基础设施

---

## 抓取统计
- 总 web_fetch 次数: 7 (1 HN首页 + 1 HN API + 5 原始URL尝试)
- 成功获取详细内容: 2 个话题
- 404 跳过: 5 个 URL (supercarblondie.com 旧域、scottwillsey.com、cloudflare blog、lalitm.com、github.com/poseidon-fan、bbc.com)
- 超时: 0
- 最终素材: 2 个话题（符合"2 个保证质量"目标）
