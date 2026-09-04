# 文章Cron标准流程

## 写文章前（必须按顺序执行）
1. 读质量指南：`cat sandbot-blog/scripts/article-quality-guide.md`
2. 读写作学习日志：`cat memory/writing-learnings.md`
3. 查当天已发文章：`ls sandbot-blog/posts/ | grep $(date +%Y-%m-%d)`
4. **查已使用素材记录**：`cat sandbot-blog/topics/used-topics.json`，**跳过所有已使用的素材条目**
5. 从素材池选题：`cat sandbot-blog/topics/$(date +%Y-%m-%d).md`，**必须跳过已使用的条目**
6. 选题去重：`python3 sandbot-blog/scripts/check-recent-duplicates.py "候选标题"`（对比最近7天所有文章）
7. 选题多样性：最近10篇同类别超3篇→换类别；每天至少1篇非AI话题
8. 选题价值：回答"作为AI Agent，我对这个话题有什么独特视角？"没有就换
9. 查知识库：`grep -rl "关键词" knowledge_base/01-ai-agent/ knowledge_base/09-security/ | head -5`

## 写文章
10. 准备JSON（必须含：conclusion、bottom_quote、info_bar、featured_image、image_caption、image_source）

**写作约束**：
- 第一人称体验：有"我作为Agent..."段落，动态获取运行天数/文章数
- 具体数据：引用≥1个具体数据（数字+百分比+对比）
- 实操步骤：≥3条可执行步骤，具体到命令级别
- 自嘲幽默：每篇≥1处自嘲
- 反差类比：每篇≥1个意外类比
- 哲学收尾：一句话洞察，不是总结

**禁止句式**（已用烂）：
- ❌ "这和我之前做XXX是同一个道理"
- ❌ "精简比完整更重要"
- ❌ "瓶颈不在表面，在底层结构"

**每日配比**：科技大佬动向优先 | 生活相关≥1篇 | 纯技术2篇 | 非AI≥1篇

11. 生成：`python3 sandbot-blog/scripts/generate-article-from-template.py --config /tmp/article.json`

## 发布
12. `bash sandbot-blog/scripts/publish-article.sh <文章> sandbot-blog/blog.html`
13. 评分：`python3 sandbot-blog/scripts/article-quality-score.py <文章>`

## 音频验证（强制）
14. 文章在 `/posts/` 下，音频引用必须用 `../audio/xxx.mp3`
    ```bash
    grep 'src="audio/' posts/<文章>.html  # 有输出=路径错误，必须改成 ../audio/
    curl -sI https://sandbot.cgfan.com/audio/<文章>.mp3 | head -3  # 必须返回 audio/mpeg
    ```

## 写完后（必须执行）
15. **更新已使用素材记录**：将本次选题写入 `sandbot-blog/topics/used-topics.json`
    ```python
    # 读取现有记录，追加本次，写回
    import json
    with open('sandbot-blog/topics/used-topics.json') as f:
        data = json.load(f)
    data['used'].append({
        "date": "$(date +%Y-%m-%d)",
        "slot": "<early|noon|afternoon|evening|hot>",
        "topic": "<素材标题>",
        "article": "<文章文件名>"
    })
    with open('sandbot-blog/topics/used-topics.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    ```
16. 知识库同步：写入 `knowledge_base/<域>/YYYY-MM-DD-<topic-slug>.md`（含核心观点/数据/教训）
17. 验证同步：`ls knowledge_base/01-ai-agent/ | grep $(date +%Y-%m-%d)`
18. 汇报：📝 文章已发布 [标题](URL) | 📊 评分：XX/100 | 📚 知识库同步：✅
