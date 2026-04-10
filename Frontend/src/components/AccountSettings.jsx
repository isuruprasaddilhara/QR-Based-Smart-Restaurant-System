import { useEffect, useState } from "react";
import { IoMailOpen } from "react-icons/io5";
import { MdCall } from "react-icons/md";
import { RiLockPasswordFill } from "react-icons/ri";
import { FaUserAlt } from "react-icons/fa";

import {
  changeMyPassword,
  fetchMyStaffProfile,
  updateMyStaffProfile,
} from "../repository/staff";
import styles from "./AccountSettings.module.css";

function AccountSettings() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNo, setPhoneNo] = useState("");

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const [loadingInitial, setLoadingInitial] = useState(true);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [loadingPassword, setLoadingPassword] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setLoadingInitial(true);
      setError("");
      try {
        const me = await fetchMyStaffProfile();
        if (cancelled) return;
        setName(me?.name || "");
        setEmail(me?.email || "");
        setPhoneNo(me?.phone_no || "");
      } catch (e) {
        if (!cancelled)
          setError(e.message || "Failed to load account details.");
      } finally {
        if (!cancelled) setLoadingInitial(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleProfileSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess("");

    setLoadingProfile(true);
    try {
      await updateMyStaffProfile({
        name: name.trim(),
        email: email.trim(),
        phone_no: phoneNo.trim(),
      });
      localStorage.setItem("name", name.trim());
      localStorage.setItem("username", email.trim());
      setSuccess("Profile updated successfully.");
    } catch (err) {
      setError(err.message || "Failed to update profile.");
    } finally {
      setLoadingProfile(false);
    }
  }

  async function handlePasswordSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!oldPassword || !newPassword) {
      setError("Please enter current and new password.");
      return;
    }

    setLoadingPassword(true);
    try {
      await changeMyPassword(oldPassword, newPassword);
      setSuccess("Password changed successfully.");
      setOldPassword("");
      setNewPassword("");
    } catch (err) {
      setError(err.message || "Failed to change password.");
    } finally {
      setLoadingPassword(false);
    }
  }

  if (loadingInitial) {
    return (
      <p className={styles.loadingText}>Loading your account details...</p>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h2 className={styles.title}>My Account</h2>
          <p className={styles.lead}>
            Update your profile details and password.
          </p>
        </div>

        {error ? <p className={styles.errorText}>{error}</p> : null}
        {success ? <p className={styles.successText}>{success}</p> : null}

        <div className={styles.formGrid}>
          <form className={styles.form} onSubmit={handleProfileSubmit}>
            <h3 className={styles.sectionTitle}>Profile Details</h3>

            <div className={styles.inputWrapper}>
              <FaUserAlt className={styles.inputIcon} aria-hidden />
              <input
                className={styles.userInput}
                type="text"
                placeholder="Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            <div className={styles.inputWrapper}>
              <IoMailOpen className={styles.inputIcon} aria-hidden />
              <input
                className={styles.userInput}
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className={styles.inputWrapper}>
              <MdCall className={styles.inputIcon} aria-hidden />
              <input
                className={styles.userInput}
                type="tel"
                placeholder="Phone Number"
                value={phoneNo}
                onChange={(e) => setPhoneNo(e.target.value)}
              />
            </div>

            <button
              className={styles.submitBtn}
              type="submit"
              disabled={loadingProfile}
            >
              {loadingProfile ? "Saving..." : "Save Profile"}
            </button>
          </form>

          <form className={styles.form} onSubmit={handlePasswordSubmit}>
            <h3 className={styles.sectionTitle}>Change Password</h3>

            <div className={styles.inputWrapper}>
              <RiLockPasswordFill className={styles.inputIcon} aria-hidden />
              <input
                className={styles.userInput}
                type="password"
                placeholder="Current Password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
              />
            </div>

            <div className={styles.inputWrapper}>
              <RiLockPasswordFill className={styles.inputIcon} aria-hidden />
              <input
                className={styles.userInput}
                type="password"
                placeholder="New Password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>

            <button
              className={styles.submitBtn}
              type="submit"
              disabled={loadingPassword}
            >
              {loadingPassword ? "Updating..." : "Update Password"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default AccountSettings;
