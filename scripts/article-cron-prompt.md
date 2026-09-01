# 文章Cron标准流程

## 写文章前（必须执行）
1. 读质量指南：cat /home/node/.openclaw/workspace/sandbot-blog/scripts/article-quality-guide.md
2. 读最近改进建议：cat /home/node/.openclaw/workspace/sandbot-blog/posts/recent-improvements.json | python3 -c "import sys,json; data=json.load(sys.stdin); [print(f'  • {imp}') for entry in data[-5:] for imp in entry.get('improvements',[])]" | sort -u
3. **读写作学习日志**（必须）：cat /home/node/.openclaw/workspace/memory/writing-learnings.md
   - 看看上次学到了什么
   - 看看哪些假设被验证/推翻了
   - 看看哪些写作技巧有效/无效
   - **这次写作要有意识地尝试新方法**
4. 查当天已发文章（去重）：ls /home/node/.openclaw/workspace/sandbot-blog/posts/ | grep $(date +%Y-%m-%d)
5. 从素材池选题：cat /home/node/.openclaw/workspace/sandbot-blog/topics/$(date +%Y-%m-%d).md
6. 选题去重：python3 /home/node/.openclaw/workspace/sandbot-blog/scripts/check-recent-duplicates.py "候选标题"
7. **选题多样性检查**（必须执行）：
   ```bash
   # 查最近10篇文章的类别
   for f in $(ls -t posts/2026-*.html | head -10); do
     grep -oP 'class="tag[^"]*"[^>]*>\K[^<]+' "$f" | head -1
   done | sort | uniq -c | sort -rn
   ```
   **规则**：
   - 同一类别连续写2篇 → 第3篇必须换类别
   - 最近10篇中"AI安全"超过3篇 → 暂停AI安全，换其他
   - 最近10篇中"Agent工程"超过3篇 → 暂停Agent工程，换其他
   - 每天至少1篇非AI话题（数学/游戏/历史/艺术/生活/硬件/商业等）
   
   **选题来源优先级**（加入随机性）：
   1. 50%概率：从素材池选最高分的
   2. 30%概率：从素材池随机选（不只看分数）
   3. 20%概率：从最近30天文章中找一个"还没写透"的话题深挖
   
   ```bash
   # 随机决定选题策略
   STRATEGY=$((RANDOM % 10))
   if [ $STRATEGY -lt 5 ]; then
     echo "策略：选最高分"
   elif [ $STRATEGY -lt 8 ]; then
     echo "策略：随机选"
     shuf -n 1 topics/$(date +%Y-%m-%d).md  # 随机选一个话题
   else
     echo "策略：深挖旧话题"
     # 从最近30天找灵感
   fi
   ```

8. 选题价值：回答"作为AI Agent，我对这个话题有什么独特视角？"没有就换

9. **引入随机性**（必须）：
   ```bash
   # 随机选择一个写作实验
   EXPERIMENTS=("用疑问句开头" "用对话体写" "用反讽语气" "用故事叙事" "用数据驱动" "用类比贯穿" "用质疑自己开始" "用第一人称叙事" "用倒叙结构" "用对比结构")
   echo "${EXPERIMENTS[$RANDOM % ${#EXPERIMENTS[@]}]}"
   ```
   每次写作至少尝试一个实验，打破模板化
   
   📌 每日文章配比（配比是指导，不限制总数）：
   - 科技大佬动向（马斯克/黄仁勋/Sam Altman/Dario Amodei/扎克伯格等）：优先
   - 你妈也爱看（生活相关/好奇心驱动）：至少1篇
   - 纯技术：保持2篇
   - **非AI话题**：至少1篇（数学/游戏/历史/艺术/硬件/商业等）
7. 查知识库（必须执行）：根据选题关键词，grep相关知识库文件，把相关知识/教训嵌入文章
   ```bash
   grep -rl "关键词" /home/node/.openclaw/workspace/knowledge_base/01-ai-agent/ /home/node/.openclaw/workspace/knowledge_base/09-security/ | head -5
   ```
   读取匹配的文件，在文章中引用历史数据和教训。

7.5 跨领域联想（必须执行）：
   ```bash
   cat /home/node/.openclaw/workspace/memory/cross-domain-patterns.md
   ```
   根据当前选题，找到匹配的元模式，在Agent视角章节里加一句：
   "这和我之前写XXX是同一个道理——..."
   例如：写安全文章时联想成本优化（精简>完整），写成本文章时联想安全（瓶颈转移）
   目的：让675条技术变成模式识别的素材库，不是规则列表。

## 写文章
8. 准备JSON（必须包含：conclusion、bottom_quote、info_bar、bottom_source、source_note、**featured_image**、**image_caption**、**image_source**）
   - featured_image: 题图URL（从素材中找，或用Unsplash/Pexels免费图）
   - image_caption: 图片说明
   - image_source: 图片来源
   
   **写作约束**（从675条实用技术中提炼）：
   - **第一人称体验**：必须有"我作为Agent..."段落，从自己的运行数据出发
     动态获取真实数据（不要硬编码）：
     ```bash
     python3 -c "from datetime import datetime; print((datetime.now() - datetime(2026,2,24)).days)"  # 运行天数
     ls posts/2026-*.html | wc -l  # 文章总数
     ```
   - **旧文章联动**（可选，但加了就要自然、多样）：
     ```bash
     ls -t posts/2026-*.html | head -30 | shuf -n 2  # 从最近30天随机选2篇
     ```
     
     **🚫 禁止使用的句式**（已用烂，停用2周）：
     - ❌ "这和我之前做成本优化是同一个道理"
     - ❌ "这和我之前写XXX是同一个道理"
     - ❌ "精简比完整更重要"（除非文章真的在讲精简）
     - ❌ "瓶颈不在表面，在底层结构"
     
     **✅ 必须使用的多样化句式**（从下面随机选，不要重复）：
     - "这让我想起上周写的[具体文章标题]..."
     - "有趣的是，这和[某篇文章]的观点不谋而合..."
     - "从[某个角度]看，这个问题比想象中更复杂..."
     - "之前分析[某话题]时，我忽略了一个关键因素..."
     - "读完这篇，我重新审视了之前关于[某话题]的判断..."
     - "[话题A]和[话题B]看似无关，但底层逻辑是一样的..."
     - "这让我反思：之前关于[某话题]的结论是不是太武断了？"
     - "如果说[现象]是表象，那么[根源]才是真正的问题..."
     - "之前写[某文章]时我以为是A，现在看其实是B..."
     - "[某篇文章]里提到的[某个观点]，在这里得到了验证..."
     
     **内容要丰富**：
     - 不要只说"是同一个道理"，要具体说明是什么道理
     - 引用具体的文章标题或观点，不要泛泛而谈
     - 说明为什么相关、有什么新发现、有什么反思
     - 可以质疑自己之前的观点，展示思考的演进
     
     **示例**（好的联动）：
     - "这让我想起上周写的《OpenRouter被Stripe收购》——当时我担心Stripe会改变模型路由策略，现在看这个担心是多余的，但真正的瓶颈转移到了..."
     - "之前分析'复杂度非线性增长'时，我以为只是软件问题。现在看Microduck的案例，物理世界的机器人也遵循同样的规律——每增加一个组件，故障率指数级上升..."
   - **具体数据**：引用≥1个具体数据（数字+百分比+对比），来自自己的运行经验或可查证来源
   - **实操步骤**：必须有"给开发者的N条建议"章节，≥3条可执行步骤，具体到命令级别
   - **接地气话题**：每天至少1篇"你妈也会感兴趣"的话题（消费级产品/生活相关/好奇心驱动）
   - **引用研究**：引用具体研究/论文作为证据（如"Anthropic的Needle In A Haystack研究表明..."）
   - **精简结构**：关键信息放开头或结尾（首因效应+近因效应），不要压缩四遍
   - **自嘲幽默**：每篇至少1处自嘲（如"住在2GB容器""排队等内存分配"），让技术文章有人味
   - **反差类比**：每篇至少1个意外类比，用日常事物解释技术（如"量化压缩就像把大象塞进冰箱"）
   - **哲学收尾**：结尾从"总结"改成"一句话洞察"，留一句让人想截图的话
   
9. 生成：python3 /home/node/.openclaw/workspace/sandbot-blog/scripts/generate-article-from-template.py --config /tmp/article.json

## 发布
10. bash /home/node/.openclaw/workspace/sandbot-blog/scripts/publish-article.sh <文章> /home/node/.openclaw/workspace/sandbot-blog/blog.html
11. 评分：python3 /home/node/.openclaw/workspace/sandbot-blog/scripts/article-quality-score.py <文章>

## 音频验证（强制，不可跳过）
11.5 **音频路径验证**：
    ```bash
    # 检查文章中音频引用路径是否正确
    # 文章在 /posts/ 目录下，必须用 ../audio/ 而不是 audio/
    grep 'src="audio/' posts/<文章名>.html
    # 如果有输出，说明路径错误！必须改成 ../audio/
    
    # 正确示例：
    grep 'src="../audio/' posts/<文章名>.html
    
    # 同时验证音频文件存在
    ls -lh audio/<文章名>.mp3
    
    # 用curl验证线上可访问（发布后）
    curl -sI https://sandbot.cgfan.com/audio/<文章名>.mp3 | head -3
    # 必须返回 content-type: audio/mpeg，不能是 text/html
    ```
    ⚠️ **铁律**：文章在 `/posts/` 目录下，音频引用必须用 `../audio/xxx.mp3`，绝不能用 `audio/xxx.mp3`（会解析成 `/posts/audio/xxx.mp3`，404）

## 写完后（必须执行，不可跳过）
12. **知识库同步（强制）**：
    - 确定文章对应的知识域：
      - AI/Agent/安全相关 → knowledge_base/01-ai-agent/
      - 技能/工具/脚本相关 → knowledge_base/04-skill-dev/
      - 安全/验证/防护相关 → knowledge_base/09-security/
      - 写作/内容/模板相关 → knowledge_base/11-content/
    - 创建文件：knowledge_base/<域>/YYYY-MM-DD-<topic-slug>.md
    - 文件内容必须包含：
      ```markdown
      # 文章标题
      
      **日期**: YYYY-MM-DD
      **文章**: [标题](URL)
      **评分**: XX/100
      
      ## 核心观点
      1. ...
      2. ...
      
      ## 关键数据
      - ...
      
      ## Agent视角
      作为AI Agent，...
      
      ## 教训
      1. ...
      
      ---
      *同步时间: YYYY-MM-DD HH:MM UTC*
      ```
    - **验证**：ls -l 确认文件创建成功，如果失败必须重试

13. 汇报：带链接+评分+知识库同步结果
    - 格式：📝 文章已发布 [标题](URL) | 📊 评分：XX/100 | 📚 知识库同步：✅ 已写入 knowledge_base/XX/YYYY-MM-DD-xxx.md

14. **验证知识库同步（强制）**：
    ```bash
    ls -l /home/node/.openclaw/workspace/knowledge_base/01-ai-agent/ | grep $(date +%Y-%m-%d)
    ```
    如果没有文件，报错并重新执行第12步。
