import { Bar, Line } from "react-chartjs-2";

import styles from "./RevenueSection.module.css";

function RevenueSection({
  ui,
  revenueChart,
  revenueChartOptions,
  categoryChart,
  categoryChartOptions,
}) {
  return (
    <div className={styles.revenueTabStack}>
      <div className={`${ui.cardLarge} ${ui.chartCard}`}>
        <h3>Revenue Trend</h3>
        <div className={`${ui.chartBox} ${ui.chartBoxWide}`}>
          <Line data={revenueChart} options={revenueChartOptions} />
        </div>
      </div>
      <div className={`${ui.cardLarge} ${ui.chartCard}`}>
        <h3>Revenue by Category</h3>
        <div className={`${ui.chartBox} ${ui.chartBoxWide}`}>
          <Bar data={categoryChart} options={categoryChartOptions} />
        </div>
      </div>
    </div>
  );
}

export default RevenueSection;
