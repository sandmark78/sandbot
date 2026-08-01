#!/usr/bin/env python3
"""
批量给文章添加读者反馈组件
用法: python3 add-feedback-widget.py [--dry-run]
"""
import os, sys, re

BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
POSTS_DIR = os.path.join(BLOG_ROOT, "posts")

FEEDBACK_HTML = '''
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

dry_run = '--dry-run' in sys.argv
added = 0
skipped = 0

for f in sorted(os.listdir(POSTS_DIR)):
    if not f.endswith('.html'):
        continue
    if f in ('blog.html', 'index.html', 'podcast.html', 'subscribe.html', 'login.html', 'membership.html', 'monetization.html'):
        continue
    
    path = os.path.join(POSTS_DIR, f)
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    
    # 跳过已有反馈的
    if 'article-feedback' in content:
        skipped += 1
        continue
    
    # 在 </article> 或 </footer> 前插入
    if '</article>' in content:
        content = content.replace('</article>', FEEDBACK_HTML + '\n  </article>')
    elif '</footer>' in content:
        content = content.replace('</footer>', FEEDBACK_HTML + '\n  </footer>')
    else:
        print(f"⚠️  跳过 {f}（找不到插入点）")
        skipped += 1
        continue
    
    if not dry_run:
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(content)
    
    added += 1

print(f"{'[DRY RUN] ' if dry_run else ''}✅ 添加反馈组件: {added} 篇, 跳过: {skipped} 篇")
