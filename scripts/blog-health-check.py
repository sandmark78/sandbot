#!/usr/bin/env python3
"""
blog-health-check.py — 博客健康度全面检查 v1.0
Sandbot 每周工具脚本 · 2026-08-03

解决的问题（本周反复出现的坑）：
  1. posts/ 有 457 篇文章，blog.html JS 数组只有 227 条 → 230 篇"隐身"
  2. feed.xml 只有 50 条 → RSS 订阅者看不到旧文章
  3. sitemap.xml 与磁盘不同步 → SEO 损失
  4. 文章缺少关键字段（excerpt/description）→ 卡片空白
  5. 音频覆盖率极低（36/457）→ TTS 流水线断裂
  6. 文章间内部链接可能指向已删除文章 → 404
  7. 没有统一的"一眼看全局"工具，每次只能手动 grep

核心功能：
  • 磁盘 vs blog.html vs feed.xml vs sitemap.xml 四方对比
  • 孤立文章检测（磁盘有但索引没有）
  • 文章元数据完整性评分
  • 音频覆盖率统计
  • 内部链接有效性检查
  • 健康度评分 (0-100)
  • --fix 模式自动修复可修复项

用法:
  python3 scripts/blog-health-check.py                  # 全面检查
  python3 scripts/blog-health-check.py --fix             # 检查 + 自动修复
  python3 scripts/blog-health-check.py --json            # JSON 输出
  python3 scripts/blog-health-check.py --quick           # 快速检查（跳过链接检查）
  python3 scripts/blog-health-check.py --fix-blog        # 只修复 blog.html 索引
  python3 scripts/blog-health-check.py --fix-rss         # 只修复 feed.xml
  python3 scripts/blog-health-check.py --fix-sitemap     # 只修复 sitemap.xml
  python3 scripts/blog-health-check.py --threshold 80    # 健康度低于阈值时退出码=1

退出码:
  0 = 健康度 >= 阈值
  1 = 健康度 < 阈值
  2 = 脚本错误
"""

import os
import sys
import re
import json
import glob
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── 配置 ──────────────────────────────────────────────────────────────

# 博客根目录（自动解析）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
POSTS_DIR = os.path.join(BLOG_ROOT, "posts")
BLOG_HTML = os.path.join(BLOG_ROOT, "blog.html")
FEED_XML = os.path.join(BLOG_ROOT, "feed.xml")
SITEMAP_XML = os.path.join(BLOG_ROOT, "sitemap.xml")
AUDIO_DIR = os.path.join(POSTS_DIR, "audio")
SITE_URL = "https://sandbot.cgfan.com"

# 健康度权重
WEIGHT_INDEX_COVERAGE = 30    # blog.html 索引覆盖率
WEIGHT_RSS_COVERAGE = 15      # feed.xml 覆盖率
WEIGHT_SITEMAP_COVERAGE = 10  # sitemap.xml 覆盖率
WEIGHT_META_QUALITY = 15      # 元数据完整性
WEIGHT_AUDIO_COVERAGE = 10    # 音频覆盖率
WEIGHT_INTERNAL_LINKS = 10    # 内部链接有效性
WEIGHT_TEMPLATE_COMPLIANCE = 10  # 模板合规性

# 模板必须元素
TEMPLATE_REQUIRED = [
    (r'<meta\s+[^>]*name="viewport"', "viewport meta"),
    (r'<title>[^<]+</title>', "非空 title"),
    (r'class="(site-header|header)"', "头部区域"),
    (r'class="(article-title|post-title)"', "文章标题"),
    (r'class="(post-body|article-body|article-content|container)"', "文章主体"),
    (r'class="(site-footer|footer)"', "底部区域"),
]

# 元数据必须字段
META_REQUIRED_FIELDS = ["title", "date", "url"]
META_RECOMMENDED_FIELDS = ["excerpt", "tag", "type"]

# 内部链接检查并发数
LINK_CHECK_WORKERS = 10


# ── 工具函数 ──────────────────────────────────────────────────────────

def log(msg, level="info"):
    prefix = {"info": "ℹ️ ", "ok": "✅ ", "warn": "⚠️ ", "error": "❌ ", "fix": "🔧 "}
    print(f"  {prefix.get(level, '')}{msg}")


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return None


def extract_slug_from_path(filepath):
    """从文件路径提取 slug (去掉 posts/ 前缀和 .html 后缀)"""
    return os.path.basename(filepath).replace(".html", "")


# ── 1. 磁盘文章扫描 ──────────────────────────────────────────────────

def scan_disk_posts():
    """扫描 posts/ 目录所有 HTML 文件"""
    posts = []
    if not os.path.isdir(POSTS_DIR):
        return posts
    
    for f in sorted(glob.glob(os.path.join(POSTS_DIR, "*.html"))):
        slug = extract_slug_from_path(f)
        content = read_file(f)
        if content is None:
            continue
        
        # 提取元数据
        post = {
            "slug": slug,
            "path": f,
            "size": os.path.getsize(f),
            "modified": os.path.getmtime(f),
        }
        
        # 提取 title
        title_match = re.search(r'<title>([^<]+)</title>', content)
        post["title"] = title_match.group(1).strip() if title_match else ""
        
        # 提取 article-title
        at_match = re.search(r'class="article-title"[^>]*>([^<]+)', content)
        if not at_match:
            at_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
        post["article_title"] = at_match.group(1).strip() if at_match else ""
        
        # 提取 excerpt / description
        desc_match = re.search(r'<meta\s+[^>]*name="description"\s+content="([^"]*)"', content)
        post["description"] = desc_match.group(1).strip() if desc_match else ""
        
        og_match = re.search(r'<meta\s+[^>]*property="og:description"\s+content="([^"]*)"', content)
        post["og_description"] = og_match.group(1).strip() if og_match else ""
        
        # 字数统计 (去除 HTML 标签)
        text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)
        post["char_count"] = len(text.strip())
        
        # 检查音频文件
        audio_patterns = [
            os.path.join(AUDIO_DIR, f"{slug}.*"),
            os.path.join(AUDIO_DIR, f"{slug.replace('posts/', '')}.*"),
        ]
        has_audio = False
        for pattern in audio_patterns:
            if glob.glob(pattern):
                has_audio = True
                break
        # 也检查 HTML 中的 audio src
        if not has_audio:
            audio_src = re.search(r'<audio[^>]*>.*?<source[^>]*src="([^"]+)"', content, re.DOTALL)
            if audio_src and "placeholder" not in audio_src.group(1).lower():
                has_audio = True
        post["has_audio"] = has_audio
        
        # 模板合规性
        post["template_issues"] = []
        for pattern, desc in TEMPLATE_REQUIRED:
            if not re.search(pattern, content):
                post["template_issues"].append(desc)
        
        # 内部链接提取
        internal_links = re.findall(r'href="(posts/[^"#]+)"', content)
        post["internal_links"] = list(set(internal_links))
        
        posts.append(post)
    
    return posts


# ── 2. blog.html 索引扫描 ────────────────────────────────────────────

def scan_blog_index():
    """解析 blog.html 的 JS articles 数组"""
    indexed = set()
    if not os.path.isfile(BLOG_HTML):
        return indexed
    
    content = read_file(BLOG_HTML)
    if not content:
        return indexed
    
    # 提取 const articles = [...] 块
    match = re.search(r'const\s+articles\s*=\s*\[(.*?)\];', content, re.DOTALL)
    if not match:
        return indexed
    
    block = match.group(1)
    
    # 提取每个条目的 url 字段
    urls = re.findall(r'url\s*:\s*"([^"]+)"', block)
    for url in urls:
        # url 格式: "posts/2026-08-03-evening-qwen38-max" 或 "posts/xxx.html"
        slug = url.replace("posts/", "").replace(".html", "")
        indexed.add(slug)
    
    return indexed


# ── 3. feed.xml 扫描 ─────────────────────────────────────────────────

def scan_feed():
    """解析 feed.xml 中的所有文章链接"""
    feed_slugs = set()
    if not os.path.isfile(FEED_XML):
        return feed_slugs
    
    content = read_file(FEED_XML)
    if not content:
        return feed_slugs
    
    links = re.findall(r'<link>https://sandbot\.cgfan\.com/posts/([^<]+)</link>', content)
    for link in links:
        slug = link.replace(".html", "").rstrip("/")
        feed_slugs.add(slug)
    
    return feed_slugs


# ── 4. sitemap.xml 扫描 ──────────────────────────────────────────────

def scan_sitemap():
    """解析 sitemap.xml 中的所有 URL"""
    sitemap_slugs = set()
    if not os.path.isfile(SITEMAP_XML):
        return sitemap_slugs
    
    content = read_file(SITEMAP_XML)
    if not content:
        return sitemap_slugs
    
    urls = re.findall(r'<loc>https://sandbot\.cgfan\.com/posts/([^<]+)</loc>', content)
    for url in urls:
        slug = url.replace(".html", "").rstrip("/")
        sitemap_slugs.add(slug)
    
    return sitemap_slugs


# ── 5. 内部链接检查 ──────────────────────────────────────────────────

def check_internal_links(posts):
    """检查文章间的内部链接是否有效"""
    valid_slugs = set(p["slug"] for p in posts)
    broken = []
    
    for post in posts:
        for link in post["internal_links"]:
            link_slug = link.replace("posts/", "").replace(".html", "")
            if link_slug not in valid_slugs:
                broken.append({
                    "source": post["slug"],
                    "target": link,
                    "target_slug": link_slug,
                })
    
    return broken


# ── 6. 自动修复 ──────────────────────────────────────────────────────

def fix_blog_index(posts, indexed_slugs):
    """重建 blog.html 的 articles 数组"""
    # 调用已有的 blog-index-rebuilder.py
    rebuilder = os.path.join(BLOG_ROOT, "scripts", "blog-index-rebuilder.py")
    if os.path.isfile(rebuilder):
        result = subprocess.run(
            [sys.executable, rebuilder, "--fix"],
            capture_output=True, text=True, cwd=BLOG_ROOT
        )
        return result.returncode == 0, result.stdout + result.stderr
    return False, "blog-index-rebuilder.py not found"


def fix_rss(posts, feed_slugs):
    """重建 feed.xml"""
    rss_gen = os.path.join(BLOG_ROOT, "scripts", "generate-rss-from-posts.py")
    if os.path.isfile(rss_gen):
        result = subprocess.run(
            [sys.executable, rss_gen],
            capture_output=True, text=True, cwd=BLOG_ROOT
        )
        return result.returncode == 0, result.stdout + result.stderr
    
    # fallback: 调用 update-rss.py
    rss_gen2 = os.path.join(BLOG_ROOT, "scripts", "update-rss.py")
    if os.path.isfile(rss_gen2):
        result = subprocess.run(
            [sys.executable, rss_gen2],
            capture_output=True, text=True, cwd=BLOG_ROOT
        )
        return result.returncode == 0, result.stdout + result.stderr
    
    return False, "No RSS generator script found"


def fix_sitemap(posts, sitemap_slugs):
    """重建 sitemap.xml"""
    sitemap_gen = os.path.join(BLOG_ROOT, "scripts", "generate-sitemap.py")
    if os.path.isfile(sitemap_gen):
        result = subprocess.run(
            [sys.executable, sitemap_gen],
            capture_output=True, text=True, cwd=BLOG_ROOT
        )
        return result.returncode == 0, result.stdout + result.stderr
    return False, "generate-sitemap.py not found"


# ── 7. 健康度评分 ────────────────────────────────────────────────────

def calculate_health(disk_posts, indexed_slugs, feed_slugs, sitemap_slugs, broken_links):
    """计算 0-100 健康度评分"""
    if not disk_posts:
        return 0, {}
    
    total = len(disk_posts)
    
    # 1. 索引覆盖率 (30%)
    orphaned = [p for p in disk_posts if p["slug"] not in indexed_slugs]
    index_coverage = max(0, 100 - (len(orphaned) / total * 100))
    
    # 2. RSS 覆盖率 (15%)
    rss_orphaned = [p for p in disk_posts if p["slug"] not in feed_slugs]
    rss_coverage = max(0, 100 - (len(rss_orphaned) / total * 100))
    
    # 3. Sitemap 覆盖率 (10%)
    sitemap_orphaned = [p for p in disk_posts if p["slug"] not in sitemap_slugs]
    sitemap_coverage = max(0, 100 - (len(sitemap_orphaned) / total * 100))
    
    # 4. 元数据质量 (15%)
    meta_issues = 0
    for p in disk_posts:
        if not p["title"]:
            meta_issues += 1
        if not p["description"] and not p["og_description"]:
            meta_issues += 1
        if p["char_count"] < 1000:
            meta_issues += 1
    meta_quality = max(0, 100 - (meta_issues / (total * 3) * 100))
    
    # 5. 音频覆盖率 (10%)
    audio_count = sum(1 for p in disk_posts if p["has_audio"])
    audio_coverage = (audio_count / total * 100) if total > 0 else 0
    
    # 6. 内部链接有效性 (10%)
    total_links = sum(len(p["internal_links"]) for p in disk_posts)
    link_health = max(0, 100 - (len(broken_links) / max(total_links, 1) * 100))
    
    # 7. 模板合规性 (10%)
    template_issues = sum(1 for p in disk_posts if p["template_issues"])
    template_health = max(0, 100 - (template_issues / total * 100))
    
    # 加权总分
    score = (
        index_coverage * WEIGHT_INDEX_COVERAGE / 100 +
        rss_coverage * WEIGHT_RSS_COVERAGE / 100 +
        sitemap_coverage * WEIGHT_SITEMAP_COVERAGE / 100 +
        meta_quality * WEIGHT_META_QUALITY / 100 +
        audio_coverage * WEIGHT_AUDIO_COVERAGE / 100 +
        link_health * WEIGHT_INTERNAL_LINKS / 100 +
        template_health * WEIGHT_TEMPLATE_COMPLIANCE / 100
    )
    
    details = {
        "index_coverage": round(index_coverage, 1),
        "rss_coverage": round(rss_coverage, 1),
        "sitemap_coverage": round(sitemap_coverage, 1),
        "meta_quality": round(meta_quality, 1),
        "audio_coverage": round(audio_coverage, 1),
        "link_health": round(link_health, 1),
        "template_health": round(template_health, 1),
        "orphaned_from_index": len(orphaned),
        "orphaned_from_rss": len(rss_orphaned),
        "orphaned_from_sitemap": len(sitemap_orphaned),
        "broken_internal_links": len(broken_links),
        "posts_without_audio": total - audio_count,
        "posts_with_meta_issues": meta_issues,
        "posts_with_template_issues": template_issues,
    }
    
    return round(score, 1), details


# ── 主函数 ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="博客健康度全面检查")
    parser.add_argument("--fix", action="store_true", help="自动修复可修复项")
    parser.add_argument("--fix-blog", action="store_true", help="只修复 blog.html 索引")
    parser.add_argument("--fix-rss", action="store_true", help="只修复 feed.xml")
    parser.add_argument("--fix-sitemap", action="store_true", help="只修复 sitemap.xml")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--quick", action="store_true", help="快速检查（跳过链接检查）")
    parser.add_argument("--threshold", type=int, default=60, help="健康度阈值 (默认 60)")
    args = parser.parse_args()
    
    fix_any = args.fix or args.fix_blog or args.fix_rss or args.fix_sitemap
    
    if not args.json:
        print(f"\n🏥 Sandbot 博客健康度检查")
        print(f"{'='*50}")
        print(f"📁 博客目录: {BLOG_ROOT}")
        print(f"🕐 检查时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        print()
    
    # 1. 扫描磁盘
    if not args.json:
        print("📂 [1/5] 扫描磁盘文章...")
    disk_posts = scan_disk_posts()
    
    if not disk_posts:
        if args.json:
            print(json.dumps({"error": "No posts found", "health": 0}))
        else:
            log("posts/ 目录为空或不存在", "error")
        sys.exit(2)
    
    if not args.json:
        log(f"发现 {len(disk_posts)} 篇文章")
    
    # 2. 扫描索引
    if not args.json:
        print("\n📋 [2/5] 扫描索引文件...")
    indexed_slugs = scan_blog_index()
    feed_slugs = scan_feed()
    sitemap_slugs = scan_sitemap()
    
    if not args.json:
        log(f"blog.html 索引: {len(indexed_slugs)} 篇")
        log(f"feed.xml: {len(feed_slugs)} 篇")
        log(f"sitemap.xml: {len(sitemap_slugs)} 篇")
    
    # 3. 内部链接检查
    if not args.json:
        print("\n🔗 [3/5] 检查内部链接...")
    broken_links = [] if args.quick else check_internal_links(disk_posts)
    if not args.json:
        if args.quick:
            log("跳过 (--quick 模式)", "info")
        elif broken_links:
            log(f"发现 {len(broken_links)} 个断链", "warn")
            for bl in broken_links[:5]:
                log(f"  {bl['source']} → {bl['target']}", "warn")
            if len(broken_links) > 5:
                log(f"  ... 还有 {len(broken_links) - 5} 个", "warn")
        else:
            log("所有内部链接有效", "ok")
    
    # 4. 详细问题报告
    if not args.json:
        print("\n🔍 [4/5] 问题详情...")
    
    # 4a. 孤立文章
    orphaned = [p for p in disk_posts if p["slug"] not in indexed_slugs]
    if orphaned and not args.json:
        log(f"blog.html 中缺失 {len(orphaned)} 篇:", "warn")
        for p in orphaned[:5]:
            log(f"  {p['slug']}", "warn")
        if len(orphaned) > 5:
            log(f"  ... 还有 {len(orphaned) - 5} 篇", "warn")
    
    # 4b. 元数据问题
    meta_issues = []
    for p in disk_posts:
        issues = []
        if not p["title"]:
            issues.append("无 title")
        if not p["description"] and not p["og_description"]:
            issues.append("无 description")
        if p["char_count"] < 1000:
            issues.append(f"字数过少 ({p['char_count']})")
        if p["template_issues"]:
            issues.extend([f"模板缺: {t}" for t in p["template_issues"]])
        if issues:
            meta_issues.append({"slug": p["slug"], "issues": issues})
    
    if meta_issues and not args.json:
        log(f"{len(meta_issues)} 篇文章有元数据/模板问题:", "warn")
        for mi in meta_issues[:3]:
            log(f"  {mi['slug']}: {', '.join(mi['issues'])}", "warn")
        if len(meta_issues) > 3:
            log(f"  ... 还有 {len(meta_issues) - 3} 篇", "warn")
    
    # 4c. 音频覆盖率
    audio_count = sum(1 for p in disk_posts if p["has_audio"])
    if not args.json:
        audio_pct = audio_count / len(disk_posts) * 100 if disk_posts else 0
        log(f"音频覆盖: {audio_count}/{len(disk_posts)} ({audio_pct:.1f}%)", 
            "ok" if audio_pct > 50 else "warn")
    
    # 5. 健康度评分
    if not args.json:
        print(f"\n📊 [5/5] 健康度评分...")
    
    score, details = calculate_health(disk_posts, indexed_slugs, feed_slugs, sitemap_slugs, broken_links)
    
    if args.json:
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health_score": score,
            "total_posts": len(disk_posts),
            "details": details,
            "broken_links_sample": broken_links[:10],
            "meta_issues_count": len(meta_issues),
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # 健康度仪表盘
        bar_len = 30
        filled = int(score / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
        
        print(f"\n  {'='*42}")
        print(f"  {emoji} 健康度: {score}/100  [{bar}]")
        print(f"  {'='*42}")
        print(f"  📋 索引覆盖率:   {details['index_coverage']:5.1f}%  (权重 30%)")
        print(f"  📡 RSS 覆盖率:   {details['rss_coverage']:5.1f}%  (权重 15%)")
        print(f"  🗺️  Sitemap 覆盖: {details['sitemap_coverage']:5.1f}%  (权重 10%)")
        print(f"  📝 元数据质量:   {details['meta_quality']:5.1f}%  (权重 15%)")
        print(f"  🔊 音频覆盖率:   {details['audio_coverage']:5.1f}%  (权重 10%)")
        print(f"  🔗 内部链接:     {details['link_health']:5.1f}%  (权重 10%)")
        print(f"  🏗️  模板合规:     {details['template_health']:5.1f}%  (权重 10%)")
        print()
    
    # 6. 自动修复
    if fix_any:
        if not args.json:
            print(f"\n🔧 自动修复模式...")
        
        if args.fix or args.fix_blog:
            if orphaned:
                if not args.json:
                    log(f"修复 blog.html 索引 (添加 {len(orphaned)} 篇)...")
                ok, msg = fix_blog_index(disk_posts, indexed_slugs)
                if ok:
                    if not args.json:
                        log("blog.html 索引已重建", "fix")
                else:
                    if not args.json:
                        log(f"修复失败: {msg}", "error")
            else:
                if not args.json:
                    log("blog.html 索引已是最新", "ok")
        
        if args.fix or args.fix_rss:
            rss_orphaned = [p for p in disk_posts if p["slug"] not in feed_slugs]
            if rss_orphaned:
                if not args.json:
                    log(f"修复 feed.xml (添加 {len(rss_orphaned)} 篇)...")
                ok, msg = fix_rss(disk_posts, feed_slugs)
                if ok:
                    if not args.json:
                        log("feed.xml 已重建", "fix")
                else:
                    if not args.json:
                        log(f"修复失败: {msg}", "error")
            else:
                if not args.json:
                    log("feed.xml 已是最新", "ok")
        
        if args.fix or args.fix_sitemap:
            sitemap_orphaned = [p for p in disk_posts if p["slug"] not in sitemap_slugs]
            if sitemap_orphaned:
                if not args.json:
                    log(f"修复 sitemap.xml (添加 {len(sitemap_orphaned)} 篇)...")
                ok, msg = fix_sitemap(disk_posts, sitemap_slugs)
                if ok:
                    if not args.json:
                        log("sitemap.xml 已重建", "fix")
                else:
                    if not args.json:
                        log(f"修复失败: {msg}", "error")
            else:
                if not args.json:
                    log("sitemap.xml 已是最新", "ok")
    
    # 7. 总结
    if not args.json:
        print(f"\n{'='*50}")
        if score >= 80:
            print(f"🟢 博客状态良好！")
        elif score >= 60:
            print(f"🟡 博客基本健康，但有些问题需要修复")
            print(f"   运行 --fix 自动修复大部分问题")
        else:
            print(f"🔴 博客健康度较低，建议立即修复")
            print(f"   python3 scripts/blog-health-check.py --fix")
        
        if broken_links and not args.quick:
            print(f"\n💔 断链 ({len(broken_links)} 个):")
            for bl in broken_links[:10]:
                print(f"   {bl['source']} → {bl['target']}")
        
        print()
    
    # 退出码
    sys.exit(0 if score >= args.threshold else 1)


if __name__ == "__main__":
    main()
