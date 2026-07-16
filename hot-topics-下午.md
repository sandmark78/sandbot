# 下午文章素材 (生成时间: 2026-07-16 07:15 UTC)

## 话题 1
- 标题: Grok Build is open source
- 分数: 392 points (419 comments)
- URL: https://github.com/xai-org/grok-build
- 详细描述: xAI 开源了 Grok Build，这是一个基于 Rust 开发的终端 AI 编程 Agent。它运行在全屏 TUI 中，能理解代码库、编辑文件、执行 shell 命令、搜索网络、管理长时间任务。支持交互模式、无头模式（用于脚本/CI）、以及通过 Agent Client Protocol (ACP) 嵌入编辑器。预编译二进制支持 macOS、Linux、Windows。安装只需一行命令：`curl -fsSL https://x.ai/cli/install.sh | bash`。这是 xAI 在 AI 编程工具领域的重要开源举措，直接对标 Claude Code、Cursor 等工具。项目使用 Rust 编写，需要 protoc 进行 proto 代码生成。
- 图片: https://media.x.ai/v1/website/universe-tui-screenshot-6f7a0837.png

## 话题 2
- 标题: SQLite should have (Rust-style) editions
- 分数: 222 points (82 comments)
- URL: https://mort.coffee/home/sqlite-editions/
- 详细描述: 作者提出 SQLite 应该借鉴 Rust 的"版本"(editions) 机制来解决默认值问题。SQLite 作为嵌入式数据库的行业标准，被 lobste.rs 等服务使用，但其默认设置存在严重问题：(1) 外键约束默认被忽略，这与其他所有 RDBMS 不同，可能导致数据不一致和悬空引用；(2) SQLite 的 ROWID 复用算法在某些情况下会导致 ID 重用，加剧了外键不执行的问题。作者认为引入 editions 机制可以让新版本改变默认行为而不破坏现有应用的兼容性。
- 图片: (无 og:image)

## 话题 3
- 标题: The lost joy of music piracy
- 分数: 139 points (63 comments)
- URL: https://www.pigeonsandplanes.com/read/music-piracy-what-cd-oink-nine-inch-nails-streaming
- 详细描述: Pigeons & Planes 的一篇回顾文章，探讨音乐盗版的"失落的乐趣"。文章追溯了从 CD 时代到 Oink（著名音乐 BT 站点）再到 Nine Inch Nails 等乐队实验，直至今日流媒体时代的音乐传播变迁。在流媒体统治一切的今天，人们失去了翻找盗版资源时的那种发现感和社区感。HN 社区对此热烈讨论（63 评论），涉及数字所有权、音乐发现方式的演变、以及流媒体对音乐文化的深远影响。
- 图片: (无 og:image，原始页面为 JS 渲染)

---

**备注**: 今日已有文章 `2026-07-16-early-inkling-open-weights-model`，已避开 Inkling/Open Weights 话题。话题 3 原始页面无法提取内容，使用 HN 标题和评论信息作为素材。
