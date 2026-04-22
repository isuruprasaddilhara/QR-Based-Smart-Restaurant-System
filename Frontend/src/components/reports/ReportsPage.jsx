import { useEffect, useMemo, useState } from "react";

import {
  fetchCategoryRevenue,
  fetchDashboardSummary,
  fetchFeedback,
  fetchHourlyOrders,
  fetchRevenue,
  fetchTablePerformance,
  fetchTopItems,
} from "../../repository/analytics";
import FeedbackSection from "./FeedbackSection";
import MenuSection from "./MenuSection";
import OrdersSection from "./OrdersSection";
import OverviewSection from "./OverviewSection";
import RevenueSection from "./RevenueSection";
import TablesSection from "./TablesSection";
import {
  CHART_COLORS,
  baseChartOptions,
  daysAgoIso,
  formatRangeLabel,
  registerReportCharts,
  sectionOptions,
  todayIso,
} from "./reportUtils";
import styles from "./ReportsPage.module.css";

registerReportCharts();

function ReportsPage() {
  const [activeSection, setActiveSection] = useState("overview");
  const [startDate, setStartDate] = useState(daysAgoIso(30));
  const [endDate, setEndDate] = useState(todayIso());

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [summary, setSummary] = useState(null);
  const [revenueSeries, setRevenueSeries] = useState([]);
  const [hourlySeries, setHourlySeries] = useState([]);
  const [topItems, setTopItems] = useState([]);
  const [categorySeries, setCategorySeries] = useState([]);
  const [feedback, setFeedback] = useState(null);
  const [tablePerf, setTablePerf] = useState([]);

  const params = useMemo(
    () => ({ start: startDate, end: endDate }),
    [startDate, endDate],
  );

  const rangeBackwards = Boolean(
    startDate && endDate && startDate > endDate,
  );

  useEffect(() => {
    let cancelled = false;

    function clearAnalyticsState() {
      setSummary(null);
      setRevenueSeries([]);
      setHourlySeries([]);
      setTopItems([]);
      setCategorySeries([]);
      setFeedback(null);
      setTablePerf([]);
    }

    const { start, end } = params;
    if (start && end && start > end) {
      clearAnalyticsState();
      setLoading(false);
      return;
    }

    async function loadAll() {
      setLoading(true);
      setError("");
      try {
        const [s, r, h, top, cat, fb, tbl] = await Promise.all([
          fetchDashboardSummary(params),
          fetchRevenue({ ...params, group_by: "day" }),
          fetchHourlyOrders(params),
          fetchTopItems({ ...params, limit: 8 }),
          fetchCategoryRevenue(params),
          fetchFeedback(params),
          fetchTablePerformance(params),
        ]);

        if (cancelled) return;
        setSummary(s);
        setRevenueSeries(r);
        setHourlySeries(h);
        setTopItems(top);
        setCategorySeries(cat);
        setFeedback(fb);
        setTablePerf(tbl);
      } catch (e) {
        if (!cancelled) setError(e.message || "Failed to load reports.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadAll();
    return () => {
      cancelled = true;
    };
  }, [params]);

  const totalRev = Number(summary?.total_revenue || 0);
  const totalOrd = Number(summary?.total_orders || 0);
  const aov = Number(summary?.average_order_value || 0);

  const sortedTopItems = useMemo(
    () =>
      [...topItems].sort(
        (a, b) => Number(b.total_quantity || 0) - Number(a.total_quantity || 0),
      ),
    [topItems],
  );

  const revenueChart = {
    labels: revenueSeries.map((x) => x.period),
    datasets: [
      {
        label: "Revenue (LKR)",
        data: revenueSeries.map((x) => Number(x.total_revenue || 0)),
        borderColor: CHART_COLORS.purple,
        backgroundColor: "rgba(155, 114, 201, 0.18)",
        fill: true,
        tension: 0.35,
        pointBackgroundColor: CHART_COLORS.purple,
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  };

  const revenueChartOptions = {
    ...baseChartOptions,
    layout: { padding: { left: 12, right: 12, top: 8, bottom: 8 } },
    scales: {
      x: {
        ticks: { font: { size: 11 }, maxRotation: 45 },
        grid: { color: "rgba(0,0,0,0.05)" },
      },
      y: {
        beginAtZero: true,
        ticks: { font: { size: 11 } },
        grid: { color: "rgba(0,0,0,0.06)" },
      },
    },
  };

  const hourlyChart = {
    labels: hourlySeries.map((x) => `${String(x.hour).padStart(2, "0")}:00`),
    datasets: [
      {
        label: "Orders",
        data: hourlySeries.map((x) => x.order_count),
        backgroundColor: CHART_COLORS.barNeutral,
        borderRadius: 6,
      },
    ],
  };

  const barChartOptions = {
    ...baseChartOptions,
    scales: {
      x: {
        ticks: { font: { size: 12 }, maxRotation: 0 },
        grid: { display: false },
      },
      y: {
        beginAtZero: true,
        ticks: { font: { size: 12 } },
        grid: { color: "rgba(0,0,0,0.06)" },
      },
    },
  };

  const categoryChart = {
    labels: categorySeries.map((x) => x.menu_item__category__name || "Unknown"),
    datasets: [
      {
        label: "Revenue (LKR)",
        data: categorySeries.map((x) => Number(x.total_revenue || 0)),
        backgroundColor: CHART_COLORS.barNeutral,
        borderRadius: 8,
      },
    ],
  };

  const categoryChartOptions = {
    ...baseChartOptions,
    indexAxis: "y",
    scales: {
      x: {
        beginAtZero: true,
        ticks: { font: { size: 12 } },
        grid: { color: "rgba(0,0,0,0.06)" },
      },
      y: {
        ticks: { font: { size: 12 } },
        grid: { display: false },
      },
    },
  };

  const topItemsChart = {
    labels: sortedTopItems.map((x) => x.menu_item__name),
    datasets: [
      {
        label: "Qty sold",
        data: sortedTopItems.map((x) => x.total_quantity),
        backgroundColor: CHART_COLORS.barNeutral,
        borderRadius: 8,
      },
    ],
  };

  const topItemsChartOptions = {
    ...baseChartOptions,
    indexAxis: "y",
    scales: {
      x: {
        beginAtZero: true,
        ticks: { font: { size: 12 } },
        grid: { color: "rgba(0,0,0,0.06)" },
      },
      y: {
        ticks: { font: { size: 11 } },
        grid: { display: false },
      },
    },
  };

  const orderRows = useMemo(
    () =>
      sortedTopItems.map((it) => {
        const qty = Number(it.total_quantity || 0);
        const raw =
          it.total_revenue != null && it.total_revenue !== ""
            ? Number(it.total_revenue)
            : NaN;
        const revenue = Number.isNaN(raw) ? 0 : Math.round(raw);
        const unitVal = qty > 0 && !Number.isNaN(raw) ? raw / qty : 0;
        return { ...it, qty, revenue, unitVal };
      }),
    [sortedTopItems],
  );

  const tableRowsOrdered = useMemo(
    () =>
      [...tablePerf].sort(
        (a, b) => Number(b.total_revenue || 0) - Number(a.total_revenue || 0),
      ),
    [tablePerf],
  );

  return (
    <div className={styles.page}>
      <div className={styles.dashShell}>
        <header className={styles.dashHeader}>
          <div>
            <h1 className={styles.title}>Reports</h1>
            <p className={styles.subtitle}>
              Analytics overview — {formatRangeLabel(startDate, endDate)}
            </p>
          </div>
        </header>

        <div className={styles.toolbar}>
          <div className={styles.dateRow}>
            <div className={styles.dateGroup}>
              <label className={styles.label}>
                From
                <input
                  className={styles.input}
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </label>
              <label className={styles.label}>
                To
                <input
                  className={styles.input}
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </label>
            </div>
            {rangeBackwards ? (
              <p className={styles.rangeHint} role="status">
                From must be on or before To.
              </p>
            ) : null}
          </div>

          <div className={styles.sectionTabs}>
            {sectionOptions.map((s) => (
              <button
                key={s.id}
                type="button"
                className={`${styles.tabBtn} ${activeSection === s.id ? styles.activeTab : ""}`}
                onClick={() => setActiveSection(s.id)}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {error ? <p className={styles.errorBanner}>{error}</p> : null}
        {loading ? <p className={styles.loading}>Loading analytics…</p> : null}

        {!loading && !error && !rangeBackwards && (
          <>
            {activeSection === "overview" && (
              <OverviewSection
                ui={styles}
                totalRev={totalRev}
                totalOrd={totalOrd}
                aov={aov}
                feedback={feedback}
                revenueChart={revenueChart}
                revenueChartOptions={revenueChartOptions}
                orderRows={orderRows}
                tableRowsOrdered={tableRowsOrdered}
              />
            )}

            {activeSection === "revenue" && (
              <RevenueSection
                ui={styles}
                revenueChart={revenueChart}
                revenueChartOptions={revenueChartOptions}
                categoryChart={categoryChart}
                categoryChartOptions={categoryChartOptions}
              />
            )}

            {activeSection === "orders" && (
              <OrdersSection
                ui={styles}
                hourlyChart={hourlyChart}
                barChartOptions={barChartOptions}
              />
            )}

            {activeSection === "menu" && (
              <MenuSection
                ui={styles}
                topItemsChart={topItemsChart}
                topItemsChartOptions={topItemsChartOptions}
                sortedTopItems={sortedTopItems}
              />
            )}

            {activeSection === "tables" && (
              <TablesSection ui={styles} tablePerf={tablePerf} />
            )}

            {activeSection === "feedback" && (
              <FeedbackSection ui={styles} feedback={feedback} />
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default ReportsPage;
