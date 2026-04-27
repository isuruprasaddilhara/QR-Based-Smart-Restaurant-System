import SignUpSideBar from "./SignUpSideBar";

import styles from "./SignUpCard.module.css";

function SignUpCard() {
  return (
    <div className={styles.wrapper}>
      <SignUpSideBar />
      <img src="/image-signUp.png" alt="" className={styles.heroImg} />
    </div>
  );
}

export default SignUpCard;
