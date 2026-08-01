#!/usr/bin/env python3
"""
article-prepublish-checker.py — 文章发布前质量关卡 v1.0
Sandbot 每周工具脚本 · 2026-07-13

解决的问题（本周反复出现的坑）：
  1. 文章排版不符合 V4 模板（07-11 "不是第一次了"）
  2. 文章类型标签硬编码为"早鸟"（07-13 修复）
  3. 选题去重不够智能，同主题重复发布（07-13）
  4. 字数不足 / 播客未生成
  5. 发布后只输出相对路径，老大无法访问（07-13）

用法:
  python3 scripts/article-prepublish-checker.py <article.html>
  python3 scripts/article-prepublish-checker.py <article.html> --fix
  python3 scripts/article-prepublish-checker.py --scan-dir {BLOG_ROOT}/posts/
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

POSTS_DIR = os.path.join(BLOG_ROOT, "posts")
BLOG_HTML = os.path.join(BLOG_ROOT, "blog.html")
TEMPLATE_V4 = os.path.join(BLOG_ROOT, "templates/post-template-v4.html")
SITE_URL = "https://sandbot.cgfan.com"

CFG = {"min_words": 300}

# V4 模板必须元素
REQUIRED_ELEMENTS = [
    ("viewport_meta", r'<meta\s+name="viewport"', "error", "缺少 viewport meta，移动端无法适配"),
    ("charset", r'<meta\s+charset="UTF-8"', "error", "缺少 charset UTF-8"),
    ("title", r'<title>[^<]+</title>', "error", "缺少 <title> 或为空"),
    ("google_fonts", r'fonts\.googleapis\.com', "warning", "缺少 Google Fonts 链接"),
    ("site_header", r'class="site-header"', "error", "缺少 .site-header（V4 模板核心元素）"),
    ("overline", r'class="overline"', "error", "缺少 .overline（Sandbot Blog 标识）"),
    ("nav", r'<nav[^>]*>.*?</nav>', "error", "缺少 <nav> 导航栏"),
    ("article_label", r'class="label-category"', "warning", "缺少 .label-category（分类标签）"),
    ("article_title", r'class="article-title"', "error", "缺少 .article-title（V4 文章标题）"),
    ("article_subtitle", r'class="article-subtitle"', "warning", "缺少 .article-subtitle（副标题）"),
    ("article_meta", r'class="article-meta"', "error", "缺少 .article-meta（元信息行）"),
    ("quick_glance", r'class="quick-glance"', "warning", "缺少 .quick-glance（三十秒速览）"),
    ("post_body", r'class="(post-body|article-body|article-content)"', "error", "缺少文章主体区域"),
    ("site_footer", r'class="site-footer"', "error", "缺少 .site-footer（V4 页脚）"),
    ("sandbot_cgfan", r'sandbot\.cgfan\.com', "warning", "页脚未包含 sandbot.cgfan.com"),
]

# 文件名 → 文章类型映射
FILENAME_TYPE_MAP = [
    ("morning", "early", "早鸟"),
    ("early", "early", "早鸟"),
    ("noon", "noon", "午间"),
    ("afternoon", "afternoon", "下午"),
    ("hot", "hot", "热点"),
    ("night", "evening", "晚间"),
    ("evening", "evening", "晚间"),
    ("launch", "launch", "产品发布"),
    ("research", "research", "深度研究"),
    ("deep", "deep", "深度"),
]

STOP_WORDS = set('的了是在和与为从到对中theaanisinonfortoofandor')


def count_words(html_content):
    """统计文章正文的中文字数"""
    text = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    body_match = re.search(
        r'class="(?:post-body|article-body|article-content)"[^>]*>(.*?)</div>\s*(?:</article>|<footer)',
        text, re.DOTALL
    )
    if body_match:
        text = body_match.group(1)
    text = re.sub(r'<[^>]+>', '', text)
    chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
    english = len(re.findall(r'[a-zA-Z]+', text))
    return chinese + english


def detect_type(filename):
    """从文件名推断文章类型"""
    base = os.path.basename(filename).lower()
    for kw, tc, tl in FILENAME_TYPE_MAP:
        if kw in base:
            return tc, tl
    return None, None


def check_type_label(html, filename):
    """检查类型标签是否与文件名匹配"""
    exp_class, exp_label = detect_type(filename)
    if exp_class is None:
        return []
    tags = re.findall(r'class="tag\s+tag-(\w+)"', html)
    if tags and exp_class not in set(tags):
        return ["类型标签不匹配: 文件名暗示 '%s'(%s), HTML 中有 %s" % (exp_class, exp_label, set(tags))]
    return []


def check_duplication(title, posts_dir, days=3):
    """检查近 N 天相似主题"""
    kws = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', title.lower())) - STOP_WORDS
    if len(kws) < 3:
        return []
    cutoff = datetime.now() - timedelta(days=days)
    dupes = []
    for f in glob.glob(os.path.join(posts_dir, "*.html")):
        if datetime.fromtimestamp(os.path.getmtime(f)) < cutoff:
            continue
        with open(f, 'r', encoding='utf-8') as fh:
            c = fh.read()
        m = re.search(r'<title>([^<]+)</title>', c) or re.search(r'class="article-title"[^>]*>(.*?)</', c)
        if not m:
            continue
        other = m.group(1).strip()
        if other == title:
            continue
        okws = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', other.lower())) - STOP_WORDS
        if kws and okws:
            sim = len(kws & okws) / len(kws | okws)
            if sim > 0.4:
                dupes.append({"file": os.path.basename(f), "title": other,
                              "sim": round(sim, 2), "shared": list(kws & okws)[:5]})
    return dupes


def check_article(filepath, fix_mode=False):
    """全面检查单篇文章"""
    if not os.path.exists(filepath):
        return {"pass": False, "errors": ["文件不存在: " + filepath], "warnings": [], "info": [],
                "file": os.path.basename(filepath), "title": "", "word_count": 0, "full_url": ""}

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    fname = os.path.basename(filepath)
    errors, warnings, info = [], [], []

    # 1. V4 模板元素
    for name, pat, sev, msg in REQUIRED_ELEMENTS:
        if not re.search(pat, content, re.DOTALL):
            (errors if sev == "error" else warnings).append("[V4模板] " + msg)

    # 2. 字数
    wc = count_words(content)
    min_w = CFG["min_words"]
    if wc < min_w:
        errors.append("[字数] 仅 %d 字，低于最低要求 %d" % (wc, min_w))
    else:
        info.append("[字数] %d 字 ✅" % wc)

    # 3. 类型标签
    for issue in check_type_label(content, fname):
        errors.append("[类型标签] " + issue)

    # 4. 选题去重
    title = ""
    tm = re.search(r'<title>([^<]+)</title>', content) or \
         re.search(r'class="article-title"[^>]*>(.*?)</', content, re.DOTALL)
    if tm:
        title = tm.group(1).strip()
        for d in check_duplication(title, POSTS_DIR):
            warnings.append("[去重] 与 '%s' 相似度 %.0f%% (共享: %s)" %
                            (d["title"], d["sim"] * 100, ", ".join(d["shared"][:3])))

    # 5. 音频
    tc, _ = detect_type(fname)
    if tc != "early" and wc >= 3000:
        audio_path = os.path.join(POSTS_DIR, "audio", fname.replace('.html', '') + '.mp3')
        if os.path.exists(audio_path):
            info.append("[播客] 音频已生成 ✅")
        else:
            warnings.append("[播客] %d 字 >= 3000 但音频不存在" % wc)

    # 6. 内部链接
    for link in re.findall(r'href="([^"]*)"', content):
        if link.startswith(('http', 'mailto:', '#', 'javascript:')):
            continue
        # Resolve relative to the article's directory
        article_dir = os.path.dirname(os.path.abspath(filepath))
        resolved = os.path.normpath(os.path.join(article_dir, link))
        if not os.path.exists(resolved):
            warnings.append("[链接] 死链: " + link)
            if len([w for w in warnings if w.startswith("[链接]")]) > 10:
                break

    # 7. 完整 URL
    full_url = "%s/posts/%s" % (SITE_URL, fname)
    info.append("[发布URL] " + full_url)

    # 8. HTML 标签平衡
    opens = len(re.findall(r'<(p|div|span|h[1-6]|ul|ol|li|a|strong|em)\b', content))
    closes = len(re.findall(r'</(p|div|span|h[1-6]|ul|ol|li|a|strong|em)>', content))
    if abs(opens - closes) > 3:
        warnings.append("[HTML] 标签不平衡: 开 %d / 闭 %d" % (opens, closes))

    # 9. 中文引号
    cq = re.findall(r'[\u201c\u201d\u201e]', content)
    if cq:
        warnings.append("[引号] %d 个中文引号，可能导致 JS 解析失败" % len(cq))
        if fix_mode:
            content = content.replace('\u201c', '\u300c').replace('\u201d', '\u300d').replace('\u201e', '\u300c')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            info.append("[引号] 已自动修复 ✅")

    return {"pass": len(errors) == 0, "file": fname, "title": title, "word_count": wc,
            "errors": errors, "warnings": warnings, "info": info, "full_url": full_url}


def print_result(r):
    status = "✅ PASS" if r["pass"] else "❌ FAIL"
    print("\n" + "=" * 60)
    print("%s  %s" % (status, r.get("file", "?")))
    if r.get("title"):
        print("  标题: %s" % r["title"])
    if r.get("word_count"):
        print("  字数: %d" % r["word_count"])
    print("=" * 60)
    if r["errors"]:
        print("\n  ❌ 错误 (%d):" % len(r["errors"]))
        for e in r["errors"]:
            print("    • " + e)
    if r["warnings"]:
        print("\n  ⚠️  警告 (%d):" % len(r["warnings"]))
        for w in r["warnings"]:
            print("    • " + w)
    if r["info"]:
        print("\n  ℹ️  信息:")
        for i in r["info"]:
            print("    • " + i)


def main():
    parser = argparse.ArgumentParser(description="文章发布前质量关卡")
    parser.add_argument("article", nargs="?", help="文章 HTML 文件")
    parser.add_argument("--fix", action="store_true", help="自动修复")
    parser.add_argument("--scan-dir", metavar="DIR", help="扫描目录")
    parser.add_argument("--days", type=int, default=7, help="扫描天数")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--min-words", type=int, default=300, help="最低字数")
    args = parser.parse_args()

    CFG["min_words"] = args.min_words

    if args.scan_dir:
        cutoff = datetime.now() - timedelta(days=args.days)
        results = []
        for f in sorted(glob.glob(os.path.join(args.scan_dir, "*.html"))):
            if datetime.fromtimestamp(os.path.getmtime(f)) < cutoff:
                continue
            r = check_article(f)
            r["mtime"] = datetime.fromtimestamp(os.path.getmtime(f)).isoformat()
            results.append(r)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for r in results:
                print_result(r)
            total = len(results)
            passed = sum(1 for r in results if r["pass"])
            print("\n📊 汇总: %d 篇, %d 通过, %d 失败" % (total, passed, total - passed))
        sys.exit(0 if all(r["pass"] for r in results) else 1)

    elif args.article:
        r = check_article(args.article, fix_mode=args.fix)
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            print_result(r)
        sys.exit(0 if r["pass"] else 1)

    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
