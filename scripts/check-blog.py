#!/usr/bin/env python3
"""
检查并修复 blog.html 中的中文引号问题
在 git push 前运行，避免 JS 解析失败
"""

import re
import sys

def check_chinese_quotes(file_path):
    """检查文件中的中文引号"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找中文引号
    chinese_quotes = re.findall(r'["""]', content)
    
    if chinese_quotes:
        print(f"⚠️  发现 {len(chinese_quotes)} 个中文引号")
        return False
    else:
        print("✅ 没有中文引号")
        return True

def fix_chinese_quotes(file_path):
    """修复中文引号"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换中文引号为「」
    content = content.replace('"', '「').replace('"', '」').replace('"', '「')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 已修复中文引号")

def check_js_parse(file_path):
    """检查 JS 是否能正常解析"""
    import subprocess
    result = subprocess.run(
        ['node', '-e', f'''
const fs = require('fs');
const content = fs.readFileSync('{file_path}', 'utf8');
const match = content.match(/const articles = (\\[[\\s\\S]*?\\n\\]);/);
if (match) {{
  try {{
    const articles = eval(match[1]);
    console.log('✅ JS 解析正常，文章数量:', articles.length);
    process.exit(0);
  }} catch(e) {{
    console.log('❌ JS 解析错误:', e.message);
    process.exit(1);
  }}
}} else {{
  console.log('❌ 找不到 articles 数组');
  process.exit(1);
}}
        '''],
        capture_output=True,
        text=True
    )
    print(result.stdout.strip())
    return result.returncode == 0

if __name__ == '__main__':
    file_path = sys.argv[1] if len(sys.argv) > 1 else 'blog.html'
    
    print(f"检查文件: {file_path}")
    print()
    
    # 检查中文引号
    if not check_chinese_quotes(file_path):
        print("正在修复...")
        fix_chinese_quotes(file_path)
        print()
    
    # 检查 JS 解析
    if check_js_parse(file_path):
        print()
        print("✅ 文件可以安全推送")
        sys.exit(0)
    else:
        print()
        print("❌ 文件仍有问题，请手动检查")
        sys.exit(1)
