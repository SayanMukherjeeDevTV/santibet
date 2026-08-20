import re

with open("Client/lib/api.ts", "r") as f:
    content = f.read()

# Don't patch it twice
if "async function apiFetch" in content:
    print("Already patched")
    exit(0)

# Add apiFetch definition after API_BASE_URL
header_part = """const API_BASE_URL = typeof window !== 'undefined' ? '/v1' : 'http://127.0.0.1:8000/v1';

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
"""

content = content.replace("const API_BASE_URL = typeof window !== 'undefined' ? '/v1' : 'http://127.0.0.1:8000/v1';", header_part)

# Replace all `await fetch(` with `await apiFetch(`
content = content.replace("await fetch(", "await apiFetch(")

# But revert the one inside apiFetch itself
content = content.replace("let res = await apiFetch(url, options);", "let res = await fetch(url, options);")
content = content.replace("res = await apiFetch(url, options);", "res = await fetch(url, options);")
content = content.replace("refreshPromise = apiFetch(", "refreshPromise = fetch(")
content = content.replace("return apiFetch(url, options);", "return fetch(url, options);")

with open("Client/lib/api.ts", "w") as f:
    f.write(content)

print("Patched api.ts successfully!")
