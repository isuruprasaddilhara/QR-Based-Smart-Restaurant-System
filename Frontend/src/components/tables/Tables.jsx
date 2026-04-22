import { useCallback, useEffect, useState } from "react";
import { FaPlus } from "react-icons/fa";

import TableItem from "./TableItem";
import TableEdit from "./TableEdit";

import {
  createTable,
  deleteTable,
  downloadTableQr,
  fetchTables,
  updateTable,
} from "../../repository/tables";

import styles from "./Tables.module.css";

const pollMs = 15000;

function Tables() {
  const [tables, setTables] = useState([]);
  const [isDrawerVisible, setIsDrawerVisible] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [selectedTable, setSelectedTable] = useState(null);
  const [isAddMode, setIsAddMode] = useState(false);

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [mutationError, setMutationError] = useState("");

  const loadTables = useCallback(async () => {
    setLoadError("");
    try {
      const list = await fetchTables();
      setTables(list);
    } catch (e) {
      setLoadError(e.message || "Failed to load tables.");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const list = await fetchTables();
        if (!cancelled) setTables(list);
      } catch (e) {
        if (!cancelled) setLoadError(e.message || "Failed to load tables.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    const intervalId = setInterval(() => {
      fetchTables()
        .then((list) => {
          if (!cancelled) setTables(list);
        })
        .catch(() => {});
    }, pollMs);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, []);

  const totalTables = tables.length;
  const availableTables = tables.filter(
    (table) => table.status === "Available",
  ).length;
  const occupiedTables = tables.filter(
    (table) => table.status === "Occupied",
  ).length;

  function handleEdit(table) {
    setMutationError("");
    setSelectedTable(table);
    setIsAddMode(false);
    setIsDrawerVisible(true);

    setTimeout(() => {
      setIsDrawerOpen(true);
    }, 10);
  }

  function handleAddOpen() {
    setMutationError("");
    setSelectedTable(null);
    setIsAddMode(true);
    setIsDrawerVisible(true);

    setTimeout(() => {
      setIsDrawerOpen(true);
    }, 10);
  }

  function handleCloseDrawer() {
    setIsDrawerOpen(false);

    setTimeout(() => {
      setIsDrawerVisible(false);
      setSelectedTable(null);
    }, 300);
  }

  async function handleSaveTable(draft) {
    setMutationError("");
    if (isAddMode) {
      const created = await createTable({
        tableNo: draft.tableNo,
        section: draft.section,
        capacity: draft.capacity,
      });
      setTables((prev) => [...prev, created]);
    } else {
      const saved = await updateTable(draft.id, {
        tableNo: draft.tableNo,
        section: draft.section,
        capacity: draft.capacity,
        status: draft.status === "Occupied",
      });
      setTables((prev) => prev.map((t) => (t.id === saved.id ? saved : t)));
    }
  }

  async function handleDeleteTable(id) {
    setMutationError("");
    if (!window.confirm("Delete this table? This cannot be undone.")) return;
    await deleteTable(id);
    setTables((prev) => prev.filter((t) => t.id !== id));
    handleCloseDrawer();
  }

  async function handleDownloadQr(tableId) {
    setMutationError("");
    try {
      await downloadTableQr(tableId);
    } catch (e) {
      setMutationError(e.message || "Could not download QR.");
    }
  }

  return (
    <div className={styles.page}>
      {loadError || mutationError ? (
        <div className={styles.alertStack} role="alert">
          {loadError ? <p className={styles.errorBanner}>{loadError}</p> : null}
          {mutationError ? (
            <p className={styles.errorBanner}>{mutationError}</p>
          ) : null}
        </div>
      ) : null}

      <header className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Tables</h1>
        <p className={styles.pageSubtitle}>
          Manage seating, capacity, and table status
        </p>
      </header>
      <div className={styles.statsSection}>
        <div className={`${styles.statCard} ${styles.total}`}>
          <p className={styles.statTitle}>Total Tables</p>
          <p className={styles.statValue}>{totalTables}</p>
        </div>

        <div className={`${styles.statCard} ${styles.available}`}>
          <p className={styles.statTitle}>Available</p>
          <p className={styles.statValue}>{availableTables}</p>
        </div>

        <div className={`${styles.statCard} ${styles.occupied}`}>
          <p className={styles.statTitle}>Occupied</p>
          <p className={styles.statValue}>{occupiedTables}</p>
        </div>
      </div>

      <div className={styles.topSection}>
        <button type="button" className={styles.addBtn} onClick={handleAddOpen}>
          <FaPlus className={styles.addBtnIcon} aria-hidden />
          <span>Add New Item</span>
        </button>
      </div>

      {loading ? (
        <p className={styles.loading}>Loading tables…</p>
      ) : (
        <div className={styles.tableCard}>
          <div className={styles.tableHeadings}>
            <span>Table #</span>
            <span>Capacity</span>
            <span>Status</span>
            <span>Actions</span>
          </div>
          {tables.length === 0 ? (
            <p className={styles.emptyHint}>No tables yet. Add one above.</p>
          ) : (
            tables.map((table) => (
              <TableItem
                key={table.id}
                tableId={table.id}
                tableNo={table.tableNo}
                capacity={table.capacity}
                status={table.status}
                onEdit={() => handleEdit(table)}
                onDelete={() => handleDeleteTable(table.id)}
                onDownloadQr={() => handleDownloadQr(table.id)}
              />
            ))
          )}
        </div>
      )}

      {isDrawerVisible && (
        <TableEdit
          isDrawerOpen={isDrawerOpen}
          handleCloseDrawer={handleCloseDrawer}
          selectedTable={selectedTable}
          handleSaveTable={handleSaveTable}
          handleDeleteTable={handleDeleteTable}
          isAddMode={isAddMode}
        />
      )}
    </div>
  );
}

export default Tables;
