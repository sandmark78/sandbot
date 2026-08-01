#!/usr/bin/env python3
"""
blog-dedup-and-label-check.py — blog.html 去重 + 类型标签校验 v1.0
Sandbot 每周工具脚本 · 2026-07-17

解决的问题（本周反复出现的坑）：
  1. blog.html articles 数组出现重复条目，首页显示同一篇文章多次 (07-17)
  2. 文章类型标签与文件名不匹配（文件名 evening 但标签"早鸟"）(07-13, 07-14)
  3. URL 微变导致去重失败（有无 trailing slash、http vs https）

用法:
  python3 scripts/blog-dedup-and-label-check.py              # 检查模式
  python3 scripts/blog-dedup-and-label-check.py --fix        # 自动修复重复
  python3 scripts/blog-dedup-and-label-check.py --verbose    # 显示所有条目
  python3 scripts/blog-dedup-and-label-check.py --json       # JSON 输出
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime
from collections import Counter
# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# ── 配置 ──────────────────────────────────────────────────────────────

BLOG_DIR = BLOG_ROOT
BLOG_HTML = os.path.join(BLOG_DIR, "blog.html")

# 文件名关键词 → 正确的 typeLabel 映射
# 注意: type 字段是内容分类（深度/研究/商业等），不在本脚本校验范围
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


def extract_articles_with_positions():
    """从 blog.html 提取 articles 数组，返回条目列表和原始文本位置"""
    if not os.path.exists(BLOG_HTML):
        print("❌ blog.html 不存在: %s" % BLOG_HTML)
        sys.exit(1)

    with open(BLOG_HTML, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r"const articles\s*=\s*(\[[\s\S]*?\n\s*\]);", content)
    if not match:
        print("❌ 无法找到 articles 数组")
        sys.exit(1)

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
            "raw": m.group(0),
            "start": m.start(),
            "end": m.end(),
        })

    return articles, content, match


def normalize_url(url):
    """标准化 URL 用于去重比较"""
    url = url.strip()
    # 统一 https
    url = re.sub(r'^http://', 'https://', url)
    # 去掉域名前缀，提取 posts/ 之后的部分
    url = re.sub(r'^https?://[^/]+/', '', url)
    # 去掉 trailing slash
    url = url.rstrip('/')
    # 提取文件名部分（posts/xxx.html 或 posts/xxx）
    m = re.search(r'posts/([^/?#]+)', url)
    if m:
        return m.group(1)
    return url


def find_duplicates(articles):
    """查找重复条目（基于标准化后的 URL）"""
    seen = {}
    duplicates = []

    for i, article in enumerate(articles):
        norm_url = normalize_url(article["url"])
        if norm_url in seen:
            duplicates.append({
                "original_idx": seen[norm_url],
                "duplicate_idx": i,
                "original": articles[seen[norm_url]],
                "duplicate": article,
                "norm_url": norm_url,
            })
        else:
            seen[norm_url] = i

    return duplicates


def check_type_labels(articles):
    """检查文章类型标签是否与文件名匹配"""
    mismatches = []

    for i, article in enumerate(articles):
        url = article["url"]
        # 从 URL 提取文件名（支持相对路径 posts/xxx 和绝对路径）
        m = re.search(r'posts/([^/?#]+)', url)
        if not m:
            continue
        filename = m.group(1)

        # 从文件名推断 typeLabel
        expected_label = None
        for keyword, elabel in FILENAME_TYPE_MAP.items():
            if keyword in filename.lower():
                expected_label = elabel
                break

        if expected_label and article["typeLabel"] != expected_label:
            mismatches.append({
                "idx": i,
                "filename": filename,
                "actual_label": article["typeLabel"],
                "expected_label": expected_label,
                "title": article["title"][:40],
            })

    return mismatches


def fix_duplicates(content, match, articles, duplicates):
    """从 blog.html 中移除重复条目（保留第一个出现的）"""
    if not duplicates:
        return content, 0

    # 收集要移除的重复条目的 raw 文本
    articles_str = match.group(1)
    new_articles_str = articles_str

    # 从后往前替换，避免位置偏移
    for dup in sorted(duplicates, key=lambda d: d["duplicate"]["start"], reverse=True):
        raw = dup["duplicate"]["raw"]
        # 移除该条目（包括前后的逗号和换行）
        # 找到完整的条目文本（包括前导空白和尾部逗号）
        start = dup["duplicate"]["start"]
        end = dup["duplicate"]["end"]

        # 扩展范围以包含尾部逗号和换行
        while end < len(new_articles_str) and new_articles_str[end] in ' \t':
            end += 1
        if end < len(new_articles_str) and new_articles_str[end] == ',':
            end += 1
        if end < len(new_articles_str) and new_articles_str[end] == '\n':
            end += 1

        # 也检查前导逗号
        pre_start = start
        while pre_start > 0 and new_articles_str[pre_start - 1] in ' \t':
            pre_start -= 1

        new_articles_str = new_articles_str[:pre_start] + new_articles_str[end:]

    # 替换 blog.html 中的 articles 数组
    new_content = content[:match.start(1)] + new_articles_str + content[match.end(1):]
    return new_content, len(duplicates)


def fix_labels(content, match, articles, mismatches):
    """修复 typeLabel 不匹配的条目"""
    if not mismatches:
        return content, 0

    articles_str = match.group(1)
    new_articles_str = articles_str

    # 从后往前替换，避免位置偏移
    for m in sorted(mismatches, key=lambda x: x["idx"], reverse=True):
        article = articles[m["idx"]]
        old_raw = article["raw"]
        # 替换 typeLabel
        new_raw = old_raw.replace(
            'typeLabel: "%s"' % article["typeLabel"],
            'typeLabel: "%s"' % m["expected_label"],
        )
        # 重新计算在 articles_str 中的位置
        old_start = article["start"]
        # 由于从后往前替换，需要重新查找
        pos = new_articles_str.find(old_raw)
        if pos >= 0:
            new_articles_str = new_articles_str[:pos] + new_raw + new_articles_str[pos + len(old_raw):]

    new_content = content[:match.start(1)] + new_articles_str + content[match.end(1):]
    return new_content, len(mismatches)


def main():
    parser = argparse.ArgumentParser(description="blog.html 去重 + 类型标签校验")
    parser.add_argument("--fix", action="store_true", help="自动修复重复条目")
    parser.add_argument("--fix-labels", action="store_true", help="自动修复类型标签")
    parser.add_argument("--fix-all", action="store_true", help="修复所有问题")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示所有条目")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    if args.fix_all:
        args.fix = True
        args.fix_labels = True

    articles, content, match = extract_articles_with_positions()

    # ── 1. 重复检查 ──────────────────────────────────────────────
    duplicates = find_duplicates(articles)

    # ── 2. 类型标签检查 ──────────────────────────────────────────
    label_mismatches = check_type_labels(articles)

    # ── 3. 统计 ──────────────────────────────────────────────────
    url_counts = Counter(normalize_url(a["url"]) for a in articles)
    multi_urls = {url: count for url, count in url_counts.items() if count > 1}

    if args.json:
        result = {
            "total_articles": len(articles),
            "unique_urls": len(url_counts),
            "duplicates": len(duplicates),
            "label_mismatches": len(label_mismatches),
            "duplicate_details": [
                {
                    "url": d["original"]["url"],
                    "title": d["original"]["title"],
                    "original_date": d["original"]["date"],
                    "duplicate_date": d["duplicate"]["date"],
                }
                for d in duplicates
            ],
            "label_mismatch_details": [
                {
                    "filename": m["filename"],
                    "title": m["title"],
                    "actual_label": m["actual_label"],
                    "expected_label": m["expected_label"],
                }
                for m in label_mismatches
            ],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # ── 文本输出 ─────────────────────────────────────────────────
    print("=" * 60)
    print("📋 blog.html 去重 + 标签校验报告")
    print("=" * 60)
    print()
    print("📊 总览: %d 个条目, %d 个唯一 URL" % (len(articles), len(url_counts)))
    print()

    # 重复
    if duplicates:
        print("❌ 发现 %d 个重复条目:" % len(duplicates))
        for d in duplicates:
            print("  • %s" % d["original"]["title"][:50])
            print("    URL: %s" % d["original"]["url"])
            print("    条目 #%d 和 #%d 重复" % (d["original_idx"] + 1, d["duplicate_idx"] + 1))
        print()

        if args.fix:
            new_content, removed = fix_duplicates(content, match, articles, duplicates)
            if removed > 0:
                with open(BLOG_HTML, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print("✅ 已移除 %d 个重复条目" % removed)
                print("   文件: %s" % BLOG_HTML)
            print()
        else:
            print("💡 运行 --fix 自动移除重复条目")
            print()
    else:
        print("✅ 无重复条目")
        print()

    # 类型标签
    if label_mismatches:
        print("⚠️  发现 %d 个类型标签不匹配:" % len(label_mismatches))
        for m in label_mismatches:
            print("  • %s" % m["title"])
            print("    文件: %s" % m["filename"])
            print("    当前标签: %s" % m["actual_label"])
            print("    应为标签: %s" % m["expected_label"])
        print()
        if args.fix_labels:
            new_content, fixed = fix_labels(content, match, articles, label_mismatches)
            if fixed > 0:
                with open(BLOG_HTML, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print("✅ 已修复 %d 个类型标签" % fixed)
                print("   文件: %s" % BLOG_HTML)
            print()
        else:
            print("💡 运行 --fix-labels 自动修复类型标签")
            print()
    else:
        print("✅ 所有类型标签与文件名匹配")
        print()

    # 详细列表
    if args.verbose:
        print("─" * 60)
        print("📝 所有条目:")
        for i, a in enumerate(articles):
            norm = normalize_url(a["url"])
            dup_mark = " [DUP]" if url_counts[norm] > 1 else ""
            print("  %2d. [%s] %s%s" % (i + 1, a["typeLabel"], a["title"][:40], dup_mark))
            print("      %s" % a["url"])
        print()

    # 总结
    issues = len(duplicates) + len(label_mismatches)
    if issues == 0:
        print("🎉 全部通过，blog.html 健康！")
    else:
        print("📊 共发现 %d 个问题 (%d 重复 + %d 标签错误)" % (
            issues, len(duplicates), len(label_mismatches)))

    sys.exit(1 if issues > 0 else 0)


if __name__ == "__main__":
    main()
