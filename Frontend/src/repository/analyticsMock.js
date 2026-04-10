/**
 * Random demo data for Reports when REACT_APP_REPORTS_MOCK_DATA=true
 */

function randInt(min, max) {
  return min + Math.floor(Math.random() * (max - min + 1));
}

function randFloat(min, max) {
  return min + Math.random() * (max - min);
}

function eachDayIso(start, end) {
  const out = [];
  const a = new Date(`${start}T12:00:00`);
  const b = new Date(`${end}T12:00:00`);
  if (Number.isNaN(a.getTime()) || Number.isNaN(b.getTime()) || a > b) {
    return [start];
  }
  for (let d = new Date(a); d <= b; d.setDate(d.getDate() + 1)) {
    out.push(d.toISOString().slice(0, 10));
  }
  return out;
}

const MENU_NAMES = [
  "Chicken Fried Rice",
  "Kottu Roti",
  "Devilled Prawns",
  "Cheese Kottu",
  "Naan & Curry",
  "Lamprais",
  "Hot Butter Cuttlefish",
  "String Hoppers",
];

const CATEGORIES = ["Mains", "Appetizers", "Seafood", "Beverages", "Desserts"];

function buildRatingBuckets(totalFeedback) {
  const weights = [0.45, 0.28, 0.14, 0.08, 0.05];
  let remaining = totalFeedback;
  const counts = {};
  for (let i = 0; i < 5; i++) {
    const r = 5 - i;
    const n =
      i === 4
        ? remaining
        : Math.min(remaining, Math.round(totalFeedback * weights[i]));
    counts[`rating_${r}`] = Math.max(0, n);
    remaining -= counts[`rating_${r}`];
  }
  if (remaining !== 0) {
    counts.rating_5 = (counts.rating_5 || 0) + remaining;
  }
  const avg =
    totalFeedback > 0
      ? (
          (counts.rating_5 * 5 +
            counts.rating_4 * 4 +
            counts.rating_3 * 3 +
            counts.rating_2 * 2 +
            counts.rating_1 * 1) /
          totalFeedback
        ).toFixed(2)
      : "0";
  return { counts, average_rating: avg };
}

export function mockDashboardSummary() {
  const totalOrders = randInt(32, 48);
  const totalRevenue = Math.round(totalOrders * randFloat(1200, 4200));
  const aov = totalOrders ? Math.round(totalRevenue / totalOrders) : 0;
  const peakStart = randInt(17, 19);
  const peakEnd = peakStart + randInt(1, 2);
  return {
    total_revenue: totalRevenue,
    total_orders: totalOrders,
    average_order_value: aov,
    peak_time: `${peakStart}:00 – ${peakEnd}:00`,
  };
}

export function mockRevenue(params) {
  const days = eachDayIso(params.start, params.end);
  const weights = days.map(() => randFloat(0.4, 1.6));
  const sumW = weights.reduce((a, b) => a + b, 0);
  const total = randFloat(45000, 180000);
  return days.map((period, i) => ({
    period,
    total_revenue: Math.round((total * weights[i]) / sumW),
  }));
}

export function mockOrderStatus() {
  const total = randInt(35, 55);
  const completed = Math.round(total * randFloat(0.55, 0.72));
  const preparing = randInt(2, 8);
  const served = randInt(1, 4);
  const requested = randInt(0, 5);
  const pending = Math.max(0, total - completed - preparing - served - requested);
  return [
    { status: "completed", count: completed },
    { status: "preparing", count: preparing },
    { status: "served", count: served },
    { status: "requested", count: requested },
    { status: "pending", count: pending },
  ];
}

export function mockHourlyOrders() {
  const rows = [];
  for (let hour = 0; hour < 24; hour += 1) {
    let base = 0;
    if (hour >= 11 && hour <= 14) base = randInt(2, 9);
    else if (hour >= 17 && hour <= 21) base = randInt(4, 14);
    else if (hour >= 8 && hour <= 22) base = randInt(0, 4);
    rows.push({ hour, order_count: base });
  }
  return rows;
}

export function mockTopItems(params) {
  const limit = Number(params.limit) || 8;
  const picked = [...MENU_NAMES]
    .sort(() => Math.random() - 0.5)
    .slice(0, limit);
  return picked.map((name, idx) => ({
    menu_item__id: 100 + idx,
    menu_item__name: name,
    total_quantity: randInt(8, 120),
  }));
}

export function mockCategoryRevenue() {
  return CATEGORIES.map((name) => ({
    menu_item__category__name: name,
    total_revenue: Math.round(randFloat(8000, 42000)),
  }));
}

export function mockFeedback() {
  const totalFeedback = randInt(18, 35);
  const { counts, average_rating } = buildRatingBuckets(totalFeedback);
  return {
    average_rating,
    total_feedback_count: totalFeedback,
    ...counts,
  };
}

export function mockTablePerformance() {
  const n = randInt(6, 12);
  const rows = [];
  for (let i = 0; i < n; i += 1) {
    rows.push({
      table__id: 1 + i,
      table__section: ["Ground", "First", "Garden"][i % 3],
      table__capacity: [2, 4, 4, 6, 8][i % 5],
      order_count: randInt(2, 28),
      total_revenue: Math.round(randFloat(4000, 52000)),
    });
  }
  return rows;
}

export function delay(ms = 280) {
  return new Promise((r) => setTimeout(r, ms));
}
