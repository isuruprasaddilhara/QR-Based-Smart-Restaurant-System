import Button from "./Button";

import styles from "./TableItem.module.css";

function TableItem({
  tableId,
  tableNo,
  capacity,
  status,
  onEdit,
  onDelete,
  onDownloadQr,
}) {
  return (
    <div className={styles.container}>
      <p className={styles.tableNo}>{tableNo}</p>
      <p className={styles.capacity}>{capacity}</p>

      <p
        className={`${styles.status} ${
          status === "Available" ? styles.available : styles.occupied
        }`}
      >
        {status}
      </p>

      <div className={styles.actions}>
        <Button className={styles.editBtn} type="button" onClick={onEdit}>
          Edit
        </Button>
        <Button className={styles.deleteBtn} type="button" onClick={onDelete}>
          Delete
        </Button>
        <Button
          className={styles.qrBtn}
          type="button"
          onClick={() => onDownloadQr(tableId)}
        >
          Download QR
        </Button>
      </div>
    </div>
  );
}

export default TableItem;
