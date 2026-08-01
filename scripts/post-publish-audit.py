#!/usr/bin/env python3
"""
post-publish-audit.py — 文章发布后完整性审计 v1.0
Sandbot 每周工具脚本 · 2026-07-16

解决的问题（本周反复出现的坑）：
  1. 文章保存到错误路径 (blog/posts/ 而不是 posts/) — 07-14
  2. V4 模板不合规（暗色主题、缺少结构元素）— 07-11, 07-13
  3. blog.html / RSS 未更新 — 多次
  4. TTS 音频未生成或路径错误 — 07-14
  5. 发布后只输出相对路径 — 07-13
  6. 文章字数不足 — 多次

用法:
  python3 scripts/post-publish-audit.py                          # 审计最近发布的文章
  python3 scripts/post-publish-audit.py --file posts/xxx.html    # 审计指定文章
  python3 scripts/post-publish-audit.py --scan                   # 扫描所有近期文章
  python3 scripts/post-publish-audit.py --fix-rss                # 自动修复 RSS
  python3 scripts/post-publish-audit.py --fix-blog               # 自动修复 blog.html 索引
  python3 scripts/post-publish-audit.py --fix-all                # 自动修复所有问题
"""

import os
import sys
import re
import json
import glob
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from html.parser import HTMLParser
# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# ── 配置 ──────────────────────────────────────────────────────────────

REPO_DIR = BLOG_ROOT
POSTS_DIR = os.path.join(REPO_DIR, "posts")
BLOG_HTML = os.path.join(REPO_DIR, "blog.html")
FEED_XML = os.path.join(REPO_DIR, "feed.xml")
AUDIO_DIR = os.path.join(POSTS_DIR, "audio")
SITE_URL = "https://sandbot.cgfan.com"

# V4 模板必须元素 (selector, description, severity)
V4_REQUIRED = [
    (r'<meta\s+name="viewport"', "viewport meta", "error"),
    (r'<meta\s+charset="UTF-8"', "charset UTF-8", "error"),
    (r'<title>[^<]+</title>', "非空 <title>", "error"),
    (r'class="site-header"', ".site-header", "error"),
    (r'class="overline"', ".overline 标签", "error"),
    (r'<nav[^>]*>', "<nav> 导航栏", "error"),
    (r'class="article-title"', ".article-title", "error"),
    (r'class="article-meta"', ".article-meta", "error"),
    (r'class="(post-body|article-body|article-content)"', "文章主体区域", "error"),
    (r'class="site-footer"', ".site-footer", "error"),
]

V4_RECOMMENDED = [
    (r'class="article-subtitle"', ".article-subtitle", "warning"),
    (r'class="label-category"', ".label-category 分类标签", "warning"),
    (r'class="quick-glance"', ".quick-glance 速览", "warning"),
    (r'fonts\.googleapis\.com', "Google Fonts", "warning"),
    (r'@media', "@media 移动端适配", "warning"),
]

# V4 模板配色（暖色调）
V4_COLORS = {
    "bg": "#faf8f5",
    "bg_warm": "#f5f1eb",
    "bg_card": "#fffdf9",
    "accent": "#7a9e7e",
    "accent_warm": "#c4956a",
    "text": "#3d3d3d",
    "border": "#e8e4de",
}

# 禁止出现的暗色主题色
FORBIDDEN_COLORS = [
    "#1a1a2e", "#16213e", "#0f3460", "#1b1b2f",
    "#0a0a0a", "#111111", "#1a1a1a", "#2d2d2d",
]

MIN_WORD_COUNT = 300


# ── 工具函数 ──────────────────────────────────────────────────────────

class AuditResult:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def ok(self, msg):
        self.passed.append(msg)

    @property
    def passed_count(self):
        return len(self.passed)

    @property
    def total_count(self):
        return len(self.passed) + len(self.errors) + len(self.warnings)

    def summary(self):
        e = len(self.errors)
        w = len(self.warnings)
        p = len(self.passed)
        return f"✅ {p} 通过 | ❌ {e} 错误 | ⚠️ {w} 警告"


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return None


def extract_text_from_html(html):
    """提取 HTML 中的纯文本（用于字数统计）"""
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def count_chinese_words(text):
    """统计中文字数（中文按字计，英文按词计）"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    return chinese_chars + english_words


# ── 检查项 ────────────────────────────────────────────────────────────

def check_file_path(filepath, result):
    """检查 1: 文件路径是否正确"""
    rel = os.path.relpath(filepath, REPO_DIR)

    # 必须在 posts/ 目录下
    if rel.startswith("blog/posts/"):
        result.error(f"文件路径错误：在 blog/posts/ 而不是 posts/ ({rel})")
        return False
    elif rel.startswith("posts/"):
        result.ok(f"文件路径正确：{rel}")
        return True
    else:
        result.warn(f"文件不在 posts/ 目录：{rel}")
        return False


def check_v4_template(html, filepath, result):
    """检查 2: V4 模板合规性"""
    filename = os.path.basename(filepath)

    # 必须元素
    for selector, desc, severity in V4_REQUIRED:
        if re.search(selector, html, re.DOTALL):
            result.ok(f"V4 元素存在：{desc}")
        else:
            msg = f"缺少 V4 必须元素：{desc}"
            if severity == "error":
                result.error(msg)
            else:
                result.warn(msg)

    # 推荐元素
    for selector, desc, severity in V4_RECOMMENDED:
        if re.search(selector, html, re.DOTALL):
            result.ok(f"V4 推荐元素：{desc}")
        else:
            result.warn(f"缺少 V4 推荐元素：{desc}")

    # 禁止的暗色主题
    for color in FORBIDDEN_COLORS:
        if color.lower() in html.lower():
            result.error(f"发现禁止的暗色主题色 {color}（V4 模板是暖色调 #faf8f5）")


def check_word_count(html, filepath, result):
    """检查 3: 文章字数"""
    text = extract_text_from_html(html)
    word_count = count_chinese_words(text)

    if word_count < MIN_WORD_COUNT:
        result.error(f"字数不足：{word_count} 字（最低要求 {MIN_WORD_COUNT}）")
    else:
        result.ok(f"字数达标：{word_count} 字")

    return word_count


def check_blog_html(filepath, result):
    """检查 4: blog.html 是否已更新"""
    filename = os.path.basename(filepath)

    if not os.path.exists(BLOG_HTML):
        result.error(f"blog.html 不存在")
        return

    blog_content = read_file(BLOG_HTML)
    if blog_content is None:
        result.error("无法读取 blog.html")
        return

    if filename in blog_content:
        result.ok(f"blog.html 已包含 {filename}")
    else:
        result.error(f"blog.html 未包含 {filename}（需要更新）")


def check_rss(filepath, result):
    """检查 5: RSS feed 是否已更新"""
    filename = os.path.basename(filepath)

    if not os.path.exists(FEED_XML):
        result.warn("feed.xml 不存在")
        return

    feed_content = read_file(FEED_XML)
    if feed_content is None:
        result.warn("无法读取 feed.xml")
        return

    if filename in feed_content:
        result.ok(f"feed.xml 已包含 {filename}")
    else:
        result.error(f"feed.xml 未包含 {filename}（RSS 未更新）")


def check_tts_audio(filepath, result):
    """检查 6: TTS 音频是否已生成"""
    filename = os.path.basename(filepath)
    base_name = filename.replace(".html", "")

    # 查找对应的音频文件
    audio_patterns = [
        os.path.join(AUDIO_DIR, f"{base_name}.mp3"),
        os.path.join(AUDIO_DIR, f"*{base_name[:30]}*.mp3"),
    ]

    audio_found = False
    for pattern in audio_patterns:
        matches = glob.glob(pattern)
        if matches:
            audio_found = True
            for m in matches:
                size = os.path.getsize(m)
                if size < 1000:
                    result.warn(f"音频文件过小 ({size} bytes)：{os.path.basename(m)}")
                else:
                    result.ok(f"TTS 音频存在：{os.path.basename(m)} ({size//1024}KB)")
            break

    if not audio_found:
        result.warn(f"未找到 TTS 音频文件（{base_name}.mp3）")


def check_internal_links(html, filepath, result):
    """检查 7: 内部链接格式"""
    # 检查是否使用了旧域名
    old_domain = "sandmark78.github.io/sandbot"
    if old_domain in html:
        result.error(f"使用了旧域名 {old_domain}，应使用 {SITE_URL}")

    # 检查相对路径链接
    href_pattern = r'href="([^"]*)"'
    hrefs = re.findall(href_pattern, html)

    broken_internal = []
    for href in hrefs:
        if href.startswith("http"):
            continue  # 外部链接不检查
        if href.startswith("#") or href.startswith("mailto:"):
            continue  # 锚点和邮件不检查
        if href.startswith("https://") or href.startswith("http://"):
            continue

        # 检查内部文件链接是否存在
        abs_path = os.path.join(os.path.dirname(filepath), href)
        if not os.path.exists(abs_path) and not href.startswith("/"):
            # 尝试从 posts 目录解析
            abs_path = os.path.join(POSTS_DIR, href.lstrip("/"))
            if not os.path.exists(abs_path):
                broken_internal.append(href)

    if broken_internal:
        for link in broken_internal[:5]:
            result.warn(f"内部链接可能无效：{link}")
    else:
        result.ok("内部链接格式正确")


def check_full_url_output(filepath, result):
    """检查 8: 完整 URL 可生成性"""
    filename = os.path.basename(filepath)
    expected_url = f"{SITE_URL}/posts/{filename}"
    result.ok(f"完整 URL: {expected_url}")


def check_title_match(html, filepath, result):
    """检查 9: 文件名与标题一致性"""
    filename = os.path.basename(filepath)
    title_match = re.search(r'<title>([^<]+)</title>', html)

    if not title_match:
        result.error("缺少 <title> 标签")
        return

    title = title_match.group(1).strip()
    # 去掉 " — Sandbot Blog" 后缀
    title_clean = re.sub(r'\s*—\s*Sandbot Blog.*$', '', title).strip()

    if len(title_clean) < 5:
        result.warn(f"标题过短：'{title_clean}'")
    else:
        result.ok(f"标题正常：'{title_clean}'")


# ── 主审计流程 ────────────────────────────────────────────────────────

def audit_article(filepath, verbose=True):
    """审计单篇文章"""
    result = AuditResult()
    filename = os.path.basename(filepath)

    if verbose:
        print(f"\n{'='*60}")
        print(f"📄 审计文章：{filename}")
        print(f"{'='*60}")

    # 读取文件
    html = read_file(filepath)
    if html is None:
        result.error(f"无法读取文件：{filepath}")
        return result

    # 执行所有检查
    checks = [
        ("文件路径", lambda: check_file_path(filepath, result)),
        ("V4 模板", lambda: check_v4_template(html, filepath, result)),
        ("文章字数", lambda: check_word_count(html, filepath, result)),
        ("blog.html", lambda: check_blog_html(filepath, result)),
        ("RSS feed", lambda: check_rss(filepath, result)),
        ("TTS 音频", lambda: check_tts_audio(filepath, result)),
        ("内部链接", lambda: check_internal_links(html, filepath, result)),
        ("URL 格式", lambda: check_full_url_output(filepath, result)),
        ("标题一致性", lambda: check_title_match(html, filepath, result)),
    ]

    for name, check_fn in checks:
        try:
            check_fn()
        except Exception as e:
            result.error(f"检查 {name} 时出错：{e}")

    # 输出结果
    if verbose:
        print(f"\n{'─'*40}")
        for msg in result.passed:
            print(f"  ✅ {msg}")
        for msg in result.warnings:
            print(f"  ⚠️  {msg}")
        for msg in result.errors:
            print(f"  ❌ {msg}")
        print(f"\n{'─'*40}")
        print(f"  📊 {result.summary()}")

    return result


def get_recent_articles(days=3, limit=10):
    """获取最近发布的文章"""
    articles = []
    cutoff = datetime.now() - timedelta(days=days)

    # 扫描 posts 目录
    for f in glob.glob(os.path.join(POSTS_DIR, "*.html")):
        mtime = datetime.fromtimestamp(os.path.getmtime(f))
        if mtime >= cutoff:
            articles.append((f, mtime))

    # 按时间倒序
    articles.sort(key=lambda x: x[1], reverse=True)
    return [a[0] for a in articles[:limit]]


def scan_all_recent(days=3):
    """扫描近期所有文章"""
    articles = get_recent_articles(days=days)

    if not articles:
        print(f"❌ 最近 {days} 天没有找到文章")
        return

    print(f"\n🔍 扫描最近 {days} 天的 {len(articles)} 篇文章\n")

    total_errors = 0
    total_warnings = 0
    total_passed = 0

    for filepath in articles:
        result = audit_article(filepath, verbose=True)
        total_errors += len(result.errors)
        total_warnings += len(result.warnings)
        total_passed += len(result.passed)

    # 总结
    print(f"\n{'='*60}")
    print(f"📊 总体审计结果")
    print(f"{'='*60}")
    print(f"  文章数：{len(articles)}")
    print(f"  ✅ 通过：{total_passed}")
    print(f"  ❌ 错误：{total_errors}")
    print(f"  ⚠️  警告：{total_warnings}")

    if total_errors == 0:
        print(f"\n  🎉 所有文章审计通过！")
    else:
        print(f"\n  🔧 需要修复 {total_errors} 个错误")

    return total_errors


def fix_rss():
    """自动修复 RSS（调用 rss-auto-writer.sh）"""
    script = os.path.join(REPO_DIR, "scripts", "rss-auto-writer.sh")
    if os.path.exists(script):
        print("🔧 正在修复 RSS...")
        subprocess.run(["bash", script], cwd=REPO_DIR)
    else:
        print(f"❌ RSS 修复脚本不存在：{script}")


def fix_blog():
    """自动修复 blog.html 的文章索引"""
    print("🔧 正在修复 blog.html 索引...")
    
    # 获取所有文章文件
    articles = []
    for f in glob.glob(os.path.join(POSTS_DIR, "*.html")):
        filename = os.path.basename(f)
        html = read_file(f)
        if html is None:
            continue
        
        # 提取标题
        title_match = re.search(r'<title>([^<]+)</title>', html)
        if not title_match:
            continue
        
        title = title_match.group(1).strip()
        # 去掉 " — Sandbot Blog" 后缀
        title_clean = re.sub(r'\s*—\s*Sandbot Blog.*$', '', title).strip()
        
        # 从文件名提取日期和标签
        # 尝试多种格式：
        # 1. 2026-07-20-morning-xxx.html
        # 2. 2026-07-20-xxx.html
        # 3. xxx-2026.html (年份在末尾)
        # 4. 其他格式（使用文件修改时间）
        
        date = None
        tag = '热点'
        
        # 格式1: 2026-07-20-morning-xxx.html
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})-(morning|noon|afternoon|hot|night)', filename)
        if date_match:
            date = date_match.group(1)
            time_type = date_match.group(2)
            tag_map = {
                'morning': '早鸟',
                'noon': '午间',
                'afternoon': '下午',
                'hot': '热点',
                'night': '晚间'
            }
            tag = tag_map.get(time_type, '热点')
        
        # 格式2: 2026-07-20-xxx.html
        if not date:
            date_match = re.match(r'(\d{4}-\d{2}-\d{2})-', filename)
            if date_match:
                date = date_match.group(1)
        
        # 格式3: xxx-2026.html (年份在末尾，但没有具体日期)
        if not date:
            year_match = re.search(r'-(\d{4})\.html$', filename)
            if year_match:
                # 只有年份，使用 git log 获取完整日期
                if os.path.exists(f):
                    try:
                        result = subprocess.run(
                            ['git', 'log', '--format=%ai', '--follow', '--', f],
                            capture_output=True, text=True, cwd=REPO_DIR
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            first_commit_date = result.stdout.strip().split('\n')[-1]
                            date = first_commit_date.split(' ')[0]
                        else:
                            # 如果 git log 失败，使用文件修改时间
                            mtime = datetime.fromtimestamp(os.path.getmtime(f))
                            date = f"{year_match.group(1)}-{mtime.month:02d}-{mtime.day:02d}"
                    except Exception as e:
                        # 如果出错，使用文件修改时间
                        mtime = datetime.fromtimestamp(os.path.getmtime(f))
                        date = f"{year_match.group(1)}-{mtime.month:02d}-{mtime.day:02d}"
        
        # 格式4: 其他格式，使用 git log 获取首次提交时间
        if not date:
            if os.path.exists(f):
                try:
                    # 使用 git log 获取文件的首次提交时间
                    result = subprocess.run(
                        ['git', 'log', '--format=%ai', '--follow', '--', f],
                        capture_output=True, text=True, cwd=REPO_DIR
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        # 获取最后一次提交（首次提交）
                        first_commit_date = result.stdout.strip().split('\n')[-1]
                        # 格式: 2026-05-05 02:03:22 +0000
                        date = first_commit_date.split(' ')[0]
                    else:
                        # 如果 git log 失败，使用文件修改时间
                        mtime = datetime.fromtimestamp(os.path.getmtime(f))
                        date = mtime.strftime('%Y-%m-%d')
                except Exception as e:
                    # 如果出错，使用文件修改时间
                    mtime = datetime.fromtimestamp(os.path.getmtime(f))
                    date = mtime.strftime('%Y-%m-%d')
        
        # 提取副标题
        subtitle_match = re.search(r'<p class="article-subtitle">(.*?)</p>', html)
        subtitle = subtitle_match.group(1) if subtitle_match else ""
        
        articles.append({
            'title': f'[{tag}] {title_clean}',
            'subtitle': subtitle,
            'filename': filename,
            'date': date,
            'tag': tag
        })
    
    # 按日期倒序排序
    articles.sort(key=lambda x: x['date'], reverse=True)
    
    # 读取 blog.html
    blog_content = read_file(BLOG_HTML)
    if blog_content is None:
        print("❌ 无法读取 blog.html")
        return
    
    # 构建新的 articles 数组
    new_entries = []
    for article in articles[:50]:  # 只保留最近 50 篇
        url_filename = article['filename'].replace('.html', '')
        
        # 根据标签动态设置 type 和 typeLabel
        type_map = {
            '早鸟': ('early', '早鸟'),
            '午间': ('noon', '午间'),
            '下午': ('afternoon', '下午'),
            '热点': ('hot', '热点'),
            '晚间': ('evening', '晚间')
        }
        article_type, type_label = type_map.get(article['tag'], ('hot', '热点'))
        
        # 转义特殊字符
        title_escaped = article['title'].replace('"', '\\"').replace('"', '\\u201c').replace('"', '\\u201d')
        subtitle_escaped = article['subtitle'].replace('"', '\\"').replace('"', '\\u201c').replace('"', '\\u201d')
        
        entry = f'''  {{
    title: "{title_escaped}",
    type: "{article_type}",
    typeLabel: "{type_label}",
    tag: "{article['tag']}",
    date: "{article['date']}",
    url: "posts/{url_filename}",
    excerpt: "{subtitle_escaped}",
    duration: "6 分钟",
    access: "free"
  }}'''
        new_entries.append(entry)
    
    # 替换 articles 数组
    new_articles_str = ',\n'.join(new_entries)
    pattern = r'const articles = \[.*?\];'
    replacement = f'const articles = [\n{new_articles_str}\n];'
    new_blog_content = re.sub(pattern, replacement, blog_content, flags=re.DOTALL)
    
    # 写回文件
    with open(BLOG_HTML, 'w', encoding='utf-8') as f:
        f.write(new_blog_content)
    
    print(f"✅ 已更新 blog.html，包含 {len(new_entries)} 篇文章")


def fix_all():
    """自动修复所有问题"""
    print("🔧 正在修复所有问题...")
    fix_blog()
    fix_rss()
    print("✅ 所有修复完成")


def main():
    parser = argparse.ArgumentParser(description="文章发布后完整性审计")
    parser.add_argument("--file", help="审计指定文章")
    parser.add_argument("--scan", action="store_true", help="扫描所有近期文章")
    parser.add_argument("--days", type=int, default=3, help="扫描天数范围 (默认 3)")
    parser.add_argument("--fix-rss", action="store_true", help="自动修复 RSS")
    parser.add_argument("--fix-blog", action="store_true", help="自动修复 blog.html 索引")
    parser.add_argument("--fix-all", action="store_true", help="自动修复所有问题")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    if args.fix_all:
        fix_all()
        return

    if args.fix_blog:
        fix_blog()
        return

    if args.fix_rss:
        fix_rss()
        return

    if args.file:
        filepath = args.file
        if not os.path.isabs(filepath):
            filepath = os.path.join(REPO_DIR, filepath)
        if not os.path.exists(filepath):
            print(f"❌ 文件不存在：{filepath}")
            sys.exit(1)
        result = audit_article(filepath)
        sys.exit(1 if result.errors else 0)

    if args.scan:
        errors = scan_all_recent(days=args.days)
        sys.exit(1 if errors else 0)

    # 默认：审计最近的文章
    articles = get_recent_articles(days=1, limit=3)
    if not articles:
        print("❌ 最近没有找到文章")
        sys.exit(0)

    total_errors = 0
    for filepath in articles:
        result = audit_article(filepath)
        total_errors += len(result.errors)

    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
