# 下午文章素材 (生成时间: 2026-07-17 07:15 UTC)

## 话题 1
- 标题: Kimi K3: Open Frontier Intelligence
- 分数: 1498 points (896 comments)
- URL: https://www.kimi.com/blog/kimi-k3
- 详细描述:
Kimi K3 是月之暗面发布的最新最强模型，2.8 万亿参数，基于 Kimi Delta Attention (KDA) 和 Attention Residuals (AttnRes) 两大架构创新构建。它是全球首个开源的 3T 级别模型，拥有原生视觉能力和 100 万 token 上下文窗口。

架构亮点：采用 MoE 稀疏化设计，896 个专家中激活 16 个，配合 Stable LatentMoE 框架，整体缩放效率比 Kimi K2 提升约 2.5 倍。

性能方面：整体仍落后于 Claude Fable 5 和 GPT 5.6 Sol，但在评测中持续超越其他模型，在长周期编码、知识工作和推理方面达到前沿水平。

发布计划：已在 Kimi.com、Kimi Work、Kimi Code 和 Kimi API 上线。默认使用最大思考力度，完整模型权重将于 2026 年 7 月 27 日发布。技术报告将同步公开。

这是开源模型的重要里程碑——首次有 3T 级别的模型完全开放权重。

## 话题 2
- 标题: Microsoft Comic Chat is Now Open Source
- 分数: 639 points (142 comments)
- URL: https://opensource.microsoft.com/blog/2026/07/16/microsoft-comic-chat-is-now-open-source/
- GitHub: https://github.com/microsoft/comic-chat
- 详细描述:
微软将 1990 年代的经典聊天客户端 Comic Chat 开源了。这个软件能将 IRC 聊天自动转化为漫画面板，配有插图角色、对话气泡和表情——它还是 Comic Sans 字体的"第一个家"。

Comic Sans 的起源：1994 年由微软排版师 Vincent Connare 设计，最初就是为了配合 Comic Chat 的对话气泡风格。

历史意义：在互联网从 telnet/Usenet/IRC 向可视化 Web 过渡的时期，Comic Chat 代表了一种超前的视觉通信实验。它把参与者表现为插图角色，根据输入文字生成表情和手势——如果有人打"I like that"，角色会指向自己；如果文字暗示愤怒，角色会皱眉或交叉双臂。

现在开发者、历史学家和复古计算爱好者可以在 GitHub 上探索完整源代码。这个项目提醒我们，当今在线通信中许多习以为常的功能（表情、贴纸、GIF、虚拟形象），其精神源头可以追溯到这类早期实验。

## 话题 3
- 标题: Decoy Font — A TTF Font That Hides What You Type from AI
- 分数: 511 points (121 comments)
- URL: https://www.mixfont.com/experiments/decoy-font
- 下载: https://static.mixfont.com/assets/20260714-232642-decoyfont-htoqkd3x.ttf
- 详细描述:
Decoy Font 是一个巧妙的字体实验——每个字母同时包含"真实信息"和"诱饵信息"，利用空间频率差异实现双重编码。前景是细轮廓线（诱饵），背景是低频模糊质量（真实信息）。

工作原理：人眼和 AI 的读取方式不同。近距离看，AI（包括 GPT Sol 和 Gemini 3.5 with Thinking）只能看到前景的诱饵文字；但退后或眯眼看，人眼能识别背景的隐藏信息。这个简单的视觉错觉足以欺骗最先进的大模型。

实用性：不仅是概念实验，还是可安装的 TTF 字体文件，基于 DejaVu Sans Mono 改造，可免费用于个人、商业和客户项目。

意义：在 AI 视觉识别日益强大的今天，这展示了一种轻量级的"反 AI 读取"技术。对于隐私保护、反监控场景有潜在应用价值。也提醒我们：AI 的视觉感知方式和人类有本质差异。
