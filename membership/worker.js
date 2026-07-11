/**
 * Sandbot 会员系统 - Cloudflare Worker
 * 
 * API:
 * POST /api/activate - 激活会员 { code: string }
 * POST /api/verify - 验证会员 { token: string }
 * POST /api/decrypt - 解密文章 { token: string, articleId: string }
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // Handle preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Only allow POST
    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'Method not allowed' }), {
        status: 405,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    try {
      const body = await request.json();

      // Route requests
      if (path === '/api/activate') {
        return await handleActivate(body, env, corsHeaders);
      } else if (path === '/api/verify') {
        return await handleVerify(body, env, corsHeaders);
      } else if (path === '/api/decrypt') {
        return await handleDecrypt(body, env, corsHeaders);
      } else {
        return new Response(JSON.stringify({ error: 'Not found' }), {
          status: 404,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
    } catch (e) {
      return new Response(JSON.stringify({ error: 'Invalid request' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }
  },
};

/**
 * 激活会员
 * POST /api/activate { code: "SANDBOT-XXXX-XXXX-XXXX" }
 */
async function handleActivate(body, env, corsHeaders) {
  const { code } = body;
  
  if (!code || typeof code !== 'string') {
    return jsonResponse({ error: 'Invalid code' }, 400, corsHeaders);
  }

  // Check if code exists
  const codeKey = `codes:${code.toUpperCase()}`;
  const codeData = await env.CODES.get(codeKey, 'json');
  
  if (!codeData) {
    return jsonResponse({ error: 'Invalid or expired code' }, 401, corsHeaders);
  }

  // Check if already used
  if (codeData.used) {
    return jsonResponse({ error: 'Code already used' }, 401, corsHeaders);
  }

  // Generate token
  const token = generateToken();
  const now = Date.now();
  
  // Calculate expiry
  let expiresAt = null;
  if (codeData.plan === 'monthly') {
    expiresAt = now + 30 * 24 * 60 * 60 * 1000;
  } else if (codeData.plan === 'yearly') {
    expiresAt = now + 365 * 24 * 60 * 60 * 1000;
  }
  // 'lifetime' has no expiry

  // Create member record
  const member = {
    token,
    plan: codeData.plan,
    activatedAt: now,
    expiresAt,
    code: code.toUpperCase(),
  };

  // Save member
  await env.MEMBERS.put(`members:${token}`, JSON.stringify(member));

  // Mark code as used
  codeData.used = true;
  codeData.usedAt = now;
  codeData.usedBy = token;
  await env.CODES.put(codeKey, JSON.stringify(codeData));

  return jsonResponse({
    success: true,
    token,
    plan: codeData.plan,
    expiresAt,
  }, 200, corsHeaders);
}

/**
 * 验证会员
 * POST /api/verify { token: "xxx" }
 */
async function handleVerify(body, env, corsHeaders) {
  const { token } = body;
  
  if (!token || typeof token !== 'string') {
    return jsonResponse({ error: 'Invalid token' }, 400, corsHeaders);
  }

  const memberKey = `members:${token}`;
  const member = await env.MEMBERS.get(memberKey, 'json');
  
  if (!member) {
    return jsonResponse({ valid: false, error: 'Invalid token' }, 401, corsHeaders);
  }

  // Check expiry
  if (member.expiresAt && member.expiresAt < Date.now()) {
    return jsonResponse({ valid: false, error: 'Membership expired' }, 401, corsHeaders);
  }

  return jsonResponse({
    valid: true,
    plan: member.plan,
    expiresAt: member.expiresAt,
  }, 200, corsHeaders);
}

/**
 * 解密文章
 * POST /api/decrypt { token: "xxx", articleId: "xxx" }
 */
async function handleDecrypt(body, env, corsHeaders) {
  const { token, articleId } = body;
  
  if (!token || !articleId) {
    return jsonResponse({ error: 'Missing token or articleId' }, 400, corsHeaders);
  }

  // Verify member first
  const memberKey = `members:${token}`;
  const member = await env.MEMBERS.get(memberKey, 'json');
  
  if (!member) {
    return jsonResponse({ error: 'Invalid token' }, 401, corsHeaders);
  }

  if (member.expiresAt && member.expiresAt < Date.now()) {
    return jsonResponse({ error: 'Membership expired' }, 401, corsHeaders);
  }

  // Get encrypted article
  const articleKey = `articles:${articleId}`;
  const encrypted = await env.MEMBERS.get(articleKey);
  
  if (!encrypted) {
    return jsonResponse({ error: 'Article not found' }, 404, corsHeaders);
  }

  // Decrypt (simple XOR for demo - use proper AES in production)
  const decrypted = decryptContent(encrypted, token);

  return jsonResponse({
    success: true,
    content: decrypted,
  }, 200, corsHeaders);
}

// Helper: JSON response
function jsonResponse(data, status, headers) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...headers, 'Content-Type': 'application/json' },
  });
}

// Helper: Generate random token
function generateToken() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let token = '';
  for (let i = 0; i < 32; i++) {
    token += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return token;
}

// Helper: Simple XOR decrypt (replace with proper AES in production)
function decryptContent(encrypted, key) {
  // In production, use Web Crypto API for proper AES-256 decryption
  // This is a simplified demo
  try {
    return atob(encrypted);
  } catch {
    return encrypted;
  }
}
