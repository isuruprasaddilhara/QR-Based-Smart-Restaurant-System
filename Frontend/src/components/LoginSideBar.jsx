import { useState } from "react";
import { useNavigate } from "react-router-dom";

import Logo from "./Logo";

import {
  login,
  saveAuthFromLoginPayload,
  clearStoredAuth,
} from "../repository/auth";

import styles from "./LoginSideBar.module.css";

import { IoMailOpen } from "react-icons/io5";
import { RiLockPasswordFill } from "react-icons/ri";

function LoginSideBar() {
  const navigate = useNavigate();
  const [email, setemail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin() {
    setError("");
    if (!email.trim() || !password) {
      setError("Enter email and password.");
      return;
    }
    setLoading(true);
    try {
      const data = await login({ email, password });
      saveAuthFromLoginPayload(data);
      const role = data.user?.role;
      if (role === "customer") {
        clearStoredAuth();
        setError("This portal is for staff and admins only.");
        return;
      }
      navigate("/home", { replace: true });
    } catch (e) {
      setError(e.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Logo imgPath="/image2.png" width="72px" />
        <h1 className={styles.title}>Admin login</h1>
        <p className={styles.lead}>Sign in to manage menu and orders.</p>
      </div>

      {error ? <p className={styles.errorText}>{error}</p> : null}

      <div className={styles.form}>
        <div className={styles.inputWrapper}>
          <IoMailOpen className={styles.inputIcon} aria-hidden />
          <input
            className={styles.userInput}
            type="text"
            autoComplete="username"
            value={email}
            placeholder="Email"
            onChange={(e) => setemail(e.target.value)}
          />
        </div>

        <div className={styles.inputWrapper}>
          <RiLockPasswordFill className={styles.inputIcon} aria-hidden />
          <input
            className={styles.userInput}
            type="password"
            autoComplete="current-password"
            value={password}
            placeholder="Password"
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
      </div>

      <div className={styles.buttons}>
        <button
          type="button"
          className={styles.primaryBtn}
          disabled={loading}
          onClick={handleLogin}
        >
          {loading ? "Signing in…" : "Log in"}
        </button>
        <div className={styles.signupRow}>
          <span>Need to invite a team member? </span>
          <span>Please Log in as an Admin</span>
        </div>
      </div>
    </div>
  );
}

export default LoginSideBar;
