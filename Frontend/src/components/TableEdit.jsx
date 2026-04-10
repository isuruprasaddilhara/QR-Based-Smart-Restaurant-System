// import { useEffect, useState } from "react";

// import Button from "../components/Button";
// import styles from "./TableEdit.module.css";

// function TableEdit({
//   isDrawerOpen,
//   handleCloseDrawer,
//   selectedTable,
//   handleSaveTable,
//   handleDeleteTable,
//   isAddMode,
// }) {
//   const [tableNo, setTableNo] = useState("");
//   const [capacity, setCapacity] = useState("");
//   const [status, setStatus] = useState("");

//   useEffect(() => {
//     setTableNo(selectedTable?.tableNo || "");
//     setCapacity(selectedTable?.capacity || "");
//     setStatus(selectedTable?.status || "");
//   }, [selectedTable, isAddMode]);

//   function handleStatusToggle() {
//     setStatus((prev) => (prev === "Available" ? "Occupied" : "Available"));
//   }

//   function handleSave() {
//     const updatedTable = {
//       ...selectedTable,
//       tableNo: Number(tableNo),
//       capacity: Number(capacity),
//       status: status === "" ? "Available" : status,
//     };

//     handleSaveTable(updatedTable);
//     handleCloseDrawer();
//   }

//   return (
//     <>
//       <div
//         className={`${styles.backdrop} ${
//           isDrawerOpen ? styles.backdropShow : styles.backdropHide
//         }`}
//         onClick={handleCloseDrawer}
//       ></div>

//       <div
//         className={`${styles.editDrawer} ${
//           isDrawerOpen ? styles.drawerOpen : styles.drawerClose
//         }`}
//       >
//         <div className={styles.drawerContent}>
//           <h2>{isAddMode ? "Add Table" : "Edit Table"}</h2>

//           <div className={styles.inputSection}>
//             <p>Table Number</p>
//             <input
//               type="number"
//               value={tableNo}
//               onChange={(e) => setTableNo(e.target.value)}
//             />
//           </div>

//           <div className={styles.inputSection}>
//             <p>Capacity</p>
//             <input
//               type="number"
//               value={capacity}
//               onChange={(e) => setCapacity(e.target.value)}
//             />
//           </div>

//           <div className={`${styles.inputSection} ${styles.statusSection}`}>
//             <p>Status</p>
//             {console.log(status)}
//             <Button
//               className={`${styles.statusBtn} ${
//                 status === "Available"
//                   ? styles.available
//                   : status === ""
//                     ? styles.available
//                     : styles.occupied
//               }`}
//               onDoubleClick={handleStatusToggle}
//             >
//               {status === "" ? "Available" : status}
//             </Button>
//           </div>
//         </div>

//         <div className={styles.buttons}>
//           <Button className={styles.saveBtn} onClick={handleSave}>
//             Save
//           </Button>

//           {!isAddMode && (
//             <Button
//               className={styles.deleteBtn}
//               onClick={() => handleDeleteTable(selectedTable.id)}
//             >
//               Delete
//             </Button>
//           )}

//           <Button className={styles.closeBtn} onClick={handleCloseDrawer}>
//             Close
//           </Button>
//         </div>
//       </div>
//     </>
//   );
// }

// export default TableEdit;

import { useEffect, useState } from "react";

import Button from "./Button";
import { MdTableRestaurant } from "react-icons/md";

import styles from "./TableEdit.module.css";

function TableEdit({
  isDrawerOpen,
  handleCloseDrawer,
  selectedTable,
  handleSaveTable,
  handleDeleteTable,
  isAddMode,
}) {
  const [tableNumber, setTableNumber] = useState("");
  const [section, setSection] = useState("");
  const [capacity, setCapacity] = useState("4");
  const [status, setStatus] = useState("Available");
  const [saving, setSaving] = useState(false);
  const [localError, setLocalError] = useState("");

  useEffect(() => {
    if (selectedTable) {
      setTableNumber(String(selectedTable.tableNo ?? ""));
      setSection(selectedTable.section ?? "");
      setCapacity(String(selectedTable.capacity ?? "4"));
      setStatus(selectedTable.status || "Available");
    } else {
      setTableNumber("");
      setSection("");
      setCapacity("4");
      setStatus("Available");
    }
    setLocalError("");
  }, [selectedTable, isAddMode]);

  async function handleSave() {
    setLocalError("");
    setSaving(true);

    try {
      if (!tableNumber || Number(tableNumber) < 1) {
        throw new Error("Please enter a valid table number.");
      }

      if (isAddMode) {
        await handleSaveTable({
          tableNo: Number(tableNumber),
          section,
          capacity: Number(capacity) || 2,
        });
      } else {
        await handleSaveTable({
          id: selectedTable.id,
          tableNo: Number(tableNumber),
          section,
          capacity: Number(capacity) || 2,
          status,
        });
      }

      handleCloseDrawer();
    } catch (e) {
      setLocalError(e.message || "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className={styles.container}>
      <div
        className={`${styles.backdrop} ${
          isDrawerOpen ? styles.backdropShow : styles.backdropHide
        }`}
        onClick={handleCloseDrawer}
        role="presentation"
      />

      <aside
        className={`${styles.editDrawer} ${
          isDrawerOpen ? styles.drawerOpen : styles.drawerClose
        }`}
        aria-label={isAddMode ? "Add table" : "Edit table"}
      >
        <div className={styles.drawerHeader}>
          <h2 className={styles.drawerTitle}>
            {isAddMode ? "Add New Table" : "Edit Table"}
          </h2>
          <button
            type="button"
            className={styles.closeX}
            onClick={handleCloseDrawer}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className={styles.tableHero}>
          <MdTableRestaurant className={styles.tableHeroIcon} aria-hidden />
          <span className={styles.tableHeroText}>Table details</span>
        </div>

        {localError ? <p className={styles.inlineError}>{localError}</p> : null}

        <label className={styles.inputSection}>
          <span className={styles.label}>Table number</span>
          <input
            type="number"
            min="1"
            value={tableNumber}
            onChange={(e) => setTableNumber(e.target.value)}
            placeholder="e.g. 12"
          />
        </label>

        <label className={styles.inputSection}>
          <span className={styles.label}>Section (optional)</span>
          <input
            type="text"
            value={section}
            onChange={(e) => setSection(e.target.value)}
            placeholder="e.g. Window, Garden"
          />
        </label>

        <label className={styles.inputSection}>
          <span className={styles.label}>Capacity</span>
          <input
            type="number"
            min="1"
            value={capacity}
            onChange={(e) => setCapacity(e.target.value)}
          />
        </label>

        {!isAddMode ? (
          <label className={styles.inputSection}>
            <span className={styles.label}>Status</span>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="Available">Available</option>
              <option value="Occupied">Occupied</option>
            </select>
          </label>
        ) : null}

        {!isAddMode && (
          <button
            type="button"
            className={styles.deleteLink}
            onClick={() => handleDeleteTable(selectedTable.id)}
          >
            Delete table
          </button>
        )}

        <div className={styles.footer}>
          <Button
            type="button"
            className={styles.cancelBtn}
            onClick={handleCloseDrawer}
            disabled={saving}
          >
            Cancel
          </Button>

          <Button
            type="button"
            className={styles.saveBtn}
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </aside>
    </div>
  );
}

export default TableEdit;
