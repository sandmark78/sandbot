#!/usr/bin/env python3
"""
blog-quality-fixer.py — 博客文章质量检查与自动修复 v1.0
Sandbot 🏖️ 每周工具脚本 · 2026-08-04

解决的问题（本周审计发现的重复性 bug）：
  1. 34 篇文章 meta description 是字面量 "content= + excerpt +"（变量未替换）
  2. 114 篇文章 og:description / twitter:description 为空
  3. 文章字数不足（平均 1,100 字，目标 ≥1,500）
  4. 缺少 Sandbot 独立观点板块

用法:
  python3 scripts/blog-quality-fixer.py                    # 检查所有文章，报告问题
  python3 scripts/blog-quality-fixer.py --fix              # 自动修复 meta 描述
  python3 scripts/blog-quality-fixer.py --fix --dry-run    # 预览修复（不实际写入）
  python3 scripts/blog-quality-fixer.py --report           # 输出质量报告（JSON）
  python3 scripts/blog-quality-fixer.py --file posts/xxx.html  # 检查单篇
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# ── 路径 ──────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
BLOG_ROOT = os.path.dirname(SCRIPT_DIR)
POSTS_DIR = os.path.join(BLOG_ROOT, "posts")

# ── 配置 ──────────────────────────────────────────────────────────────
MIN_WORD_COUNT = 1500          # 目标最低字数
BROKEN_DESC_PATTERNS = [
    r'content= + excerpt +',   # 字面量变量名（未替换）
    r'content="\s*"',          # 空字符串
    r"content='\s*'",          # 空字符串（单引号）
]
MAX_DESC_LEN = 155             # SEO 最佳描述长度
EXCERPT_LEN = 140              # 从正文提取的长度


def extract_text_body(html: str) -> str:
    """从 HTML 提取正文纯文本"""
    # 匹配 post-body 开头，取到 site-footer 或文件末尾
    body = re.search(
        r'<div\s+class="(?:post-body|article-body|article-content)">(.*?)(?:<div\s+class="site-footer"|</article>|<footer)',
        html, re.DOTALL
    )
    if not body:
        # fallback: post-body 到文件末尾
        body = re.search(
            r'<div\s+class="(?:post-body|article-body|article-content)">(.*)',
            html, re.DOTALL
        )
    if not body:
        # fallback: <article> 内的内容
        body = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)
    if not body:
        return ""
    text = body.group(1)
    # 去 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)
    # 合并空白
    text = re.sub(r'\s+', ' ', text).strip()
    # 跳过导航栏文字（如 "← 博客首页 主页" 等）
    nav_prefix = re.match(r'^(?:←[^·]*·?\s*)*', text)
    if nav_prefix and nav_prefix.end() < len(text):
        text = text[nav_prefix.end():]
    return text


def count_words(text: str) -> int:
    """统计中文字符 + 英文单词"""
    cn = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))
    en = len(re.findall(r'[a-zA-Z]+', text))
    return cn + en


def generate_description(text: str, max_len: int = EXCERPT_LEN) -> str:
    """从正文前段生成 SEO 描述"""
    if not text:
        return ""
    # 取前 max_len*2 字符来截取句子
    chunk = text[:max_len * 3]
    # 按句子切分（中文句号、问号、叹号、英文句号）
    sentences = re.split(r'(?<=[。！？.!?])\s*', chunk)
    desc = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(desc) + len(s) <= max_len:
            desc += s
        else:
            # 截断到 max_len
            remaining = max_len - len(desc)
            if remaining > 10:
                desc += s[:remaining] + "…"
            break
    if not desc:
        desc = text[:max_len] + "…" if len(text) > max_len else text
    return desc


def has_sandbot_opinion(html: str) -> bool:
    """检查文章是否包含 Sandbot 独立观点板块"""
    patterns = [
        r'Sandbot\s*(点评|观点|看法|说)',
        r'(🏖️|sandbot).*(点评|观点|看法)',
        r'class="opinion"',
        r'class="sandbot-take"',
        r'## .*Sandbot',
        r'## .*(点评|观点|看法)',
    ]
    for p in patterns:
        if re.search(p, html, re.IGNORECASE):
            return True
    return False


def check_article(filepath: str, min_words: int = MIN_WORD_COUNT) -> dict:
    """检查单篇文章的质量问题"""
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    filename = os.path.basename(filepath)
    issues = []

    # 1. 检查 meta description 是否损坏
    meta_desc_match = re.search(r'<meta\s+name="description"\s+content=(?:"([^"]*)"|([^>]*))', html)
    meta_desc = ""
    if meta_desc_match:
        meta_desc = meta_desc_match.group(1) or meta_desc_match.group(2) or ""

    broken = False
    for pat in BROKEN_DESC_PATTERNS:
        if re.search(pat, meta_desc):
            broken = True
            break
    if not meta_desc.strip():
        broken = True

    if broken:
        issues.append({
            "type": "broken_meta_description",
            "severity": "error",
            "current": meta_desc[:80] if meta_desc else "(empty)",
            "fix": "auto-extractable"
        })

    # 2. 检查 og:description
    og_match = re.search(r'og:description["\s]*content="([^"]*)"', html)
    og_desc = og_match.group(1) if og_match else ""
    if not og_desc.strip() or any(re.search(p, og_desc) for p in BROKEN_DESC_PATTERNS):
        issues.append({
            "type": "empty_og_description",
            "severity": "error",
            "current": og_desc[:80] if og_desc else "(empty)",
            "fix": "auto-extractable"
        })

    # 3. 检查 twitter:description
    tw_match = re.search(r'twitter:description["\s]*content="([^"]*)"', html)
    tw_desc = tw_match.group(1) if tw_match else ""
    if not tw_desc.strip() or any(re.search(p, tw_desc) for p in BROKEN_DESC_PATTERNS):
        issues.append({
            "type": "empty_twitter_description",
            "severity": "warning",
            "current": tw_desc[:80] if tw_desc else "(empty)",
            "fix": "auto-extractable"
        })

    # 4. 字数统计
    text = extract_text_body(html)
    wc = count_words(text)
    if wc < min_words:
        issues.append({
            "type": "low_word_count",
            "severity": "warning",
            "current": wc,
            "target": MIN_WORD_COUNT
        })

    # 5. Sandbot 独立观点
    if not has_sandbot_opinion(html):
        issues.append({
            "type": "missing_sandbot_opinion",
            "severity": "info",
            "note": "文章缺少 Sandbot 独立观点板块"
        })

    return {
        "file": filename,
        "path": filepath,
        "word_count": wc,
        "meta_description": meta_desc[:100],
        "og_description": og_desc[:100],
        "has_opinion": has_sandbot_opinion(html),
        "issues": issues,
        "issue_count": len(issues)
    }


def fix_meta_descriptions(filepath: str, dry_run: bool = False) -> list:
    """修复单篇文章的 meta 描述"""
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    original = html
    text = extract_text_body(html)
    desc = generate_description(text)
    filename = os.path.basename(filepath)
    fixes = []

    if not desc:
        fixes.append(f"  ⚠️ {filename}: 无法提取正文，跳过")
        return fixes

    # 修复 meta description
    # Pattern 1: content= + excerpt + (无引号的字面量)
    html, n1 = re.subn(
        r'<meta\s+name="description"\s+content= + excerpt +>',
        f'<meta name="description" content="{desc}">',
        html
    )
    # Pattern 2: content="" (空)
    html, n2 = re.subn(
        r'<meta\s+name="description"\s+content="">',
        f'<meta name="description" content="{desc}">',
        html
    )

    if n1 or n2:
        fixes.append(f"  ✅ {filename}: meta description → \"{desc[:60]}…\"")

    # 修复 og:description
    html, n3 = re.subn(
        r'(og:description"\s*content=")",',
        lambda m: m.group(0),  # noop placeholder
        html
    )
    # 更精确的替换
    html_fixed = re.sub(
        r'(property="og:description"\s+content=")([^"]*)(")',
        lambda m: f'{m.group(1)}{desc}{m.group(3)}' if not m.group(2).strip() or 'excerpt' in m.group(2) else m.group(0),
        html
    )
    if html_fixed != html:
        fixes.append(f"  ✅ {filename}: og:description → \"{desc[:60]}…\"")
        html = html_fixed

    # 修复 twitter:description
    html_fixed = re.sub(
        r'(name="twitter:description"\s+content=")([^"]*)(")',
        lambda m: f'{m.group(1)}{desc}{m.group(3)}' if not m.group(2).strip() or 'excerpt' in m.group(2) else m.group(0),
        html
    )
    if html_fixed != html:
        fixes.append(f"  ✅ {filename}: twitter:description → \"{desc[:60]}…\"")
        html = html_fixed

    # 写入
    if html != original and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        fixes.append(f"  💾 {filename}: 已保存")
    elif html != original and dry_run:
        fixes.append(f"  🔍 {filename}: [dry-run] 有变更但未写入")

    return fixes


def main():
    parser = argparse.ArgumentParser(description="博客质量检查与修复")
    parser.add_argument("--fix", action="store_true", help="自动修复 meta 描述")
    parser.add_argument("--dry-run", action="store_true", help="预览修复但不写入")
    parser.add_argument("--report", action="store_true", help="输出 JSON 报告")
    parser.add_argument("--file", type=str, help="检查指定文章")
    parser.add_argument("--min-words", type=int, default=MIN_WORD_COUNT, help="最低字数阈值")
    args = parser.parse_args()

    min_words = args.min_words

    # 确定要检查的文件
    if args.file:
        filepath = args.file if os.path.isabs(args.file) else os.path.join(BLOG_ROOT, args.file)
        files = [filepath]
    else:
        files = sorted(glob_files())

    if not files:
        print("❌ 未找到 HTML 文章文件")
        sys.exit(1)

    # 检查
    results = []
    total_issues = 0
    broken_meta = 0
    low_wc = 0
    no_opinion = 0

    for fp in files:
        if not os.path.exists(fp):
            continue
        r = check_article(fp, min_words=min_words)
        results.append(r)
        total_issues += r["issue_count"]
        for iss in r["issues"]:
            if iss["type"] == "broken_meta_description":
                broken_meta += 1
            elif iss["type"] == "low_word_count":
                low_wc += 1
            elif iss["type"] == "missing_sandbot_opinion":
                no_opinion += 1

    # 修复模式
    if args.fix:
        print(f"\n🔧 修复 meta 描述 ({'dry-run' if args.dry_run else '实际写入'})...\n")
        all_fixes = []
        for r in results:
            if any(i["type"] in ("broken_meta_description", "empty_og_description", "empty_twitter_description") for i in r["issues"]):
                fixes = fix_meta_descriptions(r["path"], dry_run=args.dry_run)
                all_fixes.extend(fixes)
        if all_fixes:
            print("\n".join(all_fixes))
        else:
            print("✅ 无需修复")
        print(f"\n📊 修复完成: {len(all_fixes)} 项操作")
        return

    # 报告模式
    if args.report:
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_articles": len(results),
            "total_issues": total_issues,
            "summary": {
                "broken_meta_description": broken_meta,
                "low_word_count": low_wc,
                "missing_sandbot_opinion": no_opinion
            },
            "articles_with_issues": [r for r in results if r["issue_count"] > 0]
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    # 默认：打印摘要
    print(f"\n📊 Sandbot 博客质量报告")
    print(f"{'='*50}")
    print(f"📁 文章总数: {len(results)}")
    print(f"🐛 问题总数: {total_issues}")
    print(f"")
    print(f"问题分布:")
    print(f"  🔴 损坏的 meta description: {broken_meta}")
    print(f"  🟡 字数不足 (<{min_words}): {low_wc}")
    print(f"  🔵 缺少 Sandbot 观点: {no_opinion}")
    print(f"")

    # 字数分布
    wcs = [r["word_count"] for r in results]
    if wcs:
        avg_wc = sum(wcs) / len(wcs)
        print(f"📏 字数统计:")
        print(f"  平均: {avg_wc:.0f}")
        print(f"  最少: {min(wcs)}")
        print(f"  最多: {max(wcs)}")
        print(f"  达标: {sum(1 for w in wcs if w >= min_words)}/{len(wcs)}")
        print(f"")

    # 最严重的 10 篇
    worst = sorted([r for r in results if r["issue_count"] > 0], key=lambda x: -x["issue_count"])[:10]
    if worst:
        print(f"🔥 问题最多的 10 篇:")
        for r in worst:
            types = ", ".join(set(i["type"] for i in r["issues"]))
            print(f"  {r['file']}: {r['issue_count']} 个问题 [{types}]")

    print(f"\n💡 修复命令: python3 scripts/blog-quality-fixer.py --fix")
    print(f"💡 预览模式: python3 scripts/blog-quality-fixer.py --fix --dry-run")


def glob_files():
    """获取所有文章 HTML 文件"""
    import glob as g
    pattern = os.path.join(POSTS_DIR, "*.html")
    files = g.glob(pattern)
    # 排除 index.html, blog.html 等非文章文件
    exclude = {"index.html", "blog.html"}
    return [f for f in files if os.path.basename(f) not in exclude]


if __name__ == "__main__":
    main()
