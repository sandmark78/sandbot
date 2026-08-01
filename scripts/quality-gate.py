#!/usr/bin/env python3
"""
pre-publish-gate.py — 发布前质量门控 v1.0
Sandbot 每周工具脚本 · 2026-07-21

解决的问题（本周反复出现的坑）：
  1. 文章发布后 blog.html 索引未更新 → 文章"消失"
  2. RSS feed 过期 → 订阅者收不到更新
  3. V4 模板缺关键元素 → 页面结构破损
  4. 音频占位符 AUDIO_FILE_PLACEHOLDER 未替换 → 播放器报错
  5. 文件扩展名 .md 而非 .html → 404
  6. 文章字数不足 3000 字 → 不值得生成语音
  7. 图片 src 指向不存在的文件 → 破图

用法:
  python3 scripts/pre-publish-gate.py <article.html>           # 检查单篇文章
  python3 scripts/pre-publish-gate.py <article.html> --fix     # 检查并自动修复可修复项
  python3 scripts/pre-publish-gate.py --scan-all               # 扫描所有 posts/ 文章
  python3 scripts/pre-publish-gate.py <article.html> --json    # JSON 输出

退出码:
  0 = 全部通过（可以发布）
  1 = 存在阻断级错误（不可发布）
  2 = 仅警告（可发布但建议修复）
"""

import os
import sys
import re
import json
import glob
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# ── 配置 ──────────────────────────────────────────────────────────────

REPO_DIR = BLOG_ROOT
POSTS_DIR = os.path.join(REPO_DIR, "posts")
BLOG_HTML = os.path.join(REPO_DIR, "blog.html")
FEED_XML = os.path.join(REPO_DIR, "feed.xml")
AUDIO_DIR = os.path.join(POSTS_DIR, "audio")
SITE_URL = "https://sandbot.cgfan.com"

MIN_TEXT_CHARS = 3000  # 最低正文字数（生成语音的阈值）
MIN_WORD_COUNT = 1500  # 最低中文字数

# V4 模板必须元素 (regex, description, severity: error|warning)
V4_REQUIRED = [
    (r'<meta\s+[^>]*name="viewport"', "viewport meta 标签", "error"),
    (r'<meta\s+charset="UTF-8"', "charset UTF-8", "error"),
    (r'<title>[^<]+</title>', "非空 <title>", "error"),
    (r'class="site-header"', ".site-header 头部", "error"),
    (r'class="article-title"', ".article-title 标题", "error"),
    (r'class="article-meta"', ".article-meta 元信息", "error"),
    (r'class="(post-body|article-body|article-content|container)"', "文章主体区域", "error"),
    (r'class="site-footer"', ".site-footer 底部", "error"),
]

V4_RECOMMENDED = [
    (r'class="article-subtitle"', ".article-subtitle 副标题", "warning"),
    (r'class="quick-glance"', ".quick-glance 速览框", "warning"),
    (r'<nav[^>]*>', "<nav> 导航栏", "warning"),
    (r'class="overline"', ".overline 分类标签", "warning"),
]

# 音频占位符模式
AUDIO_PLACEHOLDERS = [
    r'AUDIO_FILE_PLACEHOLDER',
    r'src="audio/placeholder',
    r'src="[^"]*PLACEHOLDER[^"]*"',
]

# 文件名规范：日期前缀 YYYY-MM-DD
FILENAME_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}-')


# ── 数据结构 ──────────────────────────────────────────────────────────

class GateResult:
    def __init__(self, filepath):
        self.filepath = filepath
        self.errors = []      # 阻断级：不可发布
        self.warnings = []    # 建议级：可发布但应修复
        self.info = []        # 信息级

    @property
    def passed(self):
        return len(self.errors) == 0

    @property
    def exit_code(self):
        if self.errors:
            return 1
        if self.warnings:
            return 2
        return 0

    def to_dict(self):
        return {
            "file": self.filepath,
            "passed": self.passed,
            "exit_code": self.exit_code,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
        }


# ── 检查函数 ──────────────────────────────────────────────────────────

def check_file_extension(result, content):
    """检查 1: 文件扩展名必须是 .html"""
    if not result.filepath.endswith('.html'):
        result.errors.append(
            f"文件扩展名错误: {os.path.basename(result.filepath)} 应为 .html"
        )
        result.info.append("提示: mv {f} {f}.html".format(
            f=os.path.basename(result.filepath)))


def check_filename_convention(result, content):
    """检查 2: 文件名应符合日期前缀规范"""
    basename = os.path.basename(result.filepath)
    if not FILENAME_PATTERN.match(basename):
        result.warnings.append(
            f"文件名不符合规范: {basename} (建议: YYYY-MM-DD-slug.html)"
        )


def check_v4_template(result, content):
    """检查 3: V4 模板必须元素"""
    for pattern, desc, severity in V4_REQUIRED:
        if not re.search(pattern, content):
            msg = f"V4 模板缺失: {desc}"
            if severity == "error":
                result.errors.append(msg)
            else:
                result.warnings.append(msg)

    for pattern, desc, severity in V4_RECOMMENDED:
        if not re.search(pattern, content):
            msg = f"V4 模板建议: {desc}"
            if severity == "error":
                result.errors.append(msg)
            else:
                result.warnings.append(msg)


def check_word_count(result, content):
    """检查 4: 文章字数"""
    # 去除 HTML 标签，提取纯文本
    text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', '', text)

    char_count = len(text)
    # 粗略中文字数统计（中文字符）
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))

    result.info.append(f"字数统计: {char_count} 字符, {chinese_chars} 中文字")

    if char_count < MIN_TEXT_CHARS:
        result.errors.append(
            f"文章字数不足: {char_count} 字符 (最低要求 {MIN_TEXT_CHARS})"
        )
    if chinese_chars < MIN_WORD_COUNT:
        result.warnings.append(
            f"中文字数偏少: {chinese_chars} 字 (建议 ≥{MIN_WORD_COUNT})"
        )


def check_audio(result, content):
    """检查 5: 音频文件"""
    # 检查是否有音频占位符
    for pattern in AUDIO_PLACEHOLDERS:
        if re.search(pattern, content):
            result.errors.append(
                f"音频占位符未替换: 发现 '{pattern}' 在 HTML 中"
            )
            break

    # 检查是否有 audio 标签
    has_audio_tag = bool(re.search(r'<audio[^>]*>', content))
    if has_audio_tag:
        # 提取 audio src
        src_match = re.search(r'<audio[^>]*>.*?<source[^>]*src="([^"]+)"', content, re.DOTALL)
        if not src_match:
            src_match = re.search(r'<audio[^>]*src="([^"]+)"', content)

        if src_match:
            audio_src = src_match.group(1)
            if 'PLACEHOLDER' not in audio_src:
                # 检查音频文件是否真实存在
                if audio_src.startswith('audio/'):
                    audio_path = os.path.join(POSTS_DIR, audio_src)
                    if not os.path.exists(audio_path):
                        result.errors.append(
                            f"音频文件不存在: {audio_src}"
                        )
                    else:
                        size_mb = os.path.getsize(audio_path) / (1024 * 1024)
                        result.info.append(f"音频文件: {audio_src} ({size_mb:.1f}MB)")
    else:
        result.warnings.append("文章没有 <audio> 标签（将无语音版本）")


def check_images(result, content):
    """检查 6: 图片引用"""
    # 提取所有 img src
    img_srcs = re.findall(r'<img[^>]*src="([^"]+)"', content)
    # 过滤外部 URL
    local_imgs = [s for s in img_srcs if not s.startswith(('http://', 'https://', 'data:'))]

    if not local_imgs and not re.findall(r'<img[^>]*', content):
        result.warnings.append("文章没有图片（建议至少添加 1 张题图）")
        return

    for img_src in local_imgs:
        if img_src.startswith('/'):
            img_path = os.path.join(REPO_DIR, img_src.lstrip('/'))
        else:
            img_path = os.path.join(POSTS_DIR, img_src)

        if not os.path.exists(img_path):
            result.errors.append(f"图片文件不存在: {img_src}")
        else:
            result.info.append(f"图片: {img_src} ✓")


def check_blog_index(result, content):
    """检查 7: blog.html 索引是否包含此文章"""
    if not os.path.exists(BLOG_HTML):
        result.warnings.append("blog.html 不存在")
        return

    basename = os.path.basename(result.filepath)
    with open(BLOG_HTML, 'r', encoding='utf-8') as f:
        blog_content = f.read()

    if basename not in blog_content:
        result.errors.append(
            f"blog.html 索引未包含此文章: {basename}"
        )
        result.info.append("修复: python3 scripts/post-publish-audit.py --fix-blog")


def check_rss_freshness(result, content):
    """检查 8: RSS feed 是否近期更新"""
    if not os.path.exists(FEED_XML):
        result.warnings.append("feed.xml 不存在")
        return

    basename = os.path.basename(result.filepath)
    with open(FEED_XML, 'r', encoding='utf-8') as f:
        feed_content = f.read()

    if basename not in feed_content:
        result.warnings.append(
            f"RSS feed 未包含此文章: {basename}"
        )
        result.info.append("修复: python3 scripts/post-publish-audit.py --fix-rss")


def check_html_validity(result, content):
    """检查 9: 基本 HTML 完整性"""
    # 检查 </html> 闭合
    if '</html>' not in content:
        result.errors.append("HTML 缺少 </html> 闭合标签")

    # 检查 </body> 闭合
    if '</body>' not in content:
        result.errors.append("HTML 缺少 </body> 闭合标签")

    # 检查是否有未闭合的常见标签
    for tag in ['div', 'section', 'article', 'header', 'footer', 'nav']:
        opens = len(re.findall(f'<{tag}[\\s>]', content))
        closes = len(re.findall(f'</{tag}>', content))
        if opens != closes:
            result.warnings.append(
                f"<{tag}> 标签不匹配: {opens} 开 / {closes} 闭"
            )


# ── 自动修复 ──────────────────────────────────────────────────────────

def auto_fix(result):
    """尝试自动修复可修复的问题"""
    fixed = []

    # 修复 1: 文件扩展名 .md → .html
    if result.filepath.endswith('.md'):
        new_path = result.filepath[:-3] + '.html'
        os.rename(result.filepath, new_path)
        fixed.append(f"重命名: {os.path.basename(result.filepath)} → {os.path.basename(new_path)}")
        result.filepath = new_path

    # 修复 2: 替换音频占位符
    if os.path.exists(result.filepath):
        with open(result.filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        basename_no_ext = os.path.splitext(os.path.basename(result.filepath))[0]
        expected_audio = f"audio/{basename_no_ext}.mp3"
        audio_full_path = os.path.join(POSTS_DIR, expected_audio)

        if 'AUDIO_FILE_PLACEHOLDER' in content and os.path.exists(audio_full_path):
            content = content.replace('AUDIO_FILE_PLACEHOLDER', expected_audio)
            with open(result.filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            fixed.append(f"替换音频占位符 → {expected_audio}")

    # 修复 3: blog.html 索引
    if any("blog.html 索引未包含" in e for e in result.errors):
        try:
            subprocess.run(
                ["python3", os.path.join(os.path.dirname(__file__), "post-publish-audit.py"), "--fix-blog"],
                capture_output=True, text=True, timeout=30
            )
            fixed.append("运行 post-publish-audit.py --fix-blog")
        except Exception as e:
            fixed.append(f"blog.html 修复失败: {e}")

    return fixed


# ── 主逻辑 ────────────────────────────────────────────────────────────

def run_gate(filepath):
    """对单篇文章运行质量门控"""
    filepath = os.path.abspath(filepath)
    result = GateResult(filepath)

    if not os.path.exists(filepath):
        result.errors.append(f"文件不存在: {filepath}")
        return result

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 运行所有检查
    check_file_extension(result, content)
    check_filename_convention(result, content)
    check_v4_template(result, content)
    check_word_count(result, content)
    check_audio(result, content)
    check_images(result, content)
    check_blog_index(result, content)
    check_rss_freshness(result, content)
    check_html_validity(result, content)

    return result


def scan_all_posts():
    """扫描 posts/ 目录下所有文章"""
    if not os.path.exists(POSTS_DIR):
        print(f"❌ posts 目录不存在: {POSTS_DIR}")
        return 1

    all_html = sorted(glob.glob(os.path.join(POSTS_DIR, "*.html")))
    # 只检查日期前缀的文章文件 (YYYY-MM-DD-*.html)，排除 xia-* 等非博客文件
    html_files = [f for f in all_html if FILENAME_PATTERN.match(os.path.basename(f))]
    # 只检查最近 7 天的文件
    cutoff = datetime.now().timestamp() - 7 * 86400
    recent_files = [f for f in html_files if os.path.getmtime(f) > cutoff]

    if not recent_files:
        print("ℹ️  最近 7 天没有文章文件")
        return 0

    print(f"🔍 扫描 {len(recent_files)} 篇近期文章...\n")

    total_errors = 0
    total_warnings = 0

    for filepath in recent_files:
        result = run_gate(filepath)
        basename = os.path.basename(filepath)

        if result.passed and not result.warnings:
            print(f"  ✅ {basename}")
        else:
            status = "❌" if result.errors else "⚠️"
            print(f"  {status} {basename}")
            for err in result.errors:
                print(f"     🔴 {err}")
            for warn in result.warnings:
                print(f"     🟡 {warn}")

        total_errors += len(result.errors)
        total_warnings += len(result.warnings)

    print(f"\n{'─' * 50}")
    print(f"📊 总计: {len(recent_files)} 篇文章, {total_errors} 错误, {total_warnings} 警告")

    return 1 if total_errors else (2 if total_warnings else 0)


def print_report(result, fix_mode=False):
    """打印检查报告"""
    basename = os.path.basename(result.filepath)
    print(f"\n{'═' * 60}")
    print(f"📋 发布前质量门控 — {basename}")
    print(f"{'═' * 60}")

    if result.errors:
        print(f"\n❌ 阻断级错误 ({len(result.errors)}):")
        for i, err in enumerate(result.errors, 1):
            print(f"   {i}. {err}")

    if result.warnings:
        print(f"\n⚠️  建议修复 ({len(result.warnings)}):")
        for i, warn in enumerate(result.warnings, 1):
            print(f"   {i}. {warn}")

    if result.info:
        print(f"\nℹ️  信息:")
        for info in result.info:
            print(f"   • {info}")

    if fix_mode:
        print(f"\n🔧 尝试自动修复...")
        fixed = auto_fix(result)
        if fixed:
            for f in fixed:
                print(f"   ✅ {f}")
        else:
            print("   (无可自动修复项)")

    print(f"\n{'─' * 60}")
    if result.passed:
        if result.warnings:
            print(f"🟡 结果: 可通过（有 {len(result.warnings)} 个建议）")
        else:
            print("🟢 结果: 全部通过，可以发布！")
    else:
        print(f"🔴 结果: 未通过（{len(result.errors)} 个错误需修复）")
    print(f"{'═' * 60}\n")


def main():
    parser = argparse.ArgumentParser(description="发布前质量门控")
    parser.add_argument("file", nargs="?", help="要检查的文章文件")
    parser.add_argument("--fix", action="store_true", help="检查并自动修复")
    parser.add_argument("--scan-all", action="store_true", help="扫描所有近期文章")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--slot", choices=["morning", "noon", "afternoon", "evening", "hot"], 
                        help="文章时段（用于调整字数要求）")
    args = parser.parse_args()
    
    # --slot 参数兼容（Cron 大量引用）
    if args.slot:
        print(f"📋 时段: {args.slot}")

    if args.scan_all:
        sys.exit(scan_all_posts())

    if not args.file:
        # 没指定文件，找最新的
        if not os.path.exists(POSTS_DIR):
            print(f"❌ posts 目录不存在: {POSTS_DIR}")
            sys.exit(1)
        html_files = sorted(glob.glob(os.path.join(POSTS_DIR, "*.html")),
                           key=os.path.getmtime, reverse=True)
        if not html_files:
            print("❌ posts/ 下没有文章")
            sys.exit(1)
        args.file = html_files[0]
        print(f"ℹ️  未指定文件，检查最新文章: {os.path.basename(args.file)}")

    filepath = args.file
    if not os.path.isabs(filepath):
        filepath = os.path.join(REPO_DIR, filepath)

    result = run_gate(filepath)

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print_report(result, fix_mode=args.fix)

    sys.exit(result.exit_code)


if __name__ == "__main__":
    main()
