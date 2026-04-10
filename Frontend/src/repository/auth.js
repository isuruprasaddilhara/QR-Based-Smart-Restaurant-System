const API = (process.env.REACT_APP_API_URL || "").replace(/\/$/, "");

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
