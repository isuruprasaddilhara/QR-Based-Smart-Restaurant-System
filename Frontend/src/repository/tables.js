import { getAccessToken } from "./auth";

const apiBase = (process.env.REACT_APP_API_URL || "").replace(/\/$/, "");

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
  if (data?.error) return String(data.error);
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

export function mapTableFromApi(row) {
  const occupied = !!row.status;
  const displayNo = row.table_number ?? row.id;

  return {
    id: row.id,
    tableNo: displayNo,
    qrCode: row.qr_code,
    section: row.section ?? "",
    capacity: row.capacity,
    status: occupied ? "Occupied" : "Available",
  };
}

export async function fetchTables() {
  const res = await fetch(`${apiBase}/tables/`, { headers: jsonHeaders() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(await readErrorMessage(res, data));
  return parseList(data).map(mapTableFromApi);
}

export async function createTable({ tableNo, section = "", capacity = 2 }) {
  const body = {
    section: String(section || "").trim() || null,
    capacity: Number(capacity) || 2,
  };

  if (tableNo !== undefined && tableNo !== null && tableNo !== "") {
    body.table_number = Number(tableNo); // IMPORTANT KEY
  }

  const res = await fetch(`${apiBase}/tables/`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(await readErrorMessage(res, data));
  return mapTableFromApi(data);
}

export async function updateTable(id, { tableNo, section, capacity, status }) {
  const body = {};
  if (tableNo !== undefined && tableNo !== null && tableNo !== "") {
    body.table_number = Number(tableNo); // IMPORTANT KEY
  }
  if (section !== undefined) body.section = section || null;
  if (capacity !== undefined) body.capacity = Number(capacity);
  if (status !== undefined) body.status = status;

  const res = await fetch(`${apiBase}/tables/${id}/`, {
    method: "PATCH",
    headers: jsonHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(await readErrorMessage(res, data));
  return mapTableFromApi(data);
}

export async function deleteTable(id) {
  const res = await fetch(`${apiBase}/tables/${id}/`, {
    method: "DELETE",
    headers: jsonHeaders(),
  });
  if (res.status === 204 || res.status === 200) return;
  const data = await res.json().catch(() => ({}));
  throw new Error(await readErrorMessage(res, data));
}

export async function downloadTableQr(tableId, menuBaseUrl) {
  const base =
    menuBaseUrl ||
    `${typeof window !== "undefined" ? window.location.origin : ""}/menu`;

  const url = `${apiBase}/tables/${tableId}/download-qr/?base_url=${encodeURIComponent(base)}`;

  const res = await fetch(url, { headers: jsonHeaders() });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(await readErrorMessage(res, data));
  }

  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = `table_${tableId}_qr.png`;
  document.body.appendChild(a);
  a.click();
  a.remove();

  URL.revokeObjectURL(objectUrl);
}
