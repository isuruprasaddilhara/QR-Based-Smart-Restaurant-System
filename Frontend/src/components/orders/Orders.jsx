import { useCallback, useEffect, useMemo, useState } from "react";

import OrderItem from "./OrderItem.jsx";
import OrdersNav from "./OrdersNav.jsx";
import OrderBillModal from "./OrderBillModal.jsx";

import {
  fetchOrders,
  labelForApiStatus,
  matchesOrderFilter,
  patchOrderStatus,
} from "../../repository/orders";

import { getStoredRole } from "../../repository/auth";

import styles from "./Orders.module.css";

const POLL_MS = 15000;

function Orders() {
  const [activeNav, setActiveNav] = useState("all");
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [actionError, setActionError] = useState("");
  const [statusSavingId, setStatusSavingId] = useState(null);
  const [billOrder, setBillOrder] = useState(null);

  const loadOrders = useCallback(async () => {
    setLoadError("");
    try {
      const list = await fetchOrders();
      setOrders(list);
    } catch (e) {
      setLoadError(e.message || "Failed to load orders.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const list = await fetchOrders();
        if (!cancelled) setOrders(list);
      } catch (e) {
        if (!cancelled) setLoadError(e.message || "Failed to load orders.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    const id = setInterval(() => {
      fetchOrders()
        .then((list) => {
          if (!cancelled) setOrders(list);
        })
        .catch(() => {});
    }, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

 const role = getStoredRole();
  const isKitchen = role === "kitchen";

  const roleScopedOrders = isKitchen
    ? orders.filter(
        (o) => o.apiStatus === "pending" || o.apiStatus === "preparing" || o.apiStatus === "served"
      )
    : orders;

  const visibleOrders = useMemo(() => {
    return roleScopedOrders.filter((o) =>
      matchesOrderFilter(activeNav, o.apiStatus)
    );
  }, [roleScopedOrders, activeNav]);

  async function handleStatusChange(orderId, newApiStatus) {
    setActionError("");
    setStatusSavingId(orderId);
    try {
      await patchOrderStatus(orderId, newApiStatus);
      setOrders((prev) =>
        prev.map((o) =>
          o.id === orderId
            ? {
                ...o,
                apiStatus: newApiStatus,
                status: labelForApiStatus(newApiStatus),
              }
            : o,
        ),
      );
    } catch (e) {
      setActionError(e.message || "Could not update status.");
      loadOrders();
    } finally {
      setStatusSavingId(null);
    }
  }

  return (
    <div className={styles.page}>
      {loadError || actionError ? (
        <div className={styles.alertStack} role="alert">
          {loadError ? <p className={styles.errorBanner}>{loadError}</p> : null}
          {actionError ? (
            <p className={styles.errorBanner}>{actionError}</p>
          ) : null}
        </div>
      ) : null}

      <header className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Orders</h1>
        <p className={styles.pageSubtitle}>
          Track and manage customer orders in real time
        </p>
      </header>

      <OrdersNav
        className={styles.orderNav}
        activeNav={activeNav}
        setActiveNav={setActiveNav}
        showFilters={true}
        isKitchen={isKitchen}
      />

      {loading ? (
        <p className={styles.loading}>Loading orders…</p>
      ) : (
        <div className={styles.tableCard}>
          <div
            className={`${styles.orderHeadings} ${
              isKitchen ? styles.kitchenHeadings : ""
            }`}
          >
            <span>Order #</span>
            <span>Table #</span>
            <span>Time</span>
            <span>Ordered food</span>
            {isKitchen ? <span>Notes</span> : <span>Amount</span>}
            <span>Status</span>
            {!isKitchen ? <span>Action</span> : null}
          </div>

          {visibleOrders.length === 0 ? (
            <p className={styles.emptyHint}>No orders in this view.</p>
          ) : (
            visibleOrders.map((el) => (
              <OrderItem
                key={el.id}
                orderNum={el.orderNo}
                tableNum={el.tableNo}
                time={el.time}
                orderedFood={el.orderedFood}
                amount={el.amount}
                notes={el.specialNotes}
                apiStatus={el.apiStatus}
                statusLabel={el.status}
                orderId={el.id}
                onStatusChange={handleStatusChange}
                statusDisabled={statusSavingId === el.id}
                isKitchen={isKitchen}
                action="View"
                onView={() => setBillOrder(el)}
              />
            ))
          )}
        </div>
      )}
      {!isKitchen ? (
        <OrderBillModal order={billOrder} onClose={() => setBillOrder(null)} />
      ) : null}
    </div>
  );
}

export default Orders;
