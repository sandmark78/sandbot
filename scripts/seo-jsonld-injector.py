#!/usr/bin/env python3
"""
seo-jsonld-injector.py — 博客 JSON-LD 结构化数据批量注入 v1.0
Sandbot 每周工具脚本 · 2026-07-28

解决的问题（本周 SEO 优化遗留缺口）：
  1. 490/490 篇文章缺少 JSON-LD (schema.org/BlogPosting)
  2. Google Search Console 报告"缺少结构化数据"
  3. 搜索引擎无法识别文章作者、日期、分类等关键信息
  4. 影响富摘要展示（搜索结果中的星标、作者头像等）

本脚本：
  - 从 HTML 文章提取 title / description / date / category / author
  - 生成 schema.org/BlogPosting JSON-LD
  - 注入到 </head> 前（SEO 最佳位置）
  - 支持审计模式和批量修复

用法:
  python3 scripts/seo-jsonld-injector.py                    # 审计，输出报告
  python3 scripts/seo-jsonld-injector.py --fix              # 审计 + 注入
  python3 scripts/seo-jsonld-injector.py --fix --dry-run    # 预览，不写入
  python3 scripts/seo-jsonld-injector.py --json             # JSON 输出
  python3 scripts/seo-jsonld-injector.py --single <file>    # 处理单篇文章
"""

import os
import sys
import re
import json
import glob
import argparse
from datetime import datetime
from pathlib import Path
# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# ── 配置 ──────────────────────────────────────────────────────────────

REPO_DIR = BLOG_ROOT
POSTS_DIR = os.path.join(REPO_DIR, "posts")
SITE_URL = "https://sandbot.cgfan.com"
AUTHOR_NAME = "Sandbot 🏖️"
AUTHOR_URL = SITE_URL
ORG_NAME = "Sandbot Blog"
ORG_LOGO = f"{SITE_URL}/og-default.png"

# 文章分类标签映射（从文件名/label提取）
CATEGORY_MAP = {
    "ai": "AI",
    "前沿": "AI",
    "hot": "AI热点",
    "安全": "网络安全",
    "security": "网络安全",
    "加密": "加密货币",
    "crypto": "加密货币",
    "web3": "Web3",
    "教程": "教程",
    "tutorial": "教程",
    "工具": "工具",
    "tool": "工具",
    "观点": "观点",
    "opinion": "观点",
    "行业": "行业动态",
    "机器人": "机器人",
    "robot": "机器人",
}


# ── 工具函数 ──────────────────────────────────────────────────────────

def extract_meta(html, filename):
    """从 HTML 提取元数据"""
    meta = {}

    # Title
    m = re.search(r'<title>([^<]+)</title>', html)
    if m:
        raw_title = m.group(1).strip()
        # 去掉 " — Sandbot Blog" 后缀
        meta['title'] = re.sub(r'\s*[—|]\s*Sandbot Blog$', '', raw_title)
    else:
        meta['title'] = ''

    # Description
    m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html)
    if m:
        meta['description'] = m.group(1).strip()
    else:
        # 从第一段提取
        m = re.search(r'<article[^>]*>.*?<p>([^<]{50,300})</p>', html, re.DOTALL)
        if m:
            meta['description'] = m.group(1).strip()[:200]
        else:
            meta['description'] = meta['title']

    # Date from filename: 2026-07-28-noon-xxx.html or 2026-07-28-evening-xxx.html
    m = re.match(r'(\d{4}-\d{2}-\d{2})', os.path.basename(filename))
    if m:
        meta['datePublished'] = m.group(1)
    else:
        # 尝试从文件修改时间
        meta['datePublished'] = datetime.now().strftime('%Y-%m-%d')

    # Category from label
    m = re.search(r'label-category[^>]*>([^<]+)<', html)
    if m:
        raw_cat = m.group(1).strip()
        meta['category'] = raw_cat
    else:
        # 从文件名推断
        meta['category'] = 'AI'

    # Word count (approximate)
    text = re.sub(r'<[^>]+>', ' ', html)
    words = len(re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+', text))
    meta['wordCount'] = words

    # Image
    m = re.search(r'<meta\s+property="og:image"\s+content="([^"]*)"', html)
    if m:
        meta['image'] = m.group(1).strip()
    else:
        meta['image'] = ORG_LOGO

    # URL (from filename)
    slug = os.path.basename(filename).replace('.html', '')
    meta['url'] = f"{SITE_URL}/posts/{slug}"

    return meta


def generate_jsonld(meta):
    """生成 BlogPosting JSON-LD"""
    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": meta['title'],
        "description": meta['description'],
        "datePublished": meta['datePublished'],
        "dateModified": meta['datePublished'],
        "author": {
            "@type": "Person",
            "name": AUTHOR_NAME,
            "url": AUTHOR_URL
        },
        "publisher": {
            "@type": "Organization",
            "name": ORG_NAME,
            "logo": {
                "@type": "ImageObject",
                "url": ORG_LOGO
            }
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": meta['url']
        },
        "image": meta['image'],
        "keywords": meta['category'],
        "wordCount": meta['wordCount'],
        "inLanguage": "zh-CN"
    }
    return data


def inject_jsonld(html, jsonld_data):
    """注入 JSON-LD 到 HTML"""
    jsonld_str = json.dumps(jsonld_data, ensure_ascii=False, indent=2)
    script_tag = f'<script type="application/ld+json">\n{jsonld_str}\n</script>'

    # 检查是否已有 JSON-LD
    if 'application/ld+json' in html:
        return html, False  # 已存在，跳过

    # 注入到 </head> 前
    if '</head>' in html:
        new_html = html.replace('</head>', f'{script_tag}\n</head>')
        return new_html, True
    else:
        # 没有 </head>，注入到 <head> 后
        if '<head>' in html:
            new_html = html.replace('<head>', f'<head>\n{script_tag}', 1)
            return new_html, True
        return html, False


def audit_post(filepath):
    """审计单篇文章"""
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    has_jsonld = 'application/ld+json' in html
    meta = extract_meta(html, filepath)

    return {
        'file': os.path.basename(filepath),
        'has_jsonld': has_jsonld,
        'title': meta['title'][:60],
        'date': meta['datePublished'],
        'category': meta['category'],
        'wordCount': meta['wordCount'],
        'url': meta['url']
    }


def fix_post(filepath, dry_run=False):
    """修复单篇文章"""
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    meta = extract_meta(html, filepath)
    jsonld = generate_jsonld(meta)
    new_html, changed = inject_jsonld(html, jsonld)

    if changed and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_html)

    return changed, meta


# ── 主逻辑 ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='博客 JSON-LD 结构化数据批量注入')
    parser.add_argument('--fix', action='store_true', help='执行修复')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际写入')
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    parser.add_argument('--single', type=str, help='处理单篇文章')
    args = parser.parse_args()

    if not os.path.isdir(POSTS_DIR):
        print(f"❌ 文章目录不存在: {POSTS_DIR}")
        sys.exit(1)

    # 获取所有文章
    if args.single:
        files = [args.single]
    else:
        files = sorted(glob.glob(os.path.join(POSTS_DIR, '*.html')))

    total = len(files)
    missing = 0
    fixed = 0
    results = []

    print(f"🔍 扫描 {total} 篇文章的 JSON-LD 状态...\n")

    for filepath in files:
        audit = audit_post(filepath)
        results.append(audit)

        if not audit['has_jsonld']:
            missing += 1
            if args.fix:
                changed, meta = fix_post(filepath, args.dry_run)
                if changed:
                    fixed += 1
                    status = "✅ 已注入" if not args.dry_run else "🔧 将注入"
                    if not args.json:
                        print(f"  {status}: {audit['file']}")

    # 输出报告
    if args.json:
        output = {
            'timestamp': datetime.now().isoformat(),
            'total': total,
            'missing_jsonld': missing,
            'fixed': fixed,
            'dry_run': args.dry_run,
            'articles': results
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"📊 审计结果:")
        print(f"  总文章数: {total}")
        print(f"  缺少 JSON-LD: {missing} ({missing*100//total}%)")
        print(f"  已有 JSON-LD: {total - missing}")

        if args.fix:
            print(f"\n🔧 修复结果:")
            mode = "(dry-run)" if args.dry_run else ""
            print(f"  已注入 {fixed} 篇 {mode}")
        elif missing > 0:
            print(f"\n💡 建议:")
            print(f"  运行 python3 scripts/seo-jsonld-injector.py --fix 注入 JSON-LD")
            print(f"  运行 python3 scripts/seo-jsonld-injector.py --fix --dry-run 预览")

        # 分类统计
        cats = {}
        for r in results:
            cat = r['category']
            cats[cat] = cats.get(cat, 0) + 1
        if cats:
            print(f"\n📂 分类分布:")
            for cat, count in sorted(cats.items(), key=lambda x: -x[1])[:10]:
                print(f"  {cat}: {count} 篇")

    # 退出码
    if missing > 0 and not args.fix:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
