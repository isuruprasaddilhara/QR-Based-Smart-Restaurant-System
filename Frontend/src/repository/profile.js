import { getAccessToken, getStoredRole } from "./auth";

const API = (process.env.REACT_APP_API_URL || "").replace(/\/$/, "");

function headers() {
  const token = getAccessToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function readError(res) {
  const data = await res.json().catch(() => ({}));
  return (
    data?.detail || data?.message || JSON.stringify(data) || "Request failed"
  );
}

export async function updateMyProfile(payload) {
  const role = getStoredRole();
  const path =
    role === "customer" ? "/users/customer/edit/" : "/users/staff/edit/";

  const res = await fetch(`${API}${path}`, {
    method: "PATCH",
    headers: headers(),
    body: JSON.stringify(payload),
  });

  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function changeMyPassword(old_password, new_password) {
  const res = await fetch(`${API}/users/auth/password/change/`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ old_password, new_password }),
  });

  if (!res.ok) throw new Error(await readError(res));
  return res.json().catch(() => ({}));
}
