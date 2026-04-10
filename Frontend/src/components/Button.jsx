// import styles from "./Button.module.css";

// function Button({ children, className = "", onClick, onDoubleClick }) {
//   return (
//     <button
//       className={`${styles.btn} ${className}`}
//       onClick={onClick}
//       onDoubleClick={onDoubleClick}
//     >
//       <span>{children} </span>
//     </button>
//   );
// }

// export default Button;

import styles from "./Button.module.css";

function Button({
  children,
  className = "",
  onClick,
  onDoubleClick,
  type = "button",
}) {
  return (
    <button
      type={type}
      className={`${styles.btn} ${className}`}
      onClick={onClick}
      onDoubleClick={onDoubleClick}
    >
      <span>{children} </span>
    </button>
  );
}

export default Button;
