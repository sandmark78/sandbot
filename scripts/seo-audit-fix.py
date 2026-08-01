#!/usr/bin/env python3
"""
seo-audit-fix.py — 博客 SEO 审计 + 自动修复 v1.0
Sandbot 每周工具脚本 · 2026-07-27

解决的问题（本周 P1 任务 + 反复出现的 SEO 缺口）：
  1. 486/489 篇文章缺少 canonical URL（其中 3 篇用了错误域名 sandmark78.github.io）
  2. 421/489 篇文章缺少 og:image
  3. 5/489 篇文章缺少 twitter:card
  4. 3/489 篇文章缺少 og:description
  5. blog.html 缺少 og:title / og:description
  6. sitemap.xml 需要与文章列表同步

用法:
  python3 scripts/seo-audit-fix.py                  # 仅审计，输出报告
  python3 scripts/seo-audit-fix.py --fix             # 审计 + 自动修复
  python3 scripts/seo-audit-fix.py --fix --dry-run   # 预览修复内容，不实际写入
  python3 scripts/seo-audit-fix.py --json            # JSON 格式输出
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
# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# ── 配置 ──────────────────────────────────────────────────────────────

REPO_DIR = BLOG_ROOT
POSTS_DIR = os.path.join(REPO_DIR, "posts")
BLOG_HTML = os.path.join(REPO_DIR, "blog.html")
FEED_XML = os.path.join(REPO_DIR, "feed.xml")
SITEMAP_XML = os.path.join(REPO_DIR, "sitemap.xml")
SITE_URL = "https://sandbot.cgfan.com"
WRONG_DOMAIN = "sandmark78.github.io"
DEFAULT_OG_IMAGE = f"{SITE_URL}/og-default.png"

# SEO 检查项 (name, regex, severity, fix_description)
SEO_CHECKS = [
    ("charset", r'<meta\s+charset="UTF-8"', "error", None),
    ("viewport", r'<meta\s+name="viewport"', "error", None),
    ("title", r'<title>[^<]+</title>', "error", None),
    ("meta_description", r'<meta\s+name="description"\s+content="[^"]+"', "error", "add_meta_description"),
    ("og_title", r'<meta\s+property="og:title"', "error", "add_og_title"),
    ("og_description", r'<meta\s+property="og:description"', "warning", "add_og_description"),
    ("og_type", r'<meta\s+property="og:type"', "warning", "add_og_type"),
    ("og_url", r'<meta\s+property="og:url"', "warning", "add_og_url"),
    ("og_image", r'<meta\s+property="og:image"', "warning", "add_og_image"),
    ("twitter_card", r'<meta\s+name="twitter:card"', "warning", "add_twitter_card"),
    ("twitter_title", r'<meta\s+name="twitter:title"', "info", "add_twitter_title"),
    ("twitter_description", r'<meta\s+name="twitter:description"', "info", "add_twitter_description"),
    ("canonical", r'<link\s+rel="canonical"', "error", "fix_canonical"),
    ("lang_attr", r'<html\s+lang="', "warning", None),
]


class SEOAuditor:
    def __init__(self, posts_dir, fix=False, dry_run=False, json_output=False):
        self.posts_dir = posts_dir
        self.fix = fix
        self.dry_run = dry_run
        self.json_output = json_output
        self.results = []
        self.stats = {
            "total_articles": 0,
            "articles_with_issues": 0,
            "total_issues": 0,
            "fixed_issues": 0,
            "checks": {},
        }
        for check_name, _, _, _ in SEO_CHECKS:
            self.stats["checks"][check_name] = {"pass": 0, "fail": 0}

    def audit_article(self, filepath):
        """审计单篇文章的 SEO 合规性"""
        filename = os.path.basename(filepath)
        slug = filename.replace(".html", "")
        canonical_url = f"{SITE_URL}/posts/{filename}"

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return {"file": filename, "error": str(e), "issues": []}

        issues = []
        head_content = ""
        head_match = re.search(r"<head[^>]*>(.*?)</head>", content, re.DOTALL)
        if head_match:
            head_content = head_match.group(1)

        # Extract title for fixes
        title_match = re.search(r"<title>([^<]+)</title>", content)
        title = title_match.group(1).strip() if title_match else slug

        # Extract description for fixes
        desc_match = re.search(
            r'<meta\s+name="description"\s+content="([^"]+)"', content
        )
        description = desc_match.group(1).strip() if desc_match else ""

        for check_name, pattern, severity, fix_func_name in SEO_CHECKS:
            # lang_attr is on <html> tag, not inside <head>
            search_in = content if check_name == "lang_attr" else head_content
            found = bool(re.search(pattern, search_in, re.IGNORECASE))
            self.stats["checks"][check_name]["pass" if found else "fail"] += 1

            if not found:
                issue = {
                    "check": check_name,
                    "severity": severity,
                    "message": f"Missing {check_name}",
                    "fixable": fix_func_name is not None,
                }
                issues.append(issue)
            elif check_name == "canonical":
                # Check for wrong domain
                canon_match = re.search(
                    r'<link\s+rel="canonical"\s+href="([^"]+)"', head_content
                )
                if canon_match and WRONG_DOMAIN in canon_match.group(1):
                    issues.append(
                        {
                            "check": "canonical",
                            "severity": "error",
                            "message": f"Wrong domain in canonical: {canon_match.group(1)}",
                            "fixable": True,
                            "fix_type": "fix_canonical_domain",
                        }
                    )

        return {
            "file": filename,
            "slug": slug,
            "title": title,
            "description": description,
            "canonical_url": canonical_url,
            "issues": issues,
            "issue_count": len(issues),
        }

    def fix_article(self, filepath, audit_result):
        """自动修复文章的 SEO 问题"""
        if not self.fix or not audit_result["issues"]:
            return 0

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return 0

        original = content
        fixes_applied = 0
        canonical_url = audit_result["canonical_url"]
        title = audit_result["title"]
        description = audit_result["description"]

        for issue in audit_result["issues"]:
            check = issue["check"]

            if check == "canonical":
                fix_type = issue.get("fix_type", "")
                if fix_type == "fix_canonical_domain":
                    # Fix wrong domain
                    content = re.sub(
                        rf'<link\s+rel="canonical"\s+href="https://{WRONG_DOMAIN}/posts/([^"]+)"',
                        f'<link rel="canonical" href="{canonical_url}"',
                        content,
                    )
                    fixes_applied += 1
                elif not re.search(r'<link\s+rel="canonical"', content):
                    # Add missing canonical
                    insert = f'  <link rel="canonical" href="{canonical_url}">\n'
                    content = self._insert_before_close_head(content, insert)
                    fixes_applied += 1

            elif check == "og_image" and not re.search(
                r'<meta\s+property="og:image"', content
            ):
                insert = f'  <meta property="og:image" content="{DEFAULT_OG_IMAGE}">\n'
                content = self._insert_before_close_head(content, insert)
                fixes_applied += 1

            elif check == "og_type" and not re.search(
                r'<meta\s+property="og:type"', content
            ):
                insert = '  <meta property="og:type" content="article">\n'
                content = self._insert_before_close_head(content, insert)
                fixes_applied += 1

            elif check == "og_url" and not re.search(
                r'<meta\s+property="og:url"', content
            ):
                insert = f'  <meta property="og:url" content="{canonical_url}">\n'
                content = self._insert_before_close_head(content, insert)
                fixes_applied += 1

            elif check == "og_title" and not re.search(
                r'<meta\s+property="og:title"', content
            ):
                safe_title = title.replace('"', "&quot;")
                insert = f'  <meta property="og:title" content="{safe_title}">\n'
                content = self._insert_before_close_head(content, insert)
                fixes_applied += 1

            elif check == "og_description" and not re.search(
                r'<meta\s+property="og:description"', content
            ):
                if description:
                    safe_desc = description.replace('"', "&quot;")
                    insert = f'  <meta property="og:description" content="{safe_desc}">\n'
                    content = self._insert_before_close_head(content, insert)
                    fixes_applied += 1

            elif check == "twitter_card" and not re.search(
                r'<meta\s+name="twitter:card"', content
            ):
                safe_title = title.replace('"', "&quot;")
                safe_desc = description.replace('"', "&quot;")
                tags = f'  <meta name="twitter:card" content="summary_large_image">\n'
                tags += f'  <meta name="twitter:title" content="{safe_title}">\n'
                if description:
                    tags += f'  <meta name="twitter:description" content="{safe_desc}">\n'
                content = self._insert_before_close_head(content, tags)
                fixes_applied += 1

            elif check == "twitter_title" and not re.search(
                r'<meta\s+name="twitter:title"', content
            ):
                if re.search(r'<meta\s+name="twitter:card"', content):
                    safe_title = title.replace('"', "&quot;")
                    insert = f'  <meta name="twitter:title" content="{safe_title}">\n'
                    content = self._insert_before_close_head(content, insert)
                    fixes_applied += 1

            elif check == "twitter_description" and not re.search(
                r'<meta\s+name="twitter:description"', content
            ):
                if description and re.search(r'<meta\s+name="twitter:card"', content):
                    safe_desc = description.replace('"', "&quot;")
                    insert = f'  <meta name="twitter:description" content="{safe_desc}">\n'
                    content = self._insert_before_close_head(content, insert)
                    fixes_applied += 1

            elif check == "meta_description" and not re.search(
                r'<meta\s+name="description"', content
            ):
                # Generate description from first paragraph
                body_match = re.search(
                    r'<(?:div|section)[^>]*class="(?:post-body|article-body|article-content)"[^>]*>\s*<p>([^<]+)</p>',
                    content,
                )
                if body_match:
                    first_para = body_match.group(1).strip()[:160]
                    safe_para = first_para.replace('"', "&quot;")
                    insert = f'  <meta name="description" content="{safe_para}">\n'
                    content = self._insert_before_close_head(content, insert)
                    fixes_applied += 1

        if fixes_applied > 0 and content != original:
            if not self.dry_run:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
            return fixes_applied

        return 0

    def _insert_before_close_head(self, content, insert_text):
        """在 </head> 前插入内容"""
        if "</head>" in content:
            return content.replace("</head>", insert_text + "</head>", 1)
        return content

    def audit_blog_html(self):
        """审计 blog.html 首页的 SEO"""
        filepath = BLOG_HTML
        if not os.path.exists(filepath):
            return {"exists": False, "issues": [{"check": "file", "severity": "error", "message": "blog.html not found"}]}

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        head_content = ""
        head_match = re.search(r"<head[^>]*>(.*?)</head>", content, re.DOTALL)
        if head_match:
            head_content = head_match.group(1)

        issues = []
        checks = [
            ("og_title", r'<meta\s+property="og:title"', "error"),
            ("og_description", r'<meta\s+property="og:description"', "warning"),
            ("og_image", r'<meta\s+property="og:image"', "warning"),
            ("og_type", r'<meta\s+property="og:type"', "warning"),
            ("twitter_card", r'<meta\s+name="twitter:card"', "warning"),
            ("canonical", r'<link\s+rel="canonical"', "warning"),
        ]

        for check_name, pattern, severity in checks:
            if not re.search(pattern, head_content, re.IGNORECASE):
                issues.append({"check": check_name, "severity": severity, "message": f"blog.html missing {check_name}"})

        return {"exists": True, "file": "blog.html", "issues": issues}

    def generate_sitemap(self):
        """生成/更新 sitemap.xml"""
        html_files = sorted(glob.glob(os.path.join(POSTS_DIR, "*.html")))
        # Filter out audio TTS text files and non-article HTML
        articles = [f for f in html_files if not f.endswith(".tts.txt")]

        urls = []
        for filepath in articles:
            filename = os.path.basename(filepath)
            url = f"{SITE_URL}/posts/{filename}"
            mtime = os.path.getmtime(filepath)
            lastmod = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
            urls.append({"loc": url, "lastmod": lastmod})

        # Add main pages
        main_pages = [
            {"loc": SITE_URL + "/", "lastmod": datetime.now().strftime("%Y-%m-%d")},
            {"loc": SITE_URL + "/blog", "lastmod": datetime.now().strftime("%Y-%m-%d")},
        ]

        sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

        for page in main_pages:
            sitemap_content += "  <url>\n"
            sitemap_content += f'    <loc>{page["loc"]}</loc>\n'
            sitemap_content += f'    <lastmod>{page["lastmod"]}</lastmod>\n'
            sitemap_content += '    <changefreq>daily</changefreq>\n'
            sitemap_content += '    <priority>1.0</priority>\n'
            sitemap_content += "  </url>\n"

        for url_entry in urls:
            sitemap_content += "  <url>\n"
            sitemap_content += f'    <loc>{url_entry["loc"]}</loc>\n'
            sitemap_content += f'    <lastmod>{url_entry["lastmod"]}</lastmod>\n'
            sitemap_content += '    <changefreq>monthly</changefreq>\n'
            sitemap_content += '    <priority>0.8</priority>\n'
            sitemap_content += "  </url>\n"

        sitemap_content += "</urlset>\n"

        if not self.dry_run:
            with open(SITEMAP_XML, "w", encoding="utf-8") as f:
                f.write(sitemap_content)

        return len(urls) + len(main_pages)

    def run(self):
        """运行完整审计"""
        html_files = sorted(glob.glob(os.path.join(POSTS_DIR, "*.html")))
        self.stats["total_articles"] = len(html_files)

        # Audit each article
        for filepath in html_files:
            result = self.audit_article(filepath)
            self.results.append(result)

            if result["issues"]:
                self.stats["articles_with_issues"] += 1
                self.stats["total_issues"] += len(result["issues"])

                if self.fix:
                    fixed = self.fix_article(filepath, result)
                    self.stats["fixed_issues"] += fixed

        # Audit blog.html
        blog_result = self.audit_blog_html()

        # Generate sitemap
        sitemap_count = 0
        if self.fix:
            sitemap_count = self.generate_sitemap()

        # Build report
        report = {
            "timestamp": datetime.now().isoformat(),
            "site_url": SITE_URL,
            "stats": self.stats,
            "blog_html": blog_result,
            "sitemap_urls": sitemap_count if self.fix else None,
            "summary": self._build_summary(),
        }

        if not self.json_output:
            self._print_report(report)
        else:
            print(json.dumps(report, indent=2, ensure_ascii=False))

        return report

    def _build_summary(self):
        """构建摘要报告"""
        lines = []
        lines.append(f"📊 SEO 审计报告 — {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append(f"站点: {SITE_URL}")
        lines.append(f"文章总数: {self.stats['total_articles']}")
        lines.append(f"有问题文章: {self.stats['articles_with_issues']}")
        lines.append(f"问题总数: {self.stats['total_issues']}")
        if self.fix:
            lines.append(f"已修复: {self.stats['fixed_issues']}")
        lines.append("")
        lines.append("📋 各项检查通过率:")

        for check_name, _, severity, _ in SEO_CHECKS:
            passed = self.stats["checks"][check_name]["pass"]
            failed = self.stats["checks"][check_name]["fail"]
            total = passed + failed
            pct = (passed / total * 100) if total > 0 else 0
            icon = "✅" if pct == 100 else ("⚠️" if pct >= 90 else "❌")
            sev_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(severity, "")
            lines.append(f"  {icon} {check_name:25s} {passed}/{total} ({pct:.0f}%) {sev_icon}")

        return "\n".join(lines)

    def _print_report(self, report):
        """打印可读报告"""
        print(report["summary"])
        print()

        # Show worst offenders (articles with most issues)
        worst = sorted(self.results, key=lambda x: x["issue_count"], reverse=True)[:5]
        if worst and worst[0]["issue_count"] > 0:
            print("🔴 问题最多的 5 篇文章:")
            for r in worst:
                checks = [i["check"] for i in r["issues"]]
                print(f"  {r['file']}: {r['issue_count']} issues ({', '.join(checks)})")
            print()

        if self.fix:
            print(f"✅ 修复完成！共修复 {self.stats['fixed_issues']} 个问题")
            if report.get("sitemap_urls"):
                print(f"📄 sitemap.xml 已更新 ({report['sitemap_urls']} URLs)")


def main():
    parser = argparse.ArgumentParser(description="博客 SEO 审计 + 自动修复")
    parser.add_argument("--fix", action="store_true", help="自动修复发现的问题")
    parser.add_argument("--dry-run", action="store_true", help="预览修复内容，不实际写入")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument(
        "--posts-dir", default=POSTS_DIR, help=f"文章目录 (默认: {POSTS_DIR})"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.posts_dir):
        print(f"❌ 文章目录不存在: {args.posts_dir}")
        sys.exit(1)

    auditor = SEOAuditor(
        posts_dir=args.posts_dir,
        fix=args.fix,
        dry_run=args.dry_run,
        json_output=args.json,
    )
    report = auditor.run()

    # Exit code: 1 if there are unfixable errors
    has_errors = any(
        i["severity"] == "error"
        for r in auditor.results
        for i in r["issues"]
        if not i.get("fixable", False)
    )
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
