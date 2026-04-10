import { Bar } from "react-chartjs-2";

function MenuSection({ ui, topItemsChart, topItemsChartOptions, sortedTopItems }) {
  return (
    <div className={ui.grid2}>
      <div className={`${ui.cardLarge} ${ui.chartCard}`}>
        <h3>Top Items (Quantity)</h3>
        <div className={`${ui.chartBox} ${ui.chartBoxWide}`}>
          <Bar data={topItemsChart} options={topItemsChartOptions} />
        </div>
      </div>
      <div className={ui.cardLarge}>
        <h3>Top Items List</h3>
        <div className={ui.listWrap}>
          {sortedTopItems.map((item, idx) => (
            <div key={`${item.menu_item__id}-${idx}`} className={ui.listRow}>
              <span>{item.menu_item__name}</span>
              <strong>{item.total_quantity}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default MenuSection;
