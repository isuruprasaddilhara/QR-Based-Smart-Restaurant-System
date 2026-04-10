import { getAccessToken } from "./auth";

const API = (process.env.REACT_APP_API_URL || "").replace(/\/$/, "");

function authHeaders() {
  const token = getAccessToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function readError(res) {
  const data = await res.json().catch(() => ({}));
  if (data?.detail) return data.detail;
  if (data?.message) return data.message;
  if (data && typeof data === "object") {
    const parts = [];
    for (const [k, v] of Object.entries(data)) {
      if (Array.isArray(v)) parts.push(`${k}: ${v.join(", ")}`);
      else if (typeof v === "string") parts.push(`${k}: ${v}`);
    }
    if (parts.length) return parts.join("; ");
  }
  return "Request failed";
}

export async function fetchStaffList() {
  const res = await fetch(`${API}/users/staff/`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function fetchStaffDetail(userId) {
  const res = await fetch(`${API}/users/staff/${userId}/`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function fetchMyStaffProfile() {
  const res = await fetch(`${API}/users/staff/me/`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function updateMyStaffProfile(payload) {
  const res = await fetch(`${API}/users/staff/edit/`, {
    method: "PATCH",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function deleteStaffAccount(userId) {
  const res = await fetch(`${API}/users/staff/delete/${userId}/`, {
    method: "DELETE",
    headers: authHeaders(),
  });

  if (!res.ok && res.status !== 204) {
    throw new Error(await readError(res));
  }
}

export async function changeMyPassword(old_password, new_password) {
  const res = await fetch(`${API}/users/auth/password/change/`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ old_password, new_password }),
  });

  if (!res.ok) throw new Error(await readError(res));
  return res.json().catch(() => ({}));
}
