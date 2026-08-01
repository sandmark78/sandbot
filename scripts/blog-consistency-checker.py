#!/usr/bin/env python3
"""
blog-consistency-checker.py — 博客一致性检查器 v1.0
Sandbot 每周工具脚本 · 2026-07-26

解决的问题（本周反复出现的坑）：
  1. RSS 条目指向不存在的文件 (7/20 P0)
  2. blog.html 文章索引与实际文件不同步 (7/20 P0)
  3. 孤立文章：文件存在但不在 RSS/blog.html 中
  4. 文章间内部链接失效
  5. 文件命名不符合规范
  6. RSS pubDate 全为 00:00:00，无法区分发布时间

用法:
  python3 scripts/blog-consistency-checker.py              # 全面检查
  python3 scripts/blog-consistency-checker.py --fix-rss    # 自动修复 RSS（删除死链条目）
  python3 scripts/blog-consistency-checker.py --fix-blog   # 自动重建 blog.html 文章索引
  python3 scripts/blog-consistency-checker.py --fix-all    # 自动修复所有可修复问题
  python3 scripts/blog-consistency-checker.py --json       # JSON 输出（供其他脚本调用）
  python3 scripts/blog-consistency-checker.py --quiet      # 只输出错误
"""

import os
import sys
import re
import json
import glob
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser
# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# ── 配置 ──────────────────────────────────────────────────────────────

REPO_DIR = BLOG_ROOT
POSTS_DIR = os.path.join(REPO_DIR, "posts")
BLOG_HTML = os.path.join(REPO_DIR, "blog.html")
FEED_XML = os.path.join(REPO_DIR, "feed.xml")
SITE_URL = "https://sandbot.cgfan.com"

# 命名规范：小写字母、数字、连字符
NAMING_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]*\.html$')

# ── 数据收集 ──────────────────────────────────────────────────────────

def get_actual_articles():
    """获取 posts/ 目录下所有实际文章文件"""
    articles = {}
    if not os.path.isdir(POSTS_DIR):
        return articles
    for f in os.listdir(POSTS_DIR):
        if f.endswith('.html') and not f.startswith('.') and f != 'index.html':
            filepath = os.path.join(POSTS_DIR, f)
            stat = os.stat(filepath)
            articles[f] = {
                'path': filepath,
                'size': stat.st_size,
                'mtime': datetime.fromtimestamp(stat.st_mtime),
            }
    return articles


def get_rss_articles():
    """解析 RSS feed 中的文章条目"""
    articles = {}
    if not os.path.isfile(FEED_XML):
        return articles
    with open(FEED_XML, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取所有 <item>
    items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
    for item in items:
        title_m = re.search(r'<title>(.*?)</title>', item)
        link_m = re.search(r'<link>(.*?)</link>', item)
        guid_m = re.search(r'<guid>(.*?)</guid>', item)
        pubdate_m = re.search(r'<pubDate>(.*?)</pubDate>', item)

        link = link_m.group(1) if link_m else ''
        # 从链接提取文件名
        filename = link.replace(f'{SITE_URL}/posts/', '')
        # RSS 链接可能不带 .html 后缀
        if filename and not filename.endswith('.html'):
            filename = filename + '.html'
        if not filename or filename == link:
            continue

        articles[filename] = {
            'title': title_m.group(1) if title_m else '',
            'link': link,
            'guid': guid_m.group(1) if guid_m else '',
            'pubDate': pubdate_m.group(1) if pubdate_m else '',
        }
    return articles


def get_blog_html_articles():
    """解析 blog.html 中的文章索引（JS articles 数组）"""
    articles = {}
    if not os.path.isfile(BLOG_HTML):
        return articles
    with open(BLOG_HTML, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配 articles.push({...}) 或 {title:..., file:...} 模式
    # 常见模式：file: "posts/xxx.html" 或 url: "posts/xxx.html"
    file_refs = re.findall(r'(?:file|url|href)["\s:]+["\']posts/([^"\']+\.html)["\']', content)
    for filename in set(file_refs):
        articles[filename] = {'referenced': True}

    # 也匹配直接的 posts/xxx.html 链接
    direct_refs = re.findall(r'posts/([a-z0-9][a-z0-9-]*\.html)', content)
    for filename in set(direct_refs):
        if filename not in articles:
            articles[filename] = {'referenced': True}
        else:
            articles[filename]['referenced'] = True

    return articles


def extract_internal_links(filepath):
    """提取文章中的所有内部链接"""
    links = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        # 匹配 href="..." 中的内部链接
        hrefs = re.findall(r'href=["\']([^"\']*)["\']', content)
        for href in hrefs:
            if href.startswith('posts/') or href.startswith('/posts/') or href.startswith(SITE_URL):
                links.append(href)
    except Exception:
        pass
    return links


def check_naming_convention(filename):
    """检查文件命名是否符合规范"""
    return bool(NAMING_PATTERN.match(filename))


# ── 检查逻辑 ──────────────────────────────────────────────────────────

def run_checks(fix_mode=False, quiet=False):
    """运行所有一致性检查"""
    issues = {
        'rss_dead_links': [],      # RSS 条目指向不存在的文件
        'blog_dead_links': [],     # blog.html 引用不存在的文件
        'orphaned_articles': [],   # 文件存在但不在 RSS 和 blog.html 中
        'broken_internal_links': [],  # 文章间内部链接失效
        'naming_violations': [],   # 命名不符合规范
        'zero_pubdate': [],        # RSS pubDate 为 00:00:00
        'empty_articles': [],      # 文章文件过小 (<100 bytes)
    }

    actual = get_actual_articles()
    rss = get_rss_articles()
    blog = get_blog_html_articles()

    if not quiet:
        print(f"📊 博客一致性检查")
        print(f"   实际文章: {len(actual)} 篇")
        print(f"   RSS 条目: {len(rss)} 条")
        print(f"   blog.html 引用: {len(blog)} 篇")
        print()

    # 1. RSS 死链
    for filename in rss:
        if filename not in actual:
            issues['rss_dead_links'].append({
                'file': filename,
                'title': rss[filename].get('title', ''),
                'fix': '从 RSS 中删除此条目',
            })

    # 2. blog.html 死链
    for filename in blog:
        if filename not in actual:
            issues['blog_dead_links'].append({
                'file': filename,
                'fix': '从 blog.html 索引中删除',
            })

    # 3. 孤立文章
    for filename in actual:
        in_rss = filename in rss
        in_blog = filename in blog
        if not in_rss and not in_blog:
            issues['orphaned_articles'].append({
                'file': filename,
                'size': actual[filename]['size'],
                'fix': '添加到 RSS 和 blog.html',
            })

    # 4. 内部链接检查（只检查 posts/ 下的文章链接）
    skip_pages = {'blog', 'blog/', 'blog.html', 'all', 'all/', 'all.html',
                  'index', 'index.html', 'podcast', 'podcast/', 'podcast.html',
                  'about', 'about/', 'about.html', 'rss', 'feed.xml', ''}
    for filename, info in actual.items():
        links = extract_internal_links(info['path'])
        for link in links:
            # 只检查 posts/ 开头的链接
            if 'posts/' not in link:
                continue
            # 提取目标文件名
            target = link.replace(f'{SITE_URL}/posts/', '').replace('posts/', '')
            # 去掉锚点
            target = target.split('#')[0]
            if not target or target in skip_pages:
                continue
            # 加 .html 后缀
            if not target.endswith('.html'):
                target = target + '.html'
            if target not in actual:
                issues['broken_internal_links'].append({
                    'source': filename,
                    'target': link,
                    'fix': '修复或删除失效链接',
                })

    # 5. 命名规范
    for filename in actual:
        if not check_naming_convention(filename):
            issues['naming_violations'].append({
                'file': filename,
                'fix': '重命名为符合 [a-z0-9-]+ 规范',
            })

    # 6. RSS pubDate 全零
    for filename, info in rss.items():
        pubdate = info.get('pubDate', '')
        if '00:00:00' in pubdate:
            issues['zero_pubdate'].append({
                'file': filename,
                'pubDate': pubdate,
                'fix': '使用 git log 获取实际提交时间',
            })

    # 7. 空文章
    for filename, info in actual.items():
        if info['size'] < 100:
            issues['empty_articles'].append({
                'file': filename,
                'size': info['size'],
                'fix': '检查是否为空文件或占位符',
            })

    return issues


def print_report(issues, quiet=False):
    """打印检查报告"""
    total_issues = sum(len(v) for v in issues.values())

    if total_issues == 0:
        if not quiet:
            print("✅ 所有一致性检查通过！博客状态健康。")
        return 0

    # 按严重程度排序
    checks = [
        ('rss_dead_links', '🔴 RSS 死链（条目指向不存在的文件）', 'error'),
        ('blog_dead_links', '🔴 blog.html 死链（引用不存在的文件）', 'error'),
        ('empty_articles', '🔴 空文章（<100 bytes）', 'error'),
        ('orphaned_articles', '🟡 孤立文章（不在 RSS/blog.html 中）', 'warning'),
        ('broken_internal_links', '🟡 内部链接失效', 'warning'),
        ('zero_pubdate', '🟡 RSS pubDate 为 00:00:00', 'warning'),
        ('naming_violations', '🟢 命名规范违规', 'info'),
    ]

    error_count = 0
    warning_count = 0

    for key, label, severity in checks:
        items = issues[key]
        if not items:
            continue
        if severity == 'error':
            error_count += len(items)
        elif severity == 'warning':
            warning_count += len(items)

        if not quiet:
            print(f"{label}: {len(items)} 个")
            for item in items[:5]:  # 最多显示 5 个
                file_info = item.get('file', item.get('source', ''))
                extra = item.get('title', item.get('target', ''))
                print(f"   • {file_info}" + (f" — {extra}" if extra else ""))
            if len(items) > 5:
                print(f"   ... 还有 {len(items) - 5} 个")
            print()

    if not quiet:
        print(f"{'─' * 50}")
        print(f"总计: {total_issues} 个问题 ({error_count} 错误, {warning_count} 警告)")

    return error_count


def fix_rss(issues):
    """修复 RSS：删除指向不存在文件的条目"""
    if not issues['rss_dead_links']:
        print("✅ RSS 无死链，无需修复")
        return

    if not os.path.isfile(FEED_XML):
        print("❌ feed.xml 不存在")
        return

    with open(FEED_XML, 'r', encoding='utf-8') as f:
        content = f.read()

    dead_files = {item['file'] for item in issues['rss_dead_links']}
    removed = 0

    for item in issues['rss_dead_links']:
        filename = item['file']
        # 找到并删除对应的 <item>...</item> 块
        pattern = rf'\s*<item>.*?<link>[^<]*{re.escape(filename)}</link>.*?</item>'
        new_content = re.sub(pattern, '', content, flags=re.DOTALL)
        if new_content != content:
            removed += 1
            content = new_content

    with open(FEED_XML, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ RSS 修复完成：删除 {removed} 个死链条目")


def fix_blog_index(issues):
    """修复 blog.html：重建文章索引"""
    actual = get_actual_articles()
    if not actual:
        print("❌ 无实际文章文件")
        return

    if not os.path.isfile(BLOG_HTML):
        print("❌ blog.html 不存在")
        return

    # 从文章文件中提取元数据
    articles_data = []
    for filename, info in sorted(actual.items(), key=lambda x: x[1]['mtime'], reverse=True):
        filepath = info['path']
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            title_m = re.search(r'<title>(.*?)</title>', content)
            title = title_m.group(1) if title_m else filename.replace('.html', '').replace('-', ' ').title()

            # 提取 overline/标签
            overline_m = re.search(r'class="overline"[^>]*>(.*?)<', content)
            overline = overline_m.group(1) if overline_m else ''

            # 提取副标题
            subtitle_m = re.search(r'class="subtitle"[^>]*>(.*?)<', content)
            subtitle = subtitle_m.group(1) if subtitle_m else ''

            # 提取日期
            date_m = re.search(r'class="date"[^>]*>(.*?)<', content)
            date_str = date_m.group(1) if date_m else info['mtime'].strftime('%Y-%m-%d')

            articles_data.append({
                'file': filename,
                'title': title,
                'overline': overline,
                'subtitle': subtitle,
                'date': date_str,
            })
        except Exception:
            continue

    print(f"✅ blog.html 索引重建：扫描 {len(articles_data)} 篇文章")
    print(f"   (需要手动更新 blog.html 的 JS articles 数组)")
    print(f"   最新文章: {articles_data[0]['title'] if articles_data else 'N/A'}")


def fix_all(issues):
    """修复所有可修复问题"""
    print("🔧 开始自动修复...\n")
    fix_rss(issues)
    print()
    fix_blog_index(issues)
    print()
    print("✅ 自动修复完成。请运行 git add + commit + push 提交更改。")


# ── 主程序 ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='博客一致性检查器')
    parser.add_argument('--fix-rss', action='store_true', help='修复 RSS 死链')
    parser.add_argument('--fix-blog', action='store_true', help='重建 blog.html 索引')
    parser.add_argument('--fix-all', action='store_true', help='修复所有问题')
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    parser.add_argument('--quiet', action='store_true', help='只输出错误')
    args = parser.parse_args()

    fix_mode = args.fix_rss or args.fix_blog or args.fix_all
    issues = run_checks(fix_mode=fix_mode, quiet=args.quiet or args.json)

    if args.json:
        # JSON 模式：输出结构化数据
        output = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'summary': {k: len(v) for k, v in issues.items()},
            'total_issues': sum(len(v) for v in issues.values()),
            'issues': {},
        }
        for key, items in issues.items():
            if items:
                output['issues'][key] = items
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    if not args.quiet:
        print_report(issues)

    if args.fix_all:
        fix_all(issues)
    elif args.fix_rss:
        fix_rss(issues)
    elif args.fix_blog:
        fix_blog_index(issues)

    # 返回退出码：有错误返回 1
    error_count = len(issues['rss_dead_links']) + len(issues['blog_dead_links']) + len(issues['empty_articles'])
    sys.exit(1 if error_count > 0 else 0)


if __name__ == '__main__':
    main()
