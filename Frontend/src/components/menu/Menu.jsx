import { useCallback, useEffect, useMemo, useState } from "react";

import MenuItem from "./MenuItem";
import MenuEdit from "./MenuEdit";

import {
  createMenuItem,
  deleteMenuItem,
  fetchCategories,
  fetchMenuItems,
  mapMenuItemFromApi,
  updateMenuItem,
} from "../../repository/menu";

import styles from "./Menu.module.css";

import { FaSearch } from "react-icons/fa";
import { FaPlus } from "react-icons/fa";

function Menu() {
  const [menuItems, setMenuItems] = useState([]);
  const [searchWord, setSearchWord] = useState("");

  const [isDrawerVisible, setIsDrawerVisible] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);

  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [mutationError, setMutationError] = useState("");


  const categoryMap = useMemo(() => {
    const m = new Map();
    categories.forEach((c) => m.set(c.id, c.name));
    return m;
  }, [categories]);

  const loadData = useCallback(async () => {
    setLoadError("");
    setLoading(true);

    try {
      const cats = await fetchCategories();
      setCategories(cats);

      const raw = await fetchMenuItems();
      setMenuItems(raw.map((row) => mapMenuItemFromApi(row, new Map(cats.map((c) => [c.id, c.name])))));
    } catch (e) {
      setLoadError(e.message || "Failed to load menu.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  function handleEdit(item) {
    setMutationError("");
    setSelectedItem(item);
    setIsDrawerVisible(true);
    setTimeout(() => setIsDrawerOpen(true), 20);
  }

  function handleCloseDrawer() {
    setIsDrawerOpen(false);
    setTimeout(() => {
      setIsDrawerVisible(false);
      setSelectedItem(null);
    }, 300);
  }

  async function handleSaveItem(formData) {
    setMutationError("");

    try {
      let saved;

      if (!selectedItem) {
        saved = await createMenuItem(formData);
        setMenuItems((prev) => [...prev, mapMenuItemFromApi(saved, categoryMap)]);
      } else {
        saved = await updateMenuItem(selectedItem.id, formData);
        const mapped = mapMenuItemFromApi(saved, categoryMap);
        setMenuItems((prev) =>
          prev.map((el) => (el.id === mapped.id ? mapped : el)),
        );
      }

      handleCloseDrawer();
    } catch (e) {
      const msg = e?.message ?? (typeof e === "string" ? e : "Save failed.");
      throw e instanceof Error ? e : new Error(msg);
    }
  }

  //-------------------------------------------------
  function handleCategoryCreated(createdCategory) {
  setCategories((prev) => {
    const exists = prev.some((c) => c.id === createdCategory.id);
    if (exists) return prev;
    return [...prev, createdCategory];
  });
  }

  function handleCategoryUpdated(updatedCategory) {
    setCategories((prev) =>
      prev.map((c) => (c.id === updatedCategory.id ? updatedCategory : c))
    );
  }

  function handleCategoryDeleted(categoryId) {
    setCategories((prev) => prev.filter((c) => c.id !== categoryId));
  }
//-------------------------------------------------

  const filteredItems = useMemo(() => {
    const q = searchWord.trim().toLowerCase();
    if (!q) return menuItems;
    return menuItems.filter((el) => el.name.toLowerCase().includes(q));
  }, [menuItems, searchWord]);

  async function handleDeleteItem(item) {
    if (!window.confirm(`Delete "${item.name}"?`)) return;

    setMutationError("");

    try {
      await deleteMenuItem(item.id);
      setMenuItems((prev) => prev.filter((el) => el.id !== item.id));

      if (selectedItem?.id === item.id) {
        handleCloseDrawer();
      }
    } catch (e) {
      setMutationError(e.message || "Delete failed.");
    }
  }

  function handleAddItem() {
    setMutationError("");
    setSelectedItem(null);
    setIsDrawerVisible(true);
    setTimeout(() => setIsDrawerOpen(true), 20);
  }

  return (
    <div className={styles.page}>
      {loadError || mutationError ? (
        <div className={styles.alertStack} role="alert">
          {loadError ? <p className={styles.errorBanner}>{loadError}</p> : null}
          {mutationError ? (
            <p className={styles.errorBanner}>{mutationError}</p>
          ) : null}
        </div>
      ) : null}

      <header className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Menu Management</h1>
        <p className={styles.pageSubtitle}>
          View and manage your food menu items
        </p>
      </header>

      <div className={styles.topSection}>
        <div className={styles.searchSection}>
          <FaSearch className={styles.searchIcon} aria-hidden />
          <input
            className={styles.userInput}
            type="search"
            value={searchWord}
            placeholder="Search menu items..."
            onChange={(e) => setSearchWord(e.target.value)}
          />
        </div>

        <button type="button" className={styles.addBtn} onClick={handleAddItem}>
          <FaPlus className={styles.addBtnIcon} aria-hidden />
          <span>Add New Item</span>
        </button>
      </div>

      {loading ? (
        <p className={styles.loading}>Loading menu…</p>
      ) : (
        <div className={styles.tableCard}>
          <div className={styles.menuHeadings}>
            <span className={styles.leftAlignHeading}>Item</span>
            <span className={styles.leftAlignHeading}>Category</span>
            <span className={styles.leftAlignHeading}>Price</span>
            <span className={styles.leftAlignHeading}>Status</span>
            <span className={styles.actionsHeading}>Actions</span>
          </div>

          {filteredItems.map((el) => (
            <MenuItem
              key={el.id}
              name={el.name}
              category={el.category}
              price={el.price}
              availability={el.availability}
              image={el.image}
              onEdit={() => handleEdit(el)}
              onDelete={() => handleDeleteItem(el)}
            />
          ))}
        </div>
      )}

      {isDrawerVisible && (
        <MenuEdit
          key={selectedItem ? selectedItem.id : "new"}
          isDrawerOpen={isDrawerOpen}
          handleCloseDrawer={handleCloseDrawer}
          selectedItem={selectedItem}
          handleSaveItem={handleSaveItem}
          categories={categories}
          existingItems={menuItems}
          onCategoryCreated={handleCategoryCreated}
          onCategoryUpdated={handleCategoryUpdated}
          onCategoryDeleted={handleCategoryDeleted}
        />
      )}
    </div>
  );
}

export default Menu;