#!/usr/bin/env python3
"""
blog-orphan-fixer.py — 博客孤立/错位文章自动修复器 v1.0
Sandbot 每周工具脚本 · 2026-07-29

解决的问题（本周反复出现的坑）：
  1. 文章保存到仓库根目录而非 posts/ — 07-27, 07-29 连续出现
  2. blog.html/RSS 引用了不存在的路径 — 多次
  3. posts/ 里的文章未被 blog.html/RSS 收录 — 孤立文章
  4. 文章文件名不符合日期命名规范

本脚本自动检测 + 修复，一条命令搞定。

用法:
  python3 scripts/blog-orphan-fixer.py                  # 全量检查（dry-run）
  python3 scripts/blog-orphan-fixer.py --fix            # 检查 + 自动修复
  python3 scripts/blog-orphan-fixer.py --fix-moved      # 只修复错位文章
  python3 scripts/blog-orphan-fixer.py --fix-index      # 只修复 blog.html/RSS 索引
  python3 scripts/blog-orphan-fixer.py --json           # JSON 输出
  python3 scripts/blog-orphan-fixer.py --verbose        # 详细输出
"""

import os
import sys
import re
import json
import glob
import shutil
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# ── 配置 ──────────────────────────────────────────────────────────────

REPO_DIR = BLOG_ROOT
POSTS_DIR = os.path.join(REPO_DIR, "posts")
BLOG_HTML = os.path.join(REPO_DIR, "blog.html")
FEED_XML = os.path.join(REPO_DIR, "feed.xml")
SITE_URL = "https://sandbot.cgfan.com"

# 仓库根目录中不应被移动的系统文件
SYSTEM_FILES = {
    "index.html", "blog.html", "login.html", "membership.html",
    "monetization.html", "404.html", "sitemap.xml", "robots.txt",
    "feed.xml", "rss.xml", "README.md", "LICENSE", ".gitignore",
    "CNAME", "favicon.ico", "package.json", "style.css",
}

# 文章文件名正则 (YYYY-MM-DD-slug.html)
ARTICLE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}-[\w-]+\.html$")

# ── 工具函数 ──────────────────────────────────────────────────────────

def run_git(*args, cwd=REPO_DIR):
    """执行 git 命令"""
    try:
        result = subprocess.run(
            ["git"] + list(args),
            cwd=cwd, capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


def find_misplaced_articles():
    """
    找到仓库根目录中不应该存在的文章文件。
    返回: [(filepath, filename, suggested_dest)]
    """
    misplaced = []
    if not os.path.isdir(REPO_DIR):
        return misplaced

    for f in os.listdir(REPO_DIR):
        fpath = os.path.join(REPO_DIR, f)
        if not os.path.isfile(fpath):
            continue
        if not f.endswith(".html"):
            continue
        if f in SYSTEM_FILES:
            continue
        if not ARTICLE_PATTERN.match(f):
            continue
        # 这是一个错位的文章文件
        dest = os.path.join(POSTS_DIR, f)
        misplaced.append((fpath, f, dest))

    return misplaced


def find_orphan_articles(days=7):
    """
    找到 posts/ 中存在但 blog.html/RSS 均未收录的近期文章。
    只检查最近 N 天的文章（老文章可能不在索引中是正常的）。
    返回: [(filepath, filename)]
    """
    orphans = []
    if not os.path.isdir(POSTS_DIR):
        return orphans

    # 读取 blog.html 和 feed.xml 内容
    blog_content = ""
    if os.path.isfile(BLOG_HTML):
        with open(BLOG_HTML, "r", encoding="utf-8") as f:
            blog_content = f.read()

    feed_content = ""
    if os.path.isfile(FEED_XML):
        with open(FEED_XML, "r", encoding="utf-8") as f:
            feed_content = f.read()

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    for f in sorted(os.listdir(POSTS_DIR)):
        if not f.endswith(".html"):
            continue
        if f == "index.html":
            continue
        # 只检查近期文章（按文件名日期）
        if len(f) < 10:
            continue
        try:
            file_date = datetime.strptime(f[:10], "%Y-%m-%d")
        except ValueError:
            continue
        if file_date < datetime.now() - timedelta(days=days):
            continue
        # 检查是否被索引
        in_blog = f in blog_content
        in_feed = f in feed_content
        if not in_blog and not in_feed:
            orphans.append((os.path.join(POSTS_DIR, f), f))

    return orphans


def find_ghost_entries():
    """
    找到 blog.html 中引用了但 posts/ 中不存在的文章。
    返回: [(referenced_path, line_snippet)]
    """
    ghosts = []
    if not os.path.isfile(BLOG_HTML):
        return ghosts

    with open(BLOG_HTML, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取所有 href="posts/xxx.html" 引用
    refs = re.findall(r'href="(posts/[^"]+\.html)"', content)
    for ref in set(refs):
        full_path = os.path.join(REPO_DIR, ref)
        if not os.path.isfile(full_path):
            # 找到对应行
            for i, line in enumerate(content.split("\n"), 1):
                if ref in line:
                    ghosts.append((ref, f"line {i}: {line.strip()[:80]}"))
                    break

    return ghosts


def find_naming_violations(days=30):
    """
    找到 posts/ 中文件名不符合命名规范的近期文章。
    只检查有日期前缀但格式不正确的文件（老文章无日期前缀的不强制）。
    返回: [(filepath, filename, issue)]
    """
    violations = []
    if not os.path.isdir(POSTS_DIR):
        return violations

    cutoff = datetime.now() - timedelta(days=days)

    for f in sorted(os.listdir(POSTS_DIR)):
        if not f.endswith(".html"):
            continue
        if f == "index.html":
            continue
        # 只检查以数字开头的文件（可能是日期前缀）
        if not f[0].isdigit():
            continue
        # 尝试解析日期前缀
        date_str = f[:10]
        try:
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            # 以数字开头但不是有效日期格式
            violations.append((
                os.path.join(POSTS_DIR, f),
                f,
                "以数字开头但日期格式无效（应为 YYYY-MM-DD-slug.html）"
            ))
            continue
        # 检查日期是否合理
        if file_date > datetime.now() + timedelta(days=1):
            violations.append((
                os.path.join(POSTS_DIR, f),
                f,
                f"文件日期 {date_str} 超过当前日期"
            ))
        elif file_date < cutoff:
            continue  # 老文章跳过
        # 检查完整格式
        if not ARTICLE_PATTERN.match(f):
            violations.append((
                os.path.join(POSTS_DIR, f),
                f,
                "文件名不符合 YYYY-MM-DD-slug.html 格式"
            ))

    return violations


def fix_misplaced(misplaced, verbose=False):
    """移动错位文章到 posts/"""
    fixed = []
    for src, fname, dest in misplaced:
        if os.path.exists(dest):
            if verbose:
                print(f"  ⚠️  目标已存在，跳过: {fname}")
            continue
        try:
            shutil.move(src, dest)
            fixed.append((src, dest, fname))
            if verbose:
                print(f"  ✅ 移动: {fname} → posts/")
        except Exception as e:
            if verbose:
                print(f"  ❌ 移动失败: {fname} — {e}")
    return fixed


def fix_blog_index(orphans, verbose=False):
    """
    将孤立文章添加到 blog.html 索引。
    简单实现：在 blog.html 的 </main> 或末尾追加链接。
    """
    if not orphans or not os.path.isfile(BLOG_HTML):
        return 0

    with open(BLOG_HTML, "r", encoding="utf-8") as f:
        content = f.read()

    added = 0
    for fpath, fname in orphans:
        # 从文章中提取标题
        title = fname.replace(".html", "").replace("-", " ").title()
        title_match = re.search(r"<title>([^<]+)</title>", open(fpath).read())
        if title_match:
            title = title_match.group(1)

        # 从文件名提取日期
        date_str = fname[:10] if len(fname) >= 10 else "unknown"

        # 构建条目
        entry = f'      <a href="posts/{fname}" class="blog-entry">\n'
        entry += f'        <span class="blog-date">{date_str}</span>\n'
        entry += f'        <span class="blog-title">{title}</span>\n'
        entry += f'      </a>\n'

        # 插入到 blog.html — 找最后一个 blog-entry 之后
        last_entry = content.rfind('</a><!-- last-entry -->')
        if last_entry == -1:
            # 尝试在 </main> 前插入
            insert_pos = content.rfind("</main>")
            if insert_pos == -1:
                insert_pos = content.rfind("</body>")
        else:
            insert_pos = last_entry

        if insert_pos != -1:
            content = content[:insert_pos] + entry + content[insert_pos:]
            added += 1
            if verbose:
                print(f"  ✅ 添加到 blog.html: {fname}")

    if added > 0:
        with open(BLOG_HTML, "w", encoding="utf-8") as f:
            f.write(content)

    return added


def fix_rss(orphans, verbose=False):
    """将孤立文章添加到 RSS feed"""
    if not orphans or not os.path.isfile(FEED_XML):
        return 0

    with open(FEED_XML, "r", encoding="utf-8") as f:
        content = f.read()

    added = 0
    items = []
    for fpath, fname in orphans:
        title = fname.replace(".html", "").replace("-", " ").title()
        title_match = re.search(r"<title>([^<]+)</title>", open(fpath).read())
        if title_match:
            title = title_match.group(1)

        date_str = fname[:10]
        try:
            pub_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 +0000")
        except ValueError:
            pub_date = datetime.now().strftime("%a, %d %b %Y 00:00:00 +0000")

        item = f"    <item>\n"
        item += f"      <title>{title}</title>\n"
        item += f"      <link>{SITE_URL}/posts/{fname}</link>\n"
        item += f"      <guid>{SITE_URL}/posts/{fname}</guid>\n"
        item += f"      <pubDate>{pub_date}</pubDate>\n"
        item += f"    </item>\n"
        items.append(item)

    if items:
        # 插入到 </channel> 前
        insert_pos = content.rfind("</channel>")
        if insert_pos != -1:
            content = content[:insert_pos] + "\n".join(items) + content[insert_pos:]
            with open(FEED_XML, "w", encoding="utf-8") as f:
                f.write(content)
            added = len(items)
            if verbose:
                print(f"  ✅ 添加 {added} 条到 RSS feed")

    return added


# ── 主逻辑 ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="博客孤立/错位文章自动修复器")
    parser.add_argument("--fix", action="store_true", help="检查 + 自动修复所有问题")
    parser.add_argument("--fix-moved", action="store_true", help="只修复错位文章")
    parser.add_argument("--fix-index", action="store_true", help="只修复 blog.html/RSS 索引")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    parser.add_argument("--git-commit", action="store_true", help="修复后自动 git commit")
    args = parser.parse_args()

    do_fix = args.fix or args.fix_moved or args.fix_index
    verbose = args.verbose or args.json

    if not os.path.isdir(REPO_DIR):
        print(f"❌ 仓库目录不存在: {REPO_DIR}")
        sys.exit(1)

    # ── 检查阶段 ──
    misplaced = find_misplaced_articles()
    orphans = find_orphan_articles()
    ghosts = find_ghost_entries()
    naming = find_naming_violations()

    # ── 输出报告 ──
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "misplaced_articles": [
            {"file": f, "from": src, "to": dest}
            for src, f, dest in misplaced
        ],
        "orphan_articles": [
            {"file": f, "path": p} for p, f in orphans
        ],
        "ghost_entries": [
            {"ref": ref, "snippet": snip} for ref, snip in ghosts
        ],
        "naming_violations": [
            {"file": f, "issue": issue} for _, f, issue in naming
        ],
        "fixes_applied": {},
    }

    total_issues = len(misplaced) + len(orphans) + len(ghosts) + len(naming)

    if args.json:
        # JSON 模式下先输出检查结果
        pass
    else:
        print("=" * 60)
        print("🏥 博客孤立/错位文章检查报告")
        print("=" * 60)
        print()

        # 1. 错位文章
        if misplaced:
            print(f"📍 错位文章 (根目录中的文章): {len(misplaced)} 个")
            for src, f, dest in misplaced:
                print(f"   ❌ {f}  (应移至 posts/)")
        else:
            print("✅ 无错位文章")
        print()

        # 2. 孤立文章
        if orphans:
            print(f"📄 孤立文章 (未被 blog.html 收录): {len(orphans)} 个")
            for p, f in orphans[:10]:  # 只显示前 10 个
                print(f"   ⚠️  {f}")
            if len(orphans) > 10:
                print(f"   ... 还有 {len(orphans) - 10} 个")
        else:
            print("✅ 无孤立文章")
        print()

        # 3. 幽灵条目
        if ghosts:
            print(f"👻 幽灵条目 (blog.html 引用了不存在的文件): {len(ghosts)} 个")
            for ref, snip in ghosts:
                print(f"   ❌ {ref}")
        else:
            print("✅ 无幽灵条目")
        print()

        # 4. 命名违规
        if naming:
            print(f"📛 命名违规: {len(naming)} 个")
            for _, f, issue in naming[:10]:
                print(f"   ⚠️  {f} — {issue}")
        else:
            print("✅ 命名规范正常")
        print()

        print(f"📊 总计: {total_issues} 个问题")
        print()

    # ── 修复阶段 ──
    if do_fix:
        fixes = {}

        if not args.fix_index:  # 修复错位文章
            if misplaced:
                print("🔧 修复错位文章...") if not args.json else None
                fixed = fix_misplaced(misplaced, verbose=verbose)
                fixes["misplaced_fixed"] = len(fixed)
                if verbose and not args.json:
                    print(f"   ✅ 修复 {len(fixed)} 个")
                    print()

        if args.fix or args.fix_index:  # 修复索引
            # 重新扫描 orphans（因为移动后可能有新的）
            if args.fix:
                orphans = find_orphan_articles()

            if orphans:
                print("🔧 修复 blog.html 索引...") if not args.json else None
                blog_added = fix_blog_index(orphans, verbose=verbose)
                fixes["blog_entries_added"] = blog_added

                print("🔧 修复 RSS feed...") if not args.json else None
                rss_added = fix_rss(orphans, verbose=verbose)
                fixes["rss_entries_added"] = rss_added

        report["fixes_applied"] = fixes

        # Git commit
        if args.git_commit and sum(fixes.values()) > 0:
            print("📦 Git 提交...") if not args.json else None
            ok, out = run_git("add", "-A")
            if ok:
                msg = f"🔧 博客修复: 移动 {fixes.get('misplaced_fixed', 0)} 个错位文章, "
                msg += f"更新 {fixes.get('blog_entries_added', 0)} 条索引, "
                msg += f"更新 {fixes.get('rss_entries_added', 0)} 条 RSS"
                ok, out = run_git("commit", "-m", msg)
                if ok:
                    print(f"   ✅ {out}") if not args.json else None

        if not args.json:
            print()
            print("✅ 修复完成！")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    # 退出码
    sys.exit(1 if total_issues > 0 and not do_fix else 0)


if __name__ == "__main__":
    main()
