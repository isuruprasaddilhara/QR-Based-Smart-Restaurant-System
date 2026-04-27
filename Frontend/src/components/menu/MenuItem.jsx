// // import { useState } from "react";

// import Button from "../components/Button";

// import styles from "./MenuItem.module.css";

// function MenuItem({
//   name,
//   category,
//   description,
//   price,
//   availability,
//   onEdit,
// }) {
//   return (
//     <div className={styles.container}>
//       <p className={styles.itemName}>{name}</p>
//       {/* <p className={styles.itemCategory}>{category}</p>
//       <p className={styles.itemDescription}>{description}</p> */}

//       <p className={styles.itemPrice}>{price}</p>
//       <p
//         className={`${styles.itemAvailability} ${availability ? styles.available : styles.notAvailable}`}
//       >
//         {availability ? "Available" : "Not Available"}
//       </p>

//       <Button className={styles.itemEdit} onClick={onEdit}>
//         Edit
//       </Button>
//     </div>
//   );
// }

// export default MenuItem;

import { FaUtensils } from "react-icons/fa";
import { FaPencilAlt, FaTrash } from "react-icons/fa";

import styles from "./MenuItem.module.css";

function MenuItem({
  name,
  category,
  price,
  availability,
  image,
  onEdit,
  onDelete,
}) {
  return (
    <div className={styles.row}>
      <div className={styles.itemCell}>
        <img
          className={styles.thumb}
          src={image ? image : "/image2.png"}
          alt=""
        />
        <div className={styles.itemText}>
          <p className={styles.itemName}>{name}</p>
        </div>
      </div>

      <div className={styles.categoryCell}>
        <span className={styles.categoryTag}>
          <FaUtensils className={styles.categoryIcon} aria-hidden />
          {category}
        </span>
      </div>

      <p className={styles.itemPrice}>
        Rs {typeof price === "number" ? price.toLocaleString() : price}
      </p>

      <div className={styles.statusCell}>
        <span
          className={`${styles.statusPill} ${availability ? styles.available : styles.unavailable}`}
        >
          <span className={styles.statusDot} />
          {availability ? "Available" : "Unavailable"}
        </span>
      </div>

      <div className={styles.actions}>
        <button
          type="button"
          className={styles.iconBtn}
          onClick={onEdit}
          aria-label="Edit item"
        >
          <FaPencilAlt />
        </button>
        <button
          type="button"
          className={`${styles.iconBtn} ${styles.danger}`}
          onClick={onDelete}
          aria-label="Delete item"
        >
          <FaTrash />
        </button>
      </div>
    </div>
  );
}

export default MenuItem;
