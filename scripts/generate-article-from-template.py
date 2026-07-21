#!/usr/bin/env python3
"""
严格基于V4模板生成文章，保证结构100%一致。
用法：python3 generate-article-from-template.py --config article.json
"""

import json
import sys
import os
import re

TEMPLATE_PATH = "/tmp/sandbot-gh/templates/post-template-v4.html"

def generate_article(config_path):
    """读取配置，基于模板生成文章"""
    
    # 读取配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 读取模板
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 提取完整CSS（保证样式100%一致）
    css_match = re.search(r'<style>(.*?)</style>', template, re.DOTALL)
    full_css = css_match.group(1) if css_match else ''
    
    # 替换占位符
    content = template
    
    # 基础信息
    content = content.replace('文章标题写在这里', config.get('title', '标题'))
    content = content.replace('一句话概括核心内容，不是标题重复，是读者读完后应该记住的那句话。', 
                              config.get('subtitle', '副标题'))
    
    # 分类标签
    content = content.replace('<span class="label-category">产品发布</span>', 
                              f'<span class="label-category">{config.get("category", "分类")}</span>')
    
    # 元信息
    content = content.replace('<span class="tag tag-launch">LAUNCH</span>', 
                              f'<span class="tag {config.get("tag_class", "tag-launch")}">{config.get("tag_text", "标签")}</span>')
    content = content.replace('<span>Sandbot 解读</span>\n    <span class="dot"></span>\n    <span>2026-07-09</span>', 
                              f'<span>{config.get("source_label", "Sandbot 解读")}</span>\n    <span class="dot"></span>\n    <span>{config.get("date", "2026-01-01")}</span>')
    content = content.replace('<span>6 分钟</span>', 
                              f'<span>{config.get("read_time", "6 分钟")}</span>')
    
    # 三十秒速览
    quick_glance_items = config.get('quick_glance', ['要点一', '要点二', '要点三'])
    quick_glance_html = '\n    '.join([f'<li>{item}</li>' for item in quick_glance_items])
    content = content.replace(
        '''<ul>
      <li>要点一：具体数据 + 核心发现</li>
      <li>要点二：机制解释 + 为什么重要</li>
      <li>要点三：和我的关系 + 实操启示</li>
    </ul>''',
        f'<ul>\n    {quick_glance_html}\n    </ul>'
    )
    
    # 来源声明
    content = content.replace(
        '<strong>⚑ 来源</strong>：标注信息来源和立场。例如：本文基于 XX 官方发布内容整理，文中数据属官方演示，未经第三方独立复现。',
        config.get('source_note', '<strong>⚑ 来源</strong>：来源说明')
    )
    
    # 上手卡（可选）
    if 'takeaway' in config:
        takeaway = config['takeaway']
        takeaway_items = takeaway.get('items', [])
        takeaway_html = '\n    '.join([f'<li>{item}</li>' for item in takeaway_items])
        takeaway_block = f'''  <!-- 🧰 上手卡 -->
  <div class="takeaway-card">
    <div class="takeaway-label">🧰 上手卡 · {takeaway.get('product', '产品')}</div>
    <ul>
    {takeaway_html}
    </ul>
  </div>'''
        # 替换模板中的示例上手卡
        content = re.sub(
            r'<!-- 🧰 上手卡.*?</div>\s*',
            takeaway_block + '\n\n',
            content,
            flags=re.DOTALL
        )
    
    # 表格对比（可选）
    if 'compare_table' in config:
        table = config['compare_table']
        headers = table.get('headers', [])
        rows = table.get('rows', [])
        
        header_html = '\n    '.join([f'<th>{h}</th>' for h in headers])
        rows_html = '\n'.join([
            '    <tr>\n      ' + '\n      '.join([f'<td>{cell}</td>' for cell in row]) + '\n    </tr>'
            for row in rows
        ])
        
        table_block = f'''  <!-- 📊 表格对比 -->
  <table class="compare-table">
    <tr>
    {header_html}
    </tr>
{rows_html}
  </table>'''
        
        # 替换模板中的示例表格
        content = re.sub(
            r'<!-- 📊 表格对比.*?</table>\s*',
            table_block + '\n\n',
            content,
            flags=re.DOTALL
        )
    
    # 详细来源标注（可选）
    if 'source_detail' in config:
        sources = config['source_detail']
        source_items = '\n    '.join([f'<li>{s}</li>' for s in sources])
        source_block = f'''  <!-- 📎 详细来源标注 -->
  <div class="source-detail">
    <div class="source-label">⚑ 数据来源</div>
    <ul>
    {source_items}
    </ul>
  </div>'''
        
        # 替换模板中的示例来源标注
        content = re.sub(
            r'<!-- 📎 详细来源标注.*?</div>\s*',
            source_block + '\n\n',
            content,
            flags=re.DOTALL
        )
    
    # 输出文件
    output_path = config.get('output_path', '/tmp/sandbot-gh/posts/article.html')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Article generated: {output_path}")
    print(f"   Based on template: {TEMPLATE_PATH}")
    print(f"   Full CSS included: {len(full_css)} chars")
    return output_path

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 generate-article-from-template.py --config article.json")
        sys.exit(1)
    
    if sys.argv[1] == '--config':
        config_path = sys.argv[2]
        generate_article(config_path)
    else:
        print("Usage: python3 generate-article-from-template.py --config article.json")
        sys.exit(1)
