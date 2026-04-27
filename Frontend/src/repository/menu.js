import { getAccessToken } from "./auth";

const API = (process.env.REACT_APP_API_URL || "").replace(/\/$/, "");

function authHeadersWithoutContentType() {
  const token = getAccessToken();
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function jsonHeaders() {
  const token = getAccessToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function parseList(data) {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.results)) return data.results;
  return [];
}

async function readErrorMessage(res, data) {
  if (data?.detail) return String(data.detail);
  if (data?.message) return String(data.message);

  if (data && typeof data === "object") {
    const parts = [];
    for (const [k, v] of Object.entries(data)) {
      if (Array.isArray(v)) parts.push(`${k}: ${v.join(", ")}`);
      else if (typeof v === "string") parts.push(`${k}: ${v}`);
    }
    if (parts.length) return parts.join("; ");
  }

  return res.statusText || "Request failed";
}

export function mapMenuItemFromApi(row, categoryMap) {
  const catId = row.category;
  const catName =
    categoryMap instanceof Map
      ? (categoryMap.get(catId) ?? "")
      : (categoryMap?.[catId] ?? "");

  const price =
    typeof row.price === "string" ? parseFloat(row.price) : Number(row.price);

  return {
    id: row.id,
    name: row.name,
    description: row.description ?? "",
    price: Number.isFinite(price) ? price : 0,
    availability: !!row.availability,
    categoryId: catId,
    category: catName,
    image_url: row.image_url || "",
    image: row.image_url || "/image.png",
    ingredients: row.ingredients ?? "",
  };
}

// ---------------- CATEGORY ----------------

export async function fetchCategories() {
  const res = await fetch(`${API}/menu/categories/`);
  const data = await res.json().catch(() => ({}));

  if (!res.ok) throw new Error(await readErrorMessage(res, data));
  return parseList(data);
}

export async function createCategory({ name }) {
  const res = await fetch(`${API}/menu/categories/`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ name: String(name).trim() }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(await readErrorMessage(res, data));
  return data;
}

export async function updateCategory(id, { name }) {
  const res = await fetch(`${API}/menu/categories/${id}/`, {
    method: "PATCH",
    headers: jsonHeaders(),
    body: JSON.stringify({ name: String(name).trim() }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(await readErrorMessage(res, data));
  return data;
}

export async function deleteCategory(id) {
  const res = await fetch(`${API}/menu/categories/${id}/`, {
    method: "DELETE",
    headers: authHeadersWithoutContentType(),
  });

  if (res.status === 204 || res.status === 200) return true;

  const data = await res.json().catch(() => ({}));
  throw new Error(await readErrorMessage(res, data));
}

// ---------------- MENU ITEMS ----------------

export async function fetchMenuItems() {
  const res = await fetch(`${API}/menu/items/`);
  const data = await res.json().catch(() => ({}));

  if (!res.ok) throw new Error(await readErrorMessage(res, data));
  return parseList(data);
}

export async function createMenuItem(formData) {
  const res = await fetch(`${API}/menu/items/`, {
    method: "POST",
    headers: authHeadersWithoutContentType(),
    body: formData,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(await readErrorMessage(res, data));
  return data;
}

export async function updateMenuItem(id, formData) {
  const res = await fetch(`${API}/menu/items/${id}/`, {
    method: "PATCH",
    headers: authHeadersWithoutContentType(),
    body: formData,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(await readErrorMessage(res, data));
  return data;
}

export async function deleteMenuItem(id) {
  const res = await fetch(`${API}/menu/items/${id}/`, {
    method: "DELETE",
    headers: authHeadersWithoutContentType(),
  });

  if (res.status === 204 || res.status === 200) return true;

  const data = await res.json().catch(() => ({}));
  throw new Error(await readErrorMessage(res, data));
}
