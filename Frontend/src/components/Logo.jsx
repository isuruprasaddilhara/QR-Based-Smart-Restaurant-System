import styles from "./Logo.module.css";

function Logo({ imgPath, width }) {
  return (
    <div>
      <img
        src={imgPath}
        alt="Scan2Serve Logo"
        className={`${styles.logo}`}
        style={{ width: width }}
      />
    </div>
  );
}

export default Logo;
