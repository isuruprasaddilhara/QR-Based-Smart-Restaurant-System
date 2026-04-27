import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import Logo from "../shared/Logo";

import {
  login,
  requestPasswordReset,
  saveAuthFromLoginPayload,
  clearStoredAuth,
  notifyAuthUpdated,
} from "../../repository/auth";

import styles from "./LoginSideBar.module.css";

import { IoMailOpen } from "react-icons/io5";
import { RiLockPasswordFill } from "react-icons/ri";

function LoginSideBar() {
  const navigate = useNavigate();
  const [email, setemail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showForgot, setShowForgot] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotBusy, setForgotBusy] = useState(false);
  const [forgotError, setForgotError] = useState("");
  const [forgotMessage, setForgotMessage] = useState("");
  const passwordRef = useRef(null);

  async function handleLogin(e) {
    e?.preventDefault();
    setError("");
    if (!email.trim() || !password) {
      setError("Enter email and password.");
      return;
    }
    setLoading(true);
    try {
      const data = await login({ email, password });
      saveAuthFromLoginPayload(data);
      notifyAuthUpdated();
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

  async function handleForgotPassword(e) {
    e?.preventDefault();
    setForgotError("");
    setForgotMessage("");
    const targetEmail = forgotEmail.trim() || email.trim();
    if (!targetEmail) {
      setForgotError("Enter your email to receive a reset link.");
      return;
    }
    setForgotBusy(true);
    try {
      const data = await requestPasswordReset(targetEmail);
      setForgotMessage(
        data?.detail || "If that email exists, a reset link has been sent.",
      );
      if (!forgotEmail.trim()) setForgotEmail(targetEmail);
    } catch (e) {
      setForgotError(e.message || "Could not send reset link.");
    } finally {
      setForgotBusy(false);
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Logo imgPath="/image2.png" width="72px" />
        <h1 className={styles.title}>Login</h1>
        <p className={styles.lead}>Sign in to manage menu and orders.</p>
      </div>

      {error ? <p className={styles.errorText}>{error}</p> : null}

      <form onSubmit={handleLogin} noValidate>
        <div className={styles.form}>
          <div className={styles.inputWrapper}>
            <IoMailOpen className={styles.inputIcon} aria-hidden />
            <input
              className={styles.userInput}
              type="email"
              autoComplete="username"
              value={email}
              placeholder="Email"
              onChange={(e) => setemail(e.target.value)}
              onKeyDown={(e) => {
                if (e.key !== "Enter") return;
                e.preventDefault();
                if (email.trim() && password) {
                  handleLogin(e);
                } else {
                  passwordRef.current?.focus();
                }
              }}
            />
          </div>

          <div className={styles.inputWrapper}>
            <RiLockPasswordFill className={styles.inputIcon} aria-hidden />
            <input
              ref={passwordRef}
              className={styles.userInput}
              type="password"
              autoComplete="current-password"
              value={password}
              placeholder="Password"
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key !== "Enter") return;
                e.preventDefault();
                handleLogin(e);
              }}
            />
          </div>
        </div>
        <button
          type="button"
          className={styles.forgotToggle}
          onClick={() => {
            setShowForgot((prev) => !prev);
            setForgotError("");
            setForgotMessage("");
            if (!forgotEmail && email.trim()) setForgotEmail(email.trim());
          }}
        >
          Forgot password?
        </button>

        {showForgot ? (
          <div className={styles.forgotPanel}>
            <label className={styles.forgotLabel} htmlFor="forgot-email">
              Enter your account email
            </label>
            <input
              id="forgot-email"
              className={styles.userInput}
              type="email"
              autoComplete="email"
              value={forgotEmail}
              onChange={(e) => setForgotEmail(e.target.value)}
              placeholder="name@example.com"
            />
            {forgotError ? <p className={styles.errorText}>{forgotError}</p> : null}
            {forgotMessage ? (
              <p className={styles.successText}>{forgotMessage}</p>
            ) : null}
            <button
              type="button"
              className={styles.secondaryBtn}
              onClick={handleForgotPassword}
              disabled={forgotBusy}
            >
              {forgotBusy ? "Sending…" : "Send reset link"}
            </button>
          </div>
        ) : null}

        <div className={styles.buttons}>
          <button
            type="submit"
            className={styles.primaryBtn}
            disabled={loading}
          >
            {loading ? "Signing in…" : "Log in"}
          </button>
          <div className={styles.signupRow}>
            <span>Need to invite a team member? </span>
            <span>Please Log in as an Admin</span>
          </div>
        </div>
      </form>
    </div>
  );
}

export default LoginSideBar;
