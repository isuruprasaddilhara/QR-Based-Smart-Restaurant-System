// import { useState } from "react";

// import Button from "./Button";

// import styles from "./MenuEdit.module.css";

// function MenuEdit({
//   isDrawerOpen,
//   handleCloseDrawer,
//   selectedItem,
//   handleSaveItem,
//   onDelete,
// }) {
//   const [name, setName] = useState(selectedItem?.name || "");
//   const [category, setCategory] = useState(selectedItem?.category || "");
//   const [description, setDescription] = useState(
//     selectedItem?.description || "",
//   );
//   const [price, setPrice] = useState(selectedItem?.price || "");
//   const [availability, setAvailability] = useState(
//     selectedItem?.availability || "",
//   );

//   function handleAvailability(status) {
//     setAvailability(!availability);
//     console.log(availability);
//   }

//   function handleSave() {
//     const updatedItem = {
//       ...selectedItem,
//       name,
//       category,
//       description,
//       price,
//       availability: availability === "" ? false : availability,
//     };

//     handleSaveItem(updatedItem);
//     handleCloseDrawer();
//   }

//   return (
//     <div className={styles.container}>
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
//         <h2>{selectedItem ? "Edit Menu Item" : "Add New Item"}</h2>

//         <div className={`${styles.inputSection} ${styles.name}`}>
//           <p>Name</p>
//           <input value={name} onChange={(e) => setName(e.target.value)} />
//         </div>

//         <div className={`${styles.inputSection} ${styles.category}`}>
//           <p>Category</p>
//           <input
//             value={category}
//             onChange={(e) => setCategory(e.target.value)}
//           />
//         </div>

//         <div className={`${styles.inputSection} ${styles.description}`}>
//           <p>Description</p>
//           <textarea
//             value={description}
//             onChange={(e) => setDescription(e.target.value)}
//           />
//         </div>

//         <div className={`${styles.inputSection} ${styles.price}`}>
//           <p>Price</p>
//           <input
//             type="number"
//             value={price}
//             onChange={(e) => setPrice(e.target.value)}
//           />
//         </div>

//         <div className={`${styles.inputSection} ${styles.availability}`}>
//           <p>Availability</p>

//           <Button
//             className={`${styles.itemAvailability} ${
//               availability ? styles.available : styles.notAvailable
//             }`}
//             onDoubleClick={() => handleAvailability(availability)}
//           >
//             {availability ? "Available" : "Not Available"}
//           </Button>
//         </div>

//         <div className={styles.buttons}>
//           <Button className={styles.saveBtn} onClick={handleSave}>
//             Save
//           </Button>

//           <Button className={styles.deleteBtn} onClick={onDelete}>
//             Delete
//           </Button>

//           <Button className={styles.closeBtn} onClick={handleCloseDrawer}>
//             Close
//           </Button>
//         </div>
//       </div>
//     </div>
//   );
// }

// export default MenuEdit;

import { useEffect, useState } from "react";

import Button from "./Button";

import styles from "./MenuEdit.module.css";

// const CATEGORY_OPTIONS = [
//   "Main Course",
//   "Sri Lankan",
//   "Italian",
//   "Fast Food",
//   "Beverages",
//   "Salads",
//   "Fried Rice",
// ];

function MenuEdit({
  isDrawerOpen,
  handleCloseDrawer,
  selectedItem,
  handleSaveItem,
  categories = [],
}) {
  const [name, setName] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [availability, setAvailability] = useState(true);
  const [imageUrl, setImageUrl] = useState("");
  const [ingredients, setIngredients] = useState("");

  const firstCategoryId = categories[0]?.id ?? "";

  useEffect(() => {
    if (selectedItem) {
      setName(selectedItem.name ?? "");
      setCategoryId(
        selectedItem.categoryId != null
          ? selectedItem.categoryId
          : firstCategoryId,
      );
      setDescription(selectedItem.description ?? "");
      setPrice(
        selectedItem.price != null && selectedItem.price !== ""
          ? String(selectedItem.price)
          : "",
      );
      setAvailability(!!selectedItem.availability);
      setImageUrl(selectedItem.image_url || selectedItem.image || "");
      setIngredients(selectedItem.ingredients ?? "");
    } else {
      setName("");
      setCategoryId(firstCategoryId);
      setDescription("");
      setPrice("");
      setAvailability(true);
      setImageUrl("");
      setIngredients("");
    }
  }, [selectedItem, firstCategoryId]);

  function handleSave() {
    const priceNum = Number(price);
    const cid =
      categoryId === "" || categoryId == null
        ? firstCategoryId
        : Number(categoryId);
    const draft = {
      ...(selectedItem || {}),
      name: name.trim(),
      categoryId: cid,
      description: description.trim(),
      price: Number.isFinite(priceNum) ? priceNum : 0,
      availability,
      image_url: imageUrl.trim(),
      ingredients: ingredients.trim(),
    };
    handleSaveItem(draft);
  }
  const previewSrc = imageUrl.trim() || "/image.png";

  return (
    <div className={styles.container}>
      <div
        className={`${styles.backdrop} ${
          isDrawerOpen ? styles.backdropShow : styles.backdropHide
        }`}
        onClick={handleCloseDrawer}
        aria-hidden
      />
      <aside
        className={`${styles.editDrawer} ${
          isDrawerOpen ? styles.drawerOpen : styles.drawerClose
        }`}
        aria-label="Edit menu item"
      >
        <div className={styles.drawerHeader}>
          <h2 className={styles.drawerTitle}>
            {selectedItem ? "Edit Menu Item" : "Add New Item"}
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
        <div className={styles.imagePreviewWrap}>
          <img
            className={styles.imagePreview}
            src={previewSrc}
            alt=""
            onError={(e) => {
              e.target.src = "/image.png";
            }}
          />
        </div>
        <label className={styles.inputSection}>
          <span className={styles.label}>Image URL</span>
          <input
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            placeholder="https://… or /Fried-rice.jpg"
          />
        </label>
        <label className={styles.inputSection}>
          <span className={styles.label}>Item name</span>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoComplete="off"
          />
        </label>
        <label className={styles.inputSection}>
          <span className={styles.label}>Category</span>
          <select
            value={categoryId === "" ? firstCategoryId : categoryId}
            onChange={(e) => setCategoryId(Number(e.target.value))}
            disabled={categories.length === 0}
          >
            {categories.length === 0 ? (
              <option value="">Loading categories…</option>
            ) : (
              categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))
            )}
          </select>
        </label>
        <label className={styles.inputSection}>
          <span className={styles.label}>Price</span>
          <div className={styles.priceField}>
            <span className={styles.rsPrefix}>Rs</span>
            <input
              type="number"
              min="0"
              step="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
            />
          </div>
        </label>
        <label className={styles.inputSection}>
          <span className={styles.label}>Description</span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={5}
          />
        </label>
        <label className={styles.inputSection}>
          <span className={styles.label}>Ingredients (optional)</span>
          <textarea
            value={ingredients}
            onChange={(e) => setIngredients(e.target.value)}
            rows={3}
          />
        </label>
        <label className={styles.toggleRow}>
          <span className={styles.label}>Available</span>
          <input
            type="checkbox"
            className={styles.bigCheckbox}
            checked={availability}
            onChange={(e) => setAvailability(e.target.checked)}
          />
        </label>
        <div className={styles.footer}>
          <Button
            type="button"
            className={styles.cancelBtn}
            onClick={handleCloseDrawer}
          >
            Cancel
          </Button>
          <Button
            type="button"
            className={styles.saveBtn}
            onClick={handleSave}
            disabled={!name.trim() || categories.length === 0}
          >
            Save changes
          </Button>
        </div>
      </aside>
    </div>
  );
}
export default MenuEdit;
