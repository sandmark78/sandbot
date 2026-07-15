#!/usr/bin/env python3
"""
V4 模板合规检查器 — check-v4-compliance.py
检查文章 HTML 是否符合 V4 模板规范

本周问题：文章排版反复不符合 V4 模板（07-13 报告"不是第一次了"）
解决方案：自动化检查，发布前必须通过

用法:
  python3 scripts/check-v4-compliance.py posts/article.html
  python3 scripts/check-v4-compliance.py posts/  (检查目录下所有 html)
  python3 scripts/check-v4-compliance.py --fix posts/article.html  (自动修复可修复的问题)

退出码:
  0 = 全部通过
  1 = 有错误（必须修复）
  2 = 有警告（建议修复）
"""

import sys
import os
import re
import glob
import argparse
from dataclasses import dataclass, field
from typing import List

# ─── 检查项定义 ───

@dataclass
class CheckResult:
    level: str  # "ERROR" | "WARN" | "OK"
    name: str
    message: str

@dataclass
class Report:
    file: str
    results: List[CheckResult] = field(default_factory=list)
    
    @property
    def errors(self):
        return [r for r in self.results if r.level == "ERROR"]
    
    @property
    def warnings(self):
        return [r for r in self.results if r.level == "WARN"]
    
    @property
    def passed(self):
        return [r for r in self.results if r.level == "OK"]


def check_file(filepath: str, fix: bool = False) -> Report:
    """检查单个 HTML 文件"""
    report = Report(file=filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    original_html = html  # 保留原始内容用于修复
    
    # ═══ 必需结构检查 ═══
    
    # 1. DOCTYPE
    if '<!DOCTYPE html>' in html:
        report.results.append(CheckResult("OK", "DOCTYPE", "✅ DOCTYPE 声明存在"))
    else:
        report.results.append(CheckResult("ERROR", "DOCTYPE", "❌ 缺少 <!DOCTYPE html>"))
    
    # 2. lang 属性
    if 'lang="zh-CN"' in html:
        report.results.append(CheckResult("OK", "lang", "✅ lang=\"zh-CN\" 存在"))
    else:
        report.results.append(CheckResult("ERROR", "lang", "❌ 缺少 lang=\"zh-CN\""))
    
    # 3. viewport meta (移动端适配)
    if 'name="viewport"' in html:
        report.results.append(CheckResult("OK", "viewport", "✅ viewport meta 存在"))
    else:
        report.results.append(CheckResult("ERROR", "viewport", "❌ 缺少 viewport meta（移动端不适配）"))
    
    # 4. Google Fonts
    if 'fonts.googleapis.com' in html:
        report.results.append(CheckResult("OK", "fonts", "✅ Google Fonts 引入存在"))
    else:
        report.results.append(CheckResult("WARN", "fonts", "⚠️ 缺少 Google Fonts 引入（字体可能不一致）"))
    
    # 5. CSS 变量 (:root)
    if ':root' in html and '--bg:' in html or '--bg: ' in html:
        report.results.append(CheckResult("OK", "css-vars", "✅ CSS 变量 (:root) 存在"))
    else:
        report.results.append(CheckResult("ERROR", "css-vars", "❌ 缺少 CSS 变量 :root（配色体系缺失）"))
    
    # ═══ V4 核心组件检查 ═══
    
    # 6. .container
    if 'class="container"' in html:
        report.results.append(CheckResult("OK", "container", "✅ .container 存在"))
    else:
        report.results.append(CheckResult("ERROR", "container", "❌ 缺少 .container 包裹"))
    
    # 7. .site-header
    if 'class="site-header"' in html or 'site-header' in html:
        report.results.append(CheckResult("OK", "site-header", "✅ .site-header 存在"))
    else:
        report.results.append(CheckResult("ERROR", "site-header", "❌ 缺少 .site-header（页面头部缺失）"))
    
    # 8. header 内 .overline
    if 'class="overline"' in html or 'overline' in html:
        report.results.append(CheckResult("OK", "overline", "✅ .overline 存在"))
    else:
        report.results.append(CheckResult("WARN", "overline", "⚠️ 缺少 .overline（头部分类标签缺失）"))
    
    # 9. .article-label + .label-category
    if 'article-label' in html:
        report.results.append(CheckResult("OK", "article-label", "✅ .article-label 存在"))
    else:
        report.results.append(CheckResult("ERROR", "article-label", "❌ 缺少 .article-label（文章顶部分类标签缺失）"))
    
    # 10. .article-title
    if 'article-title' in html:
        report.results.append(CheckResult("OK", "article-title", "✅ .article-title 存在"))
    else:
        report.results.append(CheckResult("ERROR", "article-title", "❌ 缺少 .article-title（文章标题缺失）"))
    
    # 11. .article-subtitle
    if 'article-subtitle' in html:
        report.results.append(CheckResult("OK", "article-subtitle", "✅ .article-subtitle 存在"))
    else:
        report.results.append(CheckResult("WARN", "article-subtitle", "⚠️ 缺少 .article-subtitle（一句话摘要缺失）"))
    
    # 12. .article-meta
    if 'article-meta' in html:
        report.results.append(CheckResult("OK", "article-meta", "✅ .article-meta 存在"))
    else:
        report.results.append(CheckResult("WARN", "article-meta", "⚠️ 缺少 .article-meta（元信息行缺失）"))
    
    # 13. <article> 标签
    if '<article' in html:
        report.results.append(CheckResult("OK", "article-tag", "✅ <article> 标签存在"))
    else:
        report.results.append(CheckResult("ERROR", "article-tag", "❌ 缺少 <article> 标签"))
    
    # 14. 返回链接 / footer
    if 'back-link' in html:
        report.results.append(CheckResult("OK", "back-link", "✅ .back-link (返回链接) 存在"))
    else:
        report.results.append(CheckResult("WARN", "back-link", "⚠️ 缺少 .back-link（页脚返回链接缺失）"))
    
    # ═══ 内容质量检查 ═══
    
    # 15. 字数检查 (中文字符 + 英文单词)
    # 去掉 HTML 标签和 CSS/JS
    text_content = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text_content = re.sub(r'<script[^>]*>.*?</script>', '', text_content, flags=re.DOTALL)
    text_content = re.sub(r'<[^>]+>', '', text_content)
    text_content = re.sub(r'\s+', '', text_content)
    
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text_content))
    # 粗略估计：中文字数 ≈ 中文字符 + 英文单词数
    word_count = chinese_chars + len(re.findall(r'[a-zA-Z]+', text_content))
    
    if word_count >= 800:
        report.results.append(CheckResult("OK", "word-count", f"✅ 字数充足 ({word_count} 字)"))
    elif word_count >= 400:
        report.results.append(CheckResult("WARN", "word-count", f"⚠️ 字数偏少 ({word_count} 字，建议 ≥800)"))
    else:
        report.results.append(CheckResult("ERROR", "word-count", f"❌ 字数严重不足 ({word_count} 字，要求 ≥400)"))
    
    # 16. 域名检查 (应该用 sandbot.cgfan.com)
    if 'sandmark78.github.io/sandbot' in html:
        report.results.append(CheckResult("ERROR", "domain", "❌ 使用了旧域名 sandmark78.github.io，应为 sandbot.cgfan.com"))
        if fix:
            html = html.replace('sandmark78.github.io/sandbot', 'sandbot.cgfan.com')
    else:
        report.results.append(CheckResult("OK", "domain", "✅ 域名正确 (sandbot.cgfan.com)"))
    
    # 17. section 编号检查 (V4 模板用 section-num)
    h2_count = len(re.findall(r'<h2', html))
    section_num_count = len(re.findall(r'section-num', html))
    if h2_count > 0:
        if section_num_count >= h2_count * 0.5:
            report.results.append(CheckResult("OK", "sections", f"✅ 章节编号完整 ({h2_count} 个 h2, {section_num_count} 个编号)"))
        else:
            report.results.append(CheckResult("WARN", "sections", f"⚠️ 章节编号不完整 ({h2_count} 个 h2, 仅 {section_num_count} 个编号)"))
    
    # 18. quick-glance 框 (V4 特色组件)
    if 'quick-glance' in html:
        report.results.append(CheckResult("OK", "quick-glance", "✅ .quick-glance (速览框) 存在"))
    else:
        report.results.append(CheckResult("WARN", "quick-glance", "⚠️ 缺少 .quick-glance 速览框（V4 推荐组件）"))
    
    # 19. title 格式检查
    title_match = re.search(r'<title>(.*?)</title>', html)
    if title_match:
        title = title_match.group(1)
        if 'Sandbot Blog' in title:
            report.results.append(CheckResult("OK", "title-format", f"✅ title 格式正确"))
        else:
            report.results.append(CheckResult("WARN", "title-format", f"⚠️ title 缺少 'Sandbot Blog' 后缀: {title[:50]}"))
    else:
        report.results.append(CheckResult("ERROR", "title-format", "❌ 缺少 <title> 标签"))
    
    # 20. 图片响应式检查
    imgs = re.findall(r'<img[^>]+>', html)
    if imgs:
        responsive = sum(1 for img in imgs if 'max-width' in img or 'width:' not in img or 'loading="lazy"' in img)
        if responsive == len(imgs):
            report.results.append(CheckResult("OK", "images", f"✅ 图片响应式 ({len(imgs)} 张)"))
        else:
            report.results.append(CheckResult("WARN", "images", f"⚠️ {len(imgs) - responsive}/{len(imgs)} 张图片可能不适配移动端"))
    
    # ═══ 自动修复 ═══
    if fix and html != original_html:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        report.results.append(CheckResult("OK", "fix", "✅ 已自动修复可修复的问题"))
    
    return report


def print_report(report: Report, verbose: bool = False):
    """打印检查报告"""
    print(f"\n{'='*60}")
    print(f"📄 {report.file}")
    print(f"{'='*60}")
    
    # 按级别排序：ERROR > WARN > OK
    for r in report.errors:
        print(f"  {r.message}")
    for r in report.warnings:
        print(f"  {r.message}")
    if verbose:
        for r in report.passed:
            print(f"  {r.message}")
    
    # 摘要
    e, w, p = len(report.errors), len(report.warnings), len(report.passed)
    print(f"\n  📊 结果: {p} 通过, {w} 警告, {e} 错误")
    
    if e > 0:
        print(f"  ❌ 不合规 — 必须修复 {e} 个错误")
    elif w > 0:
        print(f"  ⚠️ 基本合规 — 建议修复 {w} 个警告")
    else:
        print(f"  ✅ 完全合规")
    print()


def main():
    parser = argparse.ArgumentParser(description='V4 模板合规检查器')
    parser.add_argument('path', help='HTML 文件或目录路径')
    parser.add_argument('--fix', action='store_true', help='自动修复可修复的问题')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示所有检查项（包括通过的）')
    parser.add_argument('--quiet', '-q', action='store_true', help='只显示错误和警告')
    args = parser.parse_args()
    
    # 收集文件
    if os.path.isdir(args.path):
        files = sorted(glob.glob(os.path.join(args.path, '*.html')))
        # 排除 index.html, blog.html 等非文章文件
        files = [f for f in files if not os.path.basename(f).startswith(('index', 'blog', 'feed'))]
    else:
        files = [args.path]
    
    if not files:
        print(f"❌ 未找到 HTML 文件: {args.path}")
        sys.exit(1)
    
    # 检查每个文件
    total_errors = 0
    total_warnings = 0
    total_passed = 0
    failed_files = []
    
    print(f"\n🔍 V4 模板合规检查 — 共 {len(files)} 个文件")
    
    for filepath in files:
        report = check_file(filepath, fix=args.fix)
        if not args.quiet or report.errors or report.warnings:
            print_report(report, verbose=args.verbose)
        total_errors += len(report.errors)
        total_warnings += len(report.warnings)
        total_passed += len(report.passed)
        if report.errors:
            failed_files.append(filepath)
    
    # 总结
    print(f"{'='*60}")
    print(f"📊 总计: {len(files)} 个文件, {total_passed} 通过, {total_warnings} 警告, {total_errors} 错误")
    
    if failed_files:
        print(f"\n❌ 不合规文件:")
        for f in failed_files:
            print(f"  • {f}")
        sys.exit(1)
    elif total_warnings > 0:
        print(f"\n⚠️ 所有文件无严重错误，但有 {total_warnings} 个建议修复项")
        sys.exit(2)
    else:
        print(f"\n✅ 全部合规！")
        sys.exit(0)


if __name__ == '__main__':
    main()
