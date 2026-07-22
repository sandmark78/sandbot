#!/usr/bin/env python3
"""
博客全面健康检查 V1.0
一次性扫描所有常见问题，替代零散的手动排查。

用法:
  python3 blog-health-check.py                    # 扫描所有问题
  python3 blog-health-check.py --fix              # 自动修复安全项
  python3 blog-health-check.py --post <file.html> # 只检查单篇文章

解决的问题（本周审计高频项）:
  • blog.html articles 数组与实际文件不同步（孤儿文件/幽灵条目）
  • AUDIO_FILE_PLACEHOLDER 残留
  • V4 模板元素缺失
  • RSS lastBuildDate 过期
  • blog.html 重复条目
  • posts/ 目录中的 .md 文件（应为 .html）
  • 文章字数不足但无音频（逻辑矛盾）
  • 文件名不规范（非 ASCII / 缺少日期前缀）
"""

import re, sys, os, json, glob
from datetime import datetime, timezone
from collections import Counter

# === 配置 ===
BLOG_DIR = "/tmp/sandbot-gh"
POSTS_DIR = os.path.join(BLOG_DIR, "posts")
BLOG_HTML = os.path.join(BLOG_DIR, "blog.html")
FEED_XML = os.path.join(BLOG_DIR, "feed.xml")

V4_ELEMENTS = [
    'quick-glance', 'why-box', 'source-note',
    'bottom-quote', 'compare-box', 'capability-box'
]

WORD_THRESHOLDS = {
    'morning': 3000, 'noon': 2000, 'afternoon': 2500,
    'hot': 2000, 'evening': 2500,
}

# === 结果收集 ===
class Report:
    def __init__(self):
        self.errors = []    # 🔴 必须修复
        self.warnings = []  # 🟡 建议修复
        self.info = []      # ℹ️ 信息
        self.fixable = []   # 🔧 可自动修复

    def error(self, category, msg, fixable=False):
        self.errors.append((category, msg))
        if fixable:
            self.fixable.append((category, msg))

    def warn(self, category, msg, fixable=False):
        self.warnings.append((category, msg))
        if fixable:
            self.fixable.append((category, msg))

    def add_info(self, msg):
        self.info.append(msg)

    def print_report(self):
        print("=" * 60)
        print("🏥 博客健康检查报告")
        print(f"   时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        print("=" * 60)

        if self.info:
            print(f"\nℹ️  信息:")
            for msg in self.info:
                print(f"   • {msg}")

        if self.errors:
            print(f"\n🔴 错误 ({len(self.errors)}):")
            for cat, msg in self.errors:
                print(f"   [{cat}] {msg}")
        else:
            print("\n✅ 无错误")

        if self.warnings:
            print(f"\n🟡 警告 ({len(self.warnings)}):")
            for cat, msg in self.warnings:
                print(f"   [{cat}] {msg}")

        if self.fixable:
            print(f"\n🔧 可自动修复: {len(self.fixable)} 项")
            print("   运行 --fix 自动修复这些项目")

        total_issues = len(self.errors) + len(self.warnings)
        print(f"\n{'=' * 60}")
        if total_issues == 0:
            print("🎉 博客状态完美！零问题。")
        elif len(self.errors) == 0:
            print(f"✅ 博客基本健康 ({len(self.warnings)} 个警告)")
        else:
            print(f"❌ 发现 {total_issues} 个问题 ({len(self.errors)} 错误 + {len(self.warnings)} 警告)")
        print(f"{'=' * 60}")
        return len(self.errors)


# === 检查函数 ===

def get_actual_posts():
    """获取 posts/ 目录下所有 .html 文件"""
    files = glob.glob(os.path.join(POSTS_DIR, "*.html"))
    return {os.path.basename(f) for f in files if os.path.basename(f).startswith("2026-")}

def get_blog_articles():
    """从 blog.html 提取 articles 数组中的 URL"""
    with open(BLOG_HTML, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 articles 数组中的 url 字段
    urls = re.findall(r'url:\s*["\']posts/([^"\']+)["\']', content)
    return urls

def get_blog_entries_with_titles():
    """从 blog.html 提取 title + url 对，用于去重检查"""
    with open(BLOG_HTML, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 简单解析：找每个 { ... } 块中的 title 和 url
    entries = []
    blocks = re.findall(r'\{[^}]*title:\s*["\']([^"\']+)["\'][^}]*url:\s*["\']posts/([^"\']+)["\'][^}]*\}', content)
    for title, url in blocks:
        entries.append((title, url))
    return entries

def get_rss_items():
    """从 feed.xml 提取 item 链接"""
    with open(FEED_XML, 'r', encoding='utf-8') as f:
        content = f.read()
    
    links = re.findall(r'<link>https://sandbot\.cgfan\.com/posts/([^<]+)</link>', content)
    # 提取 lastBuildDate
    build_match = re.search(r'<lastBuildDate>([^<]+)</lastBuildDate>', content)
    build_date = build_match.group(1) if build_match else "unknown"
    
    return links, build_date

def check_orphan_posts(report):
    """检查存在文件但不在 blog.html 中的文章（仅检查近 14 天）"""
    from datetime import timedelta
    actual = get_actual_posts()
    blog_urls = set(get_blog_articles())
    
    # 将 blog url 转为文件名比较
    blog_files = set()
    for url in blog_urls:
        basename = url.split('/')[-1] if '/' in url else url
        blog_files.add(basename + '.html')
        blog_files.add(basename)
    
    # 只检查近 14 天的文章（旧文章不在 blog.html 是正常的，只保留 ~50 条）
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).strftime('%Y-%m-%d')
    recent = {f for f in actual if f[:10] >= cutoff}
    
    orphans = recent - blog_files
    if orphans:
        for f in sorted(orphans):
            report.error("孤儿文章", f"近期文件不在 blog.html 中: {f}", fixable=True)
    else:
        report.add_info(f"近 14 天 {len(recent)} 篇文章全部在 blog.html 中")

def check_ghost_entries(report):
    """检查 blog.html 中有但文件不存在的条目"""
    actual = get_actual_posts()
    blog_urls = get_blog_articles()
    
    for url in blog_urls:
        basename = url.split('/')[-1] if '/' in url else url
        filename = basename + '.html'
        if filename not in actual and basename not in actual:
            report.error("幽灵条目", f"blog.html 引用但文件不存在: {url}", fixable=True)

def check_duplicates(report):
    """检查 blog.html 中的重复条目"""
    entries = get_blog_entries_with_titles()
    url_counts = Counter(url for _, url in entries)
    
    dupes = {url: count for url, count in url_counts.items() if count > 1}
    if dupes:
        for url, count in dupes.items():
            report.error("重复条目", f"blog.html 中重复 {count} 次: {url}", fixable=True)
    else:
        report.add_info(f"blog.html 无重复条目 ({len(entries)} 个条目)")

def check_placeholders(report):
    """检查 AUDIO_FILE_PLACEHOLDER 残留"""
    for filename in sorted(get_actual_posts()):
        filepath = os.path.join(POSTS_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'AUDIO_FILE_PLACEHOLDER' in content:
            report.error("占位符残留", f"{filename} 包含 AUDIO_FILE_PLACEHOLDER", fixable=True)

def check_md_files(report):
    """检查 posts/ 目录中的 .md 文件"""
    md_files = glob.glob(os.path.join(POSTS_DIR, "*.md"))
    if md_files:
        for f in md_files:
            report.error("错误扩展名", f"posts/ 中发现 .md 文件: {os.path.basename(f)} (应为 .html)", fixable=True)

def check_v4_template(report):
    """检查近期文章的 V4 模板元素（仅 2026-07-10 后，V4 启用后）"""
    posts = sorted(get_actual_posts())
    incomplete = []
    v4_start = '2026-07-10'  # V4 模板启用的大致日期
    
    for filename in posts:
        if filename[:10] < v4_start:
            continue  # 跳过 V4 之前的旧文章
        filepath = os.path.join(POSTS_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing = [e for e in V4_ELEMENTS if e not in content]
        if missing:
            incomplete.append((filename, missing))
    
    if incomplete:
        for filename, missing in incomplete:
            report.warn("V4模板", f"{filename} 缺少: {', '.join(missing)}")
    else:
        report.add_info(f"所有 {len(posts)} 篇文章 V4 模板完整")

def check_rss_freshness(report):
    """检查 RSS lastBuildDate 是否过期"""
    rss_items, build_date = get_rss_items()
    
    if build_date == "unknown":
        report.error("RSS", "无法解析 lastBuildDate")
        return
    
    # 解析 build date
    try:
        # Format: Wed, 22 Jul 2026 11:50:26 +0000
        from email.utils import parsedate_to_datetime
        build_dt = parsedate_to_datetime(build_date)
        now = datetime.now(timezone.utc)
        age_hours = (now - build_dt).total_seconds() / 3600
        
        if age_hours > 48:
            report.error("RSS过期", f"lastBuildDate 已 {age_hours:.0f} 小时未更新 ({build_date})", fixable=True)
        elif age_hours > 24:
            report.warn("RSS", f"lastBuildDate 已 {age_hours:.0f} 小时未更新")
        else:
            report.add_info(f"RSS 最后更新: {age_hours:.1f} 小时前")
    except Exception as e:
        report.warn("RSS", f"日期解析失败: {e}")
    
    # 检查 RSS 条目数 vs 实际文章数
    actual_count = len(get_actual_posts())
    rss_count = len(rss_items)
    if rss_count < actual_count * 0.5:
        report.warn("RSS", f"RSS 只有 {rss_count} 个条目，实际有 {actual_count} 篇文章")

def check_filename_convention(report):
    """检查文件名规范"""
    posts = sorted(get_actual_posts())
    bad_names = []
    
    for filename in posts:
        # 检查日期前缀
        if not re.match(r'^\d{4}-\d{2}-\d{2}-', filename):
            bad_names.append((filename, "缺少日期前缀"))
        # 检查非 ASCII
        if any(ord(c) >= 128 for c in filename):
            bad_names.append((filename, "包含非 ASCII 字符"))
    
    if bad_names:
        for filename, reason in bad_names:
            report.warn("文件名", f"{filename}: {reason}")
    else:
        report.add_info(f"所有 {len(posts)} 个文件名规范")

def check_audio_consistency(report):
    """检查近期文章字数 >= 3000 但没有音频"""
    posts = sorted(get_actual_posts())
    cutoff = '2026-07-10'  # 只检查近期文章
    
    for filename in posts:
        if filename[:10] < cutoff:
            continue
        filepath = os.path.join(POSTS_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计中文字数
        chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        
        # 检查是否有音频播放器
        has_audio = bool(re.search(r'<audio|audio/.*\.mp3|edge-tts|mp3', content))
        
        if chars >= 3000 and not has_audio:
            report.warn("音频缺失", f"{filename}: {chars} 字但无音频播放器")

def check_single_post(report, filepath):
    """检查单篇文章的完整健康"""
    filename = os.path.basename(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 字数
    chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    report.add_info(f"字数: {chars}")
    
    # 图片
    imgs = len(re.findall(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', content))
    if imgs < 1:
        report.error("图片", f"{filename}: 无图片")
    else:
        report.add_info(f"图片: {imgs} 张")
    
    # V4 元素
    missing = [e for e in V4_ELEMENTS if e not in content]
    if missing:
        report.warn("V4模板", f"缺少: {', '.join(missing)}")
    
    # Agent 视点
    if not re.search(r'agent.?视点|Agent.?视点|agent-view', content, re.IGNORECASE):
        report.warn("内容", f"缺少 Agent 视点")
    
    # 占位符
    if 'AUDIO_FILE_PLACEHOLDER' in content:
        report.error("占位符", f"AUDIO_FILE_PLACEHOLDER 残留", fixable=True)
    
    # 音频
    has_audio = bool(re.search(r'<audio|audio/.*\.mp3', content))
    if chars >= 3000 and not has_audio:
        report.warn("音频", f"{chars} 字但无音频")


# === 自动修复 ===

def fix_placeholders(report):
    """替换 AUDIO_FILE_PLACEHOLDER"""
    fixed = 0
    for filename in sorted(get_actual_posts()):
        filepath = os.path.join(POSTS_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'AUDIO_FILE_PLACEHOLDER' in content:
            base = filename.replace('.html', '')
            audio_path = f"audio/{base}.mp3"
            # 检查音频文件是否存在
            audio_full = os.path.join(POSTS_DIR, audio_path)
            if os.path.exists(audio_full):
                content = content.replace('AUDIO_FILE_PLACEHOLDER', audio_path)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed += 1
                print(f"   ✅ {filename}: 替换为 {audio_path}")
            else:
                # 移除占位符音频播放器
                content = re.sub(r'<div[^>]*class="audio-player"[^>]*>.*?AUDIO_FILE_PLACEHOLDER.*?</div>', '', content, flags=re.DOTALL)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed += 1
                print(f"   ✅ {filename}: 移除占位符 (音频文件不存在)")
    
    if fixed:
        print(f"   共修复 {fixed} 个占位符")
    return fixed

def fix_md_files(report):
    """重命名 .md 为 .html"""
    fixed = 0
    md_files = glob.glob(os.path.join(POSTS_DIR, "*.md"))
    for f in md_files:
        new_path = f.replace('.md', '.html')
        os.rename(f, new_path)
        fixed += 1
        print(f"   ✅ {os.path.basename(f)} → {os.path.basename(new_path)}")
    return fixed


# === 主程序 ===

def main():
    report = Report()
    
    fix_mode = '--fix' in sys.argv
    single_post = None
    if '--post' in sys.argv:
        idx = sys.argv.index('--post')
        if idx + 1 < len(sys.argv):
            single_post = sys.argv[idx + 1]
    
    print("\n🔍 正在扫描博客健康状态...\n")
    
    if single_post:
        check_single_post(report, single_post)
    else:
        # 显示概览
        total_posts = len(get_actual_posts())
        blog_count = len(get_blog_articles())
        rss_items, _ = get_rss_items()
        rss_count = len(rss_items)
        report.add_info(f"总文章: {total_posts} 篇 | blog.html: {blog_count} 条 | RSS: {rss_count} 条")
        
        # 全面检查
        check_orphan_posts(report)
        check_ghost_entries(report)
        check_duplicates(report)
        check_placeholders(report)
        check_md_files(report)
        check_v4_template(report)
        check_rss_freshness(report)
        check_filename_convention(report)
        check_audio_consistency(report)
    
    # 打印报告
    error_count = report.print_report()
    
    # 自动修复
    if fix_mode and report.fixable:
        print("\n🔧 执行自动修复...")
        
        # 修复占位符
        placeholder_fixes = [m for c, m in report.fixable if '占位符' in c]
        if placeholder_fixes:
            print("\n   [占位符修复]")
            fix_placeholders(report)
        
        # 修复 .md 文件
        md_fixes = [m for c, m in report.fixable if '扩展名' in c]
        if md_fixes:
            print("\n   [扩展名修复]")
            fix_md_files(report)
        
        print("\n   ⚠️  孤儿/幽灵/重复条目需要手动修复或运行专用脚本:")
        print("      python3 scripts/update-blog.py --rebuild-all")
    
    return error_count

if __name__ == '__main__':
    errors = main()
    sys.exit(1 if errors > 0 else 0)
