import { useEffect, useMemo, useState } from "react";
import {
  deleteStaffAccount,
  fetchStaffDetail,
  fetchStaffList,
} from "../repository/staff";
import styles from "./ManageAccounts.module.css";

function ManageAccounts() {
  const [allStaff, setAllStaff] = useState([]);
  const [nameFilter, setNameFilter] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [selected, setSelected] = useState(null);

  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setLoading(true);
      setError("");
      try {
        const data = await fetchStaffList(); // load ONCE
        if (!cancelled) setAllStaff(Array.isArray(data) ? data : []);
      } catch (e) {
        if (!cancelled) setError(e.message || "Failed to load staff.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const filteredStaff = useMemo(() => {
    const q = nameFilter.trim().toLowerCase();
    if (!q) return allStaff;
    return allStaff.filter((u) => (u.name || "").toLowerCase().includes(q));
  }, [allStaff, nameFilter]);

  async function handleView(userId) {
    setSelectedId(userId);
    setDetailLoading(true);
    setError("");
    try {
      const data = await fetchStaffDetail(userId);
      setSelected(data);
    } catch (e) {
      setError(e.message || "Failed to load staff details.");
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleDelete(user) {
    const ok = window.confirm(
      `Delete staff account: ${user.name} (${user.email})?`,
    );
    if (!ok) return;

    setError("");
    try {
      await deleteStaffAccount(user.id);
      setAllStaff((prev) => prev.filter((x) => x.id !== user.id));
      if (selectedId === user.id) {
        setSelectedId(null);
        setSelected(null);
      }
    } catch (e) {
      setError(e.message || "Failed to delete staff account.");
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h2 className={styles.title}>Manage Staff Accounts</h2>

        <div className={styles.filterRow}>
          <input
            className={styles.searchInput}
            type="text"
            placeholder="Filter by staff name"
            value={nameFilter}
            onChange={(e) => setNameFilter(e.target.value)}
          />
        </div>

        {error ? <p className={styles.errorText}>{error}</p> : null}
        {loading ? (
          <p className={styles.loadingText}>Loading staff accounts...</p>
        ) : null}

        {!loading && (
          <div className={styles.layout}>
            <div className={styles.tablePane}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone Number</th>
                    <th>Role</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredStaff.length === 0 ? (
                    <tr>
                      <td colSpan={4}>No staff found.</td>
                    </tr>
                  ) : (
                    filteredStaff.map((u) => (
                      <tr key={u.id}>
                        {console.log(u)}
                        <td>{u.name}</td>
                        <td>{u.email}</td>
                        <td>{u.phone_no ? u.phone_no : "Not Given"}</td>
                        <td>{u.role}</td>
                        <td className={styles.actions}>
                          <button
                            type="button"
                            className={styles.dangerBtn}
                            onClick={() => handleDelete(u)}
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ManageAccounts;
