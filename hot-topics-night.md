# 晚间文章素材 (生成时间: 2026-07-11 11:15 UTC)

## 话题 1: Apple 起诉 OpenAI 窃取商业机密
- 标题: Apple sues OpenAI, accuses ex-employees of stealing trade secrets
- 分数: 1125 points (586 comments)
- URL: https://9to5mac.com/2026/07/10/apple-sues-openai-trade-secret-theft/
- 描述: Apple 正式起诉 OpenAI，指控其前员工窃取 Apple 未发布技术、流程和产品的商业机密。被告包括前 iPhone/Apple Watch 设计副总裁 Tang Tan 和前高级工程师 Chang Liu。Apple 称 Tan 在面试中要求候选人携带 Apple 硬件组件和原型进行"展示"，Liu 则利用安全漏洞下载了超过 1000 页的机密工程文件。此案发生在 OpenAI 准备推出首款消费硬件设备之际，背景是 Jony Ive 领导的 io 团队（50+ 名前 Apple 员工）已加入 OpenAI。
- 图片1: https://i0.wp.com/9to5mac.com/wp-content/uploads/sites/6/2026/05/apple-openai.jpg?resize=1200%2C628&quality=82&strip=all&ssl=1

## 话题 2: 在 25GB 内存的消费级机器上运行 GLM-5.2 (744B MoE)
- 标题: Show HN: Getting GLM 5.2 running on my slow computer
- 分数: 859 points (214 comments)
- URL: https://github.com/JustVugg/colibri
- 描述: 开源项目 Colibri 用纯 C 语言（零依赖、无 GPU）实现了在仅 25GB RAM 的消费级机器上运行 GLM-5.2 744B 参数 MoE 模型。核心思路：密集部分（~17B 参数）常驻内存（int4 量化约 9.9GB），21,504 个路由专家（每个 ~19MB）存储在磁盘（~370GB）按需流式加载，配合 LRU 缓存和 MTP 投机解码。单文件 C 代码约 2400 行，支持 MLA 注意力、DSA 稀疏注意力、原生 MTP 推测解码等特性。
- 图片1: https://opengraph.githubassets.com/e04fcd6d4a92f349c12008b765592e3225ee7d25cee7c33236b4e1c7437b1c18/JustVugg/colibri

## 话题 3: QuadRF — 基于树莓派 5 的相控阵射频设备，能透视墙壁 WiFi 并追踪无人机
- 标题: QuadRF can spot drones and see WiFi through my wall
- 分数: 602 points (200 comments)
- URL: https://www.jeffgeerling.com/blog/2026/quadrf-can-spot-drones-and-see-wifi-through-my-wall/
- 描述: Jeff Geerling 评测了 QuadRF——一款围绕树莓派 5 和 FPGA 构建的相控阵射频设备，具备皮秒级时序精度。它能以 AR 可视化方式显示 4.9-6 GHz 频段的射频信号（WiFi 穿墙可见），成功追踪飞行中的 DJI 无人机。创新点：利用树莓派 5 的 MIPI 摄像头/显示接口实现 >5Gbps 低延迟 I/Q 数据流传输，替代传统 USB。Crowd Supply 基础套件 $499，众筹已超预期。
- 图片1: (页面未提供 og:image，文章含产品实物照片但无法提取直接 URL)

---
*数据来源: Hacker News 首页 | 抓取时间: 2026-07-11 11:15 UTC*
