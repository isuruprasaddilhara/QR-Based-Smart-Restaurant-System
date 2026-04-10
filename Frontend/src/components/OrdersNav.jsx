import Button from "../components/Button";

import styles from "./OrdersNav.module.css";

function OrdersNav({ activeNav, setActiveNav, showFilters = true, className }) {
  if (!showFilters) {
    return null;
  }

  return (
    <div className={`${styles.container}${className ? ` ${className}` : ""}`}>
      <div className={styles.filters}>
        <p>Filter Orders</p>
        <div className={styles.filterButtons}>
          <Button
            className={`${styles.filterBtn} ${activeNav === "all" ? styles.active : ""}`}
            onClick={() => setActiveNav("all")}
          >
            All{" "}
          </Button>

          <Button
            className={`${styles.filterBtn} ${activeNav === "new" ? styles.active : ""}`}
            onClick={() => setActiveNav("new")}
          >
            New
          </Button>
          <Button
            className={`${styles.filterBtn} ${activeNav === "preparing" ? styles.active : ""}`}
            onClick={() => setActiveNav("preparing")}
          >
            Preparing
          </Button>

          <Button
            className={`${styles.filterBtn} ${activeNav === "served" ? styles.active : ""}`}
            onClick={() => setActiveNav("served")}
          >
            Served
          </Button>

          <Button
            className={`${styles.filterBtn} ${activeNav === "requested" ? styles.active : ""}`}
            onClick={() => setActiveNav("requested")}
          >
            Requested
          </Button>

          <Button
            className={`${styles.filterBtn} ${activeNav === "completed" ? styles.active : ""}`}
            onClick={() => setActiveNav("completed")}
          >
            Completed
          </Button>
        </div>
      </div>
    </div>
  );
}

export default OrdersNav;
