import { getAccessToken } from "./auth";
//
import {
  mockDashboardSummary,
  mockRevenue,
  mockOrderStatus,
  mockHourlyOrders,
  mockTopItems,
  mockCategoryRevenue,
  mockFeedback,
  mockTablePerformance,
  delay,
} from "./analyticsMock";

const reportsMock = process.env.REACT_APP_REPORTS_MOCK_DATA === "true";
//

const apiBase = (process.env.REACT_APP_API_URL || "").replace(/\/$/, "");

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
  if (data?.error) return data.error;
  if (data && typeof data === "object") {
    const first = Object.values(data)[0];
    if (Array.isArray(first) && first.length) return String(first[0]);
  }
  return "Request failed";
}

async function getJson(path, params = {}) {
  //

  if (reportsMock) {
    await delay();
    if (path === "dashboard/") return mockDashboardSummary();
    if (path === "revenue/") return mockRevenue(params);
    if (path === "orders/status/") return mockOrderStatus();
    if (path === "orders/hourly/") return mockHourlyOrders();
    if (path === "menu/top-items/") return mockTopItems(params);
    if (path === "menu/categories/") return mockCategoryRevenue();
    if (path === "feedback/") return mockFeedback();
    if (path === "tables/") return mockTablePerformance();
  }

  //
  const query = new URLSearchParams(params);
  const url = `${apiBase}/analytics/${path}${query.toString() ? `?${query}` : ""}`;

  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function fetchDashboardSummary(params) {
  return getJson("dashboard/", params);
}

export async function fetchRevenue(params) {
  return getJson("revenue/", params);
}

export async function fetchOrderStatus(params) {
  return getJson("orders/status/", params);
}

export async function fetchHourlyOrders(params) {
  return getJson("orders/hourly/", params);
}

export async function fetchTopItems(params) {
  return getJson("menu/top-items/", params);
}

export async function fetchCategoryRevenue(params) {
  return getJson("menu/categories/", params);
}

export async function fetchFeedback(params) {
  return getJson("feedback/", params);
}

export async function fetchTablePerformance(params) {
  return getJson("tables/", params);
}
