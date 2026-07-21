# 热点文章素材 (生成时间: 2026-07-21 09:15)

## 今日已有文章（已去重）
- china-open-weights-ai-strategy (中国AI开放权重)
- early-open-weights-strategy (开放权重策略)
- early-romania-data-wipe (罗马尼亚数据擦除)
- noon-jelly-ui-soft-body-web-components (Jelly UI软体组件)
- test-v41-template (测试模板)

---

## 话题 1: AI 正在击败人类数学家
- 标题: Human mathematicians are being outcounterexampled
- 分数: 338 points | 137 comments
- URL: https://xenaproject.wordpress.com/2026/07/20/human-mathematicians-are-being-outcounterexampled/
- 来源: Xena Project (Kevin Buzzard, 帝国理工)
- 详细描述:
  2026年5月20日，ChatGPT 反驳了 Erdős 单位距离猜想——这是离散几何领域的著名未解问题。OpenAI 宣布时，多位人类数学家验证了论证过程。核心思路是利用 Golod-Shafarevich 定理（1960年代数论深刻定理）构造反例。

  不到一周后（5月26日），Fields 奖章得主 Mike Freedman（现为 Logical Intelligence 首席科学官，该公司由图灵奖得主 Yann LeCun 联合创立）发邮件告知：他们的系统已经用 Lean 自动形式化了整篇 ChatGPT 生成的论文。这意味着 LLM 生成的突破性数学成果正在被实时形式化验证。

  但问题在于：Golod-Shafarevich 定理的证明超过100页，需要大量全局类域论（20世纪初发展的理论，至今仍无简短证明）。这引发了深层问题——AI 能生成证明，但人类是否真正理解了证明？形式化验证是否是必须的？

  这篇文章来自 Kevin Buzzard（帝国理工教授），他9年前开始倡导交互式定理证明器应在数学未来中扮演重要角色。这篇文章在 HN 引发137条讨论，核心争论：AI 是在"做数学"还是"模仿数学"？形式化验证是否成为 AI 时代数学的必需品？
- 图片: 无（WordPress 页面未提取到 og:image）
- 写作角度: AI 从写代码到做数学的跨越，形式化验证成为新基础设施

---

## 话题 2: 美国五大科技巨头隐藏债务飙升至 1.65 万亿美元
- 标题: Five US tech giants' hidden debts soar to $1.65tn on opaque AI funding
- 分数: 275 points | 141 comments
- URL: https://asia.nikkei.com/business/technology/five-us-tech-giants-hidden-debts-soar-to-1.65tn-on-opaque-ai-funding
- 来源: Nikkei Asia (日本经济新闻)
- 详细描述:
  日经新闻研究显示，美国五大科技巨头的隐藏债务在约4年内膨胀了8倍，达到估计的1.65万亿美元，超过了其实际公开债务。这些隐藏债务主要来自数据中心租赁和 GPU 供应合同，使得投资者更难评估风险。

  以 Meta 为例，其表外债务约4200亿美元，几乎是其透明债务的3倍。这些债务与 AI 基础设施投资直接相关——数据中心建设、GPU 采购合同、长期租赁协议等。

  关键问题：
  1. 这些债务为什么不透明？因为数据中心租赁和 GPU 供应合同通常不计入资产负债表
  2. 投资者无法准确评估风险——公开财报显示的债务远低于实际水平
  3. AI 投资的回报周期长，但债务义务是刚性的
  4. 如果 AI 商业化不及预期，这些隐藏债务可能引发系统性风险

  HN 讨论（141条）聚焦：这是否是另一个"次贷危机"式的系统性风险？科技公司的 AI 投资是否过度？
- 图片: 无（Nikkei 付费墙，内容有限）
- 写作角度: AI 军备竞赛的隐藏成本，1.65万亿美元的定时炸弹？

---

## 话题 3: 在自制 CPU 上运行 Doom 并走红网络
- 标题: Running DOOM on our Custom CPU and Going Viral
- 分数: 63 points | 12 comments
- URL: https://www.armaangomes.com/blogs/doom/
- 来源: Armaan Gomes (独立开发者/硬件爱好者)
- 详细描述:
  两周前，作者团队成功在他们从零构建的 CPU 上运行了 Doom（然后发了个视频，获得了几百万播放量）。

  技术细节：
  - 他们在逻辑门级别设计了一个自定义 CPU
  - 连接了外设，改编了 Doom 源码以在其机器上运行
  - 部署到 FPGA 上实时运行
  - 之前只运行过自己写的简单程序（Pong、Mandelbrot 集）

  面临的两大挑战：
  1. **内存问题**：原设计只能使用 FPGA 的 BRAM（不到1MB），而 Doom 基础共享版 (doom1.wad) 有14MB
  2. **速度问题**：Doom 对现代 PC 很轻松，但对他们的 CPU 来说太慢了

  解决方案：
  - 队友 Liam 在研究乱序处理（out-of-order processing）以实现更大的并行性
  - 作者负责内存集成—— hook 额外内存芯片远比听起来复杂

  这篇文章展示了硬核硬件工程的魅力：从逻辑门到运行完整游戏。"Doom can run on anything" 的说法再次得到验证。
- 图片: 无（博客页面未提取到 og:image）
- 写作角度: 从零造 CPU 到跑 Doom，硬核工程浪漫主义

---

## 备选话题（未抓取详细内容）
- Incremental – Jane Street 增量计算库 (180pts) - github.com/janestreet/incremental
- Nativ: 在 Mac 本地运行前沿开源模型 (271pts) - blaizzy.github.io/nativ/
- Linux kernel will support $ORIGIN (35pts) - fzakaria.com
- Kimi Work (539pts) - 和中国AI话题可能重复，跳过
- Who's afraid of Chinese models? (624pts) - 和中国AI话题重复，跳过
