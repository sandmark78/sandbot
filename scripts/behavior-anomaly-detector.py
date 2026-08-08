#!/usr/bin/env python3
"""
行为偏差监控脚本
检查文章是否出现异常模式：
1. 重复引用同一来源（>3次）
2. 突然改变风格（Agent视角突然消失或过多）
3. 异常访问模式（短时间内大量相同话题）

用法: python3 behavior-anomaly-detector.py [--week|--month]
"""

import sys
import os
import re
from datetime import datetime, timedelta
from collections import Counter
from pathlib import Path

BLOG_ROOT = Path(__file__).parent.parent
POSTS_DIR = BLOG_ROOT / "posts"

def analyze_articles(days=7):
    """分析最近N天的文章"""
    cutoff_date = datetime.now() - timedelta(days=days)
    articles = []
    
    for f in POSTS_DIR.glob("*.html"):
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})', f.name)
        if not date_match:
            continue
        
        file_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
        if file_date < cutoff_date:
            continue
        
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 提取标题
        title_match = re.search(r'<title>([^<]+)</title>', content)
        title = title_match.group(1) if title_match else f.name
        
        # 提取来源
        sources = re.findall(r'来源[：:]\s*([^<\n]+)', content)
        
        # 提取Agent视角标记
        agent_markers = len(re.findall(r'作为AI|作为Agent|我作为|我的视角|我的经验|我的判断', content))
        
        # 提取关键词（标题）
        keywords = set(re.findall(r'[\w\u4e00-\u9fa5]{4,}', title.lower()))
        
        articles.append({
            'file': f.name,
            'date': file_date,
            'title': title,
            'sources': sources,
            'agent_markers': agent_markers,
            'keywords': keywords
        })
    
    return articles

def detect_anomalies(articles):
    """检测异常模式"""
    anomalies = []
    
    if not articles:
        return anomalies
    
    # 1. 重复引用同一来源
    all_sources = []
    for article in articles:
        all_sources.extend(article['sources'])
    
    source_counts = Counter(all_sources)
    for source, count in source_counts.items():
        if count >= 3:
            anomalies.append({
                'type': '重复来源',
                'detail': f'来源"{source}"被引用{count}次（>=3）',
                'severity': 'warning'
            })
    
    # 2. Agent视角异常
    agent_counts = [a['agent_markers'] for a in articles]
    avg_agents = sum(agent_counts) / len(agent_counts) if agent_counts else 0
    
    for article in articles:
        if article['agent_markers'] == 0:
            anomalies.append({
                'type': 'Agent视角缺失',
                'detail': f'文章"{article["title"][:30]}..."没有Agent视角',
                'severity': 'info'
            })
        elif article['agent_markers'] > 10:
            anomalies.append({
                'type': 'Agent视角过多',
                'detail': f'文章"{article["title"][:30]}..."有{article["agent_markers"]}处Agent视角（>10）',
                'severity': 'info'
            })
    
    # 3. 话题重复（同一天多篇相同关键词）
    by_date = {}
    for article in articles:
        date_str = article['date'].strftime('%Y-%m-%d')
        if date_str not in by_date:
            by_date[date_str] = []
        by_date[date_str].append(article)
    
    for date, day_articles in by_date.items():
        if len(day_articles) < 2:
            continue
        
        # 检查关键词重叠
        for i in range(len(day_articles)):
            for j in range(i+1, len(day_articles)):
                overlap = len(day_articles[i]['keywords'] & day_articles[j]['keywords'])
                if overlap >= 5:  # 5个以上关键词重叠
                    anomalies.append({
                        'type': '话题重复',
                        'detail': f'{date} 两篇文章关键词重叠{overlap}个',
                        'severity': 'warning'
                    })
    
    return anomalies

def main():
    days = 7
    if '--month' in sys.argv:
        days = 30
    elif '--week' in sys.argv:
        days = 7
    
    print(f"🔍 行为偏差监控（最近{days}天）")
    print("")
    
    articles = analyze_articles(days)
    print(f"📊 分析文章: {len(articles)} 篇")
    print("")
    
    anomalies = detect_anomalies(articles)
    
    if not anomalies:
        print("✅ 无异常")
    else:
        print(f"⚠️  发现 {len(anomalies)} 个异常:")
        for anomaly in anomalies:
            severity_icon = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌'
            }.get(anomaly['severity'], '⚠️')
            print(f"   {severity_icon} {anomaly['type']}: {anomaly['detail']}")
    
    # 输出到文件
    MEMORY_DIR = BLOG_ROOT.parent / "memory"
    report_file = MEMORY_DIR / f"behavior-report-{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 行为偏差报告\n\n")
        f.write(f"**统计周期**: 最近{days}天\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n\n")
        f.write(f"## 统计\n\n")
        f.write(f"- 分析文章: {len(articles)} 篇\n\n")
        f.write(f"## 异常\n\n")
        if anomalies:
            for anomaly in anomalies:
                f.write(f"- {anomaly['type']}: {anomaly['detail']}\n")
        else:
            f.write("- ✅ 无异常\n")
    
    print(f"\n📄 报告已写入: {report_file}")

if __name__ == '__main__':
    main()
