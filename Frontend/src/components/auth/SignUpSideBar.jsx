import { useState } from "react";
import { useNavigate } from "react-router-dom";

import Logo from "../shared/Logo";
import { registerStaff, formatRoleLabel } from "../../repository/auth";
import { isValidPhone10Digits, normalizePhoneDigits } from "../../utils/phone";
import styles from "./SignUpSideBar.module.css";

import { FaUserAlt } from "react-icons/fa";
import { IoMailOpen } from "react-icons/io5";
import { MdCall } from "react-icons/md";
import { RiLockPasswordFill } from "react-icons/ri";
import { FaArrowLeft } from "react-icons/fa";

function SignUpSideBar() {
  const navigate = useNavigate();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [staffRole, setStaffRole] = useState("kitchen");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSubmit() {
    setError("");
    setSuccess("");

    if (!email.trim() || !password) {
      setError("Email and password are required.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    const name = [firstName, lastName].filter(Boolean).join(" ").trim();
    if (!name) {
      setError("Please enter a name.");
      return;
    }

    const phoneDigits = normalizePhoneDigits(phoneNumber);
    if (!isValidPhone10Digits(phoneDigits)) {
      setError("Phone number must be exactly 10 digits (0–9).");
      return;
    }

    setLoading(true);
    try {
      await registerStaff({
        email,
        name,
        password,
        phone_no: phoneDigits,
        role: staffRole,
      });
      setSuccess(`Account created with ${formatRoleLabel(staffRole)} access.`);
      setEmail("");
      setFirstName("");
      setLastName("");
      setPhoneNumber("");
      setPassword("");
      setConfirmPassword("");
    } catch (e) {
      setError(e.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.container}>
      <button
        type="button"
        className={styles.backLink}
        onClick={() => navigate("/home")}
      >
        <FaArrowLeft aria-hidden />
        Back to dashboard
      </button>
      <div className={styles.header}>
        <Logo imgPath="/image2.png" width="72px" />
        <h1 className={styles.title}>Invite staff</h1>
        <p className={styles.lead}>
          Add an admin, kitchen, or cashier account. An <strong>admin</strong>{" "}
          must be logged in on this device first.{" "}
        </p>
      </div>

      {error ? <p className={styles.errorText}>{error}</p> : null}
      {success ? <p className={styles.successText}>{success}</p> : null}

      <div className={styles.form}>
        <label className={styles.selectWrap}>
          <span className={styles.selectLabel}>Role</span>
          <select
            className={styles.select}
            value={staffRole}
            onChange={(e) => setStaffRole(e.target.value)}
          >
            <option value="admin">Admin</option>
            <option value="kitchen">Kitchen</option>
            <option value="cashier">Cashier</option>
          </select>
        </label>

        <div className={styles.row}>
          <div className={styles.inputWrapper}>
            <FaUserAlt className={styles.inputIcon} aria-hidden />
            <input
              className={styles.userInput}
              type="text"
              value={firstName}
              placeholder="First name"
              onChange={(e) => setFirstName(e.target.value)}
              autoComplete="given-name"
            />
          </div>
          <div className={styles.inputWrapper}>
            <FaUserAlt className={styles.inputIcon} aria-hidden />
            <input
              className={styles.userInput}
              type="text"
              value={lastName}
              placeholder="Last name"
              onChange={(e) => setLastName(e.target.value)}
              autoComplete="family-name"
            />
          </div>
        </div>

        <div className={styles.inputWrapper}>
          <IoMailOpen className={styles.inputIcon} aria-hidden />
          <input
            className={styles.userInput}
            type="email"
            autoComplete="email"
            value={email}
            placeholder="Work email"
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className={styles.inputWrapper}>
          <MdCall className={styles.inputIcon} aria-hidden />
          <input
            className={styles.userInput}
            type="tel"
            inputMode="numeric"
            autoComplete="tel"
            maxLength={10}
            placeholder="10 digits (e.g. 0771234567)"
            aria-invalid={phoneNumber.length > 0 && phoneNumber.length !== 10}
            value={phoneNumber}
            onChange={(e) =>
              setPhoneNumber(e.target.value.replace(/\D/g, "").slice(0, 10))
            }
          />
        </div>

        <div className={styles.row}>
          <div className={styles.inputWrapper}>
            <RiLockPasswordFill className={styles.inputIcon} aria-hidden />
            <input
              className={styles.userInput}
              type="password"
              autoComplete="new-password"
              value={password}
              placeholder="Password"
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <div className={styles.inputWrapper}>
            <RiLockPasswordFill className={styles.inputIcon} aria-hidden />
            <input
              className={styles.userInput}
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              placeholder="Confirm password"
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className={styles.buttons}>
        <button
          type="button"
          className={styles.primaryBtn}
          disabled={loading}
          onClick={handleSubmit}
        >
          {loading ? "Creating…" : "Create staff account"}
        </button>

      </div>
    </div>
  );
}

export default SignUpSideBar;
