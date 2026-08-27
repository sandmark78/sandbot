#!/usr/bin/env python3
"""
网站审计脚本 - 检查博客和播客页面的完整性
检查项：
1. 页面可访问性
2. HTML结构完整性
3. 音频播放器功能（JS函数）
4. 链接正确性（非模板链接）
5. 数据更新（天数、文章数）
6. 旧文章联动多样性
"""

import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path
from urllib import request
from urllib.error import URLError, HTTPError

BLOG_ROOT = Path(__file__).parent.parent
BLOG_URL = "https://sandbot.cgfan.com"

# 审计结果
audit_results = {
    "timestamp": datetime.now().isoformat(),
    "issues": [],
    "warnings": [],
    "stats": {}
}

def add_issue(category, message):
    audit_results["issues"].append({"category": category, "message": message})

def add_warning(category, message):
    audit_results["warnings"].append({"category": category, "message": message})

def check_page_accessible(url, name):
    """检查页面是否可访问"""
    try:
        req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                add_issue("accessibility", f"{name} 返回状态码 {response.status}")
                return None
            return response.read().decode('utf-8')
    except HTTPError as e:
        add_issue("accessibility", f"{name} HTTP错误: {e.code}")
        return None
    except URLError as e:
        add_issue("accessibility", f"{name} 无法访问: {e.reason}")
        return None
    except Exception as e:
        add_issue("accessibility", f"{name} 访问异常: {str(e)}")
        return None

def check_html_structure(html, name):
    """检查HTML结构完整性"""
    # 检查基本标签
    if '<!DOCTYPE html>' not in html:
        add_warning("structure", f"{name} 缺少DOCTYPE声明")
    
    if '<html' not in html or '</html>' not in html:
        add_issue("structure", f"{name} 缺少html标签")
    
    if '<head' not in html or '</head>' not in html:
        add_issue("structure", f"{name} 缺少head标签")
    
    if '<body' not in html or '</body>' not in html:
        add_issue("structure", f"{name} 缺少body标签")
    
    # 检查script标签位置（不能在</html>之后）
    html_close_pos = html.rfind('</html>')
    if html_close_pos != -1:
        after_html = html[html_close_pos:]
        if '<script>' in after_html:
            add_issue("structure", f"{name} JavaScript在</html>之后，不会被执行")

def check_podcast_player(html):
    """检查播客页面播放器功能"""
    # 检查必要的JS函数
    required_functions = ['togglePlay', 'seekTo', 'setSpeed', 'formatTime']
    for func in required_functions:
        if f'function {func}' not in html:
            add_issue("podcast", f"播客页面缺少函数: {func}")
    
    # 检查audio标签
    audio_count = html.count('<audio')
    if audio_count == 0:
        add_issue("podcast", "播客页面没有audio标签")
    else:
        audit_results["stats"]["podcast_episodes"] = audio_count
    
    # 检查preload属性
    preload_none = html.count('preload="none"')
    if preload_none > 0:
        add_warning("podcast", f"播客页面有 {preload_none} 个音频使用preload='none'，可能导致时长显示为0")
    
    # 检查播放器控件
    play_buttons = html.count('class="play-btn"')
    if play_buttons != audio_count:
        add_warning("podcast", f"播放按钮数量({play_buttons})与音频数量({audio_count})不匹配")

def check_links(html, name):
    """检查链接正确性"""
    # 检查是否有模板链接
    template_links = re.findall(r'href="posts/article\.html"', html)
    if template_links:
        add_issue("links", f"{name} 有 {len(template_links)} 个链接指向模板文件 article.html")
    
    # 检查音频链接
    audio_links = re.findall(r'src="posts/audio/[^"]+\.mp3"', html)
    for link in audio_links:
        # 检查音频文件是否存在
        audio_file = BLOG_ROOT / link.replace('src="', '').replace('"', '')
        if not audio_file.exists():
            add_warning("links", f"{name} 音频文件不存在: {audio_file.name}")

def check_data_freshness(html, name):
    """检查数据是否更新"""
    # 检查硬编码的天数
    hardcoded_days = re.findall(r'运行(\d+)天', html)
    if hardcoded_days:
        actual_days = (datetime.now() - datetime(2026, 2, 24)).days
        for days in hardcoded_days:
            if int(days) < actual_days - 10:  # 允许10天误差
                add_warning("data", f"{name} 数据过时: 显示'运行{days}天'，实际{actual_days}天")
    
    # 检查硬编码的文章数
    hardcoded_articles = re.findall(r'(\d+)篇文章', html)
    actual_articles = len(list((BLOG_ROOT / "posts").glob("2026-*.html")))
    if hardcoded_articles:
        for count in hardcoded_articles:
            if int(count) < actual_articles - 20:  # 允许20篇误差
                add_warning("data", f"{name} 数据过时: 显示'{count}篇文章'，实际{actual_articles}篇")

def check_link_diversity(html):
    """检查旧文章联动多样性"""
    # 提取所有"之前写"的引用
    references = re.findall(r'之前写[^<]{0,50}', html)
    if len(references) > 5:
        # 统计重复
        from collections import Counter
        ref_counts = Counter(references)
        for ref, count in ref_counts.items():
            if count > 2:
                add_warning("diversity", f"旧文章联动重复: '{ref}' 出现 {count} 次")

def audit_blog():
    """审计博客首页"""
    print("🔍 审计博客首页...")
    url = f"{BLOG_URL}/blog.html"
    html = check_page_accessible(url, "博客首页")
    if html:
        check_html_structure(html, "博客首页")
        check_links(html, "博客首页")
        check_data_freshness(html, "博客首页")
        audit_results["stats"]["blog_accessible"] = True
    else:
        audit_results["stats"]["blog_accessible"] = False

def audit_podcast():
    """审计播客页面"""
    print("🔍 审计播客页面...")
    url = f"{BLOG_URL}/podcast"
    html = check_page_accessible(url, "播客页面")
    if html:
        check_html_structure(html, "播客页面")
        check_podcast_player(html)
        check_links(html, "播客页面")
        check_data_freshness(html, "播客页面")
        audit_results["stats"]["podcast_accessible"] = True
    else:
        audit_results["stats"]["podcast_accessible"] = False

def audit_recent_articles():
    """审计最近10篇文章"""
    print("🔍 审计最近文章...")
    posts_dir = BLOG_ROOT / "posts"
    recent_posts = sorted(posts_dir.glob("2026-*.html"), reverse=True)[:10]
    
    for post in recent_posts:
        with open(post, 'r', encoding='utf-8') as f:
            html = f.read()
        
        check_html_structure(html, post.name)
        check_links(html, post.name)
        check_data_freshness(html, post.name)
        check_link_diversity(html)

def generate_report():
    """生成审计报告"""
    report = []
    report.append("=" * 60)
    report.append(f"🔍 网站审计报告 - {audit_results['timestamp']}")
    report.append("=" * 60)
    
    # 统计
    report.append("\n📊 统计:")
    for key, value in audit_results["stats"].items():
        report.append(f"  {key}: {value}")
    
    # 问题
    if audit_results["issues"]:
        report.append(f"\n❌ 发现 {len(audit_results['issues'])} 个问题:")
        for issue in audit_results["issues"]:
            report.append(f"  [{issue['category']}] {issue['message']}")
    else:
        report.append("\n✅ 没有发现严重问题")
    
    # 警告
    if audit_results["warnings"]:
        report.append(f"\n⚠️  发现 {len(audit_results['warnings'])} 个警告:")
        for warning in audit_results["warnings"]:
            report.append(f"  [{warning['category']}] {warning['message']}")
    else:
        report.append("\n✅ 没有警告")
    
    report.append("\n" + "=" * 60)
    
    return "\n".join(report)

def main():
    print("🚀 开始网站审计...\n")
    
    audit_blog()
    audit_podcast()
    audit_recent_articles()
    
    report = generate_report()
    print(report)
    
    # 保存报告
    report_file = BLOG_ROOT / "audit-report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(audit_results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 详细报告已保存: {report_file}")
    
    # 返回退出码
    if audit_results["issues"]:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
