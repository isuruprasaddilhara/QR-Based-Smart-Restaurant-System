const API = (process.env.REACT_APP_API_URL || "").replace(/\/$/, "");

export const AUTH_UPDATED_EVENT = "scan2serve:auth-updated";
export const SESSION_EXPIRED_EVENT = "scan2serve:session-expired";

let sessionExpiredHandling = false;

function parseJwtPayload(token) {
  if (!token || typeof token !== "string") return null;
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;
    let base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    while (base64.length % 4) base64 += "=";
    const json = atob(base64);
    return JSON.parse(json);
  } catch {
    return null;
  }
}

/** Milliseconds since epoch when access JWT expires, or null if unknown. */
export function getAccessTokenExpiresAtMs() {
  const token = getAccessToken();
  if (!token) return null;
  const p = parseJwtPayload(token);
  if (!p || typeof p.exp !== "number") return null;
  return p.exp * 1000;
}

/**
 * Clears stored auth and notifies listeners (redirect to login).
 * Safe to call when token is already cleared.
 */
export function notifySessionExpired() {
  if (sessionExpiredHandling) return;
  if (!getAccessToken()) return;
  sessionExpiredHandling = true;
  clearStoredAuth();
  window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT));
  window.setTimeout(() => {
    sessionExpiredHandling = false;
  }, 2000);
}

export function notifyAuthUpdated() {
  window.dispatchEvent(new CustomEvent(AUTH_UPDATED_EVENT));
}

/**
 * Intercept 401 responses (expired/invalid JWT) so the user is logged out.
 * Must not run on failed login (same status).
 */
export function installAuthFetchInterceptor() {
  if (typeof window === "undefined") return;
  if (window.__scan2serveAuthFetchInstalled) return;
  window.__scan2serveAuthFetchInstalled = true;
  const orig = window.fetch.bind(window);
  window.fetch = async function authFetch(input, init) {
    const response = await orig(input, init);
    if (response.status !== 401) return response;
    let url = "";
    if (typeof input === "string") url = input;
    else if (input && typeof input === "object" && "url" in input)
      url = String(input.url);
    if (url.includes("/users/auth/login/")) return response;
    // Wrong current password can be 401; do not treat as session expiry.
    if (url.includes("/users/auth/password/change/")) return response;
    notifySessionExpired();
    return response;
  };
}

export function getAccessToken() {
  return localStorage.getItem("access");
}

export function getStoredRole() {
  return localStorage.getItem("role") || "";
}

export function saveAuthFromLoginPayload(data) {
  const u = data.user;
  if (!u?.access) return;
  localStorage.setItem("access", u.access);
  localStorage.setItem("refresh", u.refresh);
  localStorage.setItem("role", u.role || "");
  localStorage.setItem("username", u.username || "");

  if (u.name != null && u.name !== "") {
    localStorage.setItem("name", u.name);
  }
}

export function clearStoredAuth() {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  localStorage.removeItem("role");
  localStorage.removeItem("username");
  localStorage.removeItem("name");
}

export function getDisplayName() {
  return localStorage.getItem("name") || localStorage.getItem("username") || "";
}

export function formatRoleLabel(role) {
  if (!role) return "Cashier";
  const map = {
    admin: "Admin",
    kitchen: "Kitchen",
    cashier: "Cashier",
  };
  return map[role] || role;
}

export function isAdminSession() {
  return Boolean(getAccessToken() && getStoredRole() === "admin");
}

export async function login({ email, password }) {
  const res = await fetch(`${API}/users/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: email.trim(), password }),
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const msg =
      data.errors?.non_field_errors?.[0] ||
      (typeof data.errors === "object" ? JSON.stringify(data.errors) : null) ||
      data.message ||
      "Login failed";
    throw new Error(msg);
  }

  return data;
}

export async function requestPasswordReset(email) {
  const res = await fetch(`${API}/users/auth/forgot-password/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: String(email || "").trim() }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg =
      data.errors?.email?.[0] ||
      data.detail ||
      data.message ||
      "Could not send reset email.";
    throw new Error(msg);
  }

  return data;
}

/**
 * Invite staff — admin JWT required.
 * role: "admin" | "kitchen" | "cashier"
 */
export async function registerStaff({
  email,
  name,
  password,
  phone_no = "",
  role = "kitchen",
}) {
  if (!isAdminSession()) {
    throw new Error(
      "Log in as an admin first. Only admins can invite staff accounts.",
    );
  }
  const access = getAccessToken();

  const res = await fetch(`${API}/users/auth/register/staff/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access}`,
    },
    body: JSON.stringify({
      email: email.trim(),
      name: name.trim(),
      password,
      phone_no: String(phone_no || "").trim(),
      role,
    }),
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const msg =
      data.errors && typeof data.errors === "object"
        ? JSON.stringify(data.errors)
        : data.detail || data.message || "Staff registration failed";
    throw new Error(msg);
  }

  return data;
}


//Password reset - added by Isuru
export async function confirmPasswordReset({ uid, token, new_password }) {
  const res = await fetch(
    `${API}/users/auth/reset-password/?uid=${encodeURIComponent(uid)}&token=${encodeURIComponent(token)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_password }),
    }
  );

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const msg =
      data.non_field_errors?.[0] ||
      data.detail ||
      data.message ||
      (typeof data === "object" ? JSON.stringify(data) : null) ||
      "Password reset failed.";
    throw new Error(msg);
  }

  return data;
}