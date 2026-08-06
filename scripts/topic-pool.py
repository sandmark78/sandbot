#!/usr/bin/env python3
"""
统一素材池管理器
用法:
  python3 topic-pool.py add --title "标题" --score 300 --url "URL" --summary "摘要" [--source hn] [--slot early]
  python3 topic-pool.py add-batch --json '[{"title":"...", "score":300, ...}, ...]' [--slot early]
  python3 topic-pool.py list [--limit 10] [--unused-only]
  python3 topic-pool.py use --title "标题"
  python3 topic-pool.py stats

素材池文件: topics/YYYY-MM-DD-pool.json
"""

import json
import os
import sys
import re
import argparse
from datetime import datetime

BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
TOPICS_DIR = os.path.join(BLOG_ROOT, "topics")
TITLES_FILE = os.path.join(BLOG_ROOT, "article-titles.txt")

def get_pool_path(date=None):
    if date is None:
        date = datetime.utcnow().strftime("%Y-%m-%d")
    return os.path.join(TOPICS_DIR, f"{date}-pool.json")

def load_pool(date=None):
    path = get_pool_path(date)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"date": datetime.utcnow().strftime("%Y-%m-%d"), "topics": []}

def save_pool(pool, date=None):
    path = get_pool_path(date)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)

def normalize_title(title):
    """标准化标题用于去重比较"""
    t = title.lower().strip()
    # 去掉常见前缀
    t = re.sub(r'^(show hn|ask hn|tell hn|launch hn):\s*', '', t)
    # 去掉特殊字符
    t = re.sub(r'[^\w\s]', ' ', t)
    # 压缩空白
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def is_duplicate(pool, new_title, threshold=0.6):
    """检查是否和池中已有话题重复"""
    new_norm = normalize_title(new_title)
    new_words = set(new_norm.split())
    
    for topic in pool["topics"]:
        existing_norm = normalize_title(topic["title"])
        existing_words = set(existing_norm.split())
        
        if not new_words or not existing_words:
            continue
        
        # Jaccard 相似度
        intersection = new_words & existing_words
        union = new_words | existing_words
        similarity = len(intersection) / len(union) if union else 0
        
        if similarity >= threshold:
            return True, topic["title"], similarity
        
        # 完全包含关系
        if new_norm in existing_norm or existing_norm in new_norm:
            return True, topic["title"], 0.9
    
    return False, None, 0

def check_against_articles(new_title):
    """检查是否和已发布文章重复"""
    if not os.path.exists(TITLES_FILE):
        return False, None
    
    new_norm = normalize_title(new_title)
    new_words = set(new_norm.split())
    
    with open(TITLES_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取标题行
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('[') or line.startswith('#') or not line:
            continue
        # 去掉 [早鸟] 等前缀
        title = re.sub(r'^\[[^\]]+\]\s*', '', line).strip()
        if not title:
            continue
        
        existing_norm = normalize_title(title)
        existing_words = set(existing_norm.split())
        
        if not new_words or not existing_words:
            continue
        
        intersection = new_words & existing_words
        union = new_words | existing_words
        similarity = len(intersection) / len(union) if union else 0
        
        if similarity >= 0.5:
            return True, title
    
    return False, None

def add_topic(pool, title, score, url, summary, source="unknown", slot="unknown"):
    """添加话题到池，返回 (success, message)"""
    # 检查与已发布文章重复
    dup_article, article_title = check_against_articles(title)
    if dup_article:
        return False, f"❌ 与已发布文章重复: {article_title}"
    
    # 检查与池中已有话题重复
    dup_pool, pool_title, sim = is_duplicate(pool, title)
    if dup_pool:
        return False, f"❌ 与池中话题重复 (相似度{sim:.0%}): {pool_title}"
    
    topic = {
        "title": title,
        "score": score,
        "url": url,
        "summary": summary,
        "source": source,
        "slot": slot,
        "added_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "used": False,
        "used_by": None
    }
    pool["topics"].append(topic)
    return True, f"✅ 已添加: {title} (分数: {score})"

def cmd_add(args):
    pool = load_pool()
    success, msg = add_topic(pool, args.title, args.score, args.url, args.summary, args.source, args.slot)
    if success:
        save_pool(pool)
    print(msg)
    return 0 if success else 1

def cmd_add_batch(args):
    pool = load_pool()
    items = json.loads(args.json)
    added = 0
    skipped = 0
    for item in items:
        success, msg = add_topic(
            pool, 
            item["title"], 
            item.get("score", 0), 
            item.get("url", ""), 
            item.get("summary", ""),
            item.get("source", "unknown"),
            args.slot or "unknown"
        )
        if success:
            added += 1
        else:
            skipped += 1
        print(msg)
    
    save_pool(pool)
    print(f"\n📊 添加 {added} 个，跳过 {skipped} 个（重复）")
    return 0

def cmd_list(args):
    pool = load_pool()
    topics = pool["topics"]
    
    if args.unused_only:
        topics = [t for t in topics if not t.get("used", False)]
    
    # 按分数排序
    topics.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    if args.limit:
        topics = topics[:args.limit]
    
    print(f"📋 素材池 ({pool['date']}) — 共 {len(pool['topics'])} 个话题")
    if args.unused_only:
        print(f"   未使用: {len(topics)} 个")
    print()
    
    for i, t in enumerate(topics, 1):
        status = "✅已用" if t.get("used") else "⬜未用"
        used_info = f" → {t['used_by']}" if t.get("used_by") else ""
        print(f"{i}. [{status}] {t['title']}")
        print(f"   分数: {t['score']} | 来源: {t['source']} | 时段: {t['slot']}{used_info}")
        print(f"   URL: {t['url']}")
        if t.get('summary'):
            print(f"   摘要: {t['summary'][:100]}...")
        print()

def cmd_use(args):
    pool = load_pool()
    found = False
    for topic in pool["topics"]:
        if normalize_title(topic["title"]) == normalize_title(args.title):
            topic["used"] = True
            topic["used_by"] = args.used_by or "unknown"
            topic["used_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            found = True
            print(f"✅ 标记已用: {topic['title']} → {topic['used_by']}")
            break
    
    if not found:
        # 模糊匹配
        for topic in pool["topics"]:
            if is_duplicate({"topics": [topic]}, args.title, threshold=0.7)[0]:
                topic["used"] = True
                topic["used_by"] = args.used_by or "unknown"
                topic["used_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
                found = True
                print(f"✅ 标记已用(模糊匹配): {topic['title']} → {topic['used_by']}")
                break
    
    if found:
        save_pool(pool)
    else:
        print(f"⚠️ 未找到话题: {args.title}")
    
    return 0 if found else 1

def cmd_stats(args):
    pool = load_pool()
    total = len(pool["topics"])
    used = len([t for t in pool["topics"] if t.get("used")])
    unused = total - used
    
    print(f"📊 素材池统计 ({pool['date']})")
    print(f"   总话题: {total}")
    print(f"   已用: {used}")
    print(f"   未用: {unused}")
    
    # 按来源统计
    sources = {}
    for t in pool["topics"]:
        s = t.get("source", "unknown")
        sources[s] = sources.get(s, 0) + 1
    print(f"   来源: {', '.join(f'{k}:{v}' for k,v in sorted(sources.items()))}")

def main():
    parser = argparse.ArgumentParser(description="统一素材池管理器")
    subparsers = parser.add_subparsers(dest="command")
    
    # add
    p_add = subparsers.add_parser("add")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--score", type=int, default=0)
    p_add.add_argument("--url", default="")
    p_add.add_argument("--summary", default="")
    p_add.add_argument("--source", default="unknown")
    p_add.add_argument("--slot", default="unknown")
    
    # add-batch
    p_batch = subparsers.add_parser("add-batch")
    p_batch.add_argument("--json", required=True)
    p_batch.add_argument("--slot", default="unknown")
    
    # list
    p_list = subparsers.add_parser("list")
    p_list.add_argument("--limit", type=int)
    p_list.add_argument("--unused-only", action="store_true")
    
    # use
    p_use = subparsers.add_parser("use")
    p_use.add_argument("--title", required=True)
    p_use.add_argument("--used-by", default="")
    
    # stats
    subparsers.add_parser("stats")
    
    args = parser.parse_args()
    
    if args.command == "add":
        sys.exit(cmd_add(args))
    elif args.command == "add-batch":
        sys.exit(cmd_add_batch(args))
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "use":
        sys.exit(cmd_use(args))
    elif args.command == "stats":
        cmd_stats(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
