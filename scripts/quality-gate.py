#!/usr/bin/env python3
"""
文章质量门禁 V2 - 全面检查
用法: python3 quality-gate.py <html-file> [--slot morning|noon|afternoon|hot|evening]

检查项:
1. 中文字数 >= 阈值 (早间3000, 下午/晚间2500, 其他2000)
2. 图片 >= 1 (img 标签含 https src)
3. V4 模板 7 元素完整
4. Agent 视点段落存在
5. 文件名 ASCII + 日期前缀

退出码: 0=pass, 1=fail
"""
import re, sys, os

THRESHOLDS = {
    'morning': 3000,
    'noon': 2000,
    'afternoon': 2500,
    'hot': 2000,
    'evening': 2500,
}

V4_ELEMENTS = [
    'quick-glance', 'why-box', 'source-note',
    'bottom-quote', 'compare-box', 'capability-box', 'article-img'
]

def check(filepath, slot='noon'):
    errors = []
    warnings = []
    
    html = open(filepath, encoding='utf-8').read()
    filename = os.path.basename(filepath)
    
    # 1. Word count
    chars = len(re.findall(r'[\u4e00-\u9fff]', html))
    threshold = THRESHOLDS.get(slot, 2000)
    if chars < threshold:
        errors.append(f'字数不足: {chars} < {threshold}')
    elif chars < threshold * 0.8:
        warnings.append(f'字数偏低: {chars} (目标 {threshold})')
    
    # 2. Images
    imgs = len(re.findall(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', html))
    if imgs < 1:
        errors.append(f'缺少图片: 找到 {imgs} 张 (需要 >= 1)')
    
    # 3. V4 elements
    missing_v4 = [e for e in V4_ELEMENTS if e not in html]
    if missing_v4:
        errors.append(f'缺少V4元素: {missing_v4}')
    
    # 4. Agent 视点
    has_agent_view = bool(re.search(r'agent.?视点|Agent.?视点|agent-view', html, re.IGNORECASE))
    if not has_agent_view:
        errors.append('缺少 Agent 视点段落')
    
    # 5. Filename check
    ascii_ok = all(ord(c) < 128 for c in filename)
    date_prefix = r'^\d{4}-\d{2}-\d{2}-'
    fname_ok = ascii_ok and bool(re.match(date_prefix, filename))
    if not ascii_ok:
        errors.append(f'文件名含非ASCII字符: {filename}')
    if not re.match(date_prefix, filename):
        errors.append(f'文件名缺少日期前缀: {filename}')
    
    # Report
    print(f'📋 质量门禁检查: {filename}')
    print(f'   字数: {chars} (要求 >= {threshold}) {"✅" if chars >= threshold else "❌"}')
    print(f'   图片: {imgs} (要求 >= 1) {"✅" if imgs >= 1 else "❌"}')
    print(f'   V4元素: {7 - len(missing_v4)}/7 {"✅" if not missing_v4 else "❌ " + str(missing_v4)}')
    print(f'   Agent视点: {"✅" if has_agent_view else "❌"}')
    fname_status = "✅" if fname_ok else "❌"
    print(f'   文件名规范: {fname_status}')
    
    if warnings:
        for w in warnings:
            print(f'   ⚠️ {w}')
    
    if errors:
        print(f'\n❌ 门禁未通过 ({len(errors)} 个问题):')
        for e in errors:
            print(f'   • {e}')
        return False
    else:
        print(f'\n✅ 门禁通过！')
        return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 quality-gate.py <html-file> [--slot morning|noon|afternoon|hot|evening]')
        sys.exit(1)
    
    filepath = sys.argv[1]
    slot = 'noon'
    if '--slot' in sys.argv:
        idx = sys.argv.index('--slot')
        if idx + 1 < len(sys.argv):
            slot = sys.argv[idx + 1]
    
    ok = check(filepath, slot)
    sys.exit(0 if ok else 1)
