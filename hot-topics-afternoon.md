# 下午热点素材 (生成时间: 2026-07-11 07:15 UTC)

## 话题 1
- 标题: Apple sues OpenAI, accuses ex-employees of stealing trade secrets
- 分数: 928 points
- URL: https://9to5mac.com/2026/07/10/apple-sues-openai-trade-secret-theft/
- 描述: Apple 起诉 OpenAI，指控其前员工窃取商业秘密。诉讼指出，前 iPhone/Apple Watch 设计副总裁 Tang Tan 利用 Apple 内部项目代号面试候选人，并要求仍在 Apple 工作的候选人携带实际硬件组件进行"展示"。另一名前工程师 Chang Liu 被指控利用安全漏洞在离职后下载机密工程文件。此案发生在 OpenAI 正准备推出首款消费硬件设备之际，背景是 OpenAI 以 65 亿美元收购了 Jony Ive 的 io 公司。
- 图片1: https://i0.wp.com/9to5mac.com/wp-content/uploads/sites/6/2026/05/apple-openai.jpg?resize=1200%2C628&quality=82&strip=all&ssl=1

## 话题 2
- 标题: Show HN: Getting GLM 5.2 running on my slow computer
- 分数: 846 points
- URL: https://github.com/JustVugg/colibri
- 描述: 开源项目 Colibri 实现了在仅 25GB RAM 的消费级机器上运行 GLM-5.2 (744B 参数 MoE 模型)。纯 C 语言编写，零依赖，无需 GPU。核心原理：744B MoE 模型每个 token 仅激活约 40B 参数，其中仅约 11GB 的路由专家需要频繁更新。密集部分 (~17B 参数, int4 约 9.9GB) 常驻内存，21,504 个路由专家 (~370GB 磁盘) 按需流式加载，配合 LRU 缓存。单 C 文件约 2,400 行代码。
- 图片1: https://opengraph.githubassets.com/7ab83f046e464f88379cb8d981a13d73e1a957c44a100777b8a80c4c9463b311/JustVugg/colibri

## 话题 3
- 标题: QuadRF can spot drones and see WiFi through my wall
- 分数: 536 points
- URL: https://www.jeffgeerling.com/blog/2026/quadrf-can-spot-drones-and-see-wifi-through-my-wall/
- 描述: Jeff Geerling 评测 QuadRF——一款基于 Raspberry Pi 5 和 FPGA 的相控阵无线电设备，具备皮秒级时序精度。该设备可穿透墙壁可视化 WiFi 信号，并追踪飞行中的无人机。工作频率 4.9-6 GHz，利用 Pi 5 的 MIPI 通道实现超过 5 Gbps 的低延迟 SDR 流传输。基础套件 Crowd Supply 预售价 $499。开源硬件，可多模块级联，最高支持 1.15 MW EIRP。
- 图片1: https://www.jeffgeerling.com/blog/2026/quadrf-can-spot-drones-and-see-wifi-through-my-wall/quadrf-antennna-array.jpeg
- 图片2: https://www.jeffgeerling.com/blog/2026/quadrf-can-spot-drones-and-see-wifi-through-my-wall/quadrf-drone-flying-blob.jpg
