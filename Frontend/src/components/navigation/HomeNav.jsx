// // import { useState } from "react";
// // import { NavLink } from "react-router-dom";

// import Logo from "../shared/Logo";

// import { HiHome } from "react-icons/hi";
// import { MdEdit } from "react-icons/md";
// import { MdTableBar } from "react-icons/md";
// import { IoStatsChart } from "react-icons/io5";

// import styles from "./HomeNav.module.css";

// function HomeNav({ activeTab, setActiveTab }) {
//   return (
//     <div className={styles.container}>
//       <div className={styles.logoWithName}>
//         <Logo imgPath="image2.png" width="150px" />
//         <h1>Scan2Serve</h1>
//       </div>

//       <ul className={styles.navElements}>
//         <li
//           className={`${styles.navElement} ${activeTab === "home" ? styles.active : ""}`}
//           onClick={() => setActiveTab("home")}
//         >
//           <HiHome className={styles.icon} />

//           <p>Home</p>
//         </li>
//         <li
//           className={`${styles.navElement} ${activeTab === "menu" ? styles.active : ""}`}
//           onClick={() => setActiveTab("menu")}
//         >
//           <MdEdit className={styles.icon} />
//           <p>Menu</p>
//         </li>
//         <li
//           className={`${styles.navElement} ${activeTab === "table" ? styles.active : ""}`}
//           onClick={() => setActiveTab("table")}
//         >
//           <MdTableBar className={styles.icon} />
//           <p>Tables</p>
//         </li>
//         <li
//           className={`${styles.navElement} ${activeTab === "stat" ? styles.active : ""}`}
//           onClick={() => setActiveTab("stat")}
//         >
//           <IoStatsChart className={styles.icon} />
//           <p>Statistics</p>
//         </li>
//       </ul>
//     </div>
//   );
// }

// export default HomeNav;

import Logo from "../shared/Logo";

import { getStoredRole } from "../../repository/auth";
import { canAccess } from "../../repository/roleAccess";

import {
  MdDashboard,
  MdReceiptLong,
  MdSettings,
  MdTableBar,
} from "react-icons/md";
import { FaUtensils } from "react-icons/fa";
import { HiUsers } from "react-icons/hi2";
import { IoStatsChart } from "react-icons/io5";

import styles from "./HomeNav.module.css";

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", Icon: MdDashboard },
  { id: "orders", label: "Orders", Icon: MdReceiptLong },

  { id: "menu", label: "Menu", Icon: FaUtensils },

  { id: "tables", label: "Tables", Icon: MdTableBar },
  { id: "users", label: "Manage Accounts", Icon: HiUsers },
  { id: "reports", label: "Reports", Icon: IoStatsChart },
  { id: "settings", label: "Settings", Icon: MdSettings },
];

function HomeNav({ activeTab, setActiveTab }) {
  const role = getStoredRole();
  const visibleNavItems = NAV_ITEMS.filter((item) => canAccess(role, item.id));

  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <Logo className={styles.brandLogo} imgPath="/image2.png" width="72px" />
        <span className={styles.brandName}>Scan2Serve</span>
      </div>

      <nav className={styles.nav} aria-label="Main">
        <ul className={styles.navList}>
          {visibleNavItems.map(({ id, label, Icon }) => (
            <li key={id}>
              <button
                type="button"
                className={`${styles.navBtn} ${activeTab === id ? styles.navBtnActive : ""}`}
                onClick={() => setActiveTab(id)}
              >
                <Icon className={styles.navIcon} aria-hidden />
                <span className={styles.navLabel}>{label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}

export default HomeNav;
