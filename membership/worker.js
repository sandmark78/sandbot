/**
 * Sandbot 会员系统 - Cloudflare Worker
 * 
 * API:
 * POST /api/register - 注册 { email, password }
 * POST /api/login - 登录 { email, password }
 * POST /api/logout - 登出 { token }
 * POST /api/verify - 验证会员 { token }
 * POST /api/check-access - 检查文章访问权限 { token?, articleId }
 * POST /api/activate - 激活付费会员 { token, code }
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
      if (path === '/api/register') {
        return await handleRegister(body, env, corsHeaders);
      } else if (path === '/api/login') {
        return await handleLogin(body, env, corsHeaders);
      } else if (path === '/api/logout') {
        return await handleLogout(body, env, corsHeaders);
      } else if (path === '/api/verify') {
        return await handleVerify(body, env, corsHeaders);
      } else if (path === '/api/check-access') {
        return await handleCheckAccess(body, env, corsHeaders);
      } else if (path === '/api/activate') {
        return await handleActivate(body, env, corsHeaders);
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
 * 注册用户
 * POST /api/register { email, password }
 */
async function handleRegister(body, env, corsHeaders) {
  const { email, password } = body;
  
  if (!email || !password) {
    return jsonResponse({ error: 'Email and password required' }, 400, corsHeaders);
  }

  // Validate email
  if (!email.includes('@') || !email.includes('.')) {
    return jsonResponse({ error: 'Invalid email' }, 400, corsHeaders);
  }

  // Validate password
  if (password.length < 6) {
    return jsonResponse({ error: 'Password must be at least 6 characters' }, 400, corsHeaders);
  }

  // Check if user exists
  const userKey = `users:${email.toLowerCase()}`;
  const existingUser = await env.MEMBERS.get(userKey);
  
  if (existingUser) {
    return jsonResponse({ error: 'Email already registered' }, 409, corsHeaders);
  }

  // Hash password (simple hash for demo - use bcrypt in production)
  const hashedPassword = await hashPassword(password);

  // Create user
  const user = {
    email: email.toLowerCase(),
    password: hashedPassword,
    plan: 'free', // free or paid
    createdAt: Date.now(),
    articleCount: 0, // Track articles read (for guest/free limits)
  };

  // Save user
  await env.MEMBERS.put(userKey, JSON.stringify(user));

  // Generate session token
  const token = generateToken();
  const session = {
    email: user.email,
    plan: user.plan,
    createdAt: Date.now(),
    expiresAt: Date.now() + 7 * 24 * 60 * 60 * 1000, // 7 days
  };

  await env.MEMBERS.put(`sessions:${token}`, JSON.stringify(session));

  return jsonResponse({
    success: true,
    token,
    email: user.email,
    plan: user.plan,
  }, 200, corsHeaders);
}

/**
 * 登录
 * POST /api/login { email, password }
 */
async function handleLogin(body, env, corsHeaders) {
  const { email, password } = body;
  
  if (!email || !password) {
    return jsonResponse({ error: 'Email and password required' }, 400, corsHeaders);
  }

  // Get user
  const userKey = `users:${email.toLowerCase()}`;
  const userData = await env.MEMBERS.get(userKey);
  
  if (!userData) {
    return jsonResponse({ error: 'Invalid credentials' }, 401, corsHeaders);
  }

  const user = JSON.parse(userData);

  // Verify password
  const hashedPassword = await hashPassword(password);
  if (user.password !== hashedPassword) {
    return jsonResponse({ error: 'Invalid credentials' }, 401, corsHeaders);
  }

  // Generate session token
  const token = generateToken();
  const session = {
    email: user.email,
    plan: user.plan,
    createdAt: Date.now(),
    expiresAt: Date.now() + 7 * 24 * 60 * 60 * 1000, // 7 days
  };

  await env.MEMBERS.put(`sessions:${token}`, JSON.stringify(session));

  return jsonResponse({
    success: true,
    token,
    email: user.email,
    plan: user.plan,
  }, 200, corsHeaders);
}

/**
 * 登出
 * POST /api/logout { token }
 */
async function handleLogout(body, env, corsHeaders) {
  const { token } = body;
  
  if (!token) {
    return jsonResponse({ error: 'Token required' }, 400, corsHeaders);
  }

  await env.MEMBERS.delete(`sessions:${token}`);

  return jsonResponse({ success: true }, 200, corsHeaders);
}

/**
 * 验证会员状态
 * POST /api/verify { token }
 */
async function handleVerify(body, env, corsHeaders) {
  const { token } = body;
  
  if (!token) {
    return jsonResponse({ valid: false, error: 'Token required' }, 400, corsHeaders);
  }

  const sessionData = await env.MEMBERS.get(`sessions:${token}`);
  
  if (!sessionData) {
    return jsonResponse({ valid: false, error: 'Invalid session' }, 401, corsHeaders);
  }

  const session = JSON.parse(sessionData);

  // Check expiry
  if (session.expiresAt && session.expiresAt < Date.now()) {
    await env.MEMBERS.delete(`sessions:${token}`);
    return jsonResponse({ valid: false, error: 'Session expired' }, 401, corsHeaders);
  }

  // Get user data for plan info
  const userData = await env.MEMBERS.get(`users:${session.email}`);
  const user = userData ? JSON.parse(userData) : { plan: 'free' };

  return jsonResponse({
    valid: true,
    email: session.email,
    plan: user.plan,
    expiresAt: session.expiresAt,
  }, 200, corsHeaders);
}

/**
 * 检查文章访问权限
 * POST /api/check-access { token?, articleId, articleAccess }
 */
async function handleCheckAccess(body, env, corsHeaders) {
  const { token, articleId, articleAccess } = body;
  
  if (!articleId || !articleAccess) {
    return jsonResponse({ error: 'articleId and articleAccess required' }, 400, corsHeaders);
  }

  // Free articles are accessible to everyone
  if (articleAccess === 'free') {
    return jsonResponse({ allowed: true }, 200, corsHeaders);
  }

  // Member articles require authentication
  if (articleAccess === 'member') {
    if (!token) {
      return jsonResponse({ allowed: false, reason: 'login_required' }, 200, corsHeaders);
    }

    const sessionData = await env.MEMBERS.get(`sessions:${token}`);
    if (!sessionData) {
      return jsonResponse({ allowed: false, reason: 'invalid_session' }, 200, corsHeaders);
    }

    const session = JSON.parse(sessionData);
    const userData = await env.MEMBERS.get(`users:${session.email}`);
    const user = userData ? JSON.parse(userData) : { plan: 'free' };

    // Paid members can access all articles
    if (user.plan === 'paid') {
      return jsonResponse({ allowed: true, plan: 'paid' }, 200, corsHeaders);
    }

    // Free users cannot access member articles
    return jsonResponse({ allowed: false, reason: 'upgrade_required' }, 200, corsHeaders);
  }

  return jsonResponse({ allowed: false }, 200, corsHeaders);
}

/**
 * 激活付费会员
 * POST /api/activate { token, code }
 */
async function handleActivate(body, env, corsHeaders) {
  const { token, code } = body;
  
  if (!token || !code) {
    return jsonResponse({ error: 'Token and code required' }, 400, corsHeaders);
  }

  // Verify session
  const sessionData = await env.MEMBERS.get(`sessions:${token}`);
  if (!sessionData) {
    return jsonResponse({ error: 'Invalid session' }, 401, corsHeaders);
  }

  const session = JSON.parse(sessionData);

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

  // Update user plan to paid
  const userKey = `users:${session.email}`;
  const userData = await env.MEMBERS.get(userKey);
  const user = JSON.parse(userData);
  
  user.plan = 'paid';
  user.activatedAt = Date.now();
  user.code = code.toUpperCase();
  
  // Calculate expiry based on plan
  if (codeData.plan === 'monthly') {
    user.expiresAt = Date.now() + 30 * 24 * 60 * 60 * 1000;
  } else if (codeData.plan === 'yearly') {
    user.expiresAt = Date.now() + 365 * 24 * 60 * 60 * 1000;
  }
  // 'lifetime' has no expiry

  await env.MEMBERS.put(userKey, JSON.stringify(user));

  // Update session
  session.plan = 'paid';
  await env.MEMBERS.put(`sessions:${token}`, JSON.stringify(session));

  // Mark code as used
  codeData.used = true;
  codeData.usedAt = Date.now();
  codeData.usedBy = session.email;
  await env.CODES.put(codeKey, JSON.stringify(codeData));

  return jsonResponse({
    success: true,
    plan: 'paid',
    expiresAt: user.expiresAt,
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

// Helper: Simple password hash (use bcrypt in production)
async function hashPassword(password) {
  const encoder = new TextEncoder();
  const data = encoder.encode(password + 'sandbot_salt_2026');
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}
