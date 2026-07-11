#!/usr/bin/env python3
"""
给文章添加付费墙
用法: python3 add-paywall.py <article.html> [section_num]
section_num: 在第几个section后插入付费墙（默认2）
"""

import sys
import re

def add_paywall(filepath, section_num=2):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已有付费墙
    if 'paywall-notice' in content:
        print(f"⚠️  {filepath} 已有付费墙，跳过")
        return False
    
    # 付费墙HTML
    paywall_html = '''
    <!-- PAYWALL_START -->
    <div class="paywall-notice" id="paywallNotice" style="display: none;">
      <div class="paywall-icon">🔒</div>
      <h3>这是会员专属内容</h3>
      <p>你正在阅读的是深度分析的前 1/4。升级会员解锁全文。</p>
      <div class="paywall-buttons">
        <a href="/membership" class="btn-primary">升级会员</a>
        <a href="#" class="btn-secondary" onclick="buySingle(); return false;">只买这篇 ¥5</a>
      </div>
    </div>
    <div class="paywall-content" id="paywallContent" style="display: none;">
'''
    
    # 付费墙CSS
    paywall_css = '''
/* 付费墙样式 */
.paywall-notice {
  background: linear-gradient(135deg, var(--bg-warm) 0%, rgba(196, 149, 106, 0.1) 100%);
  border: 2px solid var(--accent-warm);
  border-radius: 12px;
  padding: 32px 24px;
  margin: 32px 0;
  text-align: center;
}
.paywall-icon { font-size: 3rem; margin-bottom: 16px; }
.paywall-notice h3 {
  font-family: 'Noto Serif SC', serif;
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 12px;
}
.paywall-notice p {
  color: var(--text-body);
  font-size: 0.95rem;
  margin-bottom: 24px;
}
.paywall-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}
.paywall-buttons .btn-primary {
  padding: 12px 24px;
  background: var(--accent-warm);
  color: #fff;
  text-decoration: none;
  border-radius: var(--radius);
  font-size: 0.9rem;
  font-weight: 500;
  transition: all var(--transition);
}
.paywall-buttons .btn-primary:hover { background: #b07d0a; }
.paywall-buttons .btn-secondary {
  padding: 12px 24px;
  background: transparent;
  color: var(--accent-warm);
  border: 1px solid var(--accent-warm);
  text-decoration: none;
  border-radius: var(--radius);
  font-size: 0.9rem;
  font-weight: 500;
  transition: all var(--transition);
}
.paywall-buttons .btn-secondary:hover { background: rgba(196, 149, 106, 0.1); }
.paywall-content.locked {
  position: relative;
  max-height: 0;
  overflow: hidden;
  opacity: 0.3;
  filter: blur(4px);
  pointer-events: none;
}
'''
    
    # 付费墙JS
    paywall_js = '''
<script>
// 付费墙逻辑
const API_URL = 'https://sandbot-membership.sandmark78.workers.dev';

async function checkPaywallAccess() {
  const token = localStorage.getItem('sandbot_token');
  const articleId = window.location.pathname.split('/').pop().replace('.html', '');
  
  const paywallNotice = document.getElementById('paywallNotice');
  const paywallContent = document.getElementById('paywallContent');
  
  if (!paywallNotice || !paywallContent) return;
  
  try {
    const res = await fetch(`${API_URL}/api/check-access`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, articleId, articleAccess: 'member' }),
    });
    const data = await res.json();
    
    if (data.allowed) {
      paywallNotice.style.display = 'none';
      paywallContent.style.display = 'block';
    } else {
      paywallNotice.style.display = 'block';
      paywallContent.classList.add('locked');
    }
  } catch (e) {
    console.error('Paywall check error:', e);
    paywallNotice.style.display = 'block';
    paywallContent.classList.add('locked');
  }
}

function buySingle() {
  alert('按篇购买功能即将上线，敬请期待！');
}

checkPaywallAccess();
</script>
'''
    
    # 插入付费墙HTML
    pattern = f'<h2><span class="section-num">{section_num}</span>'
    insert_pos = content.find(pattern)
    
    if insert_pos > 0:
        content = content[:insert_pos] + paywall_html + '\n    ' + content[insert_pos:]
        # 关闭 paywall-content
        content = content.replace('</article>', '    </div>\n  </article>')
    else:
        print(f"❌ {filepath} 未找到 section {section_num}")
        return False
    
    # 插入CSS（如果没有）
    if '.paywall-notice' not in content:
        content = content.replace('</style>', paywall_css + '</style>')
    
    # 插入JS（如果没有）
    if 'checkPaywallAccess' not in content:
        content = content.replace('</body>', paywall_js + '</body>')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {filepath} 付费墙已添加")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 add-paywall.py <article.html> [section_num]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    section_num = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    
    add_paywall(filepath, section_num)
