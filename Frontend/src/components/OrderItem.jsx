import Button from "./Button";

import styles from "./OrderItem.module.css";

import { nextOrderStatus, orderStatus } from "../repository/orders";

function statusButtonClass(apiStatus) {
  if (apiStatus === orderStatus.pending) return styles.new;
  if (apiStatus === orderStatus.preparing) return styles.preparing;
  if (apiStatus === orderStatus.served) return styles.served;
  if (apiStatus === orderStatus.requested) return styles.billRequested;
  return styles.completed;
}

function OrderItem({
  orderNum,
  tableNum,
  time,
  orderedFood,
  amount,
  apiStatus,
  statusLabel,
  orderId,
  onStatusChange,
  statusDisabled,
  action,
  onView,
}) {
  const canAdvance = nextOrderStatus(apiStatus) != null;

  function handleStatusDoubleClick() {
    if (statusDisabled || !canAdvance) return;
    const next = nextOrderStatus(apiStatus);
    if (next) onStatusChange(orderId, next);
  }

  return (
    <div className={styles.container}>
      <p className={styles.orderNumber}>{orderNum}</p>
      <p className={styles.tableNumber}>{tableNum}</p>
      <p className={styles.time}>{time}</p>

      <div className={styles.orderedFood}>
        {orderedFood.map((el, i) => (
          <p key={`${el.name}-${i}`}>
            {el.name} × {el.quantity}
          </p>
        ))}
      </div>

      <p className={styles.amount}>{amount}</p>

      <Button
        type="button"
        className={`${styles.status} ${statusButtonClass(apiStatus)}`}
        onDoubleClick={handleStatusDoubleClick}
        disabled={statusDisabled || !canAdvance}
        title={
          canAdvance
            ? "Double-click to move to the next status"
            : "Final status"
        }
      >
        {statusLabel}
      </Button>

      <Button className={styles.action} type="button" onClick={onView}>
        {action}
      </Button>
    </div>
  );
}

export default OrderItem;
