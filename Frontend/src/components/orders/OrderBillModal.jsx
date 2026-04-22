import { useEffect, useRef, useState } from "react";

import {
  fetchBillPrintPdf,
  labelForApiStatus,
  sendBillSoftCopy,
} from "../../repository/orders";

import { useEscapeKey } from "../../hooks/useEscapeKey";

import styles from "./OrderBillModal.module.css";

function formatRs(value) {
  const n = value != null ? Number(value) : 0;
  if (Number.isNaN(n)) return "Rs. 0.00";
  return `Rs. ${n.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function statusPillClass(apiStatus) {
  if (apiStatus === "pending") return styles.new;
  if (apiStatus === "preparing") return styles.preparing;
  if (apiStatus === "served") return styles.served;
  if (apiStatus === "requested") return styles.billRequested;
  return styles.completed;
}

function OrderBillModal({ order, onClose }) {
  const printRef = useRef(null);
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [printing, setPrinting] = useState(false);
  const [actionErr, setActionErr] = useState("");
  const [actionMsg, setActionMsg] = useState("");

  useEscapeKey(!!order, onClose);

  useEffect(() => {
    setEmail(order?.customerEmail || "");
    setActionErr("");
    setActionMsg("");
  }, [order?.id, order?.customerEmail]);

  if (!order) return null;

  async function handleSendBill() {
    setActionErr("");
    setActionMsg("");
    if (!email.trim()) {
      setActionErr("Enter an email address to send the bill.");
      return;
    }
    setSending(true);
    try {
      const data = await sendBillSoftCopy(order.id, email);
      setActionMsg(data?.message || "Bill sent.");
    } catch (e) {
      setActionErr(e.message || "Failed to send bill.");
    } finally {
      setSending(false);
    }
  }

  async function handlePrintBill() {
    setActionErr("");
    setActionMsg("");
    setPrinting(true);
    try {
      const blob = await fetchBillPrintPdf(order.id);
      const url = URL.createObjectURL(blob);
      const w = window.open(url, "_blank", "noopener,noreferrer");
      if (!w) {
        URL.revokeObjectURL(url);
        throw new Error("Popup blocked. Allow popups to open the bill PDF.");
      }
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (e) {
      setActionErr(e.message || "Could not load bill PDF.");
    } finally {
      setPrinting(false);
    }
  }

  return (
    <div
      className={styles.overlay}
      role="dialog"
      aria-modal="true"
      aria-labelledby="bill-modal-title"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className={styles.card} onMouseDown={(e) => e.stopPropagation()}>
        <div className={styles.cardHeader}>
          <div>
            <h2 id="bill-modal-title" className={styles.title}>
              Order #{order.orderNo}
            </h2>
            <p className={styles.meta}>
              Table {order.tableNo} · {order.time}
            </p>
          </div>
          <button type="button" className={styles.closeBtn} onClick={onClose}>
            ×
          </button>
        </div>

        <div className={styles.body}>
          <div className={styles.mainCol}>
            <section className={styles.section} ref={printRef}>
              <h3 className={styles.sectionLabel}>Bill</h3>
              <div className={styles.tableWrap}>
                <table className={styles.billTable}>
                  <thead>
                    <tr>
                      <th>Item</th>
                      <th className={styles.num}>Qty</th>
                      <th className={styles.num}>Unit</th>
                      <th className={styles.num}>Line</th>
                    </tr>
                  </thead>
                  <tbody>
                    {order.orderedFood.map((row, i) => (
                      <tr key={`${row.name}-${i}`}>
                        <td>{row.name}</td>
                        <td className={styles.num}>{row.quantity}</td>
                        <td className={styles.num}>
                          {row.unitPrice != null && !Number.isNaN(row.unitPrice)
                            ? formatRs(row.unitPrice)
                            : "—"}
                        </td>
                        <td className={styles.num}>
                          {formatRs(row.lineTotal)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className={styles.totalRow}>
                <span>Total</span>
                <strong>{formatRs(order.totalAmountNumeric)}</strong>
              </div>
            </section>

            <section className={styles.section}>
              <h3 className={styles.sectionLabel}>Actions</h3>
              <label className={styles.emailLabel}>
                <span className={styles.emailLabelText}>Email for bill</span>
                <input
                  type="email"
                  className={styles.emailInput}
                  placeholder="customer@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                />
              </label>
              {actionErr ? (
                <p className={styles.actionError} role="alert">
                  {actionErr}
                </p>
              ) : null}
              {actionMsg ? (
                <p className={styles.actionSuccess}>{actionMsg}</p>
              ) : null}
              <div className={styles.actions}>
                <button
                  type="button"
                  className={styles.btnPrimary}
                  onClick={handleSendBill}
                  disabled={sending || printing}
                >
                  {sending ? "Sending…" : "Send Bill"}
                </button>
                <button
                  type="button"
                  className={styles.btnSecondary}
                  onClick={handlePrintBill}
                  disabled={sending || printing}
                >
                  {printing ? "Opening…" : "Print Bill"}
                </button>
              </div>
            </section>
          </div>

          <aside className={styles.sideCol}>
            <section className={styles.section}>
              <h3 className={styles.sectionLabel}>Special notes</h3>
              <p className={styles.notes}>{order.specialNotes}</p>
            </section>
            <section className={styles.section}>
              <h3 className={styles.sectionLabel}>Order status</h3>
              <p
                className={`${styles.statusPill} ${statusPillClass(order.apiStatus)}`}
              >
                {labelForApiStatus(order.apiStatus)}
              </p>
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}

export default OrderBillModal;
