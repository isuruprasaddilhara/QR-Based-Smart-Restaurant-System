function TablesSection({ ui, tablePerf }) {
  return (
    <div className={`${ui.cardLarge} ${ui.tablesCard}`}>
      <h3>Table Performance</h3>
      <div className={ui.tableWrap}>
        <table className={`${ui.table} ${ui.tablePerf}`}>
          <thead>
            <tr>
              <th>Table ID</th>
              <th>Section</th>
              <th>Capacity</th>
              <th>Orders</th>
              <th>Revenue</th>
            </tr>
          </thead>
          <tbody>
            {tablePerf.map((t, idx) => (
              <tr key={`${t.table__id}-${idx}`}>
                <td>{t.table__id}</td>
                <td>{t.table__section || "-"}</td>
                <td>{t.table__capacity}</td>
                <td>{t.order_count}</td>
                <td>LKR {Number(t.total_revenue || 0).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TablesSection;
