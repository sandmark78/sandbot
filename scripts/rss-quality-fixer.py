#!/usr/bin/env python3
"""
rss-quality-fixer.py — RSS 质量修复器 v1.0
Sandbot 每周工具脚本 · 2026-07-31

解决的问题（本周反复出现的坑）：
  1. RSS pubDate 全为 00:00:00，阅读器无法区分发布时间 (07-20, 07-26, 07-31)
  2. RSS 条目缺少必要字段 (description/category)
  3. RSS 条目指向不存在的文件 (幽灵条目)
  4. 重复 GUID/条目
  5. 文章文件名含时间信息 (noon/evening/early) 但未反映到 pubDate
  6. XML 结构不合规 (缺少 required elements)

用法:
  python3 scripts/rss-quality-fixer.py                    # 检查 + 报告
  python3 scripts/rss-quality-fixer.py --fix              # 检查 + 自动修复
  python3 scripts/rss-quality-fixer.py --fix-dates        # 只修复 pubDate
  python3 scripts/rss-quality-fixer.py --fix-orphans      # 只删除幽灵条目
  python3 scripts/rss-quality-fixer.py --validate         # 只验证 XML 合规性
  python3 scripts/rss-quality-fixer.py --json             # JSON 输出
  python3 scripts/rss-quality-fixer.py --dry-run          # 模拟修复（不写入）
"""

import os
import sys
import re
import json
import glob
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET
# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# ── 配置 ──────────────────────────────────────────────────────────────

REPO_DIR = BLOG_ROOT
POSTS_DIR = os.path.join(REPO_DIR, "posts")
FEED_XML = os.path.join(REPO_DIR, "feed.xml")
SITE_URL = "https://sandbot.cgfan.com"

# 时间段 → UTC 时间映射 (基于文件名中的时段标记)
TIME_PERIODS = {
    "early":    "00:00:00",  # 早间文章 → UTC 00:00
    "noon":     "04:00:00",  # 午间文章 (北京时间 12:00) → UTC 04:00
    "afternoon":"06:00:00",  # 下午文章 (北京时间 14:00) → UTC 06:00
    "evening":  "12:00:00",  # 晚间文章 (北京时间 20:00) → UTC 12:00
    "hot":      "12:00:00",  # 热点文章 (通常晚间发布) → UTC 12:00
}

# 文件名日期模式: 2026-07-31-noon-xxx.html 或 2026-07-31-xxx.html
FILENAME_DATE_PATTERN = re.compile(
    r'^(\d{4}-\d{2}-\d{2})(?:-(early|noon|afternoon|evening|hot))?-?(.+)$'
)

# ── 问题检测 ──────────────────────────────────────────────────────────

class RSSIssue:
    def __init__(self, severity, issue_type, message, item_title=None, fixable=False):
        self.severity = severity      # "error", "warning", "info"
        self.issue_type = issue_type  # "bad_date", "orphan", "duplicate", "missing_field", "xml_error"
        self.message = message
        self.item_title = item_title
        self.fixable = fixable

    def to_dict(self):
        return {
            "severity": self.severity,
            "type": self.issue_type,
            "message": self.message,
            "item_title": self.item_title,
            "fixable": self.fixable,
        }


def parse_feed(feed_path=None):
    """解析 RSS feed，返回 ElementTree 和 namespace"""
    path = feed_path or FEED_XML
    if not os.path.exists(path):
        return None, None
    
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        return tree, root
    except ET.ParseError as e:
        return None, str(e)


def extract_date_from_filename(filename):
    """从文件名提取日期和时间段"""
    basename = os.path.splitext(os.path.basename(filename))[0]
    match = FILENAME_DATE_PATTERN.match(basename)
    if match:
        date_str = match.group(1)
        period = match.group(2) or "early"
        return date_str, period
    return None, None


def extract_slug_from_link(link):
    """从 RSS link 提取文章 slug"""
    if not link:
        return None
    # https://sandbot.cgfan.com/posts/2026-07-31-evening-gemini-robotics-2
    # → 2026-07-31-evening-gemini-robotics-2
    parts = link.rstrip("/").split("/")
    return parts[-1] if parts else None


def check_pubdate_resolution(root):
    """检查 pubDate 是否全为 00:00:00 (缺少时间分辨率)"""
    issues = []
    channel = root.find("channel")
    if channel is None:
        return issues
    
    items = channel.findall("item")
    zero_count = 0
    total = len(items)
    
    for item in items:
        pub_date = item.findtext("pubDate", "")
        if "00:00:00" in pub_date:
            zero_count += 1
    
    if zero_count > 0:
        ratio = zero_count / total if total > 0 else 0
        severity = "error" if ratio > 0.5 else "warning"
        issues.append(RSSIssue(
            severity=severity,
            issue_type="bad_date",
            message=f"{zero_count}/{total} 条目的 pubDate 时间为 00:00:00 (无时间分辨率)",
            fixable=True,
        ))
    
    return issues


def check_orphan_items(root):
    """检查 RSS 条目是否指向不存在的文件 (幽灵条目)"""
    issues = []
    channel = root.find("channel")
    if channel is None:
        return issues
    
    for item in channel.findall("item"):
        link = item.findtext("link", "")
        title = item.findtext("title", "(无标题)")
        slug = extract_slug_from_link(link)
        
        if not slug:
            issues.append(RSSIssue(
                severity="error",
                issue_type="orphan",
                message=f"条目 link 无法解析: {link}",
                item_title=title,
                fixable=True,
            ))
            continue
        
        # 检查文件是否存在 (尝试 .html 和无后缀)
        file_path_html = os.path.join(POSTS_DIR, f"{slug}.html")
        file_path_no_ext = os.path.join(POSTS_DIR, slug)
        
        if not os.path.exists(file_path_html) and not os.path.exists(file_path_no_ext):
            issues.append(RSSIssue(
                severity="error",
                issue_type="orphan",
                message=f"幽灵条目: 文件不存在 → {slug}",
                item_title=title,
                fixable=True,
            ))
    
    return issues


def check_duplicate_guids(root):
    """检查重复的 GUID"""
    issues = []
    channel = root.find("channel")
    if channel is None:
        return issues
    
    guids = {}
    for item in channel.findall("item"):
        guid = item.findtext("guid", "")
        title = item.findtext("title", "(无标题)")
        if guid:
            if guid in guids:
                issues.append(RSSIssue(
                    severity="error",
                    issue_type="duplicate",
                    message=f"重复 GUID: {guid} (首次: {guids[guid]}, 重复: {title})",
                    item_title=title,
                    fixable=True,
                ))
            else:
                guids[guid] = title
    
    return issues


def check_required_fields(root):
    """检查 RSS 条目是否缺少必要字段"""
    issues = []
    channel = root.find("channel")
    if channel is None:
        return issues
    
    required = ["title", "link", "description"]
    recommended = ["pubDate", "guid", "category"]
    
    for item in channel.findall("item"):
        title = item.findtext("title", "(无标题)")
        
        for field in required:
            if not item.findtext(field, "").strip():
                issues.append(RSSIssue(
                    severity="error",
                    issue_type="missing_field",
                    message=f"缺少必填字段 <{field}>: {title}",
                    item_title=title,
                    fixable=False,
                ))
        
        for field in recommended:
            if not item.findtext(field, "").strip():
                issues.append(RSSIssue(
                    severity="warning",
                    issue_type="missing_field",
                    message=f"缺少推荐字段 <{field}>: {title}",
                    item_title=title,
                    fixable=True,
                ))
    
    return issues


def check_xml_compliance(root):
    """检查 XML 结构合规性"""
    issues = []
    
    # 检查根元素
    if root.tag != "rss":
        issues.append(RSSIssue(
            severity="error",
            issue_type="xml_error",
            message=f"根元素应为 <rss>，实际为 <{root.tag}>",
            fixable=False,
        ))
    
    # 检查 version 属性
    version = root.get("version", "")
    if version != "2.0":
        issues.append(RSSIssue(
            severity="warning",
            issue_type="xml_error",
            message=f"RSS version 应为 '2.0'，实际为 '{version}'",
            fixable=True,
        ))
    
    # 检查 channel 存在
    channel = root.find("channel")
    if channel is None:
        issues.append(RSSIssue(
            severity="error",
            issue_type="xml_error",
            message="缺少 <channel> 元素",
            fixable=False,
        ))
        return issues
    
    # 检查 channel 必填字段
    for field in ["title", "link", "description"]:
        if not channel.findtext(field, "").strip():
            issues.append(RSSIssue(
                severity="error",
                issue_type="xml_error",
                message=f"channel 缺少必填字段 <{field}>",
                fixable=False,
            ))
    
    return issues


def check_item_count(root):
    """检查 RSS 条目数量是否合理"""
    issues = []
    channel = root.find("channel")
    if channel is None:
        return issues
    
    items = channel.findall("item")
    count = len(items)
    
    if count == 0:
        issues.append(RSSIssue(
            severity="error",
            issue_type="info",
            message="RSS 没有任何条目",
            fixable=False,
        ))
    elif count > 100:
        issues.append(RSSIssue(
            severity="warning",
            issue_type="info",
            message=f"RSS 有 {count} 条目，建议控制在 50 以内 (RSS 最佳实践)",
            fixable=True,
        ))
    
    return issues


# ── 修复功能 ──────────────────────────────────────────────────────────

def fix_pubdate(tree, root, dry_run=False):
    """修复 pubDate：从文件名提取实际时间段，更新 pubDate 时间部分"""
    channel = root.find("channel")
    if channel is None:
        return 0
    
    fixed = 0
    for item in channel.findall("item"):
        pub_date = item.findtext("pubDate", "")
        link = item.findtext("link", "")
        title = item.findtext("title", "")
        
        if "00:00:00" not in pub_date:
            continue
        
        slug = extract_slug_from_link(link)
        if not slug:
            continue
        
        date_str, period = extract_date_from_filename(slug)
        
        # 确定时间: 优先用文件名标记，其次用文件 mtime
        if date_str and period:
            time_str = TIME_PERIODS.get(period, "00:00:00")
        else:
            # 回退: 从文件修改时间推断
            time_str = _get_time_from_file(slug)
            if not date_str:
                # 文件名里连日期都没有，跳过
                continue
        
        # 解析当前 pubDate 的日期部分
        # 格式: "Fri, 31 Jul 2026 00:00:00 +0000"
        try:
            date_match = re.match(
                r'(\w+, \d+ \w+ \d{4}) \d{2}:\d{2}:\d{2} ([+-]\d{4})',
                pub_date
            )
            if date_match:
                date_part = date_match.group(1)
                tz_part = date_match.group(2)
                new_pubdate = f"{date_part} {time_str} {tz_part}"
                
                if not dry_run:
                    pub_date_elem = item.find("pubDate")
                    if pub_date_elem is not None:
                        pub_date_elem.text = new_pubdate
                
                fixed += 1
        except Exception:
            pass
    
    return fixed


def _get_time_from_file(slug):
    """从文件修改时间推断发布时间，返回 HH:MM:SS 字符串"""
    for ext in [".html", ""]:
        fpath = os.path.join(POSTS_DIR, slug + ext)
        if os.path.exists(fpath):
            mtime = os.path.getmtime(fpath)
            dt = datetime.utcfromtimestamp(mtime)
            return dt.strftime("%H:%M:%S")
    return "00:00:00"


def fix_orphan_items(tree, root, dry_run=False):
    """删除指向不存在文件的幽灵条目"""
    channel = root.find("channel")
    if channel is None:
        return 0
    
    removed = 0
    items_to_remove = []
    
    for item in channel.findall("item"):
        link = item.findtext("link", "")
        slug = extract_slug_from_link(link)
        
        if not slug:
            items_to_remove.append(item)
            continue
        
        file_path_html = os.path.join(POSTS_DIR, f"{slug}.html")
        file_path_no_ext = os.path.join(POSTS_DIR, slug)
        
        if not os.path.exists(file_path_html) and not os.path.exists(file_path_no_ext):
            items_to_remove.append(item)
    
    for item in items_to_remove:
        if not dry_run:
            channel.remove(item)
        removed += 1
    
    return removed


def fix_duplicates(tree, root, dry_run=False):
    """删除重复 GUID 的条目 (保留第一个)"""
    channel = root.find("channel")
    if channel is None:
        return 0
    
    seen_guids = {}
    items_to_remove = []
    
    for item in channel.findall("item"):
        guid = item.findtext("guid", "")
        if guid:
            if guid in seen_guids:
                items_to_remove.append(item)
            else:
                seen_guids[guid] = item
    
    for item in items_to_remove:
        if not dry_run:
            channel.remove(item)
    
    return len(items_to_remove)


def update_last_build_date(tree, root, dry_run=False):
    """更新 lastBuildDate 为当前时间"""
    channel = root.find("channel")
    if channel is None:
        return False
    
    now = datetime.utcnow()
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    new_date = "{}, {:02d} {} {:04d} {:02d}:{:02d}:{:02d} +0000".format(
        days[now.weekday()], now.day, months[now.month - 1],
        now.year, now.hour, now.minute, now.second
    )
    
    lbd = channel.find("lastBuildDate")
    if lbd is not None:
        if not dry_run:
            lbd.text = new_date
        return True
    return False


def trim_excess_items(tree, root, max_items=50, dry_run=False):
    """如果条目超过 max_items，删除最旧的"""
    channel = root.find("channel")
    if channel is None:
        return 0
    
    items = channel.findall("item")
    if len(items) <= max_items:
        return 0
    
    excess = len(items) - max_items
    # items 按新→旧排列，删除最后的
    for item in items[max_items:]:
        if not dry_run:
            channel.remove(item)
    
    return excess


def write_feed(tree):
    """写回 RSS 文件 (带备份)"""
    backup_path = FEED_XML + ".bak"
    shutil.copy2(FEED_XML, backup_path)
    
    # 注册 namespace 以保持 atom:link 格式
    ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
    
    # 使用 indent 方法美化 (Python 3.9+)
    try:
        ET.indent(tree, space="  ")
    except AttributeError:
        pass  # Python < 3.9，跳过美化
    
    tree.write(FEED_XML, encoding="UTF-8", xml_declaration=True)


def _pretty_print_xml(filepath):
    """简单 XML 美化 (添加缩进)"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # 在 > 后换行 + 缩进
    lines = []
    indent = 0
    # 简单处理：按标签缩进
    content = content.replace('><', '>\n<')
    
    for line in content.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        
        # 减少缩进 (闭合标签)
        if stripped.startswith('</') and not stripped.startswith('<?'):
            indent = max(0, indent - 1)
        
        lines.append('  ' * indent + stripped)
        
        # 增加缩进 (开始标签，非自闭合)
        if (stripped.startswith('<') and 
            not stripped.startswith('</') and 
            not stripped.startswith('<?') and
            not stripped.endswith('/>') and
            '>' in stripped and
            not stripped.startswith('<!')):
            # 如果同一行有闭合标签则不增加
            tag_name = re.match(r'<(\w+)', stripped)
            if tag_name:
                close_tag = f"</{tag_name.group(1)}>"
                if close_tag not in stripped:
                    indent += 1
    
    with open(filepath, 'w') as f:
        f.write('\n'.join(lines) + '\n')


# ── 主逻辑 ────────────────────────────────────────────────────────────

def run_checks(root):
    """运行所有检查，返回问题列表"""
    all_issues = []
    all_issues.extend(check_xml_compliance(root))
    all_issues.extend(check_pubdate_resolution(root))
    all_issues.extend(check_orphan_items(root))
    all_issues.extend(check_duplicate_guids(root))
    all_issues.extend(check_required_fields(root))
    all_issues.extend(check_item_count(root))
    return all_issues


def main():
    parser = argparse.ArgumentParser(description="RSS 质量修复器 v1.0")
    parser.add_argument("--fix", action="store_true", help="检查 + 自动修复")
    parser.add_argument("--fix-dates", action="store_true", help="只修复 pubDate")
    parser.add_argument("--fix-orphans", action="store_true", help="只删除幽灵条目")
    parser.add_argument("--validate", action="store_true", help="只验证 XML 合规性")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--dry-run", action="store_true", help="模拟修复（不写入）")
    parser.add_argument("--max-items", type=int, default=50, help="RSS 最大条目数 (默认 50)")
    parser.add_argument("--feed", type=str, default=FEED_XML, help="RSS 文件路径")
    
    args = parser.parse_args()
    
    # 更新模块级路径
    feed_path = args.feed
    if feed_path != FEED_XML:
        globals()['FEED_XML'] = feed_path
    
    # 解析
    tree, root = parse_feed()
    
    if tree is None and root is None:
        result = {"status": "error", "message": f"RSS 文件不存在: {FEED_XML}"}
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"❌ {result['message']}")
        sys.exit(1)
    
    if tree is None:
        result = {"status": "error", "message": f"RSS XML 解析失败: {root}"}
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"❌ {result['message']}")
        sys.exit(1)
    
    # 检查
    issues = run_checks(root)
    
    # 统计
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]
    
    # 修复
    fix_results = {}
    if args.fix or args.fix_dates or args.fix_orphans:
        if args.fix or args.fix_dates:
            n = fix_pubdate(tree, root, dry_run=args.dry_run)
            fix_results["pubdate_fixed"] = n
            
            n = update_last_build_date(tree, root, dry_run=args.dry_run)
            fix_results["last_build_date_updated"] = n
        
        if args.fix or args.fix_orphans:
            n = fix_orphan_items(tree, root, dry_run=args.dry_run)
            fix_results["orphans_removed"] = n
        
        if args.fix:
            n = fix_duplicates(tree, root, dry_run=args.dry_run)
            fix_results["duplicates_removed"] = n
            
            n = trim_excess_items(tree, root, max_items=args.max_items, dry_run=args.dry_run)
            fix_results["excess_trimmed"] = n
        
        # 写回
        if not args.dry_run and any(v > 0 for v in fix_results.values() if isinstance(v, int)):
            write_feed(tree)
            fix_results["written"] = True
        elif not args.dry_run:
            fix_results["written"] = False
    
    # 验证模式
    if args.validate:
        xml_issues = check_xml_compliance(root)
        if args.json:
            print(json.dumps({
                "status": "ok" if not xml_issues else "issues_found",
                "xml_issues": [i.to_dict() for i in xml_issues],
            }, ensure_ascii=False, indent=2))
        else:
            if not xml_issues:
                print("✅ XML 合规性检查通过")
            else:
                for issue in xml_issues:
                    icon = "❌" if issue.severity == "error" else "⚠️"
                    print(f"  {icon} {issue.message}")
        sys.exit(1 if xml_issues else 0)
    
    # 输出
    if args.json:
        output = {
            "status": "ok" if not errors else "issues_found",
            "summary": {
                "total_issues": len(issues),
                "errors": len(errors),
                "warnings": len(warnings),
                "infos": len(infos),
            },
            "issues": [i.to_dict() for i in issues],
            "fixes": fix_results if fix_results else None,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # 人类可读输出
        print("=" * 60)
        print("📡 RSS 质量检查报告")
        print(f"   文件: {FEED_XML}")
        print(f"   时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        print("=" * 60)
        
        channel = root.find("channel")
        item_count = len(channel.findall("item")) if channel is not None else 0
        print(f"\n📊 统计: {item_count} 条目")
        
        if errors:
            print(f"\n❌ 错误 ({len(errors)}):")
            for i in errors:
                fix_tag = " [可修复]" if i.fixable else ""
                print(f"  • {i.message}{fix_tag}")
        
        if warnings:
            print(f"\n⚠️  警告 ({len(warnings)}):")
            for i in warnings:
                fix_tag = " [可修复]" if i.fixable else ""
                print(f"  • {i.message}{fix_tag}")
        
        if not errors and not warnings:
            print("\n✅ 所有检查通过！RSS 质量良好。")
        
        if fix_results:
            print(f"\n🔧 修复结果:")
            for k, v in fix_results.items():
                if isinstance(v, bool):
                    status = "✅ 已写入" if v else "⏭️ 无需写入"
                    print(f"  • {k}: {status}")
                elif v > 0:
                    print(f"  • {k}: {v}")
            
            if args.dry_run:
                print("\n⚠️  --dry-run 模式，未实际写入文件")
        
        print()
    
    # 退出码
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
