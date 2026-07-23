#!/usr/bin/env python3
"""
blog-asset-integrity.py — 博客资产完整性检查器 v1.0
Sandbot 每周工具脚本 · 2026-07-23

解决的问题（本周审计发现的真实问题）：
  1. 音频路径不一致：../audio/ vs audio/ vs 裸文件名 — 导致部分文章音频 404
  2. 音频文件引用但缺失：文章引用了 xxx.mp3 但文件不存在
  3. AUDIO_FILE_PLACEHOLDER 残留：TTS 未生成但占位符未清理
  4. 孤儿音频文件：mp3 存在但没有任何文章引用
  5. 文件名不规范：中文文件名、.md.mp3 后缀

用法:
  python3 scripts/blog-asset-integrity.py                # 检查所有问题
  python3 scripts/blog-asset-integrity.py --fix          # 自动修复可修复的问题
  python3 scripts/blog-asset-integrity.py --fix-paths    # 只修复路径不一致
  python3 scripts/blog-asset-integrity.py --report       # 生成 JSON 报告
  python3 scripts/blog-asset-integrity.py --recent 3     # 只检查最近 3 天的文章

退出码:
  0 = 全部通过
  1 = 有错误（必须修复）
  2 = 有警告（建议修复）
"""

import os
import sys
import re
import json
import glob
import argparse
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# ── 配置 ──────────────────────────────────────────────────────────────

REPO_DIR = "/tmp/sandbot-gh"
POSTS_DIR = os.path.join(REPO_DIR, "posts")
AUDIO_DIR = os.path.join(POSTS_DIR, "audio")
SITE_URL = "https://sandbot.cgfan.com"

# 正确的音频路径格式
CORRECT_AUDIO_PREFIX = "audio/"

# 已知播客音频（不参与孤儿检查）
PODCAST_AUDIO_PATTERNS = ["podcast-", "podcast_"]


# ── 数据结构 ──────────────────────────────────────────────────────────

class Issue:
    def __init__(self, severity, category, file, message, fixable=False):
        self.severity = severity  # "ERROR" | "WARN" | "INFO"
        self.category = category
        self.file = file
        self.message = message
        self.fixable = fixable

    def __str__(self):
        icon = {"ERROR": "🔴", "WARN": "🟡", "INFO": "ℹ️"}[self.severity]
        fix = " [可修复]" if self.fixable else ""
        return f"  {icon} [{self.category}] {self.file}: {self.message}{fix}"


class Report:
    def __init__(self):
        self.issues = []
        self.stats = defaultdict(int)

    def error(self, category, file, message, fixable=False):
        self.issues.append(Issue("ERROR", category, file, message, fixable))
        self.stats[f"error_{category}"] += 1

    def warn(self, category, file, message, fixable=False):
        self.issues.append(Issue("WARN", category, file, message, fixable))
        self.stats[f"warn_{category}"] += 1

    def info(self, category, file, message):
        self.issues.append(Issue("INFO", category, file, message))

    @property
    def errors(self):
        return [i for i in self.issues if i.severity == "ERROR"]

    @property
    def warnings(self):
        return [i for i in self.issues if i.severity == "WARN"]

    def print_report(self):
        if not self.issues:
            print("✅ 所有资产完整性检查通过！")
            return

        print(f"\n{'='*60}")
        print(f"📊 博客资产完整性报告")
        print(f"{'='*60}")
        print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"文章目录: {POSTS_DIR}")
        print(f"音频目录: {AUDIO_DIR}")
        print()

        # 按严重程度分组
        for severity in ["ERROR", "WARN", "INFO"]:
            items = [i for i in self.issues if i.severity == severity]
            if not items:
                continue

            icon = {"ERROR": "🔴", "WARN": "🟡", "INFO": "ℹ️"}[severity]
            label = {"ERROR": "错误", "WARN": "警告", "INFO": "信息"}[severity]
            print(f"\n{icon} {label} ({len(items)} 项)")
            print(f"{'-'*40}")
            for issue in items:
                print(issue)

        # 统计摘要
        print(f"\n{'='*60}")
        print(f"📈 统计摘要")
        print(f"{'='*60}")
        print(f"  错误: {len(self.errors)}")
        print(f"  警告: {len(self.warnings)}")
        fixable = sum(1 for i in self.issues if i.fixable)
        print(f"  可自动修复: {fixable}")
        print()

    def to_json(self):
        return {
            "timestamp": datetime.now().isoformat(),
            "stats": dict(self.stats),
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "file": i.file,
                    "message": i.message,
                    "fixable": i.fixable,
                }
                for i in self.issues
            ],
        }


# ── 检查函数 ──────────────────────────────────────────────────────────

def get_html_articles(recent_days=None):
    """获取文章列表，可按天数过滤"""
    articles = sorted(glob.glob(os.path.join(POSTS_DIR, "*.html")))
    if recent_days:
        cutoff = (datetime.now() - timedelta(days=recent_days)).strftime("%Y-%m-%d")
        articles = [a for a in articles if os.path.basename(a)[:10] >= cutoff]
    return articles


def get_actual_audio_files():
    """获取实际存在的音频文件"""
    if not os.path.isdir(AUDIO_DIR):
        return []
    return sorted([f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")])


def extract_audio_refs(content):
    """从 HTML 中提取所有音频引用"""
    # 匹配 src="xxx.mp3" 和 data-src="xxx.mp3"
    refs = re.findall(r'(?:src|data-src)="([^"]*\.mp3)"', content)
    return refs


def normalize_audio_path(ref):
    """标准化音频路径为 audio/xxx.mp3 格式"""
    # 移除 ../ 前缀
    ref = re.sub(r'^\.\./', '', ref)
    # 移除 audio/ 前缀后统一加回
    ref = re.sub(r'^audio/', '', ref)
    return f"audio/{ref}"


def check_audio_path_consistency(report, articles):
    """检查 1: 音频路径格式是否一致"""
    for filepath in articles:
        filename = os.path.basename(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        refs = extract_audio_refs(content)
        for ref in refs:
            if ref.startswith("../audio/") or (not ref.startswith("audio/") and not ref.startswith("http")):
                expected = normalize_audio_path(ref)
                report.warn(
                    "路径不一致",
                    filename,
                    f"音频路径 '{ref}' 应改为 '{expected}'",
                    fixable=True,
                )


def check_audio_file_existence(report, articles):
    """检查 2: 引用的音频文件是否存在"""
    for filepath in articles:
        filename = os.path.basename(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        refs = extract_audio_refs(content)
        for ref in refs:
            # 标准化路径后检查文件
            normalized = normalize_audio_path(ref)
            audio_filename = normalized.replace("audio/", "")
            actual_path = os.path.join(AUDIO_DIR, audio_filename)

            if "AUDIO_FILE_PLACEHOLDER" in ref or "PLACEHOLDER" in ref:
                report.error(
                    "占位符残留",
                    filename,
                    f"发现 AUDIO_FILE_PLACEHOLDER，TTS 未生成",
                    fixable=True,
                )
            elif not os.path.exists(actual_path):
                report.error(
                    "音频缺失",
                    filename,
                    f"引用了 '{ref}' 但文件不存在",
                    fixable=False,
                )


def check_placeholder_residual(report, articles):
    """检查 3: AUDIO_FILE_PLACEHOLDER 残留"""
    for filepath in articles:
        filename = os.path.basename(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if "AUDIO_FILE_PLACEHOLDER" in content:
            # 检查是否有真实音频引用（除了 placeholder）
            refs = extract_audio_refs(content)
            real_refs = [r for r in refs if "PLACEHOLDER" not in r]
            if not real_refs:
                report.error(
                    "占位符残留",
                    filename,
                    "文章有 AUDIO_FILE_PLACEHOLDER 但无真实音频",
                    fixable=True,
                )


def check_orphan_audio(report, articles):
    """检查 4: 孤儿音频文件（存在但未被任何文章引用）"""
    actual_files = set(get_actual_audio_files())
    referenced_files = set()

    for filepath in articles:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        refs = extract_audio_refs(content)
        for ref in refs:
            normalized = normalize_audio_path(ref)
            audio_filename = normalized.replace("audio/", "")
            referenced_files.add(audio_filename)

    orphans = actual_files - referenced_files
    for orphan in sorted(orphans):
        # 跳过播客音频
        if any(orphan.startswith(p) for p in PODCAST_AUDIO_PATTERNS):
            continue
        report.warn(
            "孤儿音频",
            f"audio/{orphan}",
            f"音频文件存在但未被任何文章引用",
            fixable=False,
        )


def check_filename_convention(report):
    """检查 5: 音频文件名是否规范"""
    actual_files = get_actual_audio_files()
    for filename in actual_files:
        # 检查中文字符
        if re.search(r'[\u4e00-\u9fff]', filename):
            report.warn(
                "文件名不规范",
                f"audio/{filename}",
                "文件名包含中文字符，建议改为英文",
                fixable=False,
            )
        # 检查 .md.mp3 后缀
        if ".md.mp3" in filename:
            report.error(
                "文件名错误",
                f"audio/{filename}",
                "文件名包含 '.md.mp3'，应为 '.mp3'",
                fixable=True,
            )


def check_audio_player_markup(report, articles):
    """检查 6: 字数 >= 3000 的文章是否有音频播放器"""
    for filepath in articles:
        filename = os.path.basename(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 统计中文字数
        chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        if chars < 3000:
            continue

        # 检查音频播放器
        has_audio = bool(re.search(r'<audio|audio/.*\.mp3|\.mp3', content))
        has_placeholder = "AUDIO_FILE_PLACEHOLDER" in content

        if not has_audio and not has_placeholder:
            report.warn(
                "缺音频",
                filename,
                f"文章 {chars} 字 (>=3000) 但无音频播放器",
                fixable=False,
            )


# ── 修复函数 ──────────────────────────────────────────────────────────

def fix_audio_paths(articles):
    """修复: 标准化所有音频路径为 audio/xxx.mp3"""
    fixed = 0
    for filepath in articles:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # 修复 ../audio/xxx.mp3 → audio/xxx.mp3
        content = re.sub(
            r'(src|data-src)="\.\./audio/([^"]+\.mp3)"',
            r'\1="audio/\2"',
            content,
        )

        # 修复裸文件名 src="xxx.mp3" → src="audio/xxx.mp3"
        # 但要排除已经是 audio/ 或 http 开头的
        def fix_bare_ref(match):
            attr = match.group(1)
            ref = match.group(2)
            if ref.startswith("audio/") or ref.startswith("http") or ref.startswith("//"):
                return match.group(0)
            return f'{attr}="audio/{ref}"'

        content = re.sub(r'(src|data-src)="([^"]*\.mp3)"', fix_bare_ref, content)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            fixed += 1
            print(f"  ✅ 修复路径: {os.path.basename(filepath)}")

    return fixed


def fix_placeholder(articles):
    """修复: 移除 AUDIO_FILE_PLACEHOLDER（无真实音频的文章）"""
    fixed = 0
    for filepath in articles:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if "AUDIO_FILE_PLACEHOLDER" not in content:
            continue

        # 移除包含 placeholder 的 audio 标签
        content = re.sub(
            r'<source[^>]*AUDIO_FILE_PLACEHOLDER[^>]*/?>',
            '',
            content,
        )
        content = re.sub(
            r'src="AUDIO_FILE_PLACEHOLDER"',
            '',
            content,
        )

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        fixed += 1
        print(f"  ✅ 移除占位符: {os.path.basename(filepath)}")

    return fixed


def fix_filenames():
    """修复: 修正不规范的音频文件名"""
    fixed = 0
    actual_files = get_actual_audio_files()

    for filename in actual_files:
        new_name = filename

        # 修复 .md.mp3 → .mp3
        if ".md.mp3" in new_name:
            new_name = new_name.replace(".md.mp3", ".mp3")

        if new_name != filename:
            old_path = os.path.join(AUDIO_DIR, filename)
            new_path = os.path.join(AUDIO_DIR, new_name)
            if not os.path.exists(new_path):
                shutil.move(old_path, new_path)
                fixed += 1
                print(f"  ✅ 重命名: {filename} → {new_name}")

                # 更新所有引用此文件的文章
                for filepath in get_html_articles():
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if filename in content:
                        content = content.replace(filename, new_name)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"    📝 更新引用: {os.path.basename(filepath)}")

    return fixed


# ── 主函数 ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="博客资产完整性检查器")
    parser.add_argument("--fix", action="store_true", help="自动修复所有可修复问题")
    parser.add_argument("--fix-paths", action="store_true", help="只修复音频路径不一致")
    parser.add_argument("--report", action="store_true", help="输出 JSON 报告")
    parser.add_argument("--recent", type=int, default=None, help="只检查最近 N 天的文章")
    args = parser.parse_args()

    articles = get_html_articles(args.recent)
    if not articles:
        print("❌ 未找到文章文件")
        sys.exit(1)

    report = Report()

    # 执行检查
    check_audio_path_consistency(report, articles)
    check_audio_file_existence(report, articles)
    check_placeholder_residual(report, articles)
    check_orphan_audio(report, articles)
    check_filename_convention(report)
    check_audio_player_markup(report, articles)

    # 修复模式
    if args.fix or args.fix_paths:
        print("\n🔧 开始修复...")
        total_fixed = 0

        print("\n  [1/3] 标准化音频路径...")
        total_fixed += fix_audio_paths(articles)

        print("\n  [2/3] 清理占位符...")
        total_fixed += fix_placeholder(articles)

        print("\n  [3/3] 修正文件名...")
        total_fixed += fix_filenames()

        print(f"\n✅ 共修复 {total_fixed} 项")

        if args.fix:
            # 修复后重新检查
            report = Report()
            articles = get_html_articles(args.recent)
            check_audio_path_consistency(report, articles)
            check_audio_file_existence(report, articles)
            check_placeholder_residual(report, articles)
            check_orphan_audio(report, articles)
            check_filename_convention(report)
            check_audio_player_markup(report, articles)

    # 输出报告
    if args.report:
        print(json.dumps(report.to_json(), ensure_ascii=False, indent=2))
    else:
        report.print_report()

    # 退出码
    if report.errors:
        sys.exit(1)
    elif report.warnings:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
