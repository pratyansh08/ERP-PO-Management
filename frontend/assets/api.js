// Frontend config: update if your backend is on a different host/port.
// If you serve the frontend from the same origin as the API, you can set API_BASE to "".
const API_BASE = "http://127.0.0.1:8000/api";

const TOKEN_STORAGE_KEY = "po_jwt_token";

function getToken() {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY) || "";
  } catch {
    return "";
  }
}

function setToken(token) {
  try {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } catch {
    // ignore
  }
}

function clearToken() {
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    // ignore
  }
}

function getGoogleLoginUrl(redirectTo) {
  const u = new URL(`${API_BASE}/auth/google/login`);
  if (redirectTo) u.searchParams.set("redirect_to", redirectTo);
  return u.toString();
}

async function apiFetch(path, { method = "GET", body, headers = {} } = {}) {
  const opts = {
    method,
    headers: {
      Accept: "application/json",
      ...headers,
    },
  };

  const token = getToken();
  if (token && !opts.headers.Authorization) {
    opts.headers.Authorization = `Bearer ${token}`;
  }

  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, opts);
  } catch (err) {
    throw new Error("Network error: unable to reach API");
  }

  const isJson = (res.headers.get("content-type") || "").includes("application/json");
  const data = isJson ? await res.json().catch(() => null) : await res.text().catch(() => null);

  if (!res.ok) {
    const detail = data && typeof data === "object" && "detail" in data ? data.detail : data;
    if (res.status === 401) {
      throw new Error("Unauthorized (401). Please log in with Google again.");
    }
    throw new Error(detail || `API error (${res.status})`);
  }

  return data;
}

function formatMoney(n) {
  const num = Number(n || 0);
  return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function toNumber(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

