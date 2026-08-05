#!/usr/bin/env python3
"""
严格基于V4模板生成文章，保证结构100%一致。
用法: python3 generate-article-from-template.py --config article.json

修复记录:
- 2026-08-03: 修复 sections 替换逻辑（匹配模板实际结构：h2 + section-num）
- 2026-08-03: 修复音频路径（替换 AUDIO_FILE_PLACEHOLDER）
- 2026-08-03: 添加评分组件（article-feedback）
- 2026-08-03: 添加验证步骤，检查占位符残留
"""

import json
import sys
import os
import re
from datetime import datetime

# 博客根目录（自动解析）
BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
TEMPLATE_PATH = os.path.join(BLOG_ROOT, "templates/post-template-v4.html")


def generate_article(config_path):
    """读取配置，基于模板生成文章"""
    
    # 读取配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 读取模板
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 提取完整CSS
    css_match = re.search(r'<style>(.*?)</style>', template, re.DOTALL)
    full_css = css_match.group(1) if css_match else ''
    
    content = template
    
    # ========== 1. 基础信息替换 ==========
    content = content.replace('文章标题写在这里', config.get('title', '标题'))
    content = content.replace('一句话概括核心内容，不是标题重复，是读者读完后应该记住的那句话。', 
                              config.get('subtitle', '副标题'))
    
    # 分类标签
    content = content.replace('<span class="label-category">产品发布</span>', 
                              f'<span class="label-category">{config.get("category", "分类")}</span>')
    
    # 元信息
    content = content.replace('<span class="tag tag-launch">LAUNCH</span>', 
                              f'<span class="tag {config.get("tag_class", "tag-launch")}">{config.get("tag_text", "标签")}</span>')
    
    date_str = config.get('date', datetime.now().strftime('%Y-%m-%d'))
    content = content.replace('<span>Sandbot 解读</span>\n    <span class="dot"></span>\n    <span>2026-07-09</span>', 
                              f'<span>{config.get("source_label", "Sandbot 解读")}</span>\n    <span class="dot"></span>\n    <span>{date_str}</span>')
    content = content.replace('<span>6 分钟</span>', 
                              f'<span>{config.get("read_time", "6 分钟")}</span>')
    
    # ========== 1.5 Head 区域占位符替换 ==========
    title_text = config.get('title', '标题')
    subtitle_text = config.get('subtitle', '副标题')
    category_text = config.get('category', '分类')
    filename = config.get('filename', 'article.html')
    
    # [分类] 标题 → 实际标题
    content = content.replace('[分类] 标题', f'{category_text} {title_text}')
    # 文章文件名 → 实际文件名
    content = content.replace('文章文件名.html', filename)
    content = content.replace('文章文件名', filename.replace('.html', ''))
    # 一句话摘要 → subtitle
    content = content.replace('一句话摘要', subtitle_text)
    # 发布日期
    date_str = config.get('date', '2026-08-03')
    content = content.replace('"datePublished": "发布日期"', f'"datePublished": "{date_str}"')
    content = content.replace('"dateModified": "发布日期"', f'"dateModified": "{date_str}"')
    
    # ========== 2. 三十秒速览 ==========
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
    
    # ========== 3. Sections 替换（核心修复）==========
    # 模板结构: <h2><span class="section-num">1</span>...<p>正文内容...</p>
    # 需要替换整个正文区域（从第一个 section-num 到 Agent 视点之前）
    
    sections = config.get('sections', [])
    if sections:
        # 找到正文开始位置（第一个 section-num）
        body_start_match = re.search(r'<!-- 7\. 正文：编号 · 短标题 -->', content)
        if not body_start_match:
            # fallback: 找第一个 section-num
            body_start_match = re.search(r'<h2><span class="section-num">1</span>', content)
        
        # 找到正文结束位置（Agent 视点之前）
        body_end_match = re.search(r'<!-- (?:8\. )?Agent 视点', content)
        if not body_end_match:
            # fallback: 找 "NAgent 视点" 或 "Agent 视点"
            body_end_match = re.search(r'<h2[^>]*>.*?Agent 视点', content, re.DOTALL)
        
        if body_start_match and body_end_match:
            # 构建新的 sections HTML
            sections_html_parts = []
            for i, section in enumerate(sections, 1):
                # sub 是章节标题（显示在 section-sub），title 是分类标签
                section_sub = section.get('sub', section.get('title', f'章节 {i}'))
                section_content = section.get('content', '<p>正文内容...</p>')
                
                # 模板格式: <h2><span class="section-num">1</span><span class="section-dot">·</span><span class="section-sub">标题</span></h2>
                section_html = f'''  <h2><span class="section-num">{i}</span><span class="section-dot">·</span><span class="section-sub">{section_sub}</span></h2>
  
  {section_content}
'''
                sections_html_parts.append(section_html)
            
            new_sections_html = '\n'.join(sections_html_parts)
            
            # 替换正文区域
            content = content[:body_start_match.start()] + new_sections_html + '\n' + content[body_end_match.start():]
        else:
            print("⚠️  警告: 无法定位正文区域，sections 未替换")
    
    # ========== 3.5 Agent 视点替换 ==========
    # 模板中 Agent 视点（section N）有占位符文本，需要替换
    agent_viewpoint = config.get('agent_viewpoint', '')
    if agent_viewpoint:
        # 替换 Agent 视点区域的占位符内容
        # 模板结构: <h2><span class="section-num">N</span>...</h2> 后面是占位符内容
        import re as re2
        # 找到 Agent 视点标题之后、结论框之前的内容
        agent_pattern = r'(<h2><span class="section-num">N</span>.*?</h2>)\s*(.*?)(\s*<!-- 结论框 -->|\s*<div class="conclusion")'
        agent_match = re2.search(agent_pattern, content, re2.DOTALL)
        if agent_match:
            content = content[:agent_match.start(2)] + '\n  ' + agent_viewpoint + '\n' + content[agent_match.end(2):agent_match.start(3)] + content[agent_match.start(3):]
            print("   ✅ Agent 视点已替换")
        else:
            print("   ⚠️ 未找到 Agent 视点区域")
    
    # ========== 4. 音频路径替换 ==========
    # 自动生成带日期的文件名（如果没指定 output_path）
    output_path = config.get('output_path')
    if not output_path:
        # 自动格式: posts/YYYY-MM-DD-<slot>-<slug>.html
        date_str = config.get('date', datetime.now().strftime('%Y-%m-%d'))
        slot = config.get('slot', 'article')  # early/noon/afternoon/evening/hot
        title_slug = config.get('title', 'article')[:20].replace(' ', '-').lower()
        # 清理非 ASCII 字符
        title_slug = re.sub(r'[^\w\-]', '', title_slug)
        auto_filename = f"{date_str}-{slot}-{title_slug}.html"
        output_path = os.path.join(BLOG_ROOT, 'posts', auto_filename)
        print(f"   📝 自动生成文件名: {auto_filename}")
    
    article_filename = os.path.basename(output_path)
    article_base = os.path.splitext(article_filename)[0]
    audio_path = f'audio/{article_base}.mp3'
    content = content.replace('AUDIO_FILE_PLACEHOLDER', audio_path)
    # 也替换模板默认的 audio/article.mp3
    content = content.replace('audio/article.mp3', audio_path)
    
    # ========== 5. 添加评分组件 ==========
    if 'article-feedback' not in content:
        feedback_html = '''
    <div class="article-feedback" style="margin:40px 0;padding:24px;background:#f5f1eb;border:1px solid #e8e4de;border-radius:8px;text-align:center">
      <div style="font-family:'Noto Serif SC',serif;font-size:1.1rem;font-weight:600;color:#3d3d3d;margin-bottom:8px">你觉得这篇怎么样？</div>
      <div style="font-size:0.85rem;color:#8a8580;margin-bottom:16px">你的反馈帮我写得更好</div>
      <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
        <button onclick="fb(this,'useful')" style="padding:10px 20px;border:1px solid #e8e4de;border-radius:6px;background:#fffdf9;color:#525252;font-size:0.9rem;cursor:pointer;transition:all 0.2s">👍 有用</button>
        <button onclick="fb(this,'okay')" style="padding:10px 20px;border:1px solid #e8e4de;border-radius:6px;background:#fffdf9;color:#525252;font-size:0.9rem;cursor:pointer;transition:all 0.2s">😐 一般</button>
        <button onclick="fb(this,'not-interested')" style="padding:10px 20px;border:1px solid #e8e4de;border-radius:6px;background:#fffdf9;color:#525252;font-size:0.9rem;cursor:pointer;transition:all 0.2s">👎 不感兴趣</button>
      </div>
    </div>
    <script>
    function fb(btn,type){
      btn.parentElement.querySelectorAll('button').forEach(b=>{b.style.background='#fffdf9';b.style.color='#525252';b.disabled=false;b.textContent=b.textContent.replace('✓ ','')});
      btn.style.background='#7a9e7e';btn.style.color='#fff';btn.disabled=true;btn.textContent='✓ '+btn.textContent;
      var id=location.pathname.split('/').pop().replace('.html','');
      var f=JSON.parse(localStorage.getItem('fb')||'{}');f[id]=type;localStorage.setItem('fb',JSON.stringify(f));
    }
    (function(){
      var id=location.pathname.split('/').pop().replace('.html','');
      var f=JSON.parse(localStorage.getItem('fb')||'{}');
      if(f[id]){var btns=document.querySelectorAll('.article-feedback button');var m={'useful':0,'okay':1,'not-interested':2};var i=m[f[id]];if(btns[i]){btns[i].style.background='#7a9e7e';btns[i].style.color='#fff';btns[i].disabled=true;btns[i].textContent='✓ '+btns[i].textContent}}
    })();
    </script>
'''
        content = content.replace('</article>', feedback_html + '\n</article>')
    
    # ========== 6. 输出文件 ==========
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Article generated: {output_path}")
    print(f"   Based on template: {TEMPLATE_PATH}")
    print(f"   Full CSS included: {len(full_css)} chars")
    
    # ========== 7. 验证 ==========
    placeholders = content.count('正文内容...')
    if placeholders > 0:
        print(f"⚠️  警告: 发现 {placeholders} 处占位符残留")
    else:
        print("   ✅ 无占位符残留")
    
    if 'AUDIO_FILE_PLACEHOLDER' in content:
        print("⚠️  警告: 音频路径未替换")
    else:
        print("   ✅ 音频路径已替换")
    
    if 'article-feedback' not in content:
        print("⚠️  警告: 缺少评分组件")
    else:
        print("   ✅ 评分组件已添加")
    
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
