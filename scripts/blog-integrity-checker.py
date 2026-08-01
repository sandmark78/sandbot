#!/usr/bin/env python3
"""
blog-integrity-checker.py — 博客整体一致性审计 v1.0
Sandbot 每周工具脚本 · 2026-07-14

解决的问题（本周反复出现的坑）：
  1. 域名切换后旧链接残留 (07-13 sandmark78.github.io → sandbot.cgfan.com)
  2. blog.html articles 数组与实际帖子文件不同步
  3. feed.xml 与 blog.html 条目不一致
  4. 孤立帖子（文件存在但 blog.html 未收录）
  5. 幽灵帖子（blog.html 有条目但文件不存在）
  6. RSS 中文章缺少音频链接（长文章应自动有播客）

用法:
  python3 scripts/blog-integrity-checker.py
  python3 scripts/blog-integrity-checker.py --fix
  python3 scripts/blog-integrity-checker.py --json
  python3 scripts/blog-integrity-checker.py --skip-orphans  # 跳过孤立帖子检查
"""

import os
import sys
import re
import json
import glob
import argparse
from datetime import datetime, timedelta
# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# ── 配置 ──────────────────────────────────────────────────────────────

BLOG_DIR = BLOG_ROOT
BLOG_HTML = os.path.join(BLOG_DIR, "blog.html")
FEED_XML = os.path.join(BLOG_DIR, "feed.xml")
POSTS_DIR = os.path.join(BLOG_DIR, "posts")
SITE_URL = "https://sandbot.cgfan.com"
OLD_DOMAIN = "sandmark78.github.io/sandbot"

# 长文章阈值（超过此字数应有音频）
AUDIO_THRESHOLD_WORDS = 3000


def extract_blog_articles():
    """从 blog.html 提取 articles 数组中的条目"""
    if not os.path.exists(BLOG_HTML):
        return []
    with open(BLOG_HTML, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"const articles = (\[[\s\S]*?\n\]);", content)
    if not match:
        return []
    articles_str = match.group(1)
    pattern = (
        r'\{\s*title:\s*"([^"]*)",\s*type:\s*"([^"]*)",\s*'
        r'typeLabel:\s*"([^"]*)",\s*tag:\s*"([^"]*)",\s*'
        r'date:\s*"([^"]*)",\s*url:\s*"([^"]*)",\s*'
        r'excerpt:\s*"([^"]*)",\s*duration:\s*"([^"]*)",\s*'
        r'access:\s*"([^"]*)"\s*\}'
    )
    articles = []
    for m in re.finditer(pattern, articles_str):
        articles.append({
            "title": m.group(1),
            "type": m.group(2),
            "typeLabel": m.group(3),
            "tag": m.group(4),
            "date": m.group(5),
            "url": m.group(6),
            "excerpt": m.group(7),
            "duration": m.group(8),
            "access": m.group(9),
        })
    return articles


def extract_feed_items():
    """从 feed.xml 提取 item 条目"""
    if not os.path.exists(FEED_XML):
        return []
    with open(FEED_XML, "r", encoding="utf-8") as f:
        content = f.read()
    items = []
    for m in re.finditer(
        r"<item>\s*<title>([^<]*)</title>\s*<link>([^<]*)</link>\s*"
        r"<guid>([^<]*)</guid>\s*<pubDate>([^<]*)</pubDate>\s*"
        r"<category>([^<]*)</category>",
        content,
    ):
        items.append({
            "title": m.group(1),
            "link": m.group(2),
            "guid": m.group(3),
            "pubDate": m.group(4),
            "category": m.group(5),
        })
    return items


def list_post_files():
    """列出 posts/ 目录下所有 HTML 文件"""
    if not os.path.exists(POSTS_DIR):
        return []
    return sorted(
        os.path.basename(f)
        for f in glob.glob(os.path.join(POSTS_DIR, "*.html"))
    )


def url_to_filename(url):
    """从 URL 提取文件名"""
    # https://sandbot.cgfan.com/posts/xxx.html → xxx.html
    m = re.search(r"/posts/([^/?#]+)", url)
    return m.group(1) if m else None


def count_words_in_file(filepath):
    """统计文章字数"""
    if not os.path.exists(filepath):
        return 0
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    text = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
    english = len(re.findall(r"[a-zA-Z]+", text))
    return chinese + english


def check_integrity(fix_mode=False):
    """执行全面一致性检查"""
    errors, warnings, info = [], [], []

    articles = extract_blog_articles()
    feed_items = extract_feed_items()
    post_files = list_post_files()

    # ── 1. 旧域名检查 ─────────────────────────────────────────────
    old_domain_refs = []

    # 检查 blog.html
    if os.path.exists(BLOG_HTML):
        with open(BLOG_HTML, "r", encoding="utf-8") as f:
            blog_content = f.read()
        old_count = blog_content.count(OLD_DOMAIN)
        if old_count > 0:
            old_domain_refs.append(("blog.html", old_count))

    # 检查 feed.xml
    if os.path.exists(FEED_XML):
        with open(FEED_XML, "r", encoding="utf-8") as f:
            feed_content = f.read()
        old_count = feed_content.count(OLD_DOMAIN)
        if old_count > 0:
            old_domain_refs.append(("feed.xml", old_count))

    # 检查所有帖子文件
    for fname in post_files:
        fpath = os.path.join(POSTS_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        old_count = content.count(OLD_DOMAIN)
        if old_count > 0:
            old_domain_refs.append((f"posts/{fname}", old_count))

    if old_domain_refs:
        total = sum(c for _, c in old_domain_refs)
        errors.append(
            "[旧域名] 发现 %d 处旧域名引用 (%d 个文件): %s"
            % (total, len(old_domain_refs),
               ", ".join("%s(%d)" % (f, c) for f, c in old_domain_refs[:5]))
        )
        if fix_mode:
            for fname in post_files:
                fpath = os.path.join(POSTS_DIR, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    c = f.read()
                if OLD_DOMAIN in c:
                    c = c.replace(
                        "https://%s" % OLD_DOMAIN, SITE_URL
                    ).replace(OLD_DOMAIN, SITE_URL.replace("https://", ""))
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(c)
            info.append("[旧域名] 已自动替换帖子文件中的旧域名 ✅")
    else:
        info.append("[旧域名] 无残留 ✅")

    # ── 2. 幽灵帖子（blog.html 有但文件不存在）─────────────────────
    blog_urls = {a["url"] for a in articles}
    blog_filenames = set()
    for url in blog_urls:
        fn = url_to_filename(url)
        if fn:
            blog_filenames.add(fn)

    ghost_posts = []
    for fn in blog_filenames:
        fpath = os.path.join(POSTS_DIR, fn)
        if not os.path.exists(fpath):
            ghost_posts.append(fn)

    if ghost_posts:
        errors.append(
            "[幽灵帖] blog.html 引用了 %d 个不存在的文件: %s"
            % (len(ghost_posts), ", ".join(ghost_posts[:5]))
        )
    else:
        info.append("[幽灵帖] 无 ✅")

    # ── 3. 孤立帖子（文件存在但 blog.html 未收录）──────────────────
    post_set = set(post_files)
    orphan_posts = post_set - blog_filenames
    # 排除 index.html 等非文章文件
    orphan_posts = {f for f in orphan_posts if not f.startswith("index")}

    if orphan_posts:
        warnings.append(
            "[孤立帖] %d 个文件未在 blog.html 中列出: %s"
            % (len(orphan_posts), ", ".join(sorted(orphan_posts)[:5]))
        )
    else:
        info.append("[孤立帖] 无 ✅")

    # ── 4. blog.html ↔ feed.xml 一致性 ────────────────────────────
    feed_links = {item["link"] for item in feed_items}
    blog_full_urls = {"%s/posts/%s" % (SITE_URL, fn) for fn in blog_filenames}

    # blog 有但 feed 没有
    missing_from_feed = blog_full_urls - feed_links
    # 过滤掉非文章 URL
    missing_from_feed = {u for u in missing_from_feed if "/posts/" in u}

    if missing_from_feed:
        warnings.append(
            "[RSS缺失] %d 篇文章不在 feed.xml 中: %s"
            % (len(missing_from_feed),
               ", ".join(url_to_filename(u) for u in sorted(missing_from_feed)[:5]))
        )
    else:
        info.append("[RSS同步] blog.html 文章全部在 feed.xml 中 ✅")

    # feed 有但 blog 没有
    extra_in_feed = feed_links - blog_full_urls
    extra_in_feed = {u for u in extra_in_feed if "/posts/" in u}
    if extra_in_feed:
        warnings.append(
            "[RSS多余] feed.xml 有 %d 篇不在 blog.html 中: %s"
            % (len(extra_in_feed),
               ", ".join(url_to_filename(u) for u in sorted(extra_in_feed)[:5]))
        )

    # ── 5. 音频覆盖检查 ──────────────────────────────────────────
    audio_dir = os.path.join(POSTS_DIR, "audio")
    audio_files = set()
    if os.path.exists(audio_dir):
        audio_files = {os.path.basename(f) for f in glob.glob(os.path.join(audio_dir, "*.mp3"))}

    missing_audio = []
    has_audio_count = 0
    for fn in post_files:
        fpath = os.path.join(POSTS_DIR, fn)
        wc = count_words_in_file(fpath)
        if wc >= AUDIO_THRESHOLD_WORDS:
            expected_audio = fn.replace(".html", ".mp3")
            if expected_audio in audio_files:
                has_audio_count += 1
            else:
                missing_audio.append((fn, wc))

    if missing_audio:
        warnings.append(
            "[音频缺失] %d 篇长文章(>=%d字)无音频: %s"
            % (len(missing_audio), AUDIO_THRESHOLD_WORDS,
               ", ".join("%s(%d字)" % (f, w) for f, w in missing_audio[:5]))
        )
    else:
        info.append("[音频覆盖] 所有长文章均有音频 ✅")
    info.append("[音频统计] %d 篇长文章, %d 有音频" % (
        has_audio_count + len(missing_audio), has_audio_count))

    # ── 6. 文章数量统计 ──────────────────────────────────────────
    info.append("[数量] blog.html: %d 篇, feed.xml: %d 篇, posts/: %d 个文件"
                % (len(articles), len(feed_items), len(post_files)))

    # ── 7. 最近 7 天发布频率 ──────────────────────────────────────
    cutoff = datetime.now() - timedelta(days=7)
    recent = [f for f in post_files
              if datetime.fromtimestamp(
                  os.path.getmtime(os.path.join(POSTS_DIR, f))
              ) >= cutoff]
    info.append("[发布频率] 近 7 天: %d 篇 (%.1f 篇/天)" % (
        len(recent), len(recent) / 7.0))

    # ── 8. 类型标签分布 ──────────────────────────────────────────
    type_counts = {}
    for a in articles:
        tl = a.get("typeLabel", "?")
        type_counts[tl] = type_counts.get(tl, 0) + 1
    if type_counts:
        info.append("[类型分布] " + ", ".join(
            "%s:%d" % (k, v) for k, v in sorted(type_counts.items(), key=lambda x: -x[1])
        ))

    return {
        "pass": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "info": info,
    }


def main():
    parser = argparse.ArgumentParser(description="博客整体一致性审计")
    parser.add_argument("--fix", action="store_true", help="自动修复可修复的问题")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--skip-orphans", action="store_true", help="跳过孤立帖子检查")
    args = parser.parse_args()

    result = check_integrity(fix_mode=args.fix)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "✅ PASS" if result["pass"] else "❌ FAIL"
        print("\n" + "=" * 60)
        print("🔍 博客完整性审计  %s" % status)
        print("   %s" % datetime.now().strftime("%Y-%m-%d %H:%M UTC"))
        print("=" * 60)

        if result["errors"]:
            print("\n  ❌ 错误 (%d):" % len(result["errors"]))
            for e in result["errors"]:
                print("    • " + e)
        if result["warnings"]:
            print("\n  ⚠️  警告 (%d):" % len(result["warnings"]))
            for w in result["warnings"]:
                print("    • " + w)
        if result["info"]:
            print("\n  ℹ️  信息:")
            for i in result["info"]:
                print("    • " + i)
        print()

    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
