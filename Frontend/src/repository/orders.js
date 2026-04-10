import { getAccessToken } from "./auth";

const apiBase = (process.env.REACT_APP_API_URL || "").replace(/\/$/, "");

function jsonHeaders() {
  const token = getAccessToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function authHeadersOnly() {
  const token = getAccessToken();
  return {
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

/** API strings for each state (matches Django). */
export const orderStatus = {
  pending: "pending",
  preparing: "preparing",
  served: "served",
  /** Customer finished and asked for the bill (between served and completed). */
  requested: "requested",
  completed: "completed",
};

const statusLabels = {
  pending: "New",
  preparing: "Preparing",
  served: "Served",
  requested: "Requested",
  completed: "Completed",
};

const statusFlow = [
  orderStatus.pending,
  orderStatus.preparing,
  orderStatus.served,
  orderStatus.requested,
  orderStatus.completed,
];

export function nextOrderStatus(current) {
  const i = statusFlow.indexOf(current);
  if (i === -1 || i >= statusFlow.length - 1) return null;
  return statusFlow[i + 1];
}

export function labelForApiStatus(status) {
  return statusLabels[status] ?? status;
}

function formatRsAmount(value) {
  const n = value != null && value !== "" ? Number(value) : 0;
  if (Number.isNaN(n)) return "Rs. 0.00";
  return `Rs. ${n.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function mapOrderFromApi(order) {
  const items = order.items ?? [];
  const totalRaw = order.total_amount;
  const totalNum = totalRaw != null && totalRaw !== "" ? Number(totalRaw) : 0;

  const orderedFood = items.map((row) => {
    const qty = Number(row.quantity) || 0;
    const unitRaw = row.unit_price ?? row.unit_price_amount ?? null;
    const unit = unitRaw != null ? Number(unitRaw) : null;
    const lineRaw =
      row.line_total ?? row.subtotal ?? row.line_amount ?? row.price ?? null;
    let lineTotal = lineRaw != null ? Number(lineRaw) : null;
    if (
      (lineTotal == null || Number.isNaN(lineTotal)) &&
      unit != null &&
      !Number.isNaN(unit)
    ) {
      lineTotal = qty * unit;
    }
    if (lineTotal == null || Number.isNaN(lineTotal)) lineTotal = 0;

    const unitPrice =
      unit != null && !Number.isNaN(unit)
        ? unit
        : qty > 0
          ? lineTotal / qty
          : 0;

    return {
      name: row.menu_item_name ?? `Item #${row.menu_item}`,
      quantity: qty,
      unitPrice,
      lineTotal,
    };
  });

  const amountStr = formatRsAmount(totalNum);

  return {
    id: order.id,
    orderNo: order.id,
    tableNo: order.table,
    customerEmail: order.user_email || "",
    time: formatTimeAgo(order.created_at),
    orderedFood,
    amount: amountStr,
    totalAmountNumeric: Number.isNaN(totalNum) ? 0 : totalNum,
    specialNotes:
      (order.special_notes ?? order.notes ?? order.remark ?? "").trim() || "—",
    status: labelForApiStatus(order.status),
    apiStatus: order.status,
    created_at: order.created_at,
  };
}

function formatTimeAgo(iso) {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  const sec = Math.floor((Date.now() - then) / 1000);
  if (sec < 0) return "just now";
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} min ago`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  return `${d}d ago`;
}

export async function fetchOrders() {
  const res = await fetch(`${apiBase}/orders/`, { headers: jsonHeaders() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(await readErrorMessage(res, data));
  const list = parseList(data).map((row) => mapOrderFromApi(row));
  list.sort((a, b) => {
    const ta = a.created_at ? new Date(a.created_at).getTime() : 0;
    const tb = b.created_at ? new Date(b.created_at).getTime() : 0;
    return tb - ta; // descending ()newer) time first
  });
  return list;
}

export async function patchOrderStatus(orderId, status) {
  const res = await fetch(`${apiBase}/orders/${orderId}/status/`, {
    method: "PATCH",
    headers: jsonHeaders(),
    body: JSON.stringify({ status }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(await readErrorMessage(res, data));
  return data;
}

export function matchesOrderFilter(activeNav, apiStatus) {
  if (activeNav === "all") return true;
  if (activeNav === "new") return apiStatus === orderStatus.pending;
  if (activeNav === "preparing") return apiStatus === orderStatus.preparing;
  if (activeNav === "completed") return apiStatus === orderStatus.completed;
  if (activeNav === "served") return apiStatus === orderStatus.served;
  if (activeNav === "requested") return apiStatus === orderStatus.requested;

  return true;
}

export async function sendBillSoftCopy(orderId, email) {
  const res = await fetch(`${apiBase}/orders/${orderId}/bill/soft/`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ email: email.trim() }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(await readErrorMessage(res, data));
  return data;
}

export async function fetchBillPrintPdf(orderId) {
  const res = await fetch(`${apiBase}/orders/${orderId}/bill/print/`, {
    headers: authHeadersOnly(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(await readErrorMessage(res, data));
  }
  return res.blob();
}
