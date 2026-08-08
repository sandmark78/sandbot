#!/usr/bin/env python3
"""
成本效率追踪脚本
追踪三个核心指标：
1. 单次产出成本 = 总成本 / 有效产出数量
2. 冗余调用率 = 缓存命中前的重复调用 / 总调用
3. 成本/信息密度 = 单次调用成本 / 信息密度

用法: python3 cost-efficiency-tracker.py [--week|--month]
"""

import sys
import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path

BLOG_ROOT = Path(__file__).parent.parent
MEMORY_DIR = BLOG_ROOT.parent / "memory"

def count_articles(days=7):
    """统计指定天数内的文章数量"""
    posts_dir = BLOG_ROOT / "posts"
    cutoff_date = datetime.now() - timedelta(days=days)
    count = 0
    
    for f in posts_dir.glob("*.html"):
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})', f.name)
        if date_match:
            file_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
            if file_date >= cutoff_date:
                count += 1
    
    return count

def count_cron_runs(days=7):
    """从cron日志统计调用次数"""
    # 简化版：估算每天约5个文章cron + 其他cron
    # 实际应该从cron state里读取
    return days * 8  # 每天约8次cron调用

def estimate_cost(articles, cron_runs):
    """估算成本（基于模型定价）"""
    # qwen3.5-plus 按次计费
    # 文章生成：每篇约5-8次调用（选题+生成+验证+发布）
    # cron任务：每次约1-2次调用
    article_calls = articles * 6  # 平均6次/篇
    cron_calls = cron_runs * 1.5  # 平均1.5次/cron
    total_calls = article_calls + cron_calls
    cost_per_call = 0.01  # ¥/次（qwen3.5-plus约¥0.01/次）
    return total_calls * cost_per_call, total_calls

def calculate_information_density(days=7):
    """计算信息密度（简化版：文章总字数）"""
    posts_dir = BLOG_ROOT / "posts"
    cutoff_date = datetime.now() - timedelta(days=days)
    total_chars = 0
    
    for f in posts_dir.glob("*.html"):
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})', f.name)
        if date_match:
            file_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
            if file_date >= cutoff_date:
                with open(f, 'r', encoding='utf-8') as file:
                    content = file.read()
                    # 提取正文
                    article_match = re.search(r'<article[^>]*>(.*?)</article>', content, re.DOTALL)
                    if article_match:
                        text = re.sub(r'<[^>]+>', '', article_match.group(1))
                        total_chars += len(text)
    
    return total_chars

def main():
    days = 7
    if '--month' in sys.argv:
        days = 30
    elif '--week' in sys.argv:
        days = 7
    
    print(f"📊 成本效率追踪（最近{days}天）")
    print("")
    
    # 1. 统计产出
    articles = count_articles(days)
    print(f"📝 文章产出: {articles} 篇")
    
    # 2. 估算调用次数（简化版）
    # 实际应该从cron state里读取
    cron_runs = articles * 2  # 假设每篇文章有2个相关cron任务
    total_calls, cost = estimate_cost(articles, cron_runs)
    print(f"📞 估算调用次数: {total_calls:.0f} 次")
    print(f"💰 估算成本: ¥{cost:.2f}")
    
    # 3. 计算单次产出成本
    if articles > 0:
        cost_per_article = cost / articles
        print(f"📊 单次产出成本: ¥{cost_per_article:.2f}/篇")
    else:
        print(f"📊 单次产出成本: N/A（无产出）")
    
    # 4. 计算信息密度
    total_chars = calculate_information_density(days)
    print(f"📖 信息密度: {total_chars:,} 字符")
    
    # 5. 计算成本/信息密度
    if total_chars > 0:
        cost_per_10k_chars = (cost / total_chars) * 10000
        print(f"📊 成本/万字: ¥{cost_per_10k_chars:.2f}")
    else:
        print(f"📊 成本/万字: N/A")
    
    # 6. 告警检查
    print("")
    alerts = []
    if articles == 0:
        alerts.append("⚠️  本周无文章产出")
    if cost > 10:  # 超过¥10告警
        alerts.append(f"⚠️  成本超过基线: ¥{cost:.2f} > ¥10")
    
    if alerts:
        print("🚨 告警:")
        for alert in alerts:
            print(f"   {alert}")
    else:
        print("✅ 无告警")
    
    # 7. 输出到文件
    report_file = MEMORY_DIR / f"cost-report-{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 成本效率报告\n\n")
        f.write(f"**统计周期**: 最近{days}天\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n\n")
        f.write(f"## 核心指标\n\n")
        f.write(f"- 文章产出: {articles} 篇\n")
        f.write(f"- 估算调用次数: {total_calls:.0f} 次\n")
        f.write(f"- 估算成本: ¥{cost:.2f}\n")
        if articles > 0:
            f.write(f"- 单次产出成本: ¥{cost/articles:.2f}/篇\n")
        f.write(f"- 信息密度: {total_chars:,} 字符\n")
        if total_chars > 0:
            f.write(f"- 成本/万字: ¥{(cost/total_chars)*10000:.2f}\n")
        f.write(f"\n## 告警\n\n")
        if alerts:
            for alert in alerts:
                f.write(f"- {alert}\n")
        else:
            f.write("- ✅ 无告警\n")
    
    print(f"\n📄 报告已写入: {report_file}")

if __name__ == '__main__':
    main()
