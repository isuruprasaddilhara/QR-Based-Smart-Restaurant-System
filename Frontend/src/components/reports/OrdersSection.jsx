import { Bar } from "react-chartjs-2";

function OrdersSection({ ui, hourlyChart, barChartOptions }) {
  return (
    <div className={`${ui.cardLarge} ${ui.chartCard}`}>
      <h3>Hourly Order Pattern</h3>
      <div className={`${ui.chartBox} ${ui.chartBoxTall}`}>
        <Bar data={hourlyChart} options={barChartOptions} />
      </div>
    </div>
  );
}

export default OrdersSection;
