import { useNavigate } from "react-router-dom";

import Logo from "./Logo.jsx";
import Button from "./Button.jsx";

import styles from "./WelcomeCard.module.css";

function WelcomeCard() {
  const navigate = useNavigate();
  return (
    <div className={styles.container}>
      <Logo className={styles.logo} imgPath="/image2.png" width="180px" />
      <h1 className={styles.welcome}>Welcome to Scan2Serve Admin</h1>
      <p className={styles.subtitle}>
        Log in or create an account to continue.
      </p>

      <div className={styles.btnContainer}>
        <Button
          className={`${styles.btn} ${styles.highlight}`}
          onClick={() => navigate("/login")}
        >
          Login
        </Button>
        <Button
          className={`${styles.btn} ${styles.no_highlight}`}
          onClick={() => navigate("/signup")}
        >
          SignUp
        </Button>
      </div>

      <p className={styles.last}> Continue as a Cashier Demo </p>
    </div>
  );
}

export default WelcomeCard;
