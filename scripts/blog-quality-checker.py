#!/usr/bin/env python3
"""
blog-quality-checker.py — 博客文章质量检查器 v1.0
Sandbot 每周工具脚本 · 2026-07-09

自动检查 blog HTML 文章的：
  1. 模板元素完整性 (nav, hero, toc, footer, lang switcher)
  2. 移动端适配 (viewport meta, @media 查询)
  3. 双语内容完整性 (中英文是否都有)
  4. 内部链接有效性
  5. 图片 alt 文本
  6. 文章字数统计
  7. 基础 HTML 结构 (lang, charset, title)

用法:
  python3 scripts/blog-quality-checker.py                    # 检查默认目录
  python3 scripts/blog-quality-checker.py path/to/blog/      # 指定目录
  python3 scripts/blog-quality-checker.py --json              # JSON 输出
  python3 scripts/blog-quality-checker.py --min-words 500    # 最低字数要求
"""

import os
import sys
import re
import json
import glob
import argparse
from pathlib import Path
from html.parser import HTMLParser
from collections import Counter

# ── 配置 ──────────────────────────────────────────────────────────────

DEFAULT_BLOG_DIR = "skills/pua/landing/dist/blog"
DEFAULT_MIN_WORDS = 200

# 模板必须元素
REQUIRED_TEMPLATE_ELEMENTS = {
    "nav": {
        "selector": r'<nav\s',
        "description": "导航栏 <nav>",
        "severity": "error",
    },
    "hero": {
        "selector": r'class="hero"',
        "description": "Hero 区域 (.hero)",
        "severity": "error",
    },
    "hero_h1": {
        "selector": r'<h1[^>]*>(?!</h1>).+</h1>',
        "description": "Hero 标题 <h1>",
        "severity": "error",
    },
    "hero_sub": {
        "selector": r'class="sub"',
        "description": "Hero 副标题 (.sub)",
        "severity": "warning",
    },
    "hero_meta": {
        "selector": r'class="meta"',
        "description": "Hero 元信息 (.meta)",
        "severity": "warning",
    },
    "toc": {
        "selector": r'class="toc"',
        "description": "目录 (.toc)",
        "severity": "warning",
    },
    "lang_switcher": {
        "selector": r'class="lsw"',
        "description": "语言切换器 (.lsw)",
        "severity": "warning",
    },
    "footer": {
        "selector": r'class="footer"',
        "description": "页脚 (.footer)",
        "severity": "warning",
    },
    "sections_reveal": {
        "selector": r'class="reveal"',
        "description": "内容段落动画 (.reveal)",
        "severity": "info",
    },
}

# 移动端适配检查
MOBILE_CHECKS = {
    "viewport_meta": {
        "pattern": r'<meta[^>]*name=["\']viewport["\'][^>]*>',
        "description": "viewport meta 标签",
        "severity": "error",
    },
    "width_device": {
        "pattern": r'width\s*=\s*device-width',
        "description": "viewport 包含 width=device-width",
        "severity": "error",
    },
    "media_query": {
        "pattern": r'@media\s*\(',
        "description": "@media 响应式查询",
        "severity": "error",
    },
    "mobile_breakpoint": {
        "pattern": r'max-width\s*:\s*(600|768|480)px',
        "description": "移动端断点 (≤768px)",
        "severity": "warning",
    },
}

# 基础 HTML 结构
HTML_STRUCTURE_CHECKS = {
    "lang_attr": {
        "pattern": r'<html[^>]*\slang=["\']',
        "description": "html lang 属性",
        "severity": "warning",
    },
    "charset": {
        "pattern": r'<meta[^>]*charset',
        "description": "charset 声明",
        "severity": "error",
    },
    "title": {
        "pattern": r'<title>[^<]+</title>',
        "description": "<title> 标签",
        "severity": "error",
    },
}


# ── HTML 解析器 ────────────────────────────────────────────────────────

class LinkExtractor(HTMLParser):
    """提取 HTML 中的链接和图片"""

    def __init__(self):
        super().__init__()
        self.links = []        # (href, line)
        self.images = []       # (src, alt, line)
        self.internal_links = []
        self.external_links = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        line = self.getpos()[0]

        if tag == "a":
            href = attrs_dict.get("href", "")
            if href:
                self.links.append((href, line))
                if href.startswith(("http://", "https://")):
                    self.external_links.append((href, line))
                elif href.startswith("#") or href.endswith(".html"):
                    self.internal_links.append((href, line))

        elif tag == "img":
            src = attrs_dict.get("src", "")
            alt = attrs_dict.get("alt", "")
            self.images.append((src, alt, line))


def count_words_html(html_content):
    """统计 HTML 中的可见文本字数（中英文混合）"""
    # 移除 script/style
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)
    # 解码实体
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'&#\d+;', ' ', text)
    # 压缩空白
    text = re.sub(r'\s+', ' ', text).strip()

    # 中文字符数
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # 英文单词数
    english_words = len(re.findall(r'[a-zA-Z]+', text))

    return chinese_chars + english_words, text


def check_bilingual_completeness(html_content):
    """检查中英文内容是否都有"""
    zh_blocks = re.findall(r'data-lang="zh"[^>]*>(.*?)</div>', html_content, re.DOTALL)
    en_blocks = re.findall(r'data-lang="en"[^>]*>(.*?)</div>', html_content, re.DOTALL)

    zh_text = " ".join(zh_blocks)
    en_text = " ".join(en_blocks)

    # 统计各语言可见文本
    zh_clean = re.sub(r'<[^>]+>', '', zh_text).strip()
    en_clean = re.sub(r'<[^>]+>', '', en_text).strip()

    zh_chars = len(re.findall(r'[\u4e00-\u9fff]', zh_clean))
    en_words = len(re.findall(r'[a-zA-Z]+', en_clean))

    return {
        "zh_present": zh_chars > 50,
        "en_present": en_words > 20,
        "zh_char_count": zh_chars,
        "en_word_count": en_words,
    }


def check_section_ids(html_content):
    """检查 TOC 链接是否都有对应的 section id"""
    # 提取 TOC 中的 href
    toc_match = re.search(r'class="toc".*?</div>\s*</div>', html_content, re.DOTALL)
    if not toc_match:
        return {"toc_found": False, "broken_anchors": []}

    toc_html = toc_match.group()
    toc_links = re.findall(r'href="#([^"]+)"', toc_html)

    # 提取所有 id
    all_ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', html_content))

    broken = [link for link in toc_links if link not in all_ids]

    return {
        "toc_found": True,
        "toc_links": len(toc_links),
        "broken_anchors": broken,
    }


# ── 主检查逻辑 ────────────────────────────────────────────────────────

def check_article(filepath):
    """检查单篇文章，返回检查结果 dict"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    filename = os.path.basename(filepath)
    result = {
        "file": filename,
        "path": filepath,
        "size_bytes": len(content.encode("utf-8")),
        "errors": [],
        "warnings": [],
        "info": [],
        "score": 100,
    }

    # 1. 模板元素检查
    for name, check in REQUIRED_TEMPLATE_ELEMENTS.items():
        found = bool(re.search(check["selector"], content, re.DOTALL))
        if not found:
            msg = f"缺少{check['description']}"
            if check["severity"] == "error":
                result["errors"].append(msg)
                result["score"] -= 15
            elif check["severity"] == "warning":
                result["warnings"].append(msg)
                result["score"] -= 5
            else:
                result["info"].append(msg)

    # 2. 移动端适配检查
    for name, check in MOBILE_CHECKS.items():
        found = bool(re.search(check["pattern"], content))
        if not found:
            msg = f"移动端缺失: {check['description']}"
            if check["severity"] == "error":
                result["errors"].append(msg)
                result["score"] -= 15
            else:
                result["warnings"].append(msg)
                result["score"] -= 5

    # 3. HTML 基础结构检查
    for name, check in HTML_STRUCTURE_CHECKS.items():
        found = bool(re.search(check["pattern"], content))
        if not found:
            msg = f"HTML 结构缺失: {check['description']}"
            if check["severity"] == "error":
                result["errors"].append(msg)
                result["score"] -= 10
            else:
                result["warnings"].append(msg)
                result["score"] -= 3

    # 4. 双语内容检查
    bilingual = check_bilingual_completeness(content)
    if not bilingual["zh_present"]:
        result["warnings"].append("中文内容不足或缺失")
        result["score"] -= 5
    if not bilingual["en_present"]:
        result["info"].append("英文翻译缺失（仅中文）")
        result["score"] -= 2
    result["bilingual"] = bilingual

    # 5. TOC 锚点检查
    toc_check = check_section_ids(content)
    if toc_check["toc_found"] and toc_check["broken_anchors"]:
        for anchor in toc_check["broken_anchors"]:
            result["errors"].append(f"TOC 锚点 #{anchor} 无对应 section")
            result["score"] -= 5

    # 6. 链接和图片检查
    parser = LinkExtractor()
    try:
        parser.feed(content)
    except Exception:
        pass

    # 检查图片 alt
    for src, alt, line in parser.images:
        if not alt.strip():
            result["warnings"].append(f"图片缺少 alt 文本: {src} (行 {line})")
            result["score"] -= 2

    result["links"] = {
        "internal": len(parser.internal_links),
        "external": len(parser.external_links),
        "images": len(parser.images),
        "images_no_alt": sum(1 for _, a, _ in parser.images if not a.strip()),
    }

    # 7. 字数统计
    word_count, _ = count_words_html(content)
    result["word_count"] = word_count

    # 8. 检查内联 CSS 大小（性能）
    style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
    css_size = sum(len(b) for b in style_blocks)
    result["css_size_bytes"] = css_size
    if css_size > 50000:
        result["info"].append(f"CSS 较大 ({css_size // 1024}KB)，考虑外链")

    # 限制最低分
    result["score"] = max(0, result["score"])

    return result


def format_report(results, min_words=DEFAULT_MIN_WORDS):
    """格式化输出报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("📝 博客文章质量检查报告")
    lines.append(f"   检查时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"   文章数量: {len(results)}")
    lines.append("=" * 60)

    total_errors = 0
    total_warnings = 0
    total_score = 0

    for r in results:
        total_errors += len(r["errors"])
        total_warnings += len(r["warnings"])
        total_score += r["score"]

        # 状态标记
        if r["score"] >= 90:
            status = "✅"
        elif r["score"] >= 70:
            status = "🟡"
        else:
            status = "🔴"

        lines.append(f"\n{status} {r['file']}")
        lines.append(f"   得分: {r['score']}/100 | 字数: {r['word_count']} | 大小: {r['size_bytes'] // 1024}KB")

        # 字数警告
        if r["word_count"] < min_words:
            lines.append(f"   ⚠️  字数不足 ({r['word_count']} < {min_words})")

        # 双语信息
        bi = r.get("bilingual", {})
        if bi:
            zh_ok = "✅" if bi.get("zh_present") else "❌"
            en_ok = "✅" if bi.get("en_present") else "❌"
            lines.append(f"   双语: 中{zh_ok} ({bi.get('zh_char_count', 0)}字) 英{en_ok} ({bi.get('en_word_count', 0)}词)")

        # 链接统计
        lnk = r.get("links", {})
        if lnk:
            lines.append(f"   链接: 内部{lnk['internal']} 外部{lnk['external']} 图片{lnk['images']}(缺alt:{lnk['images_no_alt']})")

        # 错误
        for e in r["errors"]:
            lines.append(f"   ❌ {e}")
        for w in r["warnings"]:
            lines.append(f"   ⚠️  {w}")
        for i in r["info"]:
            lines.append(f"   ℹ️  {i}")

    # 汇总
    avg_score = total_score // len(results) if results else 0
    lines.append("\n" + "=" * 60)
    lines.append("📊 汇总")
    lines.append(f"   平均得分: {avg_score}/100")
    lines.append(f"   错误总数: {total_errors}")
    lines.append(f"   警告总数: {total_warnings}")

    # 字数不足文章
    low_word = [r for r in results if r["word_count"] < min_words]
    if low_word:
        lines.append(f"   字数不足: {len(low_word)} 篇")
        for r in low_word:
            lines.append(f"     - {r['file']} ({r['word_count']} 字)")

    # 得分最低文章
    if results:
        worst = min(results, key=lambda x: x["score"])
        if worst["score"] < 90:
            lines.append(f"   最需改进: {worst['file']} ({worst['score']}分)")

    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="博客文章质量检查器")
    parser.add_argument("directory", nargs="?", default=None, help="博客 HTML 目录")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--min-words", type=int, default=DEFAULT_MIN_WORDS, help=f"最低字数要求 (默认 {DEFAULT_MIN_WORDS})")
    args = parser.parse_args()

    # 确定目录
    if args.directory:
        blog_dir = args.directory
    else:
        # 尝试从 workspace 根目录定位
        workspace = os.environ.get("WORKSPACE", "/home/node/.openclaw/workspace")
        blog_dir = os.path.join(workspace, DEFAULT_BLOG_DIR)

    if not os.path.isdir(blog_dir):
        print(f"❌ 目录不存在: {blog_dir}")
        sys.exit(1)

    # 查找 HTML 文件
    html_files = sorted(glob.glob(os.path.join(blog_dir, "*.html")))
    # 排除 index.html（它是列表页不是文章）
    article_files = [f for f in html_files if os.path.basename(f) != "index.html"]

    if not article_files:
        print(f"⚠️  目录中没有找到文章 HTML 文件: {blog_dir}")
        sys.exit(0)

    # 检查每篇文章
    results = []
    for filepath in article_files:
        result = check_article(filepath)
        results.append(result)

    # 输出
    if args.json:
        # JSON 模式：移除不可序列化的字段
        output = []
        for r in results:
            output.append({
                "file": r["file"],
                "score": r["score"],
                "word_count": r["word_count"],
                "size_bytes": r["size_bytes"],
                "errors": r["errors"],
                "warnings": r["warnings"],
                "info": r["info"],
                "bilingual": r.get("bilingual", {}),
                "links": r.get("links", {}),
            })
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(format_report(results, min_words=args.min_words))

    # 退出码：有 error 返回 1
    has_errors = any(r["errors"] for r in results)
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
