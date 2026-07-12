# Sandbot 会员系统

## 架构

```
用户 → 前端 → Cloudflare Worker → KV 存储
      ↓
  会员文章（加密）→ 验证 → 解密 → 显示
```

## 组件

1. **Cloudflare Worker** (`worker.js`)
   - `/api/activate` - 激活会员
   - `/api/verify` - 验证会员状态
   - `/api/decrypt` - 解密会员文章

2. **KV 存储**
   - `members:{token}` - 会员信息
   - `codes:{code}` - 激活码

3. **前端** (`membership.html`)
   - 激活页面
   - 会员文章列表
   - 解密显示

## 激活码格式

```
SANDBOT-XXXX-XXXX-XXXX
```

## 会员等级

- 月度会员（30天）
- 年度会员（365天）
- 永久会员

## 部署

```bash
# 1. 安装 wrangler
npm install -g wrangler

# 2. 登录 Cloudflare
wrangler login

# 3. 创建 KV namespace
wrangler kv:namespace create MEMBERS
wrangler kv:namespace create CODES

# 4. 部署 Worker
wrangler deploy

# 5. 生成激活码
node generate-code.js
```

## 安全

- 会员文章 AES-256 加密
- 激活码单次使用
- Token 有效期验证
- CORS 限制域名
