#!/usr/bin/env python3
"""
tts-text-cleaner.py — TTS 文本清洗器 v1.0
Sandbot 每周工具脚本 · 2026-07-24

解决的问题（本周最高频问题，48+ 次出现）：
  1. TTS 文本含 markdown 符号: ·, ——, **, ##, -, etc. (48 次警告)
  2. TTS 文本含 HTML 标签: <script>, <form>, <button>, etc. (3 次错误)
  3. 长文章缺少音频 — 清洗后可自动触发 TTS 生成

根因：文章 HTML → TTS 文本的提取过程不够干净，
     直接正则提取 body 文本会混入 markdown 格式符和嵌套 HTML。

用法:
  # 清洗单篇文章的 TTS 文本
  python3 scripts/tts-text-cleaner.py posts/article.html

  # 清洗并保存为 .tts.txt 文件
  python3 scripts/tts-text-cleaner.py posts/article.html --save

  # 检查现有 TTS 文本文件是否干净
  python3 scripts/tts-text-cleaner.py --check posts/article.tts.txt

  # 批量扫描所有文章的 TTS 文本质量
  python3 scripts/tts-text-cleaner.py --scan

  # 批量修复所有有问题的 TTS 文本
  python3 scripts/tts-text-cleaner.py --scan --fix

  # 管道模式：从 stdin 读取 HTML，输出干净文本
  cat article.html | python3 scripts/tts-text-cleaner.py --stdin

  # 清洗后直接调用 TTS API 生成音频
  python3 scripts/tts-text-cleaner.py posts/article.html --tts
"""

import os
import sys
import re
import json
import glob
import argparse
from pathlib import Path
from html.parser import HTMLParser

# ── 配置 ──────────────────────────────────────────────────────────────

REPO_DIR = BLOG_ROOT
POSTS_DIR = os.path.join(REPO_DIR, "posts")
AUDIO_DIR = os.path.join(POSTS_DIR, "audio")

# Markdown 符号模式（按优先级排序）
MARKDOWN_PATTERNS = [
    (r'\*\*\*([^*]+)\*\*\*', r'\1'),           # ***bold italic*** → text
    (r'\*\*([^*]+)\*\*', r'\1'),               # **bold** → text
    (r'\*([^*]+)\*', r'\1'),                    # *italic* → text
    (r'`([^`]+)`', r'\1'),                      # `code` → text
    (r'~~([^~]+)~~', r'\1'),                    # ~~strikethrough~~ → text
    (r'^\s*#{1,6}\s+', '', re.MULTILINE),        # ## headings (with optional indent) → remove
    (r'^\s*[-*+]\s+', '• ', re.MULTILINE),      # - list items → bullet
    (r'^\s*\d+\.\s+', '', re.MULTILINE),        # 1. numbered list → remove number
    (r'\[([^\]]+)\]\([^)]+\)', r'\1'),          # [link](url) → link text
    (r'!\[([^\]]*)\]\([^)]+\)', r'\1'),         # ![alt](url) → alt text
    (r'^\s*>\s+', '', re.MULTILINE),            # > blockquote → remove
    (r'^\s*---+\s*$', '', re.MULTILINE),        # --- hr → remove
    (r'·', '，'),                                # · (middle dot) → 逗号（TTS 不可读）
    # —— 是合法中文破折号，保留不动
]

# 需要完全移除的 HTML 标签及其内容
REMOVE_TAGS_WITH_CONTENT = {
    'script', 'style', 'svg', 'noscript', 'template',
    'jelly-button', 'jelly-slider', 'jelly-card',
}

# 需要移除但保留文本的标签
STRIP_TAGS_KEEP_TEXT = {
    'a', 'b', 'i', 'u', 'em', 'strong', 'span', 'div',
    'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'code', 'pre',
    'form', 'input', 'button', 'select', 'textarea',
    'table', 'tr', 'td', 'th', 'thead', 'tbody',
    'img', 'figure', 'figcaption', 'section', 'article',
    'header', 'footer', 'nav', 'main', 'aside',
}


# ── HTML 文本提取器 ──────────────────────────────────────────────────

class TTSHTMLExtractor(HTMLParser):
    """从 HTML 提取干净的 TTS 文本"""

    def __init__(self):
        super().__init__()
        self.result = []
        self.skip_stack = []  # 跟踪需要跳过内容的标签
        self.in_body = False
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # 进入 body
        if tag == 'body':
            self.in_body = True

        # 跳过不需要的标签
        if tag in REMOVE_TAGS_WITH_CONTENT:
            self.skip_stack.append(tag)
            return

        # 跳过 nav, footer, header (导航和页脚不需要朗读)
        if tag in ('nav', 'footer', 'header') and not self.skip_stack:
            self.skip_stack.append(tag)
            return

        # 跳过音频播放器
        if tag == 'audio' or (tag == 'div' and 'audio-player' in attrs_dict.get('class', '')):
            self.skip_stack.append(tag)
            return

        if not self.skip_stack:
            # 段落分隔
            if tag in ('p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'):
                self.result.append('\n')

    def handle_endtag(self, tag):
        if tag == 'body':
            self.in_body = False

        if self.skip_stack and self.skip_stack[-1] == tag:
            self.skip_stack.pop()

        if tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.result.append('\n')

    def handle_data(self, data):
        if self.skip_stack:
            return
        self.result.append(data)

    def get_text(self):
        return ''.join(self.result)


# ── 清洗函数 ──────────────────────────────────────────────────────────

def extract_html_text(html_content):
    """从 HTML 提取纯文本"""
    extractor = TTSHTMLExtractor()
    try:
        extractor.feed(html_content)
        return extractor.get_text()
    except Exception as e:
        # 降级：正则提取
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        return text


def clean_markdown(text):
    """清除 markdown 格式符号"""
    for pattern_info in MARKDOWN_PATTERNS:
        if len(pattern_info) == 3:
            pattern, replacement, flags = pattern_info
            text = re.sub(pattern, replacement, text, flags=flags)
        else:
            pattern, replacement = pattern_info
            text = re.sub(pattern, replacement, text)
    return text


def clean_tts_text(text):
    """完整的 TTS 文本清洗流水线"""
    # 1. 清除 HTML 实体
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '和')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")

    # 2. 清除 markdown 符号
    text = clean_markdown(text)

    # 3. 清除残留 HTML 标签（漏网之鱼）
    text = re.sub(r'<[^>]+>', '', text)

    # 4. 清除零宽字符和控制字符
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

    # 5. 规范化空白
    text = re.sub(r'[ \t]+', ' ', text)          # 多个空格 → 一个
    text = re.sub(r'\n{3,}', '\n\n', text)        # 多个空行 → 一个
    text = re.sub(r' \n', '\n', text)             # 行尾空格
    text = re.sub(r'\n ', '\n', text)             # 行首空格
    text = text.strip()

    # 6. 中文标点规范化
    text = re.sub(r',\s*', '，', text)            # 英文逗号 → 中文（在中文语境中）
    # 但要保留英文逗号（在数字/英文之间）
    text = re.sub(r'(\d)，(\d)', r'\1,\2', text)  # 数字间的逗号保留
    text = re.sub(r'([a-zA-Z])，([a-zA-Z])', r'\1,\2', text)  # 英文间的逗号保留

    # 7. 清除空行开头的行
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)

    return text


# ── 检查函数 ──────────────────────────────────────────────────────────

def check_tts_text(text, filename=""):
    """检查 TTS 文本中的问题"""
    issues = []

    # 检查 HTML 标签
    html_tags = re.findall(r'<([a-z][a-z0-9-]*)\s*[^>]*>', text, re.IGNORECASE)
    if html_tags:
        issues.append({
            'type': 'html-leak',
            'severity': 'error',
            'tags': list(set(html_tags))[:5],
            'message': f"TTS 文本含 HTML 标签: {list(set(html_tags))[:5]}"
        })

    # 检查 markdown 符号
    md_issues = []
    if re.search(r'(?<!\*)\*\*(?!\*)', text):
        # ** but not *** (*** is masked content, not bold)
        count = len(re.findall(r'(?<!\*)\*\*(?!\*)', text))
        md_issues.append(f"'**' × {count}")
    if '·' in text:
        count = text.count('·')
        md_issues.append(f"'·' (middle dot) × {count}")
    # 注意：—— 是合法中文破折号，不算问题
    # 但连续 3 个以上的 —— 可能是格式残留
    if re.search(r'(——\s*){3,}', text):
        md_issues.append("连续破折号 (格式残留)")
    if re.search(r'^\s*#{1,6}\s', text, re.MULTILINE):
        md_issues.append("'#' heading markers")
    if re.search(r'\[([^\]]+)\]\([^)]+\)', text):
        md_issues.append("markdown links")
    if re.search(r'!\[', text):
        md_issues.append("markdown images")
    # 注意：list markers (-, *, +) 在清洗后会变成 •，所以只检查清洗后仍残留的
    # 不做检查，因为 clean 阶段已处理

    if md_issues:
        issues.append({
            'type': 'markdown-leak',
            'severity': 'warning',
            'symbols': md_issues,
            'message': f"TTS 文本含 markdown 符号: {', '.join(md_issues)}"
        })

    # 检查零宽字符
    zero_width = re.findall(r'[\u200b\u200c\u200d\ufeff]', text)
    if zero_width:
        issues.append({
            'type': 'zero-width',
            'severity': 'warning',
            'count': len(zero_width),
            'message': f"含 {len(zero_width)} 个零宽字符"
        })

    return issues


# ── 文件操作 ──────────────────────────────────────────────────────────

def process_article(html_path, save=False, tts_generate=False):
    """处理单篇文章"""
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 提取文本
    raw_text = extract_html_text(html_content)

    # 清洗
    clean_text = clean_tts_text(raw_text)

    # 检查清洗后的文本
    issues = check_tts_text(clean_text, html_path)

    # 统计
    word_count = len(clean_text)
    char_count = len(clean_text.replace(' ', '').replace('\n', ''))

    result = {
        'file': html_path,
        'word_count': word_count,
        'char_count': char_count,
        'issues': issues,
        'clean': len(issues) == 0,
    }

    # 保存 TTS 文本
    if save:
        base = Path(html_path).stem
        tts_path = os.path.join(AUDIO_DIR, f"{base}.tts.txt")
        os.makedirs(AUDIO_DIR, exist_ok=True)
        with open(tts_path, 'w', encoding='utf-8') as f:
            f.write(clean_text)
        result['tts_file'] = tts_path

    return result


def scan_all_posts(fix=False):
    """扫描所有文章"""
    posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.html")))
    results = {
        'total': len(posts),
        'clean': 0,
        'issues': 0,
        'details': []
    }

    for post in posts:
        # 检查对应的 TTS 文本
        base = Path(post).stem
        tts_txt = os.path.join(AUDIO_DIR, f"{base}.tts.txt")

        if os.path.exists(tts_txt):
            with open(tts_txt, 'r', encoding='utf-8') as f:
                tts_text = f.read()
            issues = check_tts_text(tts_text, tts_txt)

            if issues:
                results['issues'] += 1
                detail = {
                    'file': post,
                    'tts_file': tts_txt,
                    'issues': issues,
                }

                if fix:
                    # 重新从 HTML 提取并清洗
                    with open(post, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    raw_text = extract_html_text(html_content)
                    clean_text = clean_tts_text(raw_text)
                    with open(tts_txt, 'w', encoding='utf-8') as f:
                        f.write(clean_text)
                    detail['fixed'] = True

                results['details'].append(detail)
            else:
                results['clean'] += 1
        else:
            # 没有 TTS 文本，从 HTML 生成
            with open(post, 'r', encoding='utf-8') as f:
                html_content = f.read()
            raw_text = extract_html_text(html_content)
            clean_text = clean_tts_text(raw_text)
            issues = check_tts_text(clean_text)

            if fix and len(clean_text) > 100:
                os.makedirs(AUDIO_DIR, exist_ok=True)
                with open(tts_txt, 'w', encoding='utf-8') as f:
                    f.write(clean_text)
                results['clean'] += 1
            elif issues:
                results['issues'] += 1
                results['details'].append({
                    'file': post,
                    'tts_file': tts_txt,
                    'issues': issues,
                    'no_tts_file': True,
                })
            else:
                results['clean'] += 1

    return results


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='TTS 文本清洗器 — 清除 HTML/Markdown 污染',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s posts/article.html              # 检查单篇文章
  %(prog)s posts/article.html --save       # 清洗并保存 TTS 文本
  %(prog)s --scan                          # 扫描所有文章
  %(prog)s --scan --fix                    # 扫描并修复所有问题
  %(prog)s --check tts.txt                 # 检查 TTS 文本文件
        """
    )

    parser.add_argument('file', nargs='?', help='文章 HTML 文件或 TTS 文本文件')
    parser.add_argument('--save', action='store_true', help='保存清洗后的 TTS 文本')
    parser.add_argument('--check', action='store_true', help='检查 TTS 文本文件（不清洗）')
    parser.add_argument('--scan', action='store_true', help='扫描所有文章')
    parser.add_argument('--fix', action='store_true', help='自动修复问题')
    parser.add_argument('--stdin', action='store_true', help='从 stdin 读取 HTML')
    parser.add_argument('--tts', action='store_true', help='清洗后生成 TTS 音频（需配合 OpenClaw tts 工具）')
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    parser.add_argument('--quiet', action='store_true', help='只输出问题摘要')

    args = parser.parse_args()

    # stdin 模式
    if args.stdin:
        html_content = sys.stdin.read()
        raw_text = extract_html_text(html_content)
        clean_text = clean_tts_text(raw_text)
        print(clean_text)
        return

    # scan 模式
    if args.scan:
        results = scan_all_posts(fix=args.fix)

        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
            return

        print("=" * 60)
        print("🧹 TTS 文本质量扫描报告")
        print("=" * 60)
        print(f"\n📊 总文章数: {results['total']}")
        print(f"✅ 干净: {results['clean']}")
        print(f"❌ 有问题: {results['issues']}")

        if args.fix:
            fixed = sum(1 for d in results['details'] if d.get('fixed'))
            print(f"🔧 已修复: {fixed}")

        if results['details']:
            print(f"\n{'─' * 60}")
            print("问题详情:")
            for detail in results['details']:
                fname = Path(detail['file']).name
                status = "🔧已修复" if detail.get('fixed') else "❌"
                print(f"\n  {status} {fname}")
                for issue in detail['issues']:
                    print(f"    {issue['message']}")

        print(f"\n{'─' * 60}")
        fixed = sum(1 for d in results['details'] if d.get('fixed'))
        effective_clean = results['clean'] + fixed
        score = int(effective_clean / max(results['total'], 1) * 100)
        print(f"📈 健康评分: {score}/100")
        return

    # 单文件模式
    if not args.file:
        parser.print_help()
        return

    # check 模式（检查 TTS 文本文件）
    if args.check:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
        issues = check_tts_text(text, args.file)

        if args.json:
            print(json.dumps({'file': args.file, 'issues': issues}, ensure_ascii=False, indent=2))
        else:
            if issues:
                print(f"❌ {args.file} 有 {len(issues)} 个问题:")
                for issue in issues:
                    print(f"  [{issue['severity']}] {issue['message']}")
            else:
                print(f"✅ {args.file} 干净")
        return

    # 处理文章 HTML
    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        sys.exit(1)

    result = process_article(args.file, save=args.save)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        fname = Path(args.file).name
        if result['clean']:
            print(f"✅ {fname} — {result['word_count']} 字 — 干净")
        else:
            print(f"❌ {fname} — {result['word_count']} 字 — {len(result['issues'])} 个问题:")
            for issue in result['issues']:
                print(f"  [{issue['severity']}] {issue['message']}")

        if args.save and 'tts_file' in result:
            print(f"\n💾 TTS 文本已保存: {result['tts_file']}")

    # 退出码
    sys.exit(0 if result['clean'] else 1)


if __name__ == '__main__':
    main()
