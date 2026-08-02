#!/usr/bin/env python3
"""
生成 sitemap.xml
扫描 posts/ 目录下所有文章，生成完整的 sitemap
"""

import os
import re
from datetime import datetime
from pathlib import Path

BLOG_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = BLOG_ROOT / "posts"
EN_POSTS_DIR = BLOG_ROOT / "en" / "posts"
SITE_URL = "https://sandbot.cgfan.com"
OUTPUT = BLOG_ROOT / "sitemap.xml"


def get_last_modified(filepath):
    """获取文件最后修改时间"""
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")


def extract_title(html_file):
    """从 HTML 提取标题"""
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"<title>(.*?)</title>", content)
    if match:
        return match.group(1).replace(" — Sandbot Blog", "").strip()
    return ""


def scan_posts(directory, url_prefix):
    """扫描文章目录"""
    urls = []
    if not directory.exists():
        return urls
    for f in sorted(directory.glob("*.html")):
        if f.name in ("all.html", "index.html"):
            continue
        date_str = get_last_modified(f)
        title = extract_title(f)
        urls.append({
            "loc": f"{url_prefix}/{f.name}",
            "lastmod": date_str,
            "title": title,
        })
    return urls


def main():
    urls = []

    # 静态页面
    static_pages = [
        ("/blog.html", "1.0"),
        ("/podcast.html", "0.8"),
        ("/subscribe.html", "0.6"),
        ("/membership.html", "0.5"),
        ("/about.html", "0.5"),
        ("/en/", "0.8"),
        ("/en/blog.html", "0.8"),
        ("/en/podcast.html", "0.6"),
    ]
    for path, priority in static_pages:
        filepath = BLOG_ROOT / path.lstrip("/")
        if filepath.exists():
            urls.append({
                "loc": f"{SITE_URL}{path}",
                "lastmod": get_last_modified(filepath),
                "priority": priority,
            })

    # 中文文章
    cn_urls = scan_posts(POSTS_DIR, f"{SITE_URL}/posts")
    for u in cn_urls:
        u["priority"] = "0.7"
    urls.extend(cn_urls)

    # 英文文章
    en_urls = scan_posts(EN_POSTS_DIR, f"{SITE_URL}/en/posts")
    for u in en_urls:
        u["priority"] = "0.6"
    urls.extend(en_urls)

    # 生成 XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in urls:
        priority = u.get("priority", "0.5")
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{u['loc']}</loc>")
        xml_lines.append(f"    <lastmod>{u['lastmod']}</lastmod>")
        xml_lines.append(f"    <changefreq>weekly</changefreq>")
        xml_lines.append(f"    <priority>{priority}</priority>")
        xml_lines.append("  </url>")
    xml_lines.append("</urlset>")

    OUTPUT.write_text("\n".join(xml_lines), encoding="utf-8")
    print(f"✅ Sitemap generated: {OUTPUT}")
    print(f"   Total URLs: {len(urls)}")
    print(f"   - Static pages: {len(static_pages)}")
    print(f"   - CN articles: {len(cn_urls)}")
    print(f"   - EN articles: {len(en_urls)}")


if __name__ == "__main__":
    main()
