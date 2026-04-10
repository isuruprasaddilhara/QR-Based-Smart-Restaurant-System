// import { useNavigate } from "react-router-dom";
// import { useState } from "react";

// import HomeNav from "../components/HomeNav";
// import Button from "../components/Button";
// import Orders from "../components/Orders";
// import Menu from "../components/Menu";
// import Tables from "../components/Tables";

// import styles from "./Home.module.css";

// function Homepage() {
//   const navigate = useNavigate();

//   const [activeTab, setActiveTab] = useState("home");

//   return (
//     <div className={styles.container}>
//       <HomeNav activeTab={activeTab} setActiveTab={setActiveTab} />
//       <div className={styles.ordersSection}>
//         <div className={styles.logout}>
//           <p className={styles.hasToChange}>Admin</p>
//           <Button onClick={() => navigate("/login")} className={styles.btn}>
//             LogOut
//           </Button>
//         </div>

//         {activeTab === "home" && <Orders />}
//         {activeTab === "menu" && <Menu />}
//         {activeTab === "table" && <Tables />}
//       </div>
//     </div>
//   );
// }

// export default Homepage;

import { useNavigate } from "react-router-dom";
import { useState, useRef, useEffect } from "react";

import { canAccess } from "../repository/roleAccess";

import HomeNav from "../components/HomeNav";
import Logo from "../components/Logo";
import Orders from "../components/Orders";
import Menu from "../components/Menu";
import Tables from "../components/Tables";
import Reports from "../components/Reports";
import ManageAccounts from "../components/ManageAccounts";
import AccountSettings from "../components/AccountSettings";

import {
  clearStoredAuth,
  formatRoleLabel,
  getStoredRole,
  isAdminSession,
} from "../repository/auth";

import { FaChevronDown } from "react-icons/fa";

import styles from "./Home.module.css";

function Placeholder({ title }) {
  return (
    <div className={styles.placeholder}>
      <h2 className={styles.placeholderTitle}>{title}</h2>
      <p className={styles.placeholderText}>This section is coming soon.</p>
    </div>
  );
}

function initialTabForRole() {
  const r = getStoredRole();
  if (r === "kitchen") return "orders";
  return "dashboard";
}

function Homepage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(initialTabForRole);
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef(null);

  const [roleLabel, setRoleLabel] = useState(() =>
    formatRoleLabel(getStoredRole()),
  );

  const role = getStoredRole();

  useEffect(() => {
    function syncProfile() {
      setRoleLabel(formatRoleLabel(getStoredRole()));
    }
    syncProfile();
    window.addEventListener("storage", syncProfile);
    return () => window.removeEventListener("storage", syncProfile);
  }, []);

  useEffect(() => {
    function handleClickOutside(e) {
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setProfileOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const fallback = "settings";
    if (!canAccess(role, activeTab)) {
      if (canAccess(role, "dashboard")) setActiveTab("dashboard");
      else if (canAccess(role, "orders")) setActiveTab("orders");
      else setActiveTab(fallback);
    }
  }, [role, activeTab]);

  return (
    <div className={styles.shell}>
      <HomeNav activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className={styles.main}>
        <header className={styles.topBar}>
          <div className={styles.topBarSpacer} />
          <div className={styles.profileWrap} ref={profileRef}>
            <button
              type="button"
              className={styles.profileTrigger}
              onClick={() => setProfileOpen((o) => !o)}
              aria-expanded={profileOpen}
              aria-haspopup="true"
            >
              <Logo imgPath="/image2.png" width="48px" />
              <div className={styles.profileText}>
                <span className={styles.brandName}>Scan2Serve</span>

                <span className={styles.role}>{roleLabel}</span>
              </div>
              <FaChevronDown
                className={`${styles.chevron} ${profileOpen ? styles.chevronOpen : ""}`}
                aria-hidden
              />
            </button>

            {profileOpen && (
              <div className={styles.profileMenu}>
                <button
                  type="button"
                  className={styles.profileMenuItem}
                  onClick={() => {
                    setProfileOpen(false);
                    clearStoredAuth();
                    navigate("/login");
                  }}
                >
                  Log out
                </button>
                {isAdminSession() ? (
                  <button
                    type="button"
                    className={styles.profileMenuItem}
                    onClick={() => {
                      setProfileOpen(false);
                      navigate("/signup");
                    }}
                  >
                    Invite staff
                  </button>
                ) : null}
              </div>
            )}
          </div>
        </header>

        <div className={styles.content}>
          {activeTab === "dashboard" && canAccess(role, "dashboard") && (
            <Orders />
          )}
          {activeTab === "orders" && canAccess(role, "orders") && <Orders />}
          {activeTab === "menu" && canAccess(role, "menu") && <Menu />}
          {activeTab === "tables" && canAccess(role, "tables") && <Tables />}
          {activeTab === "users" && canAccess(role, "users") && (
            <ManageAccounts />
          )}
          {activeTab === "reports" && canAccess(role, "reports") && <Reports />}
          {activeTab === "settings" && canAccess(role, "settings") && (
            <AccountSettings />
          )}
        </div>
      </div>
    </div>
  );
}

export default Homepage;
