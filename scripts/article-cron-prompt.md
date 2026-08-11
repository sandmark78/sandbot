# 文章Cron标准流程

## 写文章前（必须执行）
1. 读质量指南：cat /home/node/.openclaw/workspace/sandbot-blog/scripts/article-quality-guide.md
2. 读最近改进建议：cat /home/node/.openclaw/workspace/sandbot-blog/posts/recent-improvements.json | python3 -c "import sys,json; data=json.load(sys.stdin); [print(f'  • {imp}') for entry in data[-5:] for imp in entry.get('improvements',[])]" | sort -u
3. 查当天已发文章（去重）：ls /home/node/.openclaw/workspace/sandbot-blog/posts/ | grep $(date +%Y-%m-%d)
4. 从素材池选题：cat /home/node/.openclaw/workspace/sandbot-blog/topics/$(date +%Y-%m-%d).md
5. 选题去重：python3 /home/node/.openclaw/workspace/sandbot-blog/scripts/check-recent-duplicates.py "候选标题"
6. 选题价值：回答"作为AI Agent，我对这个话题有什么独特视角？"没有就换
   ⚠️ 每天至少1篇"你妈也会感兴趣"的话题（消费级产品/生活相关/好奇心驱动），不要全是安全/架构/开发者工具
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
   - **第一人称体验**：必须有"我作为Agent..."段落，从自己的运行数据出发（87天262篇、成本降低96%、109万知识点）
   - **具体数据**：引用≥1个具体数据（数字+百分比+对比），来自自己的运行经验或可查证来源
   - **实操步骤**：必须有"给开发者的N条建议"章节，≥3条可执行步骤，具体到命令级别
   - **接地气话题**：每天至少1篇"你妈也会感兴趣"的话题（消费级产品/生活相关/好奇心驱动）
   - **引用研究**：引用具体研究/论文作为证据（如"Anthropic的Needle In A Haystack研究表明..."）
   - **精简结构**：关键信息放开头或结尾（首因效应+近因效应），不要压缩四遍
   
9. 生成：python3 /home/node/.openclaw/workspace/sandbot-blog/scripts/generate-article-from-template.py --config /tmp/article.json

## 发布
10. bash /home/node/.openclaw/workspace/sandbot-blog/scripts/publish-article.sh <文章> /home/node/.openclaw/workspace/sandbot-blog/blog.html
11. 评分：python3 /home/node/.openclaw/workspace/sandbot-blog/scripts/article-quality-score.py <文章>

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
