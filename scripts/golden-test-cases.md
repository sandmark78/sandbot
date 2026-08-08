# 黄金测试用例（10个典型任务 + 预期输出）

**创建时间**: 2026-08-07
**用途**: 回归测试，确保核心功能不退化

---

## 文章生成类（5个）

### 1. 午间文章（标准流程）
**输入**: topic-pool.py 选中的话题
**预期输出**:
- 文件: `posts/YYYY-MM-DD-noon-<topic>.html`
- 字数: >= 2000字
- Agent视角: >= 3处
- 占位符: 0处
- 质量评分: >= 70分
- 音频: 已生成（如>=3000字）
- blog.html: 已更新
- Git: 已推送

### 2. 热点文章（去重检查）
**输入**: 与已发文章相似的话题
**预期输出**:
- check-recent-duplicates.py 返回 exit code 1
- 文章不发布
- 汇报: "发现重复选题，已跳过"

### 3. 占位符拦截
**输入**: 包含"来源说明"占位符的文章
**预期输出**:
- publish-article.sh 返回 exit code 1
- 文章不发布
- 汇报: "发现占位符，拒绝发布"

### 4. 质量评分报警
**输入**: 字数<2000字的文章
**预期输出**:
- article-quality-score.py 返回 exit code 1
- 评分: <70分
- 汇报: "质量评分低于70分，建议检查"

### 5. 选题价值检查
**输入**: "千问新功能"（无独特视角）
**预期输出**:
- 回答"作为AI Agent，我对这个话题有什么独特视角？"
- 答案: "没有，我只是在报道产品更新"
- 跳过，选下一个

---

## 审计类（3个）

### 6. 每周工具审计
**输入**: cron 每周日22:00触发
**预期输出**:
- 检查 skills/knowledge/memory 状态
- 测试 AIHOT API 和 HN 是否可访问
- 写入 memory/weekly-audit-YYYY-MM-DD.md
- 汇报给老大

### 7. 每周记忆压缩
**输入**: cron 每周日23:00触发
**预期输出**:
- 读取本周每日记忆
- 提炼核心教训到 MEMORY.md
- 检查 MEMORY.md 行数（<=300行）
- 写入 memory/memory-compression-YYYY-MM-DD.md
- 汇报给老大

### 8. 每日复盘
**输入**: cron 每天23:00触发
**预期输出**:
- 检查今天文章数量
- 检查是否有占位符问题
- 检查 practical-techniques.md 是否更新
- 写入 memory/YYYY-MM-DD-review.md
- 汇报给老大

---

## 学习类（2个）

### 9. 每周学习汇报
**输入**: cron 每周一18:00触发
**预期输出**:
- 统计本周文章数量
- 检查本周发现的问题
- 检查本周更新的指南
- 写入 memory/weekly-learning-report-YYYY-MM-DD.md
- 汇报给老大: "本周学到了X，改了Y，还有Z没解决"

### 10. 成本效率追踪
**输入**: python3 cost-efficiency-tracker.py --week
**预期输出**:
- 统计文章产出
- 估算调用次数和成本
- 计算单次产出成本
- 计算信息密度
- 如果成本>¥10，告警
- 写入 memory/cost-report-YYYY-MM-DD.md

---

## 使用方法

**手动测试**:
```bash
# 测试占位符拦截
echo '<html>来源说明</html>' > /tmp/test.html
bash scripts/publish-article.sh /tmp/test.html blog.html
# 预期: exit code 1, "发现占位符"

# 测试质量评分
python3 scripts/article-quality-score.py posts/2026-08-07-evening-ai-cooking-steak.html
# 预期: 100/100, "通过"

# 测试选题去重
python3 scripts/check-recent-duplicates.py "帕累托最优选马里奥角色"
# 预期: exit code 0 或 1（取决于最近7天是否有类似标题）
```

**自动化测试**（未来）:
```bash
# 每周自动运行黄金测试
for test in 1 2 3 4 5; do
  echo "运行测试 $test..."
  # 执行测试，检查结果
done
```

---

**状态**: ✅ 已定义，待自动化
