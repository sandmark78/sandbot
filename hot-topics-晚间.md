# 晚间文章素材 (生成时间: 2026-07-19 11:15 UTC)

**今日已有文章**（已去重）:
- `2026-07-19-afternoon-kimi-k3-open-source-moment` (Kimi K3 开源)
- `2026-07-19-moonshine-micro-speech-ai-on-microcontroller` (Moonshine 微型语音AI)

---

## 话题 1
- **标题**: Codex Resets — OpenAI 用量限制重置追踪
- **分数**: 200 points (HN)
- **URL**: https://codex-resets.com/
- **详细描述**: 
  一个专门追踪 OpenAI Codex 用量限制重置的网站。OpenAI 会不定期重置所有付费用户的 Codex 使用额度，没有固定时间表，没有 changelog，只有 @thsottiaux 在 X 上的突然宣布。该网站记录了所有历史重置事件：

  **关键数据**:
  - 累计重置次数：35 次
  - 平均间隔：8.9 天
  - 最长等待：67.7 天
  - 最近一次：昨天（2026-07-18）

  **增长轨迹**（从公告摘录）:
  - 500K → 700K → 800K → 900K 活跃用户（几周内）
  - Codex + ChatGPT Work 合计
  - 用户增长过快导致频繁触达限额，OpenAI 被迫反复重置
  - 引入了"banked reset"机制，用户可在桌面端/网页端手动激活

  **为什么有趣**: 
  这个网站本身就是 AI 时代"基础设施焦虑"的缩影——900 万活跃用户把 OpenAI 的基础设施打到需要反复手动重置限额，而社区建了一个网站来"膜拜"这些重置时刻。文章角度可以是：AI 产品的增长烦恼、基础设施瓶颈、以及开发者对 AI 编码工具的依赖程度。

- **图片**: 未能提取 og:image（网站为纯文本极简风格）
- **写作角度**: AI 编码工具的增长烦恼 / Codex 从 0 到 900 万用户的野蛮生长 / 开发者对 AI 的依赖

---

## 话题 2
- **标题**: Mathematicians Still Don't Know the Fastest Way to Multiply Numbers
- **分数**: 124 points (HN)
- **URL**: https://www.scientificamerican.com/article/mathematicians-still-dont-know-the-fastest-way-to-multiply-numbers/
- **详细描述**: 
  Scientific American 深度文章，讲述数学乘法算法的未解之谜。

  **核心内容**:
  - 小学生学的乘法算法（竖式乘法）的时间复杂度是 O(n²)
  - 1960 年，23 岁的 Anatoly Karatsuba 发现了更快的方法（Karatsuba 算法）
  - 此后数十年，数学家们不断逼近理论下限，但**至今不知道最快的乘法算法是什么**
  - 这个问题对计算机科学至关重要：加密、机器人、AI、音频处理都依赖大数乘法
  - 当数字足够大时，即使是简单的乘法操作也会成为瓶颈，任何效率提升都有全球经济影响

  **Big O 解释**:
  - 竖式乘法：O(n²) — 两位数×两位数 = 4 次单 digit 乘法
  - Karatsuba：O(n^1.585)
  - Schönhage-Strassen (1971)：O(n log n log log n)
  - Harvey-van der Hoeven (2019)：O(n log n) — 目前已知最快
  - 但是否存在 O(n) 的算法？未知。

  **为什么有趣**: 
  一个看似"小学水平"的问题背后是计算机科学的核心瓶颈。在 AI 时代，大数乘法的效率直接影响 GPU 上的矩阵运算速度。文章适合写成"你以为你懂乘法，其实你不懂"的科普风格。

- **图片**: 未能提取 og:image（Scientific American 有 paywall 保护）
- **写作角度**: 科普向 / 从小学乘法到 AI 芯片的底层瓶颈 / 数学未解之谜

---

## 话题 3
- **标题**: Blender 5.2 LTS — 节点物理、音频驱动、程序化模拟
- **分数**: 26 points (HN)
- **URL**: https://www.blender.org/download/lts/5-2/
- **详细描述**: 
  Blender 5.2 LTS 于 2026 年 7 月 14 日发布，带来重大更新。

  **核心新功能**:

  1. **Geometry Nodes 重大升级**:
     - Sample Sound Frequencies 节点：可用音频文件驱动节点动画和模拟
     - Mesh Bevel 节点：程序化控制边缘/顶点的倒角
     - Lists 数据类型：支持存储任意长度的序列（数字、字符串等）
     - Geometry Bundles：可跨 modifier 和 object 边界携带任意数据

  2. **节点化物理系统（革命性）**:
     - 全新 XPBD Solver 节点
     - 毛发和布料模拟完全程序化
     - 高级用户可自定义约束、从头创建模拟系统
     - 社区已经在用节点物理创造惊人效果

  3. **LTS 意义**:
     - Long Term Support 版本，适合生产环境
     - Splash 画面：已灭绝的 Panthera spelaea（洞狮）

  **为什么有趣**: 
  Blender 正在从"建模工具"变成"程序化创作引擎"。节点化物理意味着用户可以像搭积木一样创建复杂的物理模拟，这对独立游戏开发者、影视特效师是巨大利好。AI 生成内容（AIGC）和程序化生成的结合点也在这里。

- **图片**: 未能提取 og:image（Blender 页面为 JS 渲染）
- **写作角度**: 3D 创作民主化 / Blender 的程序化革命 / 独立创作者的工具进化

---

## 备选话题（未深入抓取）

| 话题 | 分数 | URL | 备注 |
|------|------|-----|------|
| Transcribe.cpp | 553 | cjpais.com | 最高分！但原始页面内容极少，GitHub 404 |
| NYC AI 房产披露 | 483 | petapixel.com | 高分，但 PetaPixel 404 |
| AI Mania 批评 | 231 | mataroa.blog | 重定向到首页 |
| Better Than IPTV | 216 | github.com/stupside | GitHub 404 |
| Qwen 3.8 发布 | 211 | twitter.com/alibaba_qwen | 和已有 Kimi K3 话题接近 |
| IndieWeb $0.01/天 | 177 | neatnik.net | 抓取失败 |
| Claude Code 用 Bun+Rust | 61 | simonwillison.net | 404，URL 猜测错误 |
| OpenAI 缩减 Codex 上下文 | 23 | github.com/openai | GitHub 404 |

---

## 抓取总结

- **成功抓取**: 3/3 话题（Codex Resets、乘法算法、Blender 5.2）
- **失败 URL**: 8 个（404/403/paywall/JS渲染）
- **图片提取**: 0/3（目标网站均无法提取 og:image）
- **去重检查**: ✅ 与已有 Kimi K3、Moonshine 文章无重复
- **总 web_fetch 次数**: 10 次（HN 首页 1 次 + 尝试抓取 9 次）
