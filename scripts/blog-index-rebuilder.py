#!/usr/bin/env python3
"""
blog-index-rebuilder.py — 博客索引自动重建器 v1.0
Sandbot 每周工具脚本 · 2026-08-01

解决的问题（本周反复出现的坑）：
  1. posts/ 有 448 篇文章，blog.html JS 数组只有 50 条 → 398 篇文章"隐身"
  2. 每次发布文章后手动更新 blog.html 容易遗漏
  3. feed.xml 和 blog.html 不同步 → 订阅者和访客看到的内容不一致
  4. 文章缺少 excerpt/description → 卡片空白
  5. 文章文件存在但从未被索引 → 白写了

核心功能：
  • 扫描 posts/ 所有 HTML 文件，提取元数据
  • 自动重建 blog.html 的 JS articles 数组
  • 同步更新 feed.xml
  • 检测并报告问题（缺失字段、孤立文件等）

用法:
  python3 scripts/blog-index-rebuilder.py                  # 预览模式（只报告，不修改）
  python3 scripts/blog-index-rebuilder.py --fix            # 修复 blog.html 索引
  python3 scripts/blog-index-rebuilder.py --fix-rss        # 修复 feed.xml
  python3 scripts/blog-index-rebuilder.py --fix-all        # 修复所有问题
  python3 scripts/blog-index-rebuilder.py --json           # JSON 输出报告
  python3 scripts/blog-index-rebuilder.py --verbose        # 详细输出
"""

import os
import sys
import re
import json
import glob
import argparse
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser

# ── 配置 ──────────────────────────────────────────────────────────────

# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
POSTS_DIR = os.path.join(BLOG_ROOT, "posts")
BLOG_HTML = os.path.join(BLOG_ROOT, "blog.html")
FEED_XML = os.path.join(BLOG_ROOT, "feed.xml")
AUDIO_DIR = os.path.join(POSTS_DIR, "audio")
SITE_URL = "https://sandbot.cgfan.com"

# 默认语音时长（如果无法检测）
DEFAULT_DURATION = "6 分钟"

# 分类映射（从文件名/标题推断 type）
CATEGORY_MAP = {
    "early": ("early", "早间"),
    "morning": ("morning", "早间"),
    "noon": ("noon", "午间"),
    "afternoon": ("afternoon", "下午"),
    "evening": ("evening", "晚间"),
    "night": ("night", "夜间"),
    "hot": ("hot", "热点"),
    "deep": ("deep", "深度"),
    "launch": ("launch", "发布"),
    "research": ("research", "研究"),
    "business": ("business", "商业"),
}


# ── HTML 元数据提取 ──────────────────────────────────────────────────

def extract_metadata(filepath):
    """从 HTML 文章文件提取元数据"""
    filename = os.path.basename(filepath)
    slug = filename.replace('.html', '')

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取标题
    title = ""
    title_match = re.search(r'<title>([^<]+)</title>', content)
    if title_match:
        title = title_match.group(1).strip()
        title = re.sub(r'\s*[—|]\s*Sandbot Blog.*$', '', title)
        title = re.sub(r'\s*🏖️.*$', '', title)

    # 提取日期（从文件名）
    date_str = ""
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})', filename)
    if date_match:
        date_str = date_match.group(1)

    # 提取描述/excerpt
    excerpt = ""
    desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', content)
    if desc_match:
        excerpt = desc_match.group(1).strip()
    if not excerpt:
        desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', content)
        if desc_match:
            excerpt = desc_match.group(1).strip()

    # 提取分类标签
    label = ""
    label_match = re.search(r'class="article-label">([^<]+)<', content)
    if label_match:
        label = label_match.group(1).strip()

    # 提取 og:title
    og_title = ""
    og_match = re.search(r'property="og:title"\s+content="([^"]*)"', content)
    if og_match:
        og_title = og_match.group(1).strip()

    # 推断 type/typeLabel/tag
    slug_lower = slug.lower()
    type_key = "hot"  # 默认
    type_label = "热点"

    for key, (t, l) in CATEGORY_MAP.items():
        if key in slug_lower:
            type_key = t
            type_label = l
            break

    # 如果标题里有分类前缀 [xxx]，用它
    prefix_match = re.match(r'\[([^\]]+)\]\s*', title)
    if prefix_match:
        prefix = prefix_match.group(1)
        for key, (t, l) in CATEGORY_MAP.items():
            if key in prefix.lower() or l in prefix:
                type_key = t
                type_label = l
                break

    # 检查是否有音频文件
    has_audio = False
    audio_file = ""
    audio_path = os.path.join(AUDIO_DIR, slug + ".mp3")
    if os.path.exists(audio_path):
        has_audio = True
        audio_file = f"posts/audio/{slug}.mp3"

    # 计算字数
    # 去除 HTML 标签，计算纯文本长度
    text_content = re.sub(r'<[^>]+>', '', content)
    text_content = re.sub(r'\s+', '', text_content)
    char_count = len(text_content)

    return {
        "title": title or slug,
        "type": type_key,
        "typeLabel": type_label,
        "tag": type_label,
        "date": date_str,
        "url": f"posts/{slug}",
        "excerpt": excerpt,
        "duration": DEFAULT_DURATION,
        "access": "free",
        "has_audio": has_audio,
        "audio_file": audio_file,
        "char_count": char_count,
        "slug": slug,
    }


def scan_all_posts():
    """扫描 posts/ 目录所有 HTML 文件"""
    articles = []
    pattern = os.path.join(POSTS_DIR, "*.html")

    for filepath in glob.glob(pattern):
        try:
            meta = extract_metadata(filepath)
            if meta["date"]:  # 只包含有日期的文件（排除模板等）
                articles.append(meta)
        except Exception as e:
            print(f"  ⚠️  解析失败: {os.path.basename(filepath)} - {e}", file=sys.stderr)

    # 按日期降序排序（最新在前）
    articles.sort(key=lambda a: a["date"], reverse=True)
    return articles


# ── blog.html 重建 ────────────────────────────────────────────────────

def rebuild_blog_html(articles, dry_run=True):
    """重建 blog.html 的 articles JS 数组"""

    if not os.path.exists(BLOG_HTML):
        print(f"❌ blog.html 不存在: {BLOG_HTML}")
        return False

    with open(BLOG_HTML, 'r', encoding='utf-8') as f:
        content = f.read()

    # 生成新的 JS 数组
    js_entries = []
    for a in articles:
        # 转义 JS 字符串中的特殊字符
        title = a["title"].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        excerpt = a["excerpt"].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

        entry = f"""  {{
    title: "{title}",
    type: "{a['type']}",
    typeLabel: "{a['typeLabel']}",
    tag: "{a['tag']}",
    date: "{a['date']}",
    url: "{a['url']}",
    excerpt: "{excerpt}",
    duration: "{a['duration']}",
    access: "{a['access']}"
  }}"""
        js_entries.append(entry)

    new_array = "const articles = [\n" + ",\n".join(js_entries) + "\n];"

    # 替换旧数组
    pattern = r'const articles = \[.*?\];'
    new_content, count = re.subn(pattern, new_array, content, count=1, flags=re.DOTALL)

    if count == 0:
        print("❌ 未找到 articles 数组，无法替换")
        return False

    if dry_run:
        print(f"📋 [预览模式] 将更新 blog.html articles 数组:")
        print(f"   当前: {len(re.findall(pattern, content, flags=re.DOTALL))} 个数组定义")
        print(f"   新条目数: {len(articles)}")
        return True

    # 写入
    with open(BLOG_HTML, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ blog.html 已更新: {len(articles)} 篇文章已索引")
    return True


# ── feed.xml 重建 ─────────────────────────────────────────────────────

def rebuild_feed_xml(articles, dry_run=True):
    """重建 feed.xml RSS 文件"""

    now = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')

    items = []
    for a in articles[:50]:  # RSS 只保留最新 50 篇
        pub_date = ""
        try:
            pub_date = datetime.strptime(a['date'], '%Y-%m-%d').strftime('%a, %d %b %Y 00:00:00 +0000')
        except:
            pub_date = now

        title = a['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        excerpt = a['excerpt'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        url = f"{SITE_URL}/{a['url']}.html"

        item = f"""    <item>
      <title>{title}</title>
      <link>{url}</link>
      <description>{excerpt}</description>
      <pubDate>{pub_date}</pubDate>
      <guid>{url}</guid>
    </item>"""
        items.append(item)

    feed_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Sandbot Blog 🏖️</title>
    <link>{SITE_URL}</link>
    <description>一个 AI Agent 的真实生存记录与思考</description>
    <language>zh-CN</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
  </channel>
</rss>
"""

    if dry_run:
        print(f"📋 [预览模式] 将更新 feed.xml:")
        print(f"   新条目数: {len(items)}")
        return True

    with open(FEED_XML, 'w', encoding='utf-8') as f:
        f.write(feed_content)

    print(f"✅ feed.xml 已更新: {len(items)} 条 RSS 条目")
    return True


# ── 诊断报告 ──────────────────────────────────────────────────────────

def generate_report(articles):
    """生成诊断报告"""
    issues = []
    warnings = []
    stats = {}

    # 统计
    stats['total_posts'] = len(articles)
    stats['with_title'] = sum(1 for a in articles if a['title'] and a['title'] != a['slug'])
    stats['with_excerpt'] = sum(1 for a in articles if a['excerpt'])
    stats['with_date'] = sum(1 for a in articles if a['date'])
    stats['with_audio'] = sum(1 for a in articles if a['has_audio'])
    stats['avg_chars'] = sum(a['char_count'] for a in articles) // max(len(articles), 1)

    # 检查 blog.html 当前状态
    blog_listed_count = 0
    if os.path.exists(BLOG_HTML):
        with open(BLOG_HTML, 'r') as f:
            blog_content = f.read()
        blog_listed_count = len(re.findall(r'url:\s*"posts/[^"]+"', blog_content))

    stats['blog_listed'] = blog_listed_count
    stats['blog_orphaned'] = len(articles) - blog_listed_count

    # 检查 feed.xml
    feed_count = 0
    if os.path.exists(FEED_XML):
        with open(FEED_XML, 'r') as f:
            feed_content = f.read()
        feed_count = feed_content.count('<item>')

    stats['feed_items'] = feed_count

    # 问题检测
    if stats['blog_orphaned'] > 0:
        issues.append(f"🔴 {stats['blog_orphaned']} 篇文章在 posts/ 中但未在 blog.html 索引")

    if stats['feed_items'] < min(stats['total_posts'], 50):
        issues.append(f"🔴 feed.xml 只有 {stats['feed_items']} 条，但有 {stats['total_posts']} 篇文章")

    # 无标题文章
    no_title = [a for a in articles if not a['title'] or a['title'] == a['slug']]
    if no_title:
        warnings.append(f"🟡 {len(no_title)} 篇文章缺少标题")
        for a in no_title[:5]:
            warnings.append(f"   - {a['slug']}")

    # 无 excerpt 文章
    no_excerpt = [a for a in articles if not a['excerpt']]
    if no_excerpt:
        warnings.append(f"🟡 {len(no_excerpt)} 篇文章缺少 excerpt/description")

    # 无音频
    no_audio = stats['total_posts'] - stats['with_audio']
    if no_audio > 0:
        warnings.append(f"🟡 {no_audio} 篇文章没有音频文件")

    # 短文章
    short_articles = [a for a in articles if a['char_count'] < 3000]
    if short_articles:
        warnings.append(f"🟡 {len(short_articles)} 篇文章正文不足 3000 字")

    return {
        "stats": stats,
        "issues": issues,
        "warnings": warnings,
        "articles": articles,
    }


def print_report(report):
    """打印诊断报告"""
    stats = report['stats']
    issues = report['issues']
    warnings = report['warnings']

    print("=" * 60)
    print("📊 博客索引健康检查报告")
    print("=" * 60)
    print()
    print(f"📁 posts/ 文章总数: {stats['total_posts']}")
    print(f"📝 有标题: {stats['with_title']}")
    print(f"📋 有 excerpt: {stats['with_excerpt']}")
    print(f"🔊 有音频: {stats['with_audio']}")
    print(f"📏 平均字数: {stats['avg_chars']:,}")
    print()
    print(f"🌐 blog.html 已索引: {stats['blog_listed']}")
    print(f"👻 blog.html 未索引: {stats['blog_orphaned']}")
    print(f"📡 feed.xml 条目: {stats['feed_items']}")
    print()

    if issues:
        print("─── ❌ 问题 ───")
        for issue in issues:
            print(f"  {issue}")
        print()

    if warnings:
        print("─── ⚠️  警告 ───")
        for warning in warnings:
            print(f"  {warning}")
        print()

    if not issues and not warnings:
        print("✅ 一切正常！所有文章已索引，RSS 已同步。")
        print()

    print("─── 💡 建议 ───")
    if stats['blog_orphaned'] > 0:
        print("  运行: python3 scripts/blog-index-rebuilder.py --fix")
    if stats['feed_items'] < min(stats['total_posts'], 50):
        print("  运行: python3 scripts/blog-index-rebuilder.py --fix-rss")
    if stats['blog_orphaned'] > 0 and stats['feed_items'] < min(stats['total_posts'], 50):
        print("  运行: python3 scripts/blog-index-rebuilder.py --fix-all")
    print()


# ── 主入口 ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="博客索引自动重建器")
    parser.add_argument("--fix", action="store_true", help="修复 blog.html 索引")
    parser.add_argument("--fix-rss", action="store_true", help="修复 feed.xml")
    parser.add_argument("--fix-all", action="store_true", help="修复所有问题")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    args = parser.parse_args()

    print(f"🔍 扫描 {POSTS_DIR} ...")
    articles = scan_all_posts()

    if not articles:
        print("❌ 未找到任何文章文件")
        sys.exit(1)

    report = generate_report(articles)

    if args.json:
        # JSON 输出（不含完整文章列表以节省空间）
        output = {
            "stats": report["stats"],
            "issues": report["issues"],
            "warnings": report["warnings"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0)

    print_report(report)

    # 执行修复
    fixed = False

    if args.fix or args.fix_all:
        print("─── 🔧 修复 blog.html ───")
        rebuild_blog_html(articles, dry_run=False)
        fixed = True
        print()

    if args.fix_rss or args.fix_all:
        print("─── 🔧 修复 feed.xml ───")
        rebuild_feed_xml(articles, dry_run=False)
        fixed = True
        print()

    if not fixed and report['issues']:
        print("💡 发现问题，使用 --fix / --fix-rss / --fix-all 修复")

    # 退出码
    if report['issues']:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
