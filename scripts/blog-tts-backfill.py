#!/usr/bin/env python3
"""
blog-tts-backfill.py — 博客 TTS 语音批量补全脚本 v1.0
Sandbot 每周工具脚本 · 2026-07-30

解决的问题（本周反复出现的坑）：
  1. 文章发布时 TTS 未生成（edge-tts 超时/失败静默跳过）
  2. 文章有 mp3 但 HTML 缺少 <audio> 标签（注入遗漏）
  3. 手动逐篇补 TTS 太慢，容易遗漏

功能：
  • 扫描所有博客文章，检测缺失 TTS 的情况
  • 自动提取正文 → 生成 edge-tts 语音 → 注入 audio player
  • 支持 dry-run 预览、单篇修复、批量补全
  • 速率控制：每篇间隔 2 秒，避免 edge-tts 限速

用法:
  python3 scripts/blog-tts-backfill.py                    # 扫描并报告
  python3 scripts/blog-tts-backfill.py --fix              # 自动补全所有缺失
  python3 scripts/blog-tts-backfill.py --fix --recent 7   # 只补最近 7 天的
  python3 scripts/blog-tts-backfill.py --fix --file posts/xxx.html  # 补单篇
  python3 scripts/blog-tts-backfill.py --inject-only      # 只修复 HTML 标签（不生成 mp3）
"""

import os
import sys
import re
import glob
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
# 博客根目录（自动解析，不依赖硬编码路径）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# ── 配置 ──────────────────────────────────────────────────────────────

REPO_DIR = BLOG_ROOT
POSTS_DIR = os.path.join(REPO_DIR, "posts")
AUDIO_DIR = os.path.join(POSTS_DIR, "audio")
SITE_URL = "https://sandbot.cgfan.com"
EXTRACT_SCRIPT = os.path.join(REPO_DIR, "scripts/extract-article-text.py")
TTS_VOICE = "zh-CN-YunxiNeural"
TTS_RATE = "-5%"
TTS_PITCH = "+3Hz"
MIN_TEXT_LENGTH = 300  # 少于 300 字符的文章不生成 TTS
DELAY_BETWEEN = 2  # 每篇间隔秒数

# Audio player HTML template
AUDIO_PLAYER_HTML = '''
<div class="audio-player">
  <span style="font-size:1.2em">🎧</span>
  <div style="flex:1">
    <div style="font-size:0.85em;color:var(--text-muted);margin-bottom:4px">Sandbot 语音版</div>
    <audio controls preload="none" style="width:100%;height:32px" src="AUDIO_SRC"></audio>
  </div>
</div>
'''


def get_all_articles(posts_dir, recent_days=None):
    """获取所有文章 HTML 文件"""
    pattern = os.path.join(posts_dir, "*.html")
    files = glob.glob(pattern)
    
    if recent_days:
        cutoff = datetime.now() - timedelta(days=recent_days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        filtered = []
        for f in files:
            basename = os.path.basename(f)
            # Extract date from filename (2026-07-30-xxx.html)
            match = re.match(r'(\d{4}-\d{2}-\d{2})-', basename)
            if match:
                if match.group(1) >= cutoff_str:
                    filtered.append(f)
            # Non-dated files (xia-*.html etc) — skip in recent mode
        files = filtered
    
    return sorted(files, reverse=True)


def check_article(article_path):
    """检查单篇文章的 TTS 状态"""
    basename = os.path.basename(article_path).replace('.html', '')
    mp3_path = os.path.join(AUDIO_DIR, f"{basename}.mp3")
    
    with open(article_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    has_mp3_file = os.path.exists(mp3_path)
    has_audio_tag = '<audio' in html or 'audio-player' in html
    has_mp3_reference = f'{basename}.mp3' in html
    
    status = "ok"
    issues = []
    
    if not has_mp3_file and not has_audio_tag:
        status = "missing_all"  # 没 mp3 也没标签
        issues.append("无 mp3 文件 + 无 audio 标签")
    elif not has_mp3_file:
        status = "missing_mp3"  # 有标签但没 mp3
        issues.append("有 audio 标签但无 mp3 文件")
    elif not has_audio_tag:
        status = "missing_tag"  # 有 mp3 但没标签
        issues.append("有 mp3 文件但无 audio 标签")
    elif not has_mp3_reference:
        status = "broken_ref"  # 有标签但引用路径不对
        issues.append("audio 标签引用路径可能错误")
    
    return {
        "file": article_path,
        "basename": basename,
        "status": status,
        "issues": issues,
        "has_mp3": has_mp3_file,
        "has_tag": has_audio_tag,
        "mp3_path": mp3_path,
    }


def extract_text(article_path):
    """从 HTML 提取正文文本"""
    if not os.path.exists(EXTRACT_SCRIPT):
        # Fallback: simple regex extraction
        with open(article_path, 'r', encoding='utf-8') as f:
            html = f.read()
        # Remove tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    try:
        result = subprocess.run(
            ["python3", EXTRACT_SCRIPT, article_path, "/dev/stdout"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception as e:
        print(f"  ⚠️  提取脚本失败: {e}")
    
    # Fallback
    with open(article_path, 'r', encoding='utf-8') as f:
        html = f.read()
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def generate_tts(text, output_path):
    """使用 edge-tts 生成语音"""
    try:
        # Use edge-tts CLI (more reliable than Python API in some envs)
        cmd = [
            "edge-tts",
            "--voice", TTS_VOICE,
            "--rate", TTS_RATE,
            "--pitch", TTS_PITCH,
            "--text", text[:5000],  # Limit to 5000 chars (~5 min audio)
            "--write-media", output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0 and os.path.exists(output_path):
            size = os.path.getsize(output_path)
            if size > 1000:  # At least 1KB
                return True, size
        
        return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "TTS generation timed out (120s)"
    except Exception as e:
        return False, str(e)


def inject_audio_player(article_path, mp3_relative_path):
    """注入 audio player 到文章 HTML"""
    with open(article_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Already has player? Just fix the src
    if 'class="audio-player"' in html:
        # Fix placeholder or wrong src
        html = re.sub(
            r'src="AUDIO_FILE_PLACEHOLDER"',
            f'src="{mp3_relative_path}"',
            html
        )
        html = re.sub(
            r'src="[^"]*\.mp3"',
            f'src="{mp3_relative_path}"',
            html
        )
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return True, "fixed_existing_player"
    
    # Find insertion point: after article-meta or after first <h1>
    player_html = AUDIO_PLAYER_HTML.replace("AUDIO_SRC", mp3_relative_path)
    
    # Try to insert after .article-meta
    meta_match = re.search(r'(class="article-meta".*?</div>\s*</div>)', html, re.DOTALL)
    if meta_match:
        insert_pos = meta_match.end()
        html = html[:insert_pos] + "\n" + player_html + html[insert_pos:]
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return True, "injected_after_meta"
    
    # Fallback: insert after first </h1>
    h1_match = re.search(r'</h1>\s*', html)
    if h1_match:
        insert_pos = h1_match.end()
        html = html[:insert_pos] + "\n" + player_html + html[insert_pos:]
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return True, "injected_after_h1"
    
    return False, "no_insertion_point_found"


def scan(posts_dir, recent_days=None):
    """扫描所有文章，报告 TTS 状态"""
    articles = get_all_articles(posts_dir, recent_days)
    
    results = {"ok": [], "missing_all": [], "missing_mp3": [], "missing_tag": [], "broken_ref": []}
    
    for article in articles:
        check = check_article(article)
        results[check["status"]].append(check)
    
    # Print report
    total = len(articles)
    ok_count = len(results["ok"])
    bad_count = total - ok_count
    
    print(f"\n🎧 博客 TTS 语音扫描报告")
    print(f"{'='*50}")
    print(f"📊 总计: {total} 篇文章")
    print(f"✅ 正常: {ok_count}")
    print(f"❌ 有问题: {bad_count}")
    print()
    
    if results["missing_all"]:
        print(f"🔴 完全缺失 (无 mp3 + 无标签): {len(results['missing_all'])} 篇")
        for c in results["missing_all"]:
            print(f"   • {c['basename']}")
        print()
    
    if results["missing_mp3"]:
        print(f"🟡 有标签无 mp3: {len(results['missing_mp3'])} 篇")
        for c in results["missing_mp3"]:
            print(f"   • {c['basename']}")
        print()
    
    if results["missing_tag"]:
        print(f"🟠 有 mp3 无标签: {len(results['missing_tag'])} 篇")
        for c in results["missing_tag"]:
            print(f"   • {c['basename']}")
        print()
    
    if results["broken_ref"]:
        print(f"🟣 引用路径错误: {len(results['broken_ref'])} 篇")
        for c in results["broken_ref"]:
            print(f"   • {c['basename']}")
        print()
    
    return results


def fix_all(posts_dir, recent_days=None, inject_only=False, dry_run=False):
    """补全所有缺失的 TTS"""
    articles = get_all_articles(posts_dir, recent_days)
    
    fixed = 0
    skipped = 0
    failed = 0
    
    for article in articles:
        check = check_article(article)
        
        if check["status"] == "ok":
            continue
        
        basename = check["basename"]
        mp3_path = check["mp3_path"]
        mp3_rel = f"audio/{basename}.mp3"
        
        print(f"\n📝 处理: {basename}")
        
        # Step 1: Generate mp3 if missing
        if not check["has_mp3"] and not inject_only:
            print(f"  1/2 提取正文...")
            text = extract_text(article)
            
            if len(text) < MIN_TEXT_LENGTH:
                print(f"  ⏭️  正文太短 ({len(text)} 字符 < {MIN_TEXT_LENGTH})，跳过")
                skipped += 1
                continue
            
            print(f"  1/2 生成 TTS ({len(text)} 字符)...")
            
            if dry_run:
                print(f"  [DRY RUN] 将生成 mp3 → {mp3_path}")
            else:
                os.makedirs(AUDIO_DIR, exist_ok=True)
                success, info = generate_tts(text, mp3_path)
                if success:
                    print(f"  ✅ mp3 生成成功 ({info} bytes)")
                else:
                    print(f"  ❌ mp3 生成失败: {info}")
                    failed += 1
                    continue
                
                time.sleep(DELAY_BETWEEN)
        
        # Step 2: Inject audio player if missing
        if not check["has_tag"] or check["status"] in ("missing_tag", "broken_ref"):
            print(f"  2/2 注入 audio player...")
            
            if dry_run:
                print(f"  [DRY RUN] 将注入 audio player → {article}")
            else:
                success, method = inject_audio_player(article, mp3_rel)
                if success:
                    print(f"  ✅ player 注入成功 ({method})")
                else:
                    print(f"  ❌ player 注入失败: {method}")
                    failed += 1
                    continue
        
        fixed += 1
    
    print(f"\n{'='*50}")
    print(f"📊 处理完成: 修复 {fixed} 篇, 跳过 {skipped} 篇, 失败 {failed} 篇")
    
    return fixed, skipped, failed


def main():
    parser = argparse.ArgumentParser(description="博客 TTS 语音批量补全工具")
    parser.add_argument("--fix", action="store_true", help="自动补全所有缺失")
    parser.add_argument("--inject-only", action="store_true", help="只修复 HTML 标签，不生成 mp3")
    parser.add_argument("--recent", type=int, help="只处理最近 N 天的文章")
    parser.add_argument("--file", type=str, help="只处理指定文件")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际修改")
    parser.add_argument("--posts-dir", default=POSTS_DIR, help="文章目录")
    
    args = parser.parse_args()
    
    if args.file:
        # Single file mode
        article = os.path.abspath(args.file)
        if not os.path.exists(article):
            print(f"❌ 文件不存在: {article}")
            sys.exit(1)
        
        check = check_article(article)
        if check["status"] == "ok":
            print(f"✅ {check['basename']} TTS 正常")
            sys.exit(0)
        
        print(f"❌ {check['basename']}: {', '.join(check['issues'])}")
        
        if args.fix:
            fix_all(os.path.dirname(article), inject_only=args.inject_only, dry_run=args.dry_run)
        sys.exit(1)
    
    if args.fix:
        fix_all(args.posts_dir, recent_days=args.recent, inject_only=args.inject_only, dry_run=args.dry_run)
    else:
        results = scan(args.posts_dir, recent_days=args.recent)
        bad = len(results["missing_all"]) + len(results["missing_mp3"]) + len(results["missing_tag"]) + len(results["broken_ref"])
        sys.exit(1 if bad > 0 else 0)


if __name__ == "__main__":
    main()
