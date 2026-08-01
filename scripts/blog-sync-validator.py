#!/usr/bin/env python3
"""
blog-sync-validator.py — 博客全链路同步验证 v1.0
Sandbot 每周工具脚本 · 2026-07-20

解决的问题（本周 P0 事故复盘）：
  1. blog.html 文章索引不同步 → 首页"最新文章"显示空 (07-20 P0)
  2. RSS feed.xml 过期 → 近 3 天文章未出现在 RSS (07-20 P0)
  3. 文章文件存在但 blog.html/RSS 未收录 → 孤立文章
  4. blog.html/RSS 有条目但文件不存在 → 幽灵条目
  5. 已发布文章 URL 不可访问 (404/500)
  6. 长文章缺少音频文件

本脚本整合验证 + 修复，一条命令搞定全链路健康检查。

用法:
  python3 scripts/blog-sync-validator.py                  # 全量检查
  python3 scripts/blog-sync-validator.py --fix            # 检查 + 自动修复
  python3 scripts/blog-sync-validator.py --fix-blog       # 只修复 blog.html 索引
  python3 scripts/blog-sync-validator.py --fix-rss        # 只修复 RSS
  python3 scripts/blog-sync-validator.py --http-check     # 含 HTTP 可达性检查
  python3 scripts/blog-sync-validator.py --json           # JSON 输出
  python3 scripts/blog-sync-validator.py --days 7         # 只检查最近 N 天的文章
"""

import os
import sys
import re
import json
import glob
import argparse
import subprocess
import urllib.request
import urllib.error
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

# HTTP 检查超时 (秒)
HTTP_TIMEOUT = 10

# ── 工具函数 ──────────────────────────────────────────────────────────

class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"

def ok(msg): print(f"  {Colors.GREEN}✓{Colors.END} {msg}")
def warn(msg): print(f"  {Colors.YELLOW}⚠{Colors.END} {msg}")
def fail(msg): print(f"  {Colors.RED}✗{Colors.END} {msg}")
def info(msg): print(f"  {Colors.CYAN}ℹ{Colors.END} {msg}")

def count_words_html(filepath):
    """统计 HTML 文件中的纯文本字数（中文+英文单词）"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        # 去掉 script/style
        content = re.sub(r'<(script|style)[^>]*>[\s\S]*?</\1>', '', content)
        # 去掉 HTML 标签
        text = re.sub(r'<[^>]+>', '', content)
        # 中文按字计，英文按词计
        chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
        english = len(re.findall(r'[a-zA-Z]+', text))
        return chinese + english
    except Exception:
        return 0

def extract_date_from_filename(filename):
    """从文件名提取日期，如 2026-07-20-xxx.html → 2026-07-20"""
    m = re.match(r'(\d{4}-\d{2}-\d{2})', filename)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            pass
    return None

# ── 1. 扫描文章文件 ──────────────────────────────────────────────────

def scan_article_files(days=None):
    """扫描 posts/ 目录下所有 HTML 文章文件"""
    articles = {}
    if not os.path.isdir(POSTS_DIR):
        fail(f"posts 目录不存在: {POSTS_DIR}")
        return articles

    for f in sorted(glob.glob(os.path.join(POSTS_DIR, "*.html"))):
        fname = os.path.basename(f)
        slug = fname.replace(".html", "")
        date = extract_date_from_filename(fname)

        # 按天数过滤
        if days and date:
            cutoff = datetime.now().date() - timedelta(days=days)
            if date < cutoff:
                continue

        word_count = count_words_html(f)
        has_audio = False
        audio_file = None

        # 检查对应音频
        # 命名规则: audio/2026-07-20-xxx.mp3 或 audio/podcast-xxx.mp3
        date_prefix = fname.replace(".html", "")[:10]  # 2026-07-20
        slug_no_date = fname.replace(".html", "")
        if date_prefix:
            for af in glob.glob(os.path.join(AUDIO_DIR, f"{slug_no_date}*.mp3")):
                has_audio = True
                audio_file = os.path.basename(af)
                break
            if not has_audio:
                # 也检查日期前缀匹配
                for af in glob.glob(os.path.join(AUDIO_DIR, f"{date_prefix}*.mp3")):
                    # 确保是同一篇文章（slug 部分匹配）
                    af_slug = os.path.basename(af).replace(".mp3", "")
                    if slug_no_date.startswith(date_prefix) and af_slug.startswith(date_prefix):
                        has_audio = True
                        audio_file = os.path.basename(af)
                        break

        articles[slug] = {
            "file": f,
            "filename": fname,
            "slug": slug,
            "date": date,
            "word_count": word_count,
            "has_audio": has_audio,
            "audio_file": audio_file,
            "needs_audio": word_count >= AUDIO_THRESHOLD_WORDS,
        }

    return articles

# ── 2. 解析 blog.html 索引 ───────────────────────────────────────────

def parse_blog_html():
    """解析 blog.html 的 articles 数组 (JS 对象语法，非严格 JSON)"""
    entries = {}
    if not os.path.exists(BLOG_HTML):
        fail(f"blog.html 不存在: {BLOG_HTML}")
        return entries

    with open(BLOG_HTML, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取 articles 数组 (JS 语法: unquoted keys, single/double quoted strings)
    match = re.search(r'const\s+articles\s*=\s*\[([\s\S]*?)\n\s*\];', content)
    if not match:
        fail("blog.html 中未找到 articles 数组")
        return entries

    array_content = match.group(1)

    # 提取每个对象块
    # 匹配 { ... } 块
    obj_pattern = re.compile(r'\{([^{}]+)\}', re.DOTALL)
    for obj_match in obj_pattern.finditer(array_content):
        obj_text = obj_match.group(1)

        # 提取 url 字段
        url_match = re.search(r'url\s*:\s*["\']([^"\']+)["\']', obj_text)
        if not url_match:
            continue
        url = url_match.group(1)
        slug = url.split("/")[-1] if "/" in url else url

        # 提取其他字段
        title_match = re.search(r'title\s*:\s*["\']([^"\']*)["\']', obj_text)
        date_match = re.search(r'date\s*:\s*["\']([^"\']*)["\']', obj_text)
        label_match = re.search(r'typeLabel\s*:\s*["\']([^"\']*)["\']', obj_text)

        if slug:
            entries[slug] = {
                "title": title_match.group(1) if title_match else "",
                "date": date_match.group(1) if date_match else "",
                "url": url,
                "typeLabel": label_match.group(1) if label_match else "",
            }

    return entries

# ── 3. 解析 feed.xml ─────────────────────────────────────────────────

def parse_feed_xml():
    """解析 RSS feed.xml 中的条目"""
    entries = {}
    if not os.path.exists(FEED_XML):
        fail(f"feed.xml 不存在: {FEED_XML}")
        return entries

    with open(FEED_XML, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取 lastBuildDate
    build_match = re.search(r'<lastBuildDate>([^<]+)</lastBuildDate>', content)
    build_date = build_match.group(1) if build_match else "unknown"

    # 提取所有 item
    items = re.findall(r'<item>([\s\S]*?)</item>', content)
    for item in items:
        link_match = re.search(r'<link>([^<]+)</link>', item)
        title_match = re.search(r'<title>([\s\S]*?)</title>', item)
        if link_match:
            link = link_match.group(1).strip()
            slug = link.split("/")[-1] if "/" in link else link
            entries[slug] = {
                "title": title_match.group(1).strip() if title_match else "",
                "link": link,
            }

    return entries, build_date

# ── 4. HTTP 可达性检查 ────────────────────────────────────────────────

def http_check(url, timeout=HTTP_TIMEOUT):
    """HTTP HEAD 检查 URL 是否可访问"""
    try:
        # URL encode non-ASCII characters
        from urllib.parse import quote, urlparse, urlunparse
        parsed = urlparse(url)
        # Encode path while preserving /
        encoded_path = quote(parsed.path, safe="/")
        encoded_url = urlunparse((parsed.scheme, parsed.netloc, encoded_path,
                                  parsed.params, parsed.query, parsed.fragment))
        req = urllib.request.Request(encoded_url, method="HEAD")
        req.add_header("User-Agent", "Sandbot-BlogValidator/1.0")
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.status == 200, resp.status
    except urllib.error.HTTPError as e:
        return False, e.code
    except Exception as e:
        return False, str(e)

# ── 5. 交叉验证 ──────────────────────────────────────────────────────

def cross_validate(file_articles, blog_entries, feed_entries, do_http=False, days=None):
    """交叉验证文件、blog.html、RSS 三者一致性"""
    issues = {
        "orphan_files": [],      # 文件存在但 blog.html 未收录
        "ghost_blog": [],        # blog.html 有条目但文件不存在
        "ghost_rss": [],         # RSS 有条目但文件不存在
        "missing_audio": [],     # 长文章缺少音频
        "http_failures": [],     # HTTP 不可访问
        "short_articles": [],    # 字数过少
    }

    file_slugs = set(file_articles.keys())
    blog_slugs = set(blog_entries.keys())
    rss_slugs = set(feed_entries.keys()) if feed_entries else set()

    # 孤立文件 (只报告有日期前缀的文章 — 这些是正式发布过的)
    for slug in file_slugs - blog_slugs:
        art = file_articles[slug]
        # 只报告有明确日期的文章（正式发布的），跳过无日期前缀的旧内容
        if art["date"] is not None:
            issues["orphan_files"].append({
                "slug": slug,
                "date": str(art["date"]) if art["date"] else "unknown",
                "words": art["word_count"],
            })

    # 幽灵 blog.html 条目
    for slug in blog_slugs - file_slugs:
        issues["ghost_blog"].append({
            "slug": slug,
            "title": blog_entries[slug].get("title", ""),
        })

    # 幽灵 RSS 条目
    for slug in rss_slugs - file_slugs:
        issues["ghost_rss"].append({
            "slug": slug,
            "title": feed_entries[slug].get("title", ""),
        })

    # 长文章缺少音频
    for slug, art in file_articles.items():
        if art["needs_audio"] and not art["has_audio"]:
            issues["missing_audio"].append({
                "slug": slug,
                "words": art["word_count"],
                "date": str(art["date"]) if art["date"] else "unknown",
            })

    # 字数过少
    for slug, art in file_articles.items():
        if art["word_count"] < 300 and art["word_count"] > 0:
            issues["short_articles"].append({
                "slug": slug,
                "words": art["word_count"],
            })

    # HTTP 检查 (只对最近文章)
    if do_http:
        recent_slugs = sorted(
            file_slugs,
            key=lambda s: str(file_articles[s]["date"]) if file_articles[s]["date"] else "",
            reverse=True
        )[:10]  # 只检查最近 10 篇

        for slug in recent_slugs:
            url = f"{SITE_URL}/posts/{slug}"
            reachable, status = http_check(url)
            if not reachable:
                issues["http_failures"].append({
                    "slug": slug,
                    "url": url,
                    "status": status,
                })

    return issues

# ── 6. 自动修复 ──────────────────────────────────────────────────────

def fix_blog_index(file_articles, blog_entries):
    """重建 blog.html 的 articles 数组"""
    if not os.path.exists(BLOG_HTML):
        fail("blog.html 不存在，无法修复")
        return False

    with open(BLOG_HTML, "r", encoding="utf-8") as f:
        content = f.read()

    # 构建新的 articles 数组
    new_entries = []
    for slug, art in sorted(
        file_articles.items(),
        key=lambda x: str(x[1]["date"]) if x[1]["date"] else "",
        reverse=True
    ):
        # 从 HTML 提取标题和副标题
        with open(art["file"], "r", encoding="utf-8") as af:
            html = af.read()

        title_m = re.search(r'class="article-title"[^>]*>([^<]+)<', html)
        subtitle_m = re.search(r'class="article-subtitle"[^>]*>([^<]+)<', html)
        label_m = re.search(r'class="label-category"[^>]*>([^<]+)<', html)
        meta_m = re.search(r'class="article-meta"[^>]*>([^<]*)<', html)

        title = title_m.group(1).strip() if title_m else slug
        subtitle = subtitle_m.group(1).strip() if subtitle_m else ""
        label = label_m.group(1).strip() if label_m else ""

        # 提取 tags
        tags = []
        for tag_m in re.finditer(r'class="tag"[^>]*>([^<]+)<', html):
            tags.append(tag_m.group(1).strip())

        date_str = str(art["date"]) if art["date"] else ""

        # 转义特殊字符
        def esc(s):
            return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")

        entry = {
            "title": title,
            "subtitle": subtitle,
            "date": date_str,
            "url": f"/posts/{slug}",
            "tags": tags,
            "typeLabel": label,
        }
        new_entries.append(entry)

    # 保留最近 50 篇
    new_entries = new_entries[:50]

    # 生成 JS 对象数组 (匹配 blog.html 现有格式: unquoted keys)
    js_entries = []
    for entry in new_entries:
        def js_str(key, val):
            escaped = val.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
            return f"    {key}: '{escaped}'"

        tags_str = str(entry.get("tags", []))
        obj_lines = [
            "  {",
            js_str("title", entry.get("title", "")),
            f"    type: '{entry.get('typeLabel', '').lower() or 'hot'}',",
            js_str("typeLabel", entry.get("typeLabel", "")),
            js_str("tag", entry.get("typeLabel", "")),
            js_str("date", entry.get("date", "")),
            js_str("url", entry.get("url", "")),
            "    excerpt: '',",
            "    duration: '6 分钟',",
            "    access: 'free'",
            "  }",
        ]
        js_entries.append(",\n".join(obj_lines))

    new_js_array = "[\n" + ",\n".join(js_entries) + "\n]"

    # 替换 blog.html 中的 articles 数组
    pattern = r'const\s+articles\s*=\s*\[[\s\S]*?\n\s*\];'
    replacement = f"const articles = {new_js_array};"
    new_content = re.sub(pattern, replacement, content)

    if new_content == content:
        warn("blog.html 未发生变化（可能正则未匹配）")
        return False

    with open(BLOG_HTML, "w", encoding="utf-8") as f:
        f.write(new_content)

    ok(f"blog.html 已更新：{len(new_entries)} 篇文章")
    return True

def fix_rss():
    """调用 rss-auto-writer.sh 修复 RSS"""
    rss_script = os.path.join(REPO_DIR, "rss-auto-writer.sh")
    if not os.path.exists(rss_script):
        # 尝试 workspace
        rss_script = "/home/node/.openclaw/workspace/scripts/rss-auto-writer.sh"
    if os.path.exists(rss_script):
        try:
            subprocess.run(["bash", rss_script], capture_output=True, timeout=60)
            ok("RSS 已通过 rss-auto-writer.sh 修复")
            return True
        except Exception as e:
            fail(f"RSS 修复失败: {e}")
            return False
    else:
        fail("rss-auto-writer.sh 不存在")
        return False

# ── 7. 主流程 ────────────────────────────────────────────────────────

def update_paths(repo_dir):
    """更新全局路径配置"""
    global REPO_DIR, POSTS_DIR, BLOG_HTML, FEED_XML, AUDIO_DIR
    REPO_DIR = repo_dir
    POSTS_DIR = os.path.join(REPO_DIR, "posts")
    BLOG_HTML = os.path.join(REPO_DIR, "blog.html")
    FEED_XML = os.path.join(REPO_DIR, "feed.xml")
    AUDIO_DIR = os.path.join(POSTS_DIR, "audio")

def main():
    parser = argparse.ArgumentParser(description="博客全链路同步验证")
    parser.add_argument("--fix", action="store_true", help="自动修复所有问题")
    parser.add_argument("--fix-blog", action="store_true", help="只修复 blog.html 索引")
    parser.add_argument("--fix-rss", action="store_true", help="只修复 RSS")
    parser.add_argument("--http-check", action="store_true", help="启用 HTTP 可达性检查")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--days", type=int, default=None, help="只检查最近 N 天的文章")
    parser.add_argument("--repo", default=REPO_DIR, help="博客仓库路径")
    args = parser.parse_args()

    update_paths(args.repo)

    start = datetime.now()
    result = {"status": "pass", "issues": {}, "stats": {}, "timestamp": str(start)}

    if not args.json:
        print(f"\n{Colors.BOLD}🔍 博客全链路同步验证 v1.0{Colors.END}")
        print(f"   时间: {start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   仓库: {REPO_DIR}")
        print()

    # 1. 扫描文件
    if not args.json:
        print(f"{Colors.BOLD}📁 扫描文章文件...{Colors.END}")
    file_articles = scan_article_files(days=args.days)
    if not args.json:
        ok(f"找到 {len(file_articles)} 篇文章")

    # 2. 解析 blog.html
    if not args.json:
        print(f"\n{Colors.BOLD}📄 解析 blog.html...{Colors.END}")
    blog_entries = parse_blog_html()
    if not args.json:
        ok(f"blog.html 收录 {len(blog_entries)} 篇")

    # 3. 解析 RSS
    if not args.json:
        print(f"\n{Colors.BOLD}📡 解析 feed.xml...{Colors.END}")
    feed_result = parse_feed_xml()
    if isinstance(feed_result, tuple):
        feed_entries, build_date = feed_result
    else:
        feed_entries, build_date = {}, "unknown"
    if not args.json:
        ok(f"RSS 收录 {len(feed_entries)} 篇 (lastBuildDate: {build_date})")

    # 4. 交叉验证
    if not args.json:
        print(f"\n{Colors.BOLD}🔗 交叉验证...{Colors.END}")
    issues = cross_validate(
        file_articles, blog_entries, feed_entries,
        do_http=args.http_check, days=args.days
    )

    # 5. 输出问题
    total_issues = sum(len(v) for v in issues.values())

    if not args.json:
        # 孤立文件
        if issues["orphan_files"]:
            fail(f"孤立文章 (文件存在但 blog.html 未收录): {len(issues['orphan_files'])} 篇")
            for item in issues["orphan_files"][:5]:
                info(f"  {item['slug']} ({item['date']}, {item['words']}字)")
            if len(issues["orphan_files"]) > 5:
                info(f"  ... 还有 {len(issues['orphan_files'])-5} 篇")
        else:
            ok("无孤立文章")

        # 幽灵 blog 条目
        if issues["ghost_blog"]:
            fail(f"幽灵条目 (blog.html 有但文件不存在): {len(issues['ghost_blog'])} 个")
            for item in issues["ghost_blog"][:5]:
                info(f"  {item['slug']}: {item['title']}")
        else:
            ok("无幽灵 blog 条目")

        # 幽灵 RSS 条目
        if issues["ghost_rss"]:
            warn(f"幽灵 RSS 条目: {len(issues['ghost_rss'])} 个")
            for item in issues["ghost_rss"][:5]:
                info(f"  {item['slug']}: {item['title']}")
        else:
            ok("无幽灵 RSS 条目")

        # 缺少音频
        if issues["missing_audio"]:
            warn(f"长文章缺少音频: {len(issues['missing_audio'])} 篇")
            for item in issues["missing_audio"][:5]:
                info(f"  {item['slug']} ({item['words']}字)")
        else:
            ok("长文章音频齐全")

        # 字数过少
        if issues["short_articles"]:
            warn(f"字数过少 (<300): {len(issues['short_articles'])} 篇")
        else:
            ok("所有文章字数达标")

        # HTTP 检查
        if args.http_check:
            if issues["http_failures"]:
                fail(f"HTTP 不可访问: {len(issues['http_failures'])} 篇")
                for item in issues["http_failures"]:
                    fail(f"  {item['url']} → {item['status']}")
            else:
                ok("最近文章 HTTP 全部可达")

    # 6. 自动修复
    if args.fix or args.fix_blog:
        if not args.json:
            print(f"\n{Colors.BOLD}🔧 修复 blog.html 索引...{Colors.END}")
        if issues["orphan_files"]:
            fix_blog_index(file_articles, blog_entries)
        else:
            if not args.json:
                ok("blog.html 索引已同步，无需修复")

    if args.fix or args.fix_rss:
        if not args.json:
            print(f"\n{Colors.BOLD}🔧 修复 RSS...{Colors.END}")
        fix_rss()

    # 7. 总结
    elapsed = (datetime.now() - start).total_seconds()
    status = "fail" if (issues["orphan_files"] or issues["ghost_blog"]) else "pass"

    if not args.json:
        print(f"\n{Colors.BOLD}{'='*50}{Colors.END}")
        if status == "pass" and not total_issues:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ 全链路同步正常！{Colors.END}")
        elif status == "pass":
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  有 {total_issues} 个警告（非致命）{Colors.END}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ 发现 {total_issues} 个同步问题{Colors.END}")
            if not (args.fix or args.fix_blog):
                print(f"   运行 {Colors.CYAN}--fix{Colors.END} 自动修复")

        print(f"   耗时: {elapsed:.1f}s")
        print()

    # JSON 输出
    if args.json:
        result["status"] = status
        result["issues"] = {k: v for k, v in issues.items()}
        result["stats"] = {
            "total_files": len(file_articles),
            "blog_entries": len(blog_entries),
            "rss_entries": len(feed_entries),
            "rss_build_date": build_date,
            "elapsed_seconds": elapsed,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))

    # 退出码
    sys.exit(1 if status == "fail" and not (args.fix or args.fix_blog) else 0)

if __name__ == "__main__":
    main()
