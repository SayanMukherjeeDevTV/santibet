import type { Market, CategoryInfo } from './types';

let BACKEND_URL = process.env.NEXT_PUBLIC_API_URL;
if (!BACKEND_URL) {
  BACKEND_URL = process.env.NODE_ENV === 'production' 
    ? 'https://santibet-api.onrender.com'
    : 'http://127.0.0.1:8000';
}
if (!BACKEND_URL.startsWith('http')) {
  BACKEND_URL = `https://${BACKEND_URL}`;
}
BACKEND_URL = BACKEND_URL.replace(/\/$/, '');
const API_BASE_URL = typeof window !== 'undefined' ? '/v1' : `${BACKEND_URL}/v1`;

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  // If it's a login or refresh request, don't intercept 401s
  if (url.includes('/auth/login') || url.includes('/auth/refresh')) {
    return fetch(url, options);
  }

  // Ensure credentials are included so the HttpOnly refresh token is sent if needed
  options.credentials = 'include';

  let res = await fetch(url, options);

  if (res.status === 401) {
    if (!isRefreshing) {
      isRefreshing = true;
      refreshPromise = fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        credentials: 'include'
      })
      .then(async (refreshRes) => {
        if (refreshRes.ok) {
          const data = await refreshRes.json();
          // Backend uses AccessTokenResponse(access_token, user) but CamelModel converts it to accessToken
          const newAccessToken = data.accessToken;
          if (typeof window !== 'undefined') {
            localStorage.setItem('santibet_token', newAccessToken);
          }
          return newAccessToken;
        } else {
          if (typeof window !== 'undefined') {
            localStorage.removeItem('santibet_token');
            window.location.href = '/login';
          }
          return null;
        }
      })
      .catch(() => null)
      .finally(() => {
        isRefreshing = false;
        refreshPromise = null;
      });
    }

    const newAccessToken = await refreshPromise;
    if (newAccessToken) {
      const headers = new Headers(options.headers);
      headers.set('Authorization', `Bearer ${newAccessToken}`);
      options.headers = headers;
      res = await fetch(url, options);
    }
  }

  return res;
}


function getHeaders(customHeaders: Record<string, string> = {}) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('santibet_token') : null;
  const headers: Record<string, string> = { ...customHeaders };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function fetchStats() {
  const res = await apiFetch(`${API_BASE_URL}/platform-stats`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function fetchCategories(): Promise<CategoryInfo[]> {
  const res = await apiFetch(`${API_BASE_URL}/categories`, { headers: getHeaders() });
  if (!res.ok) return []; // Fallback to empty array
  return res.json();
}

export async function fetchFeaturedMarkets(): Promise<Market[]> {
  const res = await apiFetch(`${API_BASE_URL}/markets/featured`, { headers: getHeaders() });
  if (!res.ok) return [];
  return res.json();
}

export async function fetchMarkets(params?: Record<string, string>): Promise<{ items: Market[], next_cursor: string | null, total: number }> {
  let queryString = '';
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) searchParams.append(key, value);
    });
    queryString = `?${searchParams.toString()}`;
  }
  const res = await apiFetch(`${API_BASE_URL}/markets${queryString}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch markets');
  return res.json();
}

export async function fetchMarketBySlug(slug: string, range: string = '30d'): Promise<Market | null> {
  const res = await apiFetch(`${API_BASE_URL}/markets/${slug}?range=${range}`, { headers: getHeaders() });
  if (!res.ok) {
    if (res.status === 404) return null;
    throw new Error('Failed to fetch market details');
  }
  return res.json();
}

export async function reportMarket(slug: string, reason: string): Promise<void> {
  const res = await apiFetch(`${API_BASE_URL}/markets/${slug}/report`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ reason }),
  });
  if (!res.ok) throw new Error('Failed to report market');
}

export async function fetchCurrentUser() {
  const res = await apiFetch(`${API_BASE_URL}/users/me`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch user profile');
  return res.json();
}

export async function updateCurrentUser(data: { name?: string; avatarUrl?: string; regionCode?: string }) {
  const res = await apiFetch(`${API_BASE_URL}/users/me`, {
    method: 'PATCH',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update user profile');
  return res.json();
}

export async function placeOrder(slug: string, data: any) {
  const res = await apiFetch(`${API_BASE_URL}/markets/${slug}/orders`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error?.message || errorData.detail || 'Failed to place order');
  }
  return res.json();
}

export async function cancelOrder(orderId: string) {
  const res = await apiFetch(`${API_BASE_URL}/orders/${orderId}`, {
    method: 'DELETE',
    headers: getHeaders()
  });
  if (!res.ok) throw new Error('Failed to cancel order');
  return res.json();
}

export async function fetchUserOrders() {
  const res = await apiFetch(`${API_BASE_URL}/orders`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch orders');
  return res.json();
}

export async function fetchOrderBook(slug: string, outcome: string = 'YES') {
  const res = await apiFetch(`${API_BASE_URL}/markets/${slug}/orderbook?outcome=${encodeURIComponent(outcome)}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch order book');
  return res.json();
}

export async function fetchTradeHistory(slug: string, limit: number = 50) {
  const res = await apiFetch(`${API_BASE_URL}/markets/${slug}/trades?limit=${limit}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch trade history');
  return res.json();
}

export async function fetchWalletBalance() {
  const res = await apiFetch(`${API_BASE_URL}/wallet/balance`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch balance');
  return res.json();
}

export async function fetchWalletTransactions() {
  const res = await apiFetch(`${API_BASE_URL}/wallet/transactions`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch transactions');
  return res.json();
}

export async function depositFunds(amount: number, method: string = 'card') {
  const idempotencyKey = crypto.randomUUID();
  const res = await apiFetch(`${API_BASE_URL}/wallet/deposit`, {
    method: 'POST',
    headers: getHeaders({ 
      'Content-Type': 'application/json',
      'Idempotency-Key': idempotencyKey
    }),
    body: JSON.stringify({ amount, method }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error?.message || errorData.detail || 'Failed to deposit');
  }
  return res.json();
}

export async function withdrawFunds(amount: number, method: string = 'bank', destination?: string) {
  const idempotencyKey = crypto.randomUUID();
  const res = await apiFetch(`${API_BASE_URL}/wallet/withdraw`, {
    method: 'POST',
    headers: getHeaders({ 
      'Content-Type': 'application/json',
      'Idempotency-Key': idempotencyKey
    }),
    body: JSON.stringify({ amount, method, destination }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error?.message || errorData.detail || 'Failed to withdraw');
  }
  return res.json();
}

export async function fetchKycStatus() {
  const res = await apiFetch(`${API_BASE_URL}/kyc/status`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch KYC status');
  return res.json();
}

export async function startKyc() {
  const res = await apiFetch(`${API_BASE_URL}/kyc/start`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error?.message || errorData.detail || 'Failed to start KYC');
  }
  return res.json();
}

export async function fetchUserPositions() {
  const res = await apiFetch(`${API_BASE_URL}/users/me/positions`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch user positions');
  return res.json();
}

export async function fetchLeaderboard() {
  const res = await apiFetch(`${API_BASE_URL}/leaderboard`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch leaderboard');
  return res.json();
}

export async function fetchAIRecommendations(params?: Record<string, string>) {
  let queryString = '';
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) searchParams.append(key, value);
    });
    queryString = `?${searchParams.toString()}`;
  }
  const res = await apiFetch(`${API_BASE_URL}/ai/recommendations${queryString}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch AI recommendations');
  return res.json();
}

export async function fetchAIRecommendationById(id: string) {
  const res = await apiFetch(`${API_BASE_URL}/ai/recommendations/${id}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch AI recommendation details');
  return res.json();
}

export async function fetchAdminMarkets() {
  const res = await apiFetch(`${API_BASE_URL}/admin/markets`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch admin markets');
  return res.json();
}

export async function updateAdminMarket(marketId: string, data: any) {
  const res = await apiFetch(`${API_BASE_URL}/admin/markets/${marketId}`, {
    method: 'PATCH',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update market');
  return res.json();
}

export async function resolveAdminMarket(marketId: string, outcomeId: string) {
  const res = await apiFetch(`${API_BASE_URL}/admin/markets/${marketId}/resolve`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ outcome_id: outcomeId }),
  });
  if (!res.ok) throw new Error('Failed to resolve market');
  return res.json();
}

export async function fetchAdminUsers() {
  const res = await apiFetch(`${API_BASE_URL}/admin/users`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch admin users');
  return res.json();
}

export async function updateAdminUser(userId: string, data: any) {
  const res = await apiFetch(`${API_BASE_URL}/admin/users/${userId}`, {
    method: 'PATCH',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update user');
  return res.json();
}

export async function fetchAiReviewQueue() {
  const res = await apiFetch(`${API_BASE_URL}/admin/ai-review/queue`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch AI review queue');
  return res.json();
}

export async function approveAiReview(itemType: string, itemId: string) {
  const res = await apiFetch(`${API_BASE_URL}/admin/ai-review/${itemType}/${itemId}/approve`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error('Failed to approve AI item');
  return res.json();
}

export async function rejectAiReview(itemType: string, itemId: string) {
  const res = await apiFetch(`${API_BASE_URL}/admin/ai-review/${itemType}/${itemId}/reject`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error('Failed to reject AI item');
  return res.json();
}

export async function fetchAuditLog() {
  const res = await apiFetch(`${API_BASE_URL}/admin/audit-log`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch audit log');
  return res.json();
}

export async function fetchReports() {
  const res = await apiFetch(`${API_BASE_URL}/admin/reports`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch reports');
  return res.json();
}

export async function updateReport(reportId: string, data: any) {
  const res = await apiFetch(`${API_BASE_URL}/admin/reports/${reportId}`, {
    method: 'PATCH',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update report');
  return res.json();
}

// NOTE: This endpoint is meant for server-to-server communication with Stripe.
// This function is provided for manual debugging/testing purposes only.
export async function testStripeWebhook(payload: any, signature: string = 'test_signature') {
  const res = await apiFetch(`${API_BASE_URL}/webhooks/stripe`, {
    method: 'POST',
    headers: {
      'Stripe-Signature': signature,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Webhook test failed');
  return res.json();
}

export async function fetchWsTicket() {
  const res = await apiFetch(`${API_BASE_URL}/ws/ticket`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch websocket ticket');
  return res.json();
}
