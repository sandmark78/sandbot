#!/usr/bin/env python3
"""
article-link-checker.py — 文章外部链接有效性检查器
Sandbot 每周工具脚本 · 2026-07-10

自动检查博客文章中所有外部链接是否可访问：
  1. 提取文章中所有 href="https://..." 链接
  2. 并发检查 HTTP 状态码 (HEAD 请求)
  3. 标记 4xx/5xx/超时 的死链
  4. 生成报告 (终端 / JSON)

解决的问题：
  • 文章引用的新闻源链接失效 (新闻站删除/迁移)
  • GitHub 仓库链接 404
  • 参考链接超时挂起

用法:
  python3 scripts/article-link-checker.py                        # 检查默认 blog 目录
  python3 scripts/article-link-checker.py path/to/posts/         # 指定目录
  python3 scripts/article-link-checker.py --json                 # JSON 输出
  python3 scripts/article-link-checker.py --timeout 10           # 自定义超时 (秒)
  python3 scripts/article-link-checker.py --workers 5            # 并发数
  python3 scripts/article-link-checker.py --fix-redirects        # 跟踪重定向
"""

import os
import sys
import re
import json
import glob
import time
import argparse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from datetime import datetime


# ── 配置 ──────────────────────────────────────────────────────────────

DEFAULT_BLOG_DIR = "sandbot-blog"
DEFAULT_TIMEOUT = 8        # 秒
DEFAULT_WORKERS = 8        # 并发数
USER_AGENT = "Mozilla/5.0 (compatible; SandbotLinkChecker/1.0)"

# 跳过这些域名的检查 (CDN/字体/统计等)
SKIP_DOMAINS = [
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "cdn.",
    "analytics.",
    "tracking.",
    "pixel.",
    "127.0.0.1",
    "localhost",
]


# ── HTML 链接提取 ─────────────────────────────────────────────────────

class ExternalLinkExtractor(HTMLParser):
    """提取 HTML 中所有外部链接"""

    def __init__(self):
        super().__init__()
        self.links = []  # (href, line, context)

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href", "")
        line = self.getpos()[0]

        if not href.startswith(("http://", "https://")):
            return

        # 跳过 CDN/字体等
        domain = href.split("/")[2] if len(href.split("/")) >= 3 else ""
        if any(skip in domain for skip in SKIP_DOMAINS):
            return

        self.links.append((href, line))


def extract_links(filepath):
    """从 HTML 文件提取外部链接"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    parser = ExternalLinkExtractor()
    try:
        parser.feed(content)
    except Exception:
        pass

    filename = os.path.basename(filepath)
    return [(filename, href, line) for href, line in parser.links]


# ── 链接检查 ──────────────────────────────────────────────────────────

def check_link(url, timeout=DEFAULT_TIMEOUT, follow_redirects=False):
    """
    检查单个链接是否可访问
    返回: (status_code, response_time_ms, error_msg)
    """
    start = time.time()

    try:
        req = urllib.request.Request(
            url,
            method="HEAD",
            headers={"User-Agent": USER_AGENT},
        )
        resp = urllib.request.urlopen(req, timeout=timeout)
        elapsed = int((time.time() - start) * 1000)
        return (resp.status, elapsed, None)

    except urllib.error.HTTPError as e:
        elapsed = int((time.time() - start) * 1000)
        # HEAD 可能被拒，尝试 GET
        if e.code in (403, 405, 501):
            return check_link_get(url, timeout, start)
        return (e.code, elapsed, None)

    except urllib.error.URLError as e:
        elapsed = int((time.time() - start) * 1000)
        reason = str(e.reason)
        # 超时重试一次用 GET
        if "timed out" in reason.lower():
            return check_link_get(url, timeout, start)
        return (0, elapsed, reason)

    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return (0, elapsed, str(e))


def check_link_get(url, timeout, start):
    """用 GET 请求检查链接 (HEAD 失败时的 fallback)"""
    try:
        req = urllib.request.Request(
            url,
            method="GET",
            headers={"User-Agent": USER_AGENT},
        )
        resp = urllib.request.urlopen(req, timeout=timeout)
        elapsed = int((time.time() - start) * 1000)
        return (resp.status, elapsed, None)
    except urllib.error.HTTPError as e:
        elapsed = int((time.time() - start) * 1000)
        return (e.code, elapsed, None)
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return (0, elapsed, str(e))


# ── 主逻辑 ────────────────────────────────────────────────────────────

def check_articles(blog_dir, timeout, workers):
    """检查所有文章的外部链接"""
    html_files = sorted(glob.glob(os.path.join(blog_dir, "*.html")))
    # 排除 index/blog 列表页
    article_files = [
        f for f in html_files
        if os.path.basename(f) not in ("index.html", "blog.html", "all.html")
    ]

    if not article_files:
        print(f"⚠️  没有找到文章 HTML: {blog_dir}")
        return []

    # 提取所有链接
    all_links = []
    for filepath in article_files:
        links = extract_links(filepath)
        all_links.extend(links)

    if not all_links:
        print("✅ 文章中没有外部链接")
        return []

    # 去重 (同一 URL 只检查一次)
    unique_urls = list(set(href for _, href, _ in all_links))
    print(f"🔍 检查 {len(unique_urls)} 个唯一外部链接 (来自 {len(article_files)} 篇文章)...")

    # 并发检查
    url_results = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(check_link, url, timeout): url
            for url in unique_urls
        }
        for future in as_completed(futures):
            url = futures[future]
            status, elapsed, error = future.result()
            url_results[url] = (status, elapsed, error)

    # 组装结果
    results = []
    for filename, href, line in all_links:
        status, elapsed, error = url_results.get(href, (0, 0, "未检查"))
        is_ok = status in (200, 301, 302, 303, 307, 308)
        results.append({
            "file": filename,
            "line": line,
            "url": href,
            "status": status,
            "elapsed_ms": elapsed,
            "error": error,
            "ok": is_ok,
        })

    return results


def format_report(results, blog_dir):
    """格式化报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("🔗 文章外部链接检查报告")
    lines.append(f"   检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"   目录: {blog_dir}")
    lines.append("=" * 60)

    # 按文章分组
    by_file = {}
    for r in results:
        by_file.setdefault(r["file"], []).append(r)

    total = len(results)
    broken = [r for r in results if not r["ok"]]
    slow = [r for r in results if r["ok"] and r["elapsed_ms"] > 3000]

    for filename, links in sorted(by_file.items()):
        file_broken = [l for l in links if not l["ok"]]
        file_slow = [l for l in links if l["ok"] and l["elapsed_ms"] > 3000]

        if not file_broken and not file_slow:
            status = "✅"
        elif file_broken:
            status = "🔴"
        else:
            status = "🟡"

        lines.append(f"\n{status} {filename} ({len(links)} 个外链)")

        for link in links:
            if not link["ok"]:
                lines.append(f"   ❌ [{link['status']}] 行{link['line']}: {link['url']}")
                if link["error"]:
                    lines.append(f"      └─ {link['error']}")
            elif link["elapsed_ms"] > 3000:
                lines.append(f"   🐢 [{link['status']}] {link['elapsed_ms']}ms 行{link['line']}: {link['url']}")

    # 汇总
    lines.append("\n" + "=" * 60)
    lines.append("📊 汇总")
    lines.append(f"   总链接数: {total}")
    lines.append(f"   正常: {total - len(broken) - len(slow)}")
    lines.append(f"   死链: {len(broken)}")
    lines.append(f"   慢链 (>3s): {len(slow)}")

    if broken:
        lines.append("\n   🔴 死链列表:")
        seen = set()
        for r in broken:
            key = (r["url"], r["status"])
            if key not in seen:
                seen.add(key)
                lines.append(f"     [{r['status']}] {r['url']}")
                if r["error"]:
                    lines.append(f"       └─ {r['error']}")

    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="文章外部链接有效性检查器")
    parser.add_argument("directory", nargs="?", default=None, help="博客 HTML 目录")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"超时秒数 (默认 {DEFAULT_TIMEOUT})")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help=f"并发数 (默认 {DEFAULT_WORKERS})")
    args = parser.parse_args()

    # 确定目录
    if args.directory:
        blog_dir = args.directory
    else:
        workspace = os.environ.get("WORKSPACE", "/home/node/.openclaw/workspace")
        blog_dir = os.path.join(workspace, DEFAULT_BLOG_DIR)

    if not os.path.isdir(blog_dir):
        print(f"❌ 目录不存在: {blog_dir}")
        sys.exit(1)

    # 执行检查
    start = time.time()
    results = check_articles(blog_dir, args.timeout, args.workers)
    elapsed = time.time() - start

    if not results:
        print("✅ 没有需要检查的外部链接")
        sys.exit(0)

    # 输出
    if args.json:
        broken = [r for r in results if not r["ok"]]
        output = {
            "checked_at": datetime.now().isoformat(),
            "directory": blog_dir,
            "total_links": len(results),
            "broken_links": len(broken),
            "elapsed_seconds": round(elapsed, 1),
            "results": results,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(format_report(results, blog_dir))
        print(f"\n⏱️  耗时: {elapsed:.1f}s")

    # 退出码
    has_broken = any(not r["ok"] for r in results)
    sys.exit(1 if has_broken else 0)


if __name__ == "__main__":
    main()
