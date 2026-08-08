#!/usr/bin/env python3
"""
文章质量自动评分
用法: python3 article-quality-score.py <article-file>
返回: 0=通过(>=70分), 1=不通过(<70分)
"""

import sys
import os
import re

def score_article(filepath):
    """评分文章质量，返回 (总分, 详情)"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    scores = {}
    details = []
    
    # 1. 字数检查 (满分30分)
    # 提取正文（去掉header/footer/nav）
    article_match = re.search(r'<article[^>]*>(.*?)</article>', content, re.DOTALL)
    if article_match:
        article_text = re.sub(r'<[^>]+>', '', article_match.group(1))
        word_count = len(article_text)
    else:
        word_count = len(re.sub(r'<[^>]+>', '', content))
    
    if word_count >= 3000:
        scores['字数'] = 30
        details.append(f"✅ 字数: {word_count} (>=3000)")
    elif word_count >= 2000:
        scores['字数'] = 20
        details.append(f"⚠️ 字数: {word_count} (2000-3000)")
    else:
        scores['字数'] = 0
        details.append(f"❌ 字数: {word_count} (<2000)")
    
    # 2. Agent视角占比 (满分25分)
    # 检查是否有"作为AI"、"我作为Agent"等关键词
    agent_markers = ['作为AI', '作为Agent', '我作为', '我的视角', '我的经验', '我的判断']
    agent_count = sum(content.count(marker) for marker in agent_markers)
    
    if agent_count >= 5:
        scores['Agent视角'] = 25
        details.append(f"✅ Agent视角: {agent_count}处 (>=5)")
    elif agent_count >= 3:
        scores['Agent视角'] = 15
        details.append(f"⚠️ Agent视角: {agent_count}处 (3-5)")
    else:
        scores['Agent视角'] = 0
        details.append(f"❌ Agent视角: {agent_count}处 (<3)")
    
    # 3. 结构完整性 (满分20分)
    required_elements = [
        ('<header', 'header'),
        ('<footer', 'footer'),
        ('section-num', 'section标题'),
        ('article-feedback', '评分组件'),
        ('audio-player', '音频播放器'),
    ]
    
    structure_score = 0
    for element, name in required_elements:
        if element in content:
            structure_score += 4
            details.append(f"✅ {name}")
        else:
            details.append(f"❌ {name}缺失")
    
    scores['结构'] = structure_score
    
    # 4. 占位符检查 (满分15分)
    placeholders = ['来源说明', 'XX 官方', '要点一', '要点二', '要点三', '正文内容...']
    placeholder_count = sum(content.count(p) for p in placeholders)
    
    if placeholder_count == 0:
        scores['占位符'] = 15
        details.append(f"✅ 无占位符")
    else:
        scores['占位符'] = 0
        details.append(f"❌ 发现{placeholder_count}处占位符")
    
    # 5. 来源信息 (满分10分)
    if 'bottom_source' in content or '来源：' in content:
        scores['来源'] = 10
        details.append(f"✅ 来源信息完整")
    else:
        scores['来源'] = 0
        details.append(f"❌ 来源信息缺失")
    
    total = sum(scores.values())
    return total, details, scores

def main():
    if len(sys.argv) < 2:
        print("用法: python3 article-quality-score.py <article-file>")
        sys.exit(2)
    
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        sys.exit(2)
    
    total, details, scores = score_article(filepath)
    
    print(f"📊 文章质量评分: {total}/100")
    print("")
    for detail in details:
        print(f"   {detail}")
    print("")
    
    if total >= 70:
        print(f"✅ 通过 (>=70分)")
        sys.exit(0)
    else:
        print(f"❌ 不通过 (<70分)")
        sys.exit(1)

if __name__ == '__main__':
    main()
