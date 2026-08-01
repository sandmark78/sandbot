#!/usr/bin/env python3
"""
blog-weekly-health.py — 博客周度健康报告 v1.0
Sandbot 每周工具脚本 · 2026-07-19

解决的问题（本周反复出现的坑汇总）：
  1. 文章文件扩展名错误 (.md 而非 .html) — 07-18
  2. TTS 文本含 markdown 符号 (@, ·, **, ——) — 07-18
  3. 文章类型标签与文件名不匹配 — 07-13, 07-14, 07-17
  4. blog.html 重复条目 — 07-17
  5. 文章保存到错误路径 — 07-14
  6. 发布后只输出相对路径 — 07-13
  7. 长文章缺少音频 — 多次

本脚本整合所有检查，输出一份周度健康报告 + 趋势对比。

用法:
  python3 scripts/blog-weekly-health.py                  # 本周报告
  python3 scripts/blog-weekly-health.py --days 14        # 最近 14 天
  python3 scripts/blog-weekly-health.py --fix            # 自动修复可修复的问题
  python3 scripts/blog-weekly-health.py --json           # JSON 输出
  python3 scripts/blog-weekly-health.py --quiet          # 只输出摘要
"""

import os
import sys
import re
import json
import glob
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from html.parser import HTMLParser
# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# ── 配置 ──────────────────────────────────────────────────────────────

REPO_DIR = BLOG_ROOT
POSTS_DIR = os.path.join(REPO_DIR, "posts")
BLOG_HTML = os.path.join(REPO_DIR, "blog.html")
FEED_XML = os.path.join(REPO_DIR, "feed.xml")
AUDIO_DIR = os.path.join(POSTS_DIR, "audio")
SITE_URL = "https://sandbot.cgfan.com"

# 长文章应有音频的字数阈值
AUDIO_THRESHOLD_WORDS = 3000

# 文件名关键词 → 正确 typeLabel
FILENAME_TYPE_MAP = {
    "early": "早鸟",
    "morning": "早鸟",
    "noon": "午间",
    "afternoon": "下午",
    "evening": "晚间",
    "night": "晚间",
    "hot": "热点",
    "breaking": "热点",
}

# V4 模板必须元素
V4_MUST = [
    (r'<meta\s+name="viewport"', "viewport"),
    (r'<meta\s+charset="UTF-8"', "charset"),
    (r'<title>[^<]+</title>', "title"),
    (r'class="site-header"', "site-header"),
    (r'class="overline"', "overline"),
    (r'<nav[^>]*>', "nav"),
    (r'class="article-title"', "article-title"),
    (r'class="article-meta"', "article-meta"),
    (r'class="(post-body|article-body|article-content|container)"', "post-body/container"),
]

V4_RECOMMENDED = [
    (r'class="article-subtitle"', "article-subtitle"),
    (r'class="label-category"', "label-category"),
    (r'class="quick-glance"', "quick-glance"),
    (r'@media', "mobile-responsive"),
]


# ── 工具函数 ──────────────────────────────────────────────────────────

def count_words(text):
    """中英文混合字数统计"""
    chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
    english = len(re.findall(r'[a-zA-Z]+', text))
    return chinese + english


def extract_text_from_html(html):
    """从 HTML 提取纯文本"""
    class TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text = []
            self.skip = False
        def handle_starttag(self, tag, attrs):
            if tag in ('script', 'style'):
                self.skip = True
        def handle_endtag(self, tag):
            if tag in ('script', 'style'):
                self.skip = False
        def handle_data(self, data):
            if not self.skip:
                self.text.append(data)
    
    parser = TextExtractor()
    parser.feed(html)
    return ' '.join(parser.text)


def get_recent_posts(days=7):
    """获取最近 N 天的文章文件"""
    if not os.path.isdir(POSTS_DIR):
        return []
    
    cutoff = datetime.now() - timedelta(days=days)
    posts = []
    
    for f in sorted(glob.glob(os.path.join(POSTS_DIR, "*.html"))):
        basename = os.path.basename(f)
        # 提取日期: 2026-07-19-xxx.html
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})', basename)
        if not date_match:
            continue
        
        try:
            file_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
            if file_date >= cutoff:
                posts.append(f)
        except ValueError:
            continue
    
    return posts


def check_file_extension(posts):
    """检查 1: 文件扩展名错误"""
    issues = []
    repo_files = glob.glob(os.path.join(REPO_DIR, "posts", "*.md"))
    for f in repo_files:
        basename = os.path.basename(f)
        if re.match(r'\d{4}-\d{2}-\d{2}', basename):
            issues.append({
                "file": basename,
                "severity": "error",
                "check": "file-extension",
                "message": f"文件扩展名错误: {basename} 应为 .html",
                "fixable": True,
            })
    return issues


def check_wrong_path(posts):
    """检查 2: 文章在错误路径 (blog/posts/ 而不是 posts/)"""
    issues = []
    wrong_paths = [
        os.path.join(REPO_DIR, "blog", "posts"),
        os.path.join(REPO_DIR, "blog", "blog", "posts"),
    ]
    for wp in wrong_paths:
        if os.path.isdir(wp):
            for f in glob.glob(os.path.join(wp, "*.html")):
                basename = os.path.basename(f)
                if re.match(r'\d{4}-\d{2}-\d{2}', basename):
                    issues.append({
                        "file": basename,
                        "severity": "error",
                        "check": "wrong-path",
                        "message": f"文件在错误路径: {wp}/{basename}",
                        "fixable": True,
                    })
    return issues


def check_v4_compliance(post_file):
    """检查 3: V4 模板合规性"""
    issues = []
    basename = os.path.basename(post_file)
    
    with open(post_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    for pattern, name in V4_MUST:
        if not re.search(pattern, html):
            issues.append({
                "file": basename,
                "severity": "error",
                "check": "v4-missing",
                "message": f"缺少 V4 必须元素: {name}",
                "fixable": False,
            })
    
    missing_recommended = []
    for pattern, name in V4_RECOMMENDED:
        if not re.search(pattern, html):
            missing_recommended.append(name)
            issues.append({
                "file": basename,
                "severity": "warning",
                "check": "v4-recommended",
                "message": f"缺少 V4 推荐元素: {name}",
                "fixable": False,
            })
    
    return issues


def check_tts_text_quality(post_file):
    """检查 4: TTS 文本质量（markdown 符号泄漏）"""
    issues = []
    basename = os.path.basename(post_file)
    
    with open(post_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    text = extract_text_from_html(html)
    
    # 检查 markdown 符号 (只检查真正会导致 TTS 朗读问题的符号)
    # —— 和 · 是合法中文标点，只在不合理密度时才警告
    md_symbols = {
        '@': len(re.findall(r'(?<!\w)@(?!\w)', text)),
        '**': len(re.findall(r'\*\*', text)),
        '——': len(re.findall(r'——', text)),
        '·': len(re.findall(r'·', text)),
    }
    
    # 只报告真正有问题的（@ 和 ** 必须清除，—— 和 · 超过阈值才报告）
    problematic = {}
    for sym, count in md_symbols.items():
        if sym in ('@', '**') and count > 0:
            problematic[sym] = count
        elif sym == '——' and count > 15:  # 正常文章 5-15 个 em dash
            problematic[sym] = count
        elif sym == '·' and count > 12:  # 正常文章 5-12 个 middle dot
            problematic[sym] = count
    
    for symbol, count in problematic.items():
        if count > 0:
            issues.append({
                "file": basename,
                "severity": "warning",
                "check": "tts-markdown-leak",
                "message": f"TTS 文本含 markdown 符号 '{symbol}' × {count}",
                "fixable": False,
            })
    
    # 检查 HTML 标签泄漏
    html_tags = re.findall(r'<[a-z][^>]*>', text)
    if html_tags:
        issues.append({
            "file": basename,
            "severity": "error",
            "check": "tts-html-leak",
            "message": f"TTS 文本含 HTML 标签: {html_tags[:3]}",
            "fixable": False,
        })
    
    return issues


def check_audio(post_file):
    """检查 5: 长文章是否有音频"""
    issues = []
    basename = os.path.basename(post_file)
    name_no_ext = os.path.splitext(basename)[0]
    
    with open(post_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    text = extract_text_from_html(html)
    word_count = count_words(text)
    
    if word_count >= AUDIO_THRESHOLD_WORDS:
        # 检查是否有音频文件或音频播放器
        audio_file = os.path.join(AUDIO_DIR, f"{name_no_ext}.mp3")
        has_audio_player = bool(re.search(r'class="audio-player"|<audio', html))
        has_audio_ref = bool(re.search(r'audio/', html))
        
        if not os.path.exists(audio_file) and not has_audio_player and not has_audio_ref:
            issues.append({
                "file": basename,
                "severity": "warning",
                "check": "missing-audio",
                "message": f"长文章 ({word_count} 字) 缺少音频",
                "fixable": False,
            })
    
    return issues


def check_label_match(post_file):
    """检查 6: 文件名与类型标签是否匹配
    
    只检查时间标签之间的冲突（如文件名 early 但标签"下午"）。
    内容标签（深度、热点、工程实测等）不算不匹配。
    """
    issues = []
    basename = os.path.basename(post_file)
    
    with open(post_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 从文件名推断应有时间标签
    expected_label = None
    for keyword, label in FILENAME_TYPE_MAP.items():
        if keyword in basename.lower():
            expected_label = label
            break
    
    if not expected_label:
        return issues
    
    # 从 HTML 提取实际标签
    label_match = re.search(r'class="label-category"[^>]*>([^<]+)<', html)
    if not label_match:
        return issues
    
    actual_label = label_match.group(1).strip()
    
    # 只在实际标签也是时间标签且不同时才报错
    # 时间标签集合
    time_labels = set(FILENAME_TYPE_MAP.values())  # 早鸟, 午间, 下午, 晚间, 热点
    
    if actual_label in time_labels and actual_label != expected_label:
        issues.append({
            "file": basename,
            "severity": "warning",
            "check": "label-mismatch",
            "message": f"时间标签不匹配: 文件名暗示 '{expected_label}'，实际是 '{actual_label}'",
            "fixable": True,
        })
    
    return issues


def check_blog_html_consistency():
    """检查 7: blog.html 一致性问题"""
    issues = []
    
    if not os.path.exists(BLOG_HTML):
        return [{"file": "blog.html", "severity": "error", "check": "missing-blog-html",
                 "message": "blog.html 不存在", "fixable": False}]
    
    with open(BLOG_HTML, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 articles 数组中的 URL
    match = re.search(r"const articles\s*=\s*(\[[\s\S]*?\n\s*\]);", content)
    if not match:
        return [{"file": "blog.html", "severity": "error", "check": "no-articles-array",
                 "message": "blog.html 中无 articles 数组", "fixable": False}]
    
    articles_str = match.group(1)
    urls = re.findall(r'url:\s*"([^"]+)"', articles_str)
    
    # 检查重复
    url_counts = {}
    for u in urls:
        normalized = u.rstrip('/').replace('http://', 'https://')
        url_counts[normalized] = url_counts.get(normalized, 0) + 1
    
    for url, count in url_counts.items():
        if count > 1:
            issues.append({
                "file": "blog.html",
                "severity": "error",
                "check": "duplicate-entry",
                "message": f"重复条目: {url} (×{count})",
                "fixable": True,
            })
    
    # 检查幽灵帖子 (blog.html 有条目但文件不存在)
    for url in urls:
        # 从 URL 推断文件路径
        path_match = re.search(r'posts/([^"\']+)', url)
        if path_match:
            post_name = path_match.group(1).rstrip('/')
            post_file = os.path.join(POSTS_DIR, post_name)
            post_file_html = post_file if post_file.endswith('.html') else post_file + '.html'
            if not os.path.exists(post_file_html):
                # 也检查不带 .html 的情况
                if not os.path.exists(os.path.join(POSTS_DIR, post_name)):
                    issues.append({
                        "file": "blog.html",
                        "severity": "error",
                        "check": "ghost-post",
                        "message": f"幽灵帖子: blog.html 有条目但文件不存在: {post_name}",
                        "fixable": False,
                    })
    
    # 检查旧域名残留
    old_domain_refs = re.findall(r'sandmark78\.github\.io', content)
    if old_domain_refs:
        issues.append({
            "file": "blog.html",
            "severity": "error",
            "check": "old-domain",
            "message": f"旧域名残留: sandmark78.github.io (×{len(old_domain_refs)})",
            "fixable": True,
        })
    
    return issues


def check_rss_consistency():
    """检查 8: RSS 一致性"""
    issues = []
    
    if not os.path.exists(FEED_XML):
        return [{"file": "feed.xml", "severity": "error", "check": "missing-rss",
                 "message": "feed.xml 不存在", "fixable": False}]
    
    with open(FEED_XML, 'r', encoding='utf-8') as f:
        rss_content = f.read()
    
    rss_urls = set(re.findall(r'<link>([^<]+)</link>', rss_content))
    
    # 检查旧域名
    old_refs = re.findall(r'sandmark78\.github\.io', rss_content)
    if old_refs:
        issues.append({
            "file": "feed.xml",
            "severity": "error",
            "check": "rss-old-domain",
            "message": f"RSS 含旧域名 (×{len(old_refs)})",
            "fixable": True,
        })
    
    return issues


# ── 修复函数 ──────────────────────────────────────────────────────────

def fix_file_extension(issues):
    """修复文件扩展名错误"""
    fixed = 0
    for issue in issues:
        if issue["check"] == "file-extension" and issue["fixable"]:
            old_path = os.path.join(REPO_DIR, "posts", issue["file"])
            new_path = old_path.rsplit('.', 1)[0] + '.html'
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                print(f"  ✅ 修复: {issue['file']} → {os.path.basename(new_path)}")
                fixed += 1
    return fixed


def fix_label_mismatch(issues):
    """修复标签不匹配"""
    fixed = 0
    for issue in issues:
        if issue["check"] == "label-mismatch" and issue["fixable"]:
            post_file = os.path.join(POSTS_DIR, issue["file"])
            if not os.path.exists(post_file):
                continue
            
            with open(post_file, 'r', encoding='utf-8') as f:
                html = f.read()
            
            # 推断正确标签
            basename = issue["file"]
            expected_label = None
            for keyword, label in FILENAME_TYPE_MAP.items():
                if keyword in basename.lower():
                    expected_label = label
                    break
            
            if expected_label:
                # 替换标签
                new_html = re.sub(
                    r'(class="label-category"[^>]*>)[^<]+(<)',
                    f'\\g<1>{expected_label}\\g<2>',
                    html
                )
                if new_html != html:
                    with open(post_file, 'w', encoding='utf-8') as f:
                        f.write(new_html)
                    print(f"  ✅ 修复标签: {issue['file']} → '{expected_label}'")
                    fixed += 1
    
    return fixed


def fix_old_domain(issues):
    """修复旧域名引用"""
    fixed = 0
    for issue in issues:
        if issue["check"] in ("old-domain", "rss-old-domain") and issue["fixable"]:
            filepath = os.path.join(REPO_DIR, issue["file"])
            if not os.path.exists(filepath):
                continue
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content.replace(
                'sandmark78.github.io/sandbot',
                'sandbot.cgfan.com'
            ).replace(
                'sandmark78.github.io',
                'sandbot.cgfan.com'
            )
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"  ✅ 修复旧域名: {issue['file']}")
                fixed += 1
    
    return fixed


# ── 主逻辑 ────────────────────────────────────────────────────────────

def run_health_check(days=7, fix=False, quiet=False, json_output=False):
    """运行健康检查"""
    all_issues = []
    stats = {
        "days": days,
        "posts_scanned": 0,
        "errors": 0,
        "warnings": 0,
        "fixable": 0,
        "fixed": 0,
        "checks": {},
    }
    
    # 获取近期文章
    posts = get_recent_posts(days)
    stats["posts_scanned"] = len(posts)
    
    # 逐篇检查
    per_article_checks = [
        ("v4-compliance", check_v4_compliance),
        ("tts-quality", check_tts_text_quality),
        ("audio", check_audio),
        ("label-match", check_label_match),
    ]
    
    for post in posts:
        for check_name, check_fn in per_article_checks:
            issues = check_fn(post)
            all_issues.extend(issues)
            stats["checks"][check_name] = stats["checks"].get(check_name, 0) + 1
    
    # 全局检查
    global_checks_no_args = [
        ("blog-html", check_blog_html_consistency),
        ("rss", check_rss_consistency),
    ]
    
    global_checks_with_posts = [
        ("file-extension", check_file_extension),
        ("wrong-path", check_wrong_path),
    ]
    
    for check_name, check_fn in global_checks_with_posts:
        issues = check_fn(posts)
        all_issues.extend(issues)
        stats["checks"][check_name] = stats["checks"].get(check_name, 0) + 1
    
    for check_name, check_fn in global_checks_no_args:
        issues = check_fn()
        all_issues.extend(issues)
        stats["checks"][check_name] = stats["checks"].get(check_name, 0) + 1
    
    # 统计
    for issue in all_issues:
        if issue["severity"] == "error":
            stats["errors"] += 1
        else:
            stats["warnings"] += 1
        if issue["fixable"]:
            stats["fixable"] += 1
    
    # 自动修复
    if fix:
        print("\n🔧 自动修复中...")
        stats["fixed"] += fix_file_extension(all_issues)
        stats["fixed"] += fix_label_mismatch(all_issues)
        stats["fixed"] += fix_old_domain(all_issues)
    
    # 输出
    if json_output:
        result = {"stats": stats, "issues": all_issues}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    if quiet:
        score = max(0, 100 - stats["errors"] * 5 - int(stats["warnings"] * 0.5))
        print(f"📊 {days}天健康评分: {score}/100 | {stats['posts_scanned']}篇文章 | "
              f"{stats['errors']}错误 {stats['warnings']}警告"
              f"{' | ' + str(stats['fixed']) + '已修复' if fix else ''}")
        return
    
    # 完整报告
    print(f"\n{'='*60}")
    print(f"🏥 Sandbot Blog 周度健康报告")
    print(f"{'='*60}")
    print(f"📅 周期: 最近 {days} 天")
    print(f"📝 文章数: {stats['posts_scanned']}")
    print(f"🔍 检查项: {sum(stats['checks'].values())}")
    print()
    
    # 健康评分
    score = max(0, 100 - stats["errors"] * 5 - int(stats["warnings"] * 0.5))
    emoji = "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"
    print(f"{emoji} 健康评分: {score}/100")
    print(f"   错误: {stats['errors']} | 警告: {stats['warnings']}"
          f"{' | 已修复: ' + str(stats['fixed']) if fix else ''}")
    print()
    
    # 按严重度分组输出
    errors = [i for i in all_issues if i["severity"] == "error"]
    warnings = [i for i in all_issues if i["severity"] == "warning"]
    
    if errors:
        print(f"❌ 错误 ({len(errors)}):")
        for issue in errors:
            fixable_tag = " [可修复]" if issue["fixable"] else ""
            print(f"   • [{issue['check']}] {issue['message']}{fixable_tag}")
        print()
    
    if warnings:
        print(f"⚠️  警告 ({len(warnings)}):")
        for issue in warnings:
            fixable_tag = " [可修复]" if issue["fixable"] else ""
            print(f"   • [{issue['check']}] {issue['message']}{fixable_tag}")
        print()
    
    if not errors and not warnings:
        print("✅ 所有检查通过！博客状态良好。")
        print()
    
    # 各文章摘要
    print(f"📝 文章列表:")
    for post in posts:
        basename = os.path.basename(post)
        with open(post, 'r', encoding='utf-8') as f:
            html = f.read()
        text = extract_text_from_html(html)
        wc = count_words(text)
        
        post_issues = [i for i in all_issues if i["file"] == basename]
        status = "✅" if not post_issues else f"❌{len([i for i in post_issues if i['severity']=='error'])}⚠️{len([i for i in post_issues if i['severity']=='warning'])}"
        
        # 提取标题
        title_match = re.search(r'<h1 class="article-title">(.*?)</h1>', html, re.DOTALL)
        title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()[:50] if title_match else basename
        
        print(f"   {status} {basename[:45]:45s} | {wc:6d}字 | {title}")
    
    print()
    print(f"{'='*60}")
    print(f"检查项明细: {json.dumps(stats['checks'], ensure_ascii=False)}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="Sandbot Blog 周度健康报告")
    parser.add_argument("--days", type=int, default=7, help="检查最近 N 天 (默认 7)")
    parser.add_argument("--fix", action="store_true", help="自动修复可修复的问题")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--quiet", action="store_true", help="只输出摘要行")
    args = parser.parse_args()
    
    if not os.path.isdir(REPO_DIR):
        print(f"❌ 博客目录不存在: {REPO_DIR}")
        sys.exit(1)
    
    run_health_check(days=args.days, fix=args.fix, quiet=args.quiet, json_output=args.json)


if __name__ == "__main__":
    main()
