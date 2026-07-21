# 晚间文章素材 (生成时间: 2026-07-21 11:15 UTC)

## 今日已有文章（已排除）
- 2026-07-21-china-open-weights-ai-strategy (中国开放权重AI策略)
- 2026-07-21-early-open-weights-strategy (开放权重策略)
- 2026-07-21-early-romania-data-wipe (罗马尼亚数据擦除)
- 2026-07-21-jelly-ui-soft-body-physics-html (Jelly UI软体物理)
- 2026-07-21-noon-jelly-ui-soft-body-web-components (Jelly UI Web组件)
- 2026-07-21-test-v41-template (测试模板)

---

## 话题 1: AI 反例数学家
- 标题: Human mathematicians are being outcounterexampled
- 分数: 361 points (151 comments)
- URL: https://xenaproject.wordpress.com/2026/07/20/human-mathematicians-are-being-outcounterexampled/
- 图片: https://xenaproject.wordpress.com/wp-content/uploads/2020/05/cropped-twitchpfc.png?w=200
- 详细描述:
  文章讲述了AI在数学反例领域的突破性进展。2026年5月20日，ChatGPT 推翻了离散几何中著名的 Erdős 单位距离猜想——其核心结构是利用 1960 年代 Golod-Shafarevich 的数论深刻定理来构造反例。许多人类数学家声称验证了论证，但作者（Lean 形式化先驱）质疑：反例有没有在 Lean 中形式化？答案是没有。但不到一周后，Fields 奖章得主 Mike Freedman（现任 Logical Intelligence 首席科学官，该公司由图灵奖得主 Yan LeCun 联合创立）发邮件告知，他们的系统已经将 ChatGPT 生成的整篇论文自动形式化为 Lean 代码。这标志着 LLM 生成的突破性数学成果正在被实时形式化验证。文章探讨了人类数学家在技术细节上不再可信的论点，以及交互式定理证明器在数学未来的重要角色。核心问题：那个需要 100+ 页证明的数论定理（涉及全局类场论的大块内容），AI 真的理解了吗？还是只是模式匹配？这引发了关于 AI 数学能力本质的深层讨论。

---

## 话题 2: 自定义 CPU 跑 DOOM 爆红
- 标题: Running DOOM on our Custom CPU and Going Viral
- 分数: 83 points (19 comments)
- URL: https://www.armaangomes.com/blogs/doom/
- 图片: 无 og:image
- 详细描述:
  作者讲述了他们从零构建 CPU 并成功运行 DOOM 的经历，相关视频获得了数百万播放量。DOOM 自 1993 年发布以来就被移植到几乎一切设备上，从微控制器到烤面包机甚至细菌。团队在逻辑门级别设计了自定义 CPU，连接外设，改编 DOOM 源代码使其在自己的机器上运行，并部署到 FPGA 上实时运行。之前他们只运行过 Pong 和 Mandelbrot 集等简单程序。面临两大挑战：内存和速度。DOOM 基础共享软件 (doom1.wad) 有 14MB，而 FPGA 的 BRAM 不到 1MB。团队分工：Liam 负责乱序处理的基础工作以实现更大的并行性和流水线技巧，作者负责内存集成。原始设计中 FPGA BRAM 只有 1 周期延迟，流水线处理器不需要为内存停顿，但外接内存芯片的复杂性远超预期。这是一个关于硬件工程、从底层构建计算系统的深度技术故事。

---

## 话题 3: Linux 内核将支持 $ORIGIN
- 标题: Linux kernel will support $ORIGIN, sort of
- 分数: 61 points (38 comments)
- URL: https://fzakaria.com/2026/07/20/linux-kernel-will-support-origin-sort-of
- 图片: 无 og:image
- 详细描述:
  作者在 TacoSprint 2026 期间决定攻克 Nix 中的可重定位二进制文件问题。他提出了一个大胆的想法：修补 Linux 内核使 $ORIGIN 在 PT_INTERP 和 shebang 中得到支持。他通过邮件列表向 Linux 内核 mailing list 发送了提案。第一次尝试提出在 VFS 子系统中直接添加 $ORIGIN 支持。VFS 维护者 Christian Brauner 善意地回复，询问变更的理由，并最终提出了这种支持如何进入子系统的方案。John Ericson 也加入讨论，解释了为什么非固定解释器对 Nix 和其他用例（如 Buck & Bazel）很有用。Brauner 甚至提出可以利用 eBPF 作为通过 binfmt_misc 选择解释器的可编程方式——这比单纯的 $ORIGIN 支持强大得多！作者在邮件列表上往返讨论后，最终产生了一系列补丁。这个故事展示了 Linux 内核开发的开放协作精神，以及一个看似简单的需求如何演变成更优雅的技术方案。对 Nix 生态系统和整个 Linux 包管理都有深远影响。

---

## HN 首页其他热门（备选）
- Who's afraid of Chinese models? (686分) - ❌ 与已有中国AI策略文章重复
- Kimi Work (574分) - ❌ 中国AI产品，话题接近
- Jelly UI (521分) - ❌ 已有两篇
- Nativ: Run frontier open models locally (290分) - 和本地模型运行相关，可作备选
- Incremental library (230分) - Jane Street 增量计算库，技术性强但受众窄
