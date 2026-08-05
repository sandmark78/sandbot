# 早间文章素材 (生成时间: 2026-07-16 00:23 UTC)

## 今日已有文章（避免重复）
- 2026-07-15-early-app-vs-webpage (App vs 网页)
- 2026-07-15-evening-colibri-glm52-local-inference (Colibri GLM5.2 本地推理)
- 2026-07-15-hot-cursor-0day-security (Cursor 0day 安全漏洞)

---

## 话题 1: Inkling 开放权重模型
- 标题: Inkling: Our Open-Weights Model
- 分数: 539 points
- 评论: 134 comments
- URL: https://thinkingmachines.ai/news/introducing-inkling/
- HN: https://news.ycombinator.com/item?id=48924912
- 详细描述:
  Thinking Machines Lab 发布了 Inkling 开放权重模型，这是一个 Mixture-of-Experts (MoE) 架构的 transformer，总参数 975B，活跃参数 41B，支持高达 1M tokens 的上下文窗口。模型在 45 万亿 tokens（包含文本、图像、音频和视频）上进行了预训练。

  Inkling 能够原生地对文本、图像和音频进行推理，并通过高效可控的思考力度来平衡成本与性能。该模型并非当前最强的开放或闭源模型，但其组合作用使其成为良好的开放权重基础：多模态能力、高效思考、以及可在 Tinker 平台上进行微调。

  同时发布的还有 Inkling-Small，一个 12B 活跃参数的轻量级模型，采用类似训练方法，在更低成本和延迟下实现强劲性能。模型现已在 Tinker 平台上提供微调服务，并配有 Inkling Playground 供开发者测试。

  有趣的是，团队让 Inkling 自己微调自己——模型编写了自己的微调任务、运行并评估了结果。

- 图片: 未找到 og:image（页面为文字新闻稿）
- 写作角度: AI 开放权重新玩家、MoE 架构、自我微调的有趣实验

---

## 话题 2: Grok Build 开源
- 标题: Grok Build is open source
- 分数: 174 points
- 评论: 194 comments
- URL: https://github.com/xai-org/grok-build
- HN: https://news.ycombinator.com/item?id=48926590
- 详细描述:
  xAI 宣布 Grok Build 开源。Grok Build 是 xAI 的 AI 编程助手，此前因安全漏洞（工作区 git.exe 执行问题）而备受关注。现在 xAI 选择将其开源，可能是为了增加透明度和社区审查。

  这个决定很有意思：在一个 AI 编程工具因安全问题被曝光后，公司选择开源而不是闭门修复。这体现了"阳光是最好的消毒剂"的理念——让社区审查代码，发现潜在问题。

  194 条评论说明社区对此高度关注，讨论可能涉及：开源的意义、安全性、与 Cursor/Claude Code 的竞争等。

- 图片: https://opengraph.githubassets.com/1/xai-org/grok-build
- 写作角度: 开源策略、安全透明、AI 编程工具竞争格局

---

## 话题 3: 在 13 年老 Xeon 上跑 Gemma 4 26B
- 标题: Running Gemma 4 26B at 5 tokens/sec on a 13-year-old Xeon with no GPU
- 分数: 211 points
- 评论: 137 comments
- URL: https://www.neomindlabs.com/2026/06/08/running-gemma-4-26b-at-5-tokens-sec-on-a-13-year-old-xeon-with-no-gpu/
- HN: https://news.ycombinator.com/item?id=48922434
- 详细描述:
  NeoMind Labs 展示了在 13 年前的 Intel Xeon CPU（无 GPU）上运行 Google Gemma 4 26B 模型的能力，达到 5 tokens/sec 的推理速度。

  这是一个令人印象深刻的工程成就，证明了：
  1. 现代 LLM 可以在老旧硬件上运行
  2. CPU 推理并非不可行（虽然慢）
  3. 边缘计算和本地推理的可能性

  137 条评论说明社区对低成本 AI 推理的高度兴趣。讨论可能涉及：量化技术、内存优化、实际应用场景等。

- 图片: 未找到 og:image
- 写作角度: 低成本 AI、边缘计算、硬件限制突破

---

## 话题与今日已有文章无重复 ✅
