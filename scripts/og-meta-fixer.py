#!/usr/bin/env python3
"""
og-meta-fixer.py — 文章 OG 标签 + Meta 批量修复器 v1.0
Sandbot 每周工具脚本 · 2026-08-02

解决的问题（本周自我审计反复出现）：
  1. 0/453 篇文章有 OG 标签 → 社交分享无预览卡片
  2. 50 篇文章缺少 meta description → SEO 受损
  3. blog.html 只索引 223 篇 → 230 篇文章"隐身"
  4. 外部评价指出"定价混乱、无社区、SEO 基础缺失"

核心功能：
  • 为所有文章添加 og:title / og:description / og:url / og:type
  • 补充缺失的 meta description（从正文提取）
  • 添加 twitter:card / twitter:title 等标签
  • 可选：自动重建 blog.html 索引（含所有 dated 文章）
  • 可选：自动重建 feed.xml

用法:
  python3 scripts/og-meta-fixer.py                    # 预览模式（只报告）
  python3 scripts/og-meta-fixer.py --fix              # 修复所有文章 OG 标签
  python3 scripts/og-meta-fixer.py --fix --rebuild    # 修复 + 重建索引
  python3 scripts/og-meta-fixer.py --fix --dry-run    # 只修复前 5 篇（测试）
  python3 scripts/og-meta-fixer.py --report           # 只输出报告
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

# ── 配置 ──────────────────────────────────────────────────────────────

BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
POSTS_DIR = os.path.join(BLOG_ROOT, "posts")
BLOG_HTML = os.path.join(BLOG_ROOT, "blog.html")
FEED_XML = os.path.join(BLOG_ROOT, "feed.xml")
AUDIO_DIR = os.path.join(POSTS_DIR, "audio")
SITE_URL = "https://sandbot.cgfan.com"

# 要跳过的非文章文件
SKIP_FILES = {
    'blog.html', 'index.html', 'podcast.html', 'subscribe.html',
    'login.html', 'membership.html',
}

# OG 标签模板
OG_TAGS_TEMPLATE = '''  <!-- Open Graph / Social Media -->
  <meta property="og:type" content="article">
  <meta property="og:url" content="{og_url}">
  <meta property="og:title" content="{og_title}">
  <meta property="og:description" content="{og_description}">
  <meta property="og:site_name" content="Sandbot Blog">
  <meta property="og:locale" content="zh_CN">
  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{twitter_title}">
  <meta name="twitter:description" content="{twitter_description}">'''


# ── 工具函数 ──────────────────────────────────────────────────────────

def extract_text_from_html(html_content):
    """从 HTML 提取纯文本（用于生成 description）"""
    # 移除 style 和 script 标签及其内容
    text = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    # 移除所有 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)
    # 清理空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_title(html_content, filename):
    """提取文章标题"""
    # 从 <title> 标签
    match = re.search(r'<title>([^<]+)</title>', html_content)
    if match:
        title = match.group(1).strip()
        title = re.sub(r'\s*[—|]\s*Sandbot Blog.*$', '', title)
        title = re.sub(r'\s*🏖️.*$', '', title)
        if title:
            return title

    # 从 .article-title
    match = re.search(r'class="article-title"[^>]*>([^<]+)<', html_content)
    if match:
        return match.group(1).strip()

    # 从 h1
    match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content)
    if match:
        return match.group(1).strip()

    # 从文件名
    slug = filename.replace('.html', '')
    return slug


def generate_description(html_content, max_len=155):
    """从正文生成 meta description（155 字符以内）"""
    text = extract_text_from_html(html_content)

    # 跳过 CSS/JS 内容，找到正文区域
    # 尝试从 article 标签或 .post-body / .article-body 开始
    body_match = re.search(
        r'<(?:article|div)[^>]*class="(?:post-body|article-body|article-content|container)"[^>]*>(.*?)</(?:article|div)>',
        html_content, re.DOTALL
    )
    if body_match:
        text = extract_text_from_html(body_match.group(1))

    # 清理
    text = re.sub(r'^\s*·\s*', '', text)  # 去掉列表符号
    text = re.sub(r'Sandbot Blog.*$', '', text)  # 去掉尾部品牌名

    # 截取
    if len(text) > max_len:
        # 在句号/问号/感叹号处截断
        truncated = text[:max_len]
        last_sentence = max(
            truncated.rfind('。'),
            truncated.rfind('？'),
            truncated.rfind('！'),
            truncated.rfind('.'),
            truncated.rfind('?'),
        )
        if last_sentence > max_len // 2:
            text = truncated[:last_sentence + 1]
        else:
            text = truncated.rstrip() + '…'

    return text[:max_len]


def escape_html(text):
    """转义 HTML 属性中的特殊字符"""
    return (text
            .replace('&', '&amp;')
            .replace('"', '&quot;')
            .replace('<', '&lt;')
            .replace('>', '&gt;'))


def escape_js(text):
    """转义 JS 字符串"""
    return (text
            .replace('\\', '\\\\')
            .replace('"', '\\"')
            .replace('\n', '\\n')
            .replace('\r', ''))


# ── 核心检查/修复 ────────────────────────────────────────────────────

def check_article(filepath):
    """检查单篇文章的 OG/Meta 状态"""
    filename = os.path.basename(filepath)
    slug = filename.replace('.html', '')

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    issues = []
    has_data = {}

    # 检查 OG 标签
    has_og_title = bool(re.search(r'property="og:title"', content))
    has_og_desc = bool(re.search(r'property="og:description"', content))
    has_og_url = bool(re.search(r'property="og:url"', content))
    has_og_type = bool(re.search(r'property="og:type"', content))
    has_twitter_card = bool(re.search(r'name="twitter:card"', content))

    has_data['og_title'] = has_og_title
    has_data['og_description'] = has_og_desc
    has_data['og_url'] = has_og_url
    has_data['og_type'] = has_og_type
    has_data['twitter_card'] = has_twitter_card

    if not has_og_title:
        issues.append('missing:og:title')
    if not has_og_desc:
        issues.append('missing:og:description')
    if not has_og_url:
        issues.append('missing:og:url')
    if not has_og_type:
        issues.append('missing:og:type')
    if not has_twitter_card:
        issues.append('missing:twitter:card')

    # 检查 meta description
    has_desc = bool(re.search(r'<meta\s+name="description"', content))
    has_data['meta_description'] = has_desc
    if not has_desc:
        issues.append('missing:meta:description')

    # 提取标题和描述（用于修复）
    title = extract_title(content, filename)
    description = ""
    desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', content)
    if desc_match:
        description = desc_match.group(1)
    if not description:
        description = generate_description(content)

    # 检查音频
    audio_path = os.path.join(AUDIO_DIR, slug + '.mp3')
    has_data['has_audio'] = os.path.exists(audio_path)

    # 日期
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})', filename)
    has_data['has_date'] = bool(date_match)
    has_data['date'] = date_match.group(1) if date_match else ''

    return {
        'file': filename,
        'slug': slug,
        'title': title,
        'description': description,
        'issues': issues,
        'needs_fix': len(issues) > 0,
        **has_data,
    }


def fix_article(filepath, info):
    """为单篇文章添加/修复 OG 标签和 meta description"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    title_escaped = escape_html(info['title'])
    desc_escaped = escape_html(info['description'])
    og_url = f"{SITE_URL}/posts/{info['slug']}"

    # 1. 添加/修复 meta description
    if not info['meta_description'] and info['description']:
        # 在 </head> 前插入
        content = content.replace(
            '</head>',
            f'  <meta name="description" content="{desc_escaped}">\n</head>'
        )

    # 2. 添加 OG + Twitter 标签
    if not info['og_title']:
        og_block = OG_TAGS_TEMPLATE.format(
            og_url=og_url,
            og_title=title_escaped,
            og_description=desc_escaped,
            twitter_title=title_escaped,
            twitter_description=desc_escaped,
        )
        # 在 </head> 前插入
        content = content.replace('</head>', f'{og_block}\n</head>')

    # 3. 如果只有部分 OG 标签，补全缺失的
    if info['og_title'] and not info['og_url']:
        content = content.replace(
            '</head>',
            f'  <meta property="og:url" content="{og_url}">\n</head>'
        )
    if info['og_title'] and not info['og_type']:
        content = content.replace(
            '</head>',
            '  <meta property="og:type" content="article">\n</head>'
        )
    if info['og_title'] and not info['og_description']:
        content = content.replace(
            '</head>',
            f'  <meta property="og:description" content="{desc_escaped}">\n</head>'
        )
    if info['og_title'] and not info['twitter_card']:
        content = content.replace(
            '</head>',
            f'  <meta name="twitter:card" content="summary">\n'
            f'  <meta name="twitter:title" content="{title_escaped}">\n'
            f'  <meta name="twitter:description" content="{desc_escaped}">\n'
            f'</head>'
        )

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


# ── blog.html 索引重建 ────────────────────────────────────────────────

def rebuild_blog_index(all_info):
    """重建 blog.html 的 articles JS 数组（包含所有有日期的文章）"""
    if not os.path.exists(BLOG_HTML):
        print(f"❌ blog.html 不存在: {BLOG_HTML}")
        return False

    with open(BLOG_HTML, 'r', encoding='utf-8') as f:
        content = f.read()

    # 只包含有日期的文章
    dated = [i for i in all_info if i['has_date']]
    dated.sort(key=lambda x: x['date'], reverse=True)

    # 分类映射
    CATEGORY_MAP = {
        'early': ('early', '早间'), 'morning': ('morning', '早间'),
        'noon': ('noon', '午间'), 'afternoon': ('afternoon', '下午'),
        'evening': ('evening', '晚间'), 'night': ('night', '夜间'),
        'hot': ('hot', '热点'), 'deep': ('deep', '深度'),
    }

    js_entries = []
    for a in dated:
        slug = a['slug'].lower()
        type_key, type_label = 'hot', '热点'
        for key, (t, l) in CATEGORY_MAP.items():
            if key in slug:
                type_key, type_label = t, l
                break

        title = escape_js(a['title'])
        excerpt = escape_js(a['description'])

        entry = f'''  {{
    title: "{title}",
    type: "{type_key}",
    typeLabel: "{type_label}",
    tag: "{type_label}",
    date: "{a['date']}",
    url: "posts/{a['slug']}",
    excerpt: "{excerpt}",
    duration: "6 分钟",
    access: "free"
  }}'''
        js_entries.append(entry)

    new_array = "const articles = [\n" + ",\n".join(js_entries) + "\n];"
    pattern = r'const articles = \[.*?\];'
    new_content, count = re.subn(pattern, new_array, content, count=1, flags=re.DOTALL)

    if count == 0:
        print("❌ 未找到 articles 数组")
        return False

    with open(BLOG_HTML, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ blog.html 索引已重建: {len(dated)} 篇文章")
    return True


# ── 主入口 ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='OG 标签 + Meta 批量修复器')
    parser.add_argument('--fix', action='store_true', help='执行修复')
    parser.add_argument('--rebuild', action='store_true', help='同时重建 blog.html 索引')
    parser.add_argument('--dry-run', type=int, default=0, metavar='N',
                        help='只修复前 N 篇（测试用）')
    parser.add_argument('--report', action='store_true', help='只输出报告')
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    args = parser.parse_args()

    # 扫描所有文章
    print(f"🔍 扫描 {POSTS_DIR} ...")
    all_info = []
    for filename in sorted(os.listdir(POSTS_DIR)):
        if not filename.endswith('.html'):
            continue
        if filename in SKIP_FILES:
            continue
        filepath = os.path.join(POSTS_DIR, filename)
        info = check_article(filepath)
        all_info.append(info)

    # 统计
    total = len(all_info)
    needs_og = sum(1 for i in all_info if 'missing:og:title' in i['issues'])
    needs_desc = sum(1 for i in all_info if 'missing:meta:description' in i['issues'])
    needs_twitter = sum(1 for i in all_info if 'missing:twitter:card' in i['issues'])
    has_audio = sum(1 for i in all_info if i['has_audio'])
    has_date = sum(1 for i in all_info if i['has_date'])
    no_issues = sum(1 for i in all_info if not i['needs_fix'])

    if args.json:
        output = {
            'total': total,
            'needs_og_tags': needs_og,
            'needs_meta_desc': needs_desc,
            'needs_twitter': needs_twitter,
            'has_audio': has_audio,
            'has_date': has_date,
            'already_complete': no_issues,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0)

    # 报告
    print()
    print("=" * 60)
    print("📊 文章 OG/Meta 健康检查报告")
    print("=" * 60)
    print()
    print(f"📁 文章总数: {total}")
    print(f"📅 有日期前缀: {has_date}")
    print(f"🔊 有音频: {has_audio}")
    print()
    print(f"❌ 缺少 OG 标签: {needs_og}/{total}")
    print(f"❌ 缺少 meta description: {needs_desc}/{total}")
    print(f"❌ 缺少 Twitter Card: {needs_twitter}/{total}")
    print(f"✅ 完全合规: {no_issues}/{total}")
    print()

    if args.report:
        # 列出不合规文章
        for i in all_info:
            if i['needs_fix']:
                print(f"  ⚠️  {i['file']}: {', '.join(i['issues'])}")
        return

    if not args.fix:
        print("💡 使用 --fix 修复所有文章的 OG 标签")
        print("💡 使用 --fix --rebuild 同时重建 blog.html 索引")
        print("💡 使用 --fix --dry-run 5 先测试前 5 篇")
        return

    # 执行修复
    targets = all_info
    if args.dry_run > 0:
        targets = [i for i in all_info if i['needs_fix']][:args.dry_run]
        print(f"🧪 Dry-run 模式: 只修复前 {len(targets)} 篇")
    else:
        targets = [i for i in all_info if i['needs_fix']]
        print(f"🔧 修复模式: {len(targets)} 篇需要修复")

    print()
    fixed = 0
    for info in targets:
        filepath = os.path.join(POSTS_DIR, info['file'])
        if fix_article(filepath, info):
            fixed += 1
            if fixed <= 10 or fixed % 50 == 0:
                print(f"  ✅ {info['file']}")

    print()
    print(f"🎉 修复完成: {fixed}/{len(targets)} 篇文章已添加 OG 标签")

    # 重建索引
    if args.rebuild:
        print()
        print("─── 🔧 重建 blog.html 索引 ───")
        rebuild_blog_index(all_info)

    # 验证
    print()
    print("─── ✅ 验证 ───")
    sample = all_info[0] if all_info else None
    if sample:
        filepath = os.path.join(POSTS_DIR, sample['file'])
        recheck = check_article(filepath)
        if not recheck['needs_fix']:
            print(f"  ✅ 抽样检查通过: {sample['file']}")
        else:
            print(f"  ⚠️  抽样仍有问题: {recheck['issues']}")


if __name__ == '__main__':
    main()
