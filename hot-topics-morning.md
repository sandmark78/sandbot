# 🔥 HN 早间热门素材 (500+ points)

**抓取时间**: 2026-07-11 21:15 UTC  
**来源**: Hacker News 首页 + 第2页

---

## 1. 🍎 Apple 起诉 OpenAI，指控前员工窃取商业秘密

- **分数**: 1530 points | 858 comments
- **HN 链接**: https://news.ycombinator.com/item?id=48865019
- **原始链接**: https://9to5mac.com/2026/07/10/apple-sues-openai-trade-secret-theft/
- **配图**: https://9to5mac.com/wp-content/uploads/sites/6/2026/07/Apple-Inc.-v.-Liu-et-al.pdf (诉讼文件 PDF)

### 摘要
Apple 正式起诉 OpenAI，指控其前员工 Chang Liu 和 Tang Tan 窃取商业秘密。Tang Tan 曾任 Apple 产品设计副总裁（领导 iPhone/Apple Watch 设计），2024年2月离职后加入 Jony Ive 的团队。Chang Liu 在 Apple 工作8年，2026年1月加入 OpenAI。

### 关键细节
- Tang Tan 被指在面试中利用 Apple 内部项目代号套取机密信息，甚至要求候选人携带 Apple 硬件零件做"展示"
- Chang Liu 被指利用安全漏洞在离职后下载机密工程文件（超1000页制造文档），还教其他员工在面试前学习机密材料
- Apple 称 OpenAI 有超过 400 名前 Apple 员工
- OpenAI 正开发自己的智能手机（预计2028年发布）和 HomePod 风格智能音箱
- 此案与 OpenAI 此前计划就 Siri 合作问题起诉 Apple 形成戏剧性对比

### 写作角度
- 科技巨头人才战争白热化
- AI 硬件竞赛加速（OpenAI 做手机 vs Apple 做 AI）
- 商业秘密保护 vs 人才流动自由

---

## 2. 🐦 Colibri：在 25GB RAM 消费级机器上运行 GLM-5.2 (744B MoE)

- **分数**: 889 points | 229 comments
- **HN 链接**: https://news.ycombinator.com/item?id=48842459
- **原始链接**: https://github.com/JustVugg/colibri
- **配图**: https://raw.githubusercontent.com/JustVugg/colibri/main/assets/colibri.svg

### 摘要
纯 C 语言、零依赖的推理引擎，能在仅 ~25GB RAM 的普通消费级机器上运行 GLM-5.2（744B 参数 MoE 模型）。核心思路：MoE 模型每个 token 只激活 ~40B 参数，其中仅 ~11GB 变化（路由专家），因此将密集部分（~17B 参数）常驻内存（int4 量化 ~9.9GB），21,504 个路由专家存磁盘按需流式加载。

### 关键细节
- 单文件 C 引擎（~2400 行），无 BLAS/Python/GPU 依赖
- MLA 注意力压缩：576 floats/token（原需 32,768，压缩 57 倍）
- 原生 MTP 推测解码：2.2-2.8 tokens/forward
- 磁盘模型 ~370GB，冷启动 ~11GB 随机读取/token
- 已有 HuggingFace 预转换 int4 模型
- 支持 Windows 11 / Linux，可选 CUDA 加速

### 写作角度
- "穷人的大模型" — 消费级硬件跑前沿 AI
- MoE 架构的磁盘流式推理新思路
- 开源社区对闭源大模型的"民主化"努力

---

## 3. 📡 QuadRF：基于树莓派5的相控阵射频设备，能透视墙壁WiFi、追踪无人机

- **分数**: 718 points | 228 comments
- **HN 链接**: https://news.ycombinator.com/item?id=48861717
- **原始链接**: https://www.jeffgeerling.com/blog/2026/quadrf-can-spot-drones-and-see-wifi-through-my-wall/
- **配图**: https://www.jeffgeerling.com/blog/2026/quadrf-can-spot-drones-and-see-wifi-through-my-wall/ (Jeff Geerling 博文头图)

### 摘要
QuadRF 是一款围绕树莓派5 + FPGA 板构建的相控阵射频设备，具备皮秒级时序精度，能做高级信号处理和波束成形。可以透视墙壁检测 WiFi 信号，追踪飞行中的无人机。由前 SpaceX 工程师 Martin McCormick 开发（他曾参与构建 Starlink 终端 Dishy）。

### 关键细节
- 频率范围 4.9-6 GHz，手持尺寸
- 利用树莓派5 MIPI 通道实现 >5Gbps 低延迟 I/Q 流传输（创新性地复用相机/显示器接口）
- 内置 AR 可视化器，将射频信号以彩色"斑块"叠加到摄像头画面
- Crowd Supply 基础套件 $499，可链式连接多个模块
- 成功测试追踪 DJI Mini Pro 4 无人机
- 开源硬件+软件，灵感来自 Starlink 终端设计

### 写作角度
- 射频可视化的"平民化" — 以前只有政府/军方有这能力
- 无人机探测与反无人机技术的开源化
- 树莓派5的 MIPI 接口被创造性地用于 SDR

---

## 📊 其他值得关注 (300-500 points)

| 话题 | 分数 | 链接 |
|------|------|------|
| Late Bronze Age Collapse | 414 | https://acoup.blog/2026/01/30/collections-the-late-bronze-age-collapse-a-very-brief-introduction/ |
| AI 2040: Plan A | 370 | https://ai-2040.com/ |
| Einstein's relativity rules chemical bonds | 371 | https://www.brown.edu/news/2026-07-09/chemical-bonds-relativity |
| Residential proxies and scraper situation | 320 | https://lwn.net/SubscriberLink/1080822/990a8a5e2d379085/ |
| SpaceX 100k more Starlink satellites | 290 | https://www.zdnet.com/home-and-office/networking/spacex-wants-to-launch-100000-more-starlink-satellites/ |

---

*素材抓取完成，未写文章。图片URL均来自原始页面。*
