import { Line } from "react-chartjs-2";
import { FaChartLine, FaStar, FaUtensils } from "react-icons/fa";

import styles from "./OverviewSection.module.css";

function OverviewSection({
  ui,
  totalRev,
  totalOrd,
  aov,
  feedback,
  revenueChart,
  revenueChartOptions,
  orderRows,
  tableRowsOrdered,
}) {
  return (
    <>
      <div className={styles.kpiRow}>
        <div className={styles.kpiCard}>
          <div className={`${styles.kpiIcon} ${styles.kpiIconGreen}`}>
            <FaChartLine />
          </div>
          <div className={styles.kpiBody}>
            <p className={styles.kpiLabel}>Revenue</p>
            <p className={styles.kpiValue}>LKR {totalRev.toLocaleString()}</p>
          </div>
        </div>
        <div className={styles.kpiCard}>
          <div className={`${styles.kpiIcon} ${styles.kpiIconOrange}`}>
            <FaUtensils />
          </div>
          <div className={styles.kpiBody}>
            <p className={styles.kpiLabel}>Orders</p>
            <p className={styles.kpiValue}>{totalOrd}</p>
          </div>
        </div>
        <div className={styles.kpiCard}>
          <div className={`${styles.kpiIcon} ${styles.kpiIconPurple}`}>
            <FaChartLine />
          </div>
          <div className={styles.kpiBody}>
            <p className={styles.kpiLabel}>Avg. order</p>
            <p className={styles.kpiValue}>LKR {aov.toLocaleString()}</p>
          </div>
        </div>
        <div className={styles.kpiCard}>
          <div className={`${styles.kpiIcon} ${styles.kpiIconPink}`}>
            <FaStar />
          </div>
          <div className={styles.kpiBody}>
            <p className={styles.kpiLabel}>Avg. rating</p>
            <p className={styles.kpiValue}>{feedback?.average_rating ?? "—"} / 5</p>
          </div>
        </div>
      </div>

      <div className={`${ui.cardLarge} ${ui.chartCard} ${styles.revenueTrendFull}`}>
        <h3 className={ui.cardTitle}>Revenue trend</h3>
        <div className={`${ui.chartBox} ${ui.chartHero} ${styles.chartBoxClip}`}>
          <Line data={revenueChart} options={revenueChartOptions} />
        </div>
      </div>

      <div className={styles.overviewSecondRow}>
        <div className={ui.cardLarge}>
          <h3 className={ui.cardTitle}>Order summary</h3>
          <div className={ui.tableWrap}>
            <table className={ui.table}>
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Orders</th>
                  <th>Revenue</th>
                </tr>
              </thead>
              <tbody>
                {orderRows.length === 0 ? (
                  <tr>
                    <td colSpan={3}>No items in range</td>
                  </tr>
                ) : (
                  orderRows.map((row, idx) => (
                    <tr key={`${row.menu_item__id}-${idx}`}>
                      <td>{row.menu_item__name}</td>
                      <td>{row.qty}</td>
                      <td>LKR {(row.revenue ?? 0).toLocaleString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className={ui.cardLarge}>
          <h3 className={ui.cardTitle}>Table revenue summary</h3>
          <div className={ui.tableWrap}>
            <table className={ui.table}>
              <thead>
                <tr>
                  <th>Table</th>
                  <th>Orders</th>
                  <th>Revenue</th>
                </tr>
              </thead>
              <tbody>
                {tableRowsOrdered.length === 0 ? (
                  <tr>
                    <td colSpan={3}>No table data</td>
                  </tr>
                ) : (
                  tableRowsOrdered.map((t, idx) => (
                    <tr key={`${t.table__id}-${idx}`}>
                      <td>#{t.table__id}</td>
                      <td>{t.order_count}</td>
                      <td>LKR {Number(t.total_revenue || 0).toLocaleString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className={ui.cardLarge}>
          <h3 className={ui.cardTitle}>Feedback</h3>
          <div className={styles.feedbackCompact}>
            <p className={styles.feedbackStat}>
              <span>Avg. rating</span>
              <strong>{feedback?.average_rating ?? "—"} / 5</strong>
            </p>
            <p className={styles.feedbackStat}>
              <span>Total responses</span>
              <strong>{feedback?.total_feedback_count ?? 0}</strong>
            </p>
            <div className={ui.listWrap}>
              {[5, 4, 3, 2, 1].map((r) => (
                <div key={r} className={ui.feedbackRowPlain}>
                  <span>{r} star</span>
                  <strong>{feedback?.[`rating_${r}`] || 0}</strong>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default OverviewSection;
