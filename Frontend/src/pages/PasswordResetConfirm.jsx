import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { confirmPasswordReset } from "../repository/auth";

function PasswordResetConfirm() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const uid = searchParams.get("uid");
  const token = searchParams.get("token");

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  async function handleSubmit(e) {
    e?.preventDefault();
    setMessage("");
    setError("");

    if (!uid || !token) { setError("Invalid reset link."); return; }
    if (!newPassword || !confirmPassword) { setError("Please fill in all fields."); return; }
    if (newPassword !== confirmPassword) { setError("Passwords do not match."); return; }

    try {
      setLoading(true);
      const data = await confirmPasswordReset({ uid, token, new_password: newPassword });
      setMessage(data.detail || "Password has been reset successfully.");
      setNewPassword("");
      setConfirmPassword("");
      setTimeout(() => navigate("/login"), 2000);
    } catch (err) {
      setError(err.message || "Password reset failed.");
    } finally {
      setLoading(false);
    }
  }

  const getStrength = () => {
    const len = newPassword.length;
    if (len === 0) return 0;
    if (len < 6) return 1;
    if (len < 10) return 2;
    if (len < 14) return 3;
    return 4;
  };

  const strengthColors = ["#e8e3f4", "#f87171", "#fb923c", "#a3e635", "#4ade80"];
  const strength = getStrength();

  const EyeOpen = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>
  );

  const EyeOff = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
      <line x1="1" y1="1" x2="23" y2="23"/>
    </svg>
  );

  return (
    <>
      <style>{`
        /* Match the login page font: Inter from Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        .prc-wrapper {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f0eef8;
          font-family: 'Inter', sans-serif;
          padding: 24px;
        }

        .prc-card {
          background: #fff;
          border-radius: 24px;
          padding: 44px 40px 36px;
          width: 100%;
          max-width: 420px;
          box-shadow: 0 2px 32px rgba(100,75,160,0.09);
          text-align: center;
        }

        .prc-icon-wrap {
          width: 64px;
          height: 64px;
          border-radius: 18px;
          background: #ede9fe;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 30px;
          margin: 0 auto 20px;
        }

        /* Title matches login page: bold Inter, not serif */
        .prc-title {
          font-family: 'Inter', sans-serif;
          font-size: 26px;
          font-weight: 700;
          color: #1e1530;
          letter-spacing: -0.3px;
          margin-bottom: 8px;
        }

        /* Subtitle matches login page: regular Inter, muted */
        .prc-subtitle {
          font-family: 'Inter', sans-serif;
          font-size: 13.5px;
          font-weight: 400;
          color: #9585b8;
          margin-bottom: 32px;
        }

        .prc-field {
          margin-bottom: 20px;
          text-align: left;
        }

        /* Labels: Inter medium, matches login page field labels */
        .prc-label {
          display: block;
          font-family: 'Inter', sans-serif;
          font-size: 11px;
          font-weight: 600;
          color: #7c6a9e;
          letter-spacing: 0.8px;
          text-transform: uppercase;
          margin-bottom: 8px;
        }

        .prc-input-wrap {
          position: relative;
          display: flex;
          align-items: center;
        }

        /* Input: Inter regular, matching login page inputs */
        .prc-input {
          width: 100%;
          padding: 13px 44px 13px 16px;
          border: 1.5px solid #ede8f8;
          border-radius: 12px;
          font-size: 14.5px;
          font-family: 'Inter', sans-serif;
          font-weight: 400;
          color: #2d2040;
          background: #faf9fd;
          outline: none;
          transition: border-color 0.18s, box-shadow 0.18s, background 0.18s;
        }

        .prc-input::placeholder {
          color: #c4b8d8;
          font-family: 'Inter', sans-serif;
          font-weight: 400;
        }

        .prc-input:focus {
          border-color: #a78bfa;
          box-shadow: 0 0 0 3.5px rgba(167,139,250,0.14);
          background: #fff;
        }

        .prc-input.match   { border-color: #86efac; }
        .prc-input.mismatch { border-color: #fca5a5; }

        .prc-eye {
          position: absolute;
          right: 13px;
          background: none;
          border: none;
          cursor: pointer;
          color: #b8a8d8;
          display: flex;
          align-items: center;
          padding: 2px;
          transition: color 0.15s;
        }
        .prc-eye:hover { color: #7c3aed; }

        .prc-strength {
          display: flex;
          gap: 5px;
          margin-top: 8px;
        }

        .prc-seg {
          height: 3px;
          flex: 1;
          border-radius: 4px;
          transition: background 0.25s;
        }

        /* Button: Inter semibold, matches login page "Log in" button */
        .prc-btn {
          width: 100%;
          padding: 14px;
          margin-top: 8px;
          border: none;
          border-radius: 14px;
          background: #7c3aed;
          color: #fff;
          font-family: 'Inter', sans-serif;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.18s, transform 0.1s, box-shadow 0.18s;
          box-shadow: 0 4px 16px rgba(124,58,237,0.28);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          letter-spacing: -0.1px;
        }

        .prc-btn:hover:not(:disabled) {
          background: #6d28d9;
          box-shadow: 0 6px 20px rgba(124,58,237,0.35);
          transform: translateY(-1px);
        }

        .prc-btn:active:not(:disabled) { transform: translateY(0); }

        .prc-btn:disabled {
          background: #c4b5f4;
          box-shadow: none;
          cursor: not-allowed;
        }

        .spinner {
          width: 15px;
          height: 15px;
          border: 2px solid rgba(255,255,255,0.35);
          border-top-color: #fff;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
          flex-shrink: 0;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* Alert text: Inter regular */
        .prc-alert {
          display: flex;
          align-items: flex-start;
          gap: 9px;
          margin-top: 16px;
          padding: 12px 14px;
          border-radius: 11px;
          font-family: 'Inter', sans-serif;
          font-size: 13.5px;
          font-weight: 400;
          line-height: 1.45;
          text-align: left;
        }

        .prc-alert.success { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
        .prc-alert.error   { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }

        /* Back link: Inter regular, matches login page secondary links */
        .prc-back {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          margin-top: 22px;
          font-family: 'Inter', sans-serif;
          font-size: 13px;
          font-weight: 400;
          color: #9585b8;
          cursor: pointer;
          background: none;
          border: none;
          transition: color 0.15s;
        }
        .prc-back:hover { color: #7c3aed; }
      `}</style>

      <div className="prc-wrapper">
        <div className="prc-card">
          <div className="prc-icon-wrap">🔐</div>
          <h1 className="prc-title">Reset Password</h1>
          <p className="prc-subtitle">Create a new secure password for your account</p>

          <div className="prc-field">
            <label className="prc-label">New Password</label>
            <div className="prc-input-wrap">
              <input
                type={showNew ? "text" : "password"}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password"
                className="prc-input"
              />
              <button className="prc-eye" type="button" onClick={() => setShowNew(!showNew)} tabIndex={-1}>
                {showNew ? <EyeOff /> : <EyeOpen />}
              </button>
            </div>
            {newPassword.length > 0 && (
              <div className="prc-strength">
                {[0,1,2,3].map(i => (
                  <div
                    key={i}
                    className="prc-seg"
                    style={{ background: i < strength ? strengthColors[strength] : "#e8e3f4" }}
                  />
                ))}
              </div>
            )}
          </div>

          <div className="prc-field">
            <label className="prc-label">Confirm Password</label>
            <div className="prc-input-wrap">
              <input
                type={showConfirm ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                className={`prc-input${
                  confirmPassword
                    ? newPassword === confirmPassword ? " match" : " mismatch"
                    : ""
                }`}
              />
              <button className="prc-eye" type="button" onClick={() => setShowConfirm(!showConfirm)} tabIndex={-1}>
                {showConfirm ? <EyeOff /> : <EyeOpen />}
              </button>
            </div>
          </div>

          <button className="prc-btn" disabled={loading} onClick={handleSubmit}>
            {loading && <span className="spinner" />}
            {loading ? "Resetting…" : "Reset Password"}
          </button>

          {message && (
            <div className="prc-alert success">
              <span>✅</span> {message}
            </div>
          )}
          {error && (
            <div className="prc-alert error">
              <span>⚠️</span> {error}
            </div>
          )}

          <button className="prc-back" onClick={() => navigate("/login")}>
            ← Back to login
          </button>
        </div>
      </div>
    </>
  );
}

export default PasswordResetConfirm;