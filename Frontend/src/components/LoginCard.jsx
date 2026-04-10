import LoginSideBar from "./LoginSideBar";
import Logo from "./Logo";

import styles from "./LoginCard.module.css";

function LoginCard() {
  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <LoginSideBar />
      </div>
    </div>
  );
}

export default LoginCard;
