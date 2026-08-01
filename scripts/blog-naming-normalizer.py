#!/usr/bin/env python3
"""
blog-naming-normalizer.py — 文章文件命名规范化 v1.0
Sandbot 每周工具脚本 · 2026-07-18

解决的问题（本周反复出现的坑）：
  1. 233/454 篇文章缺少 YYYY-MM-DD- 日期前缀 (07-18 明确提出)
  2. 无日期前缀导致去重困难（同一话题可能重复发布）
  3. blog.html / feed.xml 中的 URL 与文件名不一致
  4. 无法按日期排序和归档

工作原理:
  1. 扫描 posts/ 目录，找出缺少日期前缀的文件
  2. 从 blog.html articles 数组中查找该文章对应的 date 字段
  3. 重命名文件：slug.html → YYYY-MM-DD-slug.html
  4. 更新 blog.html 中所有 url 引用
  5. 更新 feed.xml 中所有 link/enclosure 引用
  6. 生成变更报告

用法:
  python3 scripts/blog-naming-normalizer.py                  # 检查模式（只报告，不改）
  python3 scripts/blog-naming-normalizer.py --fix            # 执行修复
  python3 scripts/blog-naming-normalizer.py --fix --dry-run  # 模拟修复（显示将执行的操作）
  python3 scripts/blog-naming-normalizer.py --json           # JSON 输出
  python3 scripts/blog-naming-normalizer.py --stats          # 只显示统计
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime
from pathlib import Path
# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# ── 配置 ──────────────────────────────────────────────────────────────

REPO_DIR = BLOG_ROOT
POSTS_DIR = os.path.join(REPO_DIR, "posts")
BLOG_HTML = os.path.join(REPO_DIR, "blog.html")
FEED_XML = os.path.join(REPO_DIR, "feed.xml")

DATE_PREFIX_RE = re.compile(r'^(\d{4}-\d{2}-\d{2})-(.+)$')
HTML_FILE_RE = re.compile(r'^.+\.html$')


def load_blog_articles():
    """从 blog.html 提取 articles 数组（JS 对象格式，非严格 JSON）"""
    if not os.path.exists(BLOG_HTML):
        print(f"❌ blog.html 不存在: {BLOG_HTML}")
        sys.exit(1)

    with open(BLOG_HTML, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取 articles 数组的原始文本
    m = re.search(r'const\s+articles\s*=\s*(\[.*?\]);\s*\n', content, re.DOTALL)
    if not m:
        print("❌ 无法从 blog.html 提取 articles 数组")
        sys.exit(1)

    raw = m.group(1)

    # 将 JS 对象转为合法 JSON：给未加引号的 key 加双引号
    json_str = re.sub(r'(\{|,)\s*(\w+)\s*:', r'\1 "\2":', raw)
    # 修复 JS 中的转义（如 \. → \\.)
    json_str = json_str.replace('\\.', '\\\\.')

    try:
        articles = json.loads(json_str)
    except json.JSONDecodeError as e:
        # 降级：用正则直接提取 url 和 date
        print(f"⚠️  JSON 解析失败 ({e})，降级为正则提取")
        articles = []
        for block in re.finditer(r'url:\s*"([^"]+)".*?date:\s*"([^"]+)"', raw, re.DOTALL):
            articles.append({'url': block.group(1), 'date': block.group(2)})
        # 也尝试反向顺序 date...url
        if not articles:
            for block in re.finditer(r'date:\s*"([^"]+)".*?url:\s*"([^"]+)"', raw, re.DOTALL):
                articles.append({'url': block.group(2), 'date': block.group(1)})

    return articles, content


def build_url_to_date_map(articles):
    """构建 URL → date 映射"""
    url_date = {}
    for art in articles:
        url = art.get('url', '')
        date = art.get('date', '')
        if url and date:
            # 规范化 URL（去掉 posts/ 前缀和 .html 后缀）
            slug = url.replace('posts/', '').replace('.html', '')
            url_date[slug] = date
            # 也存完整路径形式
            url_date[url] = date
    return url_date


def scan_posts():
    """扫描 posts/ 目录，分类有/无日期前缀的文件"""
    if not os.path.isdir(POSTS_DIR):
        print(f"❌ posts 目录不存在: {POSTS_DIR}")
        sys.exit(1)

    with_prefix = []
    without_prefix = []

    for fname in os.listdir(POSTS_DIR):
        if not HTML_FILE_RE.match(fname):
            continue

        slug = fname.replace('.html', '')
        m = DATE_PREFIX_RE.match(slug)
        if m:
            with_prefix.append({
                'filename': fname,
                'slug': slug,
                'date': m.group(1),
                'body': m.group(2)
            })
        else:
            without_prefix.append({
                'filename': fname,
                'slug': slug,
                'date': None,
                'body': slug
            })

    return with_prefix, without_prefix


def find_date_for_slug(slug, url_date_map, filepath=None):
    """尝试从 blog.html 数据中获取 slug 的日期"""
    # 直接匹配
    if slug in url_date_map:
        return url_date_map[slug]

    # 尝试 posts/slug 形式
    if f"posts/{slug}" in url_date_map:
        return url_date_map[f"posts/{slug}"]

    # 尝试带 .html
    if f"{slug}.html" in url_date_map:
        return url_date_map[f"{slug}.html"]

    # 从文件修改时间推断
    if filepath and os.path.exists(filepath):
        mtime = os.path.getmtime(filepath)
        dt = datetime.fromtimestamp(mtime)
        return dt.strftime('%Y-%m-%d')

    return None


def check_conflicts(new_name, existing_files):
    """检查重命名后是否有冲突"""
    return new_name in existing_files


def generate_report(missing, fixed, skipped, conflicts, json_mode=False):
    """生成报告"""
    if json_mode:
        report = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_missing': len(missing),
            'fixed': len(fixed),
            'skipped': len(skipped),
            'conflicts': len(conflicts),
            'details': {
                'fixed': [{'old': f[0], 'new': f[1], 'date': f[2]} for f in fixed],
                'skipped': [{'slug': s[0], 'reason': s[1]} for s in skipped],
                'conflicts': [{'old': c[0], 'proposed': c[1], 'existing': c[2]} for c in conflicts]
            }
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print(f"\n{'='*60}")
    print(f"📝 文章命名规范化报告")
    print(f"{'='*60}")
    print(f"时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"缺少日期前缀: {len(missing)} 个文件")
    print(f"已修复: {len(fixed)} 个")
    print(f"跳过: {len(skipped)} 个")
    print(f"冲突: {len(conflicts)} 个")

    if fixed:
        print(f"\n✅ 已重命名:")
        for old, new, date in fixed:
            print(f"   {old} → {new}  (date: {date})")

    if skipped:
        print(f"\n⚠️  跳过:")
        for slug, reason in skipped:
            print(f"   {slug}: {reason}")

    if conflicts:
        print(f"\n❌ 冲突（需手动处理）:")
        for old, proposed, existing in conflicts:
            print(f"   {old} → {proposed} (但 {existing} 已存在)")

    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(description='文章文件命名规范化')
    parser.add_argument('--fix', action='store_true', help='执行修复（默认只检查）')
    parser.add_argument('--dry-run', action='store_true', help='模拟修复')
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    parser.add_argument('--stats', action='store_true', help='只显示统计')
    args = parser.parse_args()

    # 扫描
    with_prefix, without_prefix = scan_posts()
    articles, blog_content = load_blog_articles()
    url_date_map = build_url_to_date_map(articles)

    total = len(with_prefix) + len(without_prefix)

    if args.stats:
        print(f"📊 文章命名统计:")
        print(f"   总文件数: {total}")
        print(f"   ✅ 有日期前缀: {len(with_prefix)} ({100*len(with_prefix)//total}%)")
        print(f"   ❌ 无日期前缀: {len(without_prefix)} ({100*len(without_prefix)//total}%)")
        return

    if not without_prefix:
        if not args.json:
            print("✅ 所有文章文件都已有日期前缀，无需修复！")
        else:
            print(json.dumps({'status': 'ok', 'total': total, 'missing': 0}))
        return

    # 分析每个缺少前缀的文件
    existing_files = set(os.listdir(POSTS_DIR))
    fixable = []
    skipped = []
    conflicts = []

    for item in without_prefix:
        slug = item['slug']
        filepath = os.path.join(POSTS_DIR, item['filename'])

        date = find_date_for_slug(slug, url_date_map, filepath)

        if not date:
            skipped.append((slug, "无法确定日期（blog.html 无记录，文件时间不可靠）"))
            continue

        new_slug = f"{date}-{slug}"
        new_filename = f"{new_slug}.html"

        if check_conflicts(new_filename, existing_files):
            conflicts.append((item['filename'], new_filename, new_filename))
            continue

        fixable.append((item['filename'], new_filename, date, slug, new_slug))

    # 报告 / 执行
    if not args.fix and not args.dry_run:
        # 检查模式
        if args.json:
            report = {
                'status': 'issues_found',
                'total': total,
                'with_prefix': len(with_prefix),
                'without_prefix': len(without_prefix),
                'fixable': len(fixable),
                'skipped': len(skipped),
                'conflicts': len(conflicts),
                'sample_fixes': [{'old': f[0], 'new': f[1]} for f in fixable[:10]]
            }
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"📋 检查模式（使用 --fix 执行修复）")
            print(f"   总文件: {total}")
            print(f"   有日期前缀: {len(with_prefix)}")
            print(f"   无日期前缀: {len(without_prefix)}")
            print(f"   可自动修复: {len(fixable)}")
            print(f"   需手动处理: {len(skipped) + len(conflicts)}")

            if fixable:
                print(f"\n📝 前 10 个将修复的文件:")
                for old, new, date, _, _ in fixable[:10]:
                    print(f"   {old} → {new}")
                if len(fixable) > 10:
                    print(f"   ... 还有 {len(fixable) - 10} 个")

            if skipped:
                print(f"\n⚠️  前 5 个跳过的文件:")
                for slug, reason in skipped[:5]:
                    print(f"   {slug}: {reason}")

            if conflicts:
                print(f"\n❌ 冲突文件:")
                for old, proposed, existing in conflicts[:5]:
                    print(f"   {old} → {proposed} (已存在)")

        return

    # 执行修复
    if args.dry_run:
        print("🔍 模拟修复（--dry-run）:\n")

    fixed = []
    blog_updates = []
    feed_updates = []

    # 读取 blog.html 和 feed.xml 内容
    blog_text = blog_content
    feed_text = ""
    if os.path.exists(FEED_XML):
        with open(FEED_XML, 'r', encoding='utf-8') as f:
            feed_text = f.read()

    for old_fn, new_fn, date, old_slug, new_slug in fixable:
        if args.dry_run:
            print(f"   [DRY] {old_fn} → {new_fn}")
            fixed.append((old_fn, new_fn, date))
        else:
            old_path = os.path.join(POSTS_DIR, old_fn)
            new_path = os.path.join(POSTS_DIR, new_fn)

            try:
                os.rename(old_path, new_path)
                fixed.append((old_fn, new_fn, date))

                # 记录需要更新的引用
                blog_updates.append((old_slug, new_slug))
                feed_updates.append((old_slug, new_slug))

            except OSError as e:
                skipped.append((old_fn, f"重命名失败: {e}"))
                continue

    # 更新 blog.html
    if blog_updates and not args.dry_run:
        for old_slug, new_slug in blog_updates:
            # 替换 url 字段中的引用
            blog_text = blog_text.replace(
                f'"posts/{old_slug}"',
                f'"posts/{new_slug}"'
            )
            blog_text = blog_text.replace(
                f'"posts/{old_slug}.html"',
                f'"posts/{new_slug}.html"'
            )
            # 也替换不带 posts/ 前缀的
            blog_text = blog_text.replace(
                f'"{old_slug}"',
                f'"{new_slug}"'
            )

        with open(BLOG_HTML, 'w', encoding='utf-8') as f:
            f.write(blog_text)
        print(f"\n✅ blog.html 已更新 ({len(blog_updates)} 个引用)")

    # 更新 feed.xml
    if feed_updates and not args.dry_run and feed_text:
        for old_slug, new_slug in feed_updates:
            feed_text = feed_text.replace(
                f'posts/{old_slug}',
                f'posts/{new_slug}'
            )
            feed_text = feed_text.replace(
                f'posts/{old_slug}.html',
                f'posts/{new_slug}.html'
            )

        with open(FEED_XML, 'w', encoding='utf-8') as f:
            f.write(feed_text)
        print(f"✅ feed.xml 已更新 ({len(feed_updates)} 个引用)")

    # 最终报告
    generate_report(without_prefix, fixed, skipped, conflicts, args.json)

    # 返回退出码
    if conflicts or skipped:
        sys.exit(1 if not fixed else 0)


if __name__ == '__main__':
    main()
