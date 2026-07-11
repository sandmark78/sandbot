#!/usr/bin/env python3
"""
给文章添加付费墙（小互风格）
用法: python3 add-paywall.py <article.html> [section_num] [remaining_minutes]
section_num: 在第几个section后插入付费墙（默认2）
remaining_minutes: 墙内剩余阅读时间（默认5）
"""

import sys
import re

def add_paywall(filepath, section_num=2, remaining_minutes=5):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已有付费墙
    if 'paywall-divider' in content:
        print(f"⚠️  {filepath} 已有付费墙，跳过")
        return False
    
    # 付费墙HTML（小互风格）
    paywall_html = f'''
    <!-- PAYWALL -->
    <div class="paywall-divider" id="paywallDivider">
      <div class="paywall-lock">🔒 MEMBERS ONLY</div>
      <h3>后面约 {remaining_minutes} 分钟，是会员的。</h3>
      <div class="paywall-details">
        <p>免费部分到这里（约前 1/4）。墙内还有：</p>
        <ul>
          <li>约 {remaining_minutes} 分钟正文</li>
          <li>数据卡片与图表</li>
          <li>Agent 视点深度分析</li>
        </ul>
      </div>
      <div class="paywall-actions">
        <a href="/login" class="paywall-login">已是会员？登录 →</a>
        <a href="/membership" class="paywall-upgrade">升级会员</a>
      </div>
      <p class="paywall-note">本文发布 90 天后免费开放全文。</p>
    </div>
    <div class="paywall-content-locked" id="paywallContent">
'''
    
    # 付费墙CSS
    paywall_css = '''
/* 付费墙样式 - 小互风格 */
.paywall-divider {
  margin: 48px 0;
  padding: 32px 24px;
  background: var(--bg-warm);
  border: 1px solid var(--border);
  border-radius: 12px;
  text-align: center;
}
.paywall-lock {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: var(--accent-warm);
  margin-bottom: 12px;
}
.paywall-divider h3 {
  font-family: 'Noto Serif SC', serif;
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 16px;
}
.paywall-details {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 20px;
  margin: 20px auto;
  max-width: 320px;
  text-align: left;
}
.paywall-details p {
  font-size: 0.85rem;
  color: var(--text-body);
  margin-bottom: 8px;
}
.paywall-details ul {
  margin: 0;
  padding-left: 18px;
  font-size: 0.85rem;
  color: var(--text-body);
}
.paywall-details li {
  margin-bottom: 4px;
}
.paywall-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin: 24px 0 16px;
}
.paywall-login {
  color: var(--accent);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
}
.paywall-login:hover { text-decoration: underline; }
.paywall-upgrade {
  padding: 10px 24px;
  background: var(--accent-warm);
  color: #fff;
  text-decoration: none;
  border-radius: var(--radius);
  font-size: 0.9rem;
  font-weight: 500;
}
.paywall-upgrade:hover { background: #b07d0a; }
.paywall-note {
  font-size: 0.75rem;
  color: var(--text-dim);
  margin-top: 16px;
}
.paywall-content-locked {
  display: none;
}
.paywall-content-locked.unlocked {
  display: block;
}
'''
    
    # 付费墙JS
    paywall_js = '''
<script>
// 付费墙逻辑
const API_URL = 'https://sandbot-membership.sandmark78.workers.dev';

async function checkPaywallAccess() {
  const token = localStorage.getItem('sandbot_token');
  const paywallDivider = document.getElementById('paywallDivider');
  const paywallContent = document.getElementById('paywallContent');
  
  if (!paywallDivider || !paywallContent) return;
  
  try {
    const res = await fetch(`${API_URL}/api/check-access`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, articleId: 'member', articleAccess: 'member' }),
    });
    const data = await res.json();
    
    if (data.allowed) {
      paywallDivider.style.display = 'none';
      paywallContent.classList.add('unlocked');
    }
  } catch (e) {
    console.error('Paywall check error:', e);
  }
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
    if '.paywall-divider' not in content:
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
        print("用法: python3 add-paywall.py <article.html> [section_num] [remaining_minutes]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    section_num = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    remaining_minutes = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    add_paywall(filepath, section_num, remaining_minutes)
