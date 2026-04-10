import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";

let registered = false;

export function registerReportCharts() {
  if (registered) return;
  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Tooltip,
    Legend,
  );
  registered = true;
}

export const sectionOptions = [
  { id: "overview", label: "Overview" },
  { id: "revenue", label: "Revenue" },
  { id: "orders", label: "Orders" },
  { id: "menu", label: "Menu" },
  { id: "tables", label: "Tables" },
  { id: "feedback", label: "Feedback" },
];

export const CHART_COLORS = {
  purple: "#9b72c9",
  barNeutral: "rgba(155, 114, 201, 0.55)",
};

export const baseChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        usePointStyle: true,
        padding: 18,
        font: { size: 13, weight: "500" },
      },
    },
    tooltip: {
      bodyFont: { size: 13 },
      titleFont: { size: 13 },
    },
  },
};

export function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export function daysAgoIso(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

export function formatRangeLabel(start, end) {
  const a = new Date(`${start}T12:00:00`);
  const b = new Date(`${end}T12:00:00`);
  if (Number.isNaN(a.getTime()) || Number.isNaN(b.getTime())) return "";
  const opts = { month: "short", day: "numeric", year: "numeric" };
  return `${a.toLocaleDateString(undefined, opts)} → ${b.toLocaleDateString(undefined, opts)}`;
}
