import { useEffect, useState } from "react";

import Button from "../shared/Button";
import { createCategory, updateCategory, deleteCategory } from "../../repository/menu";
import { useEscapeKey } from "../../hooks/useEscapeKey";

import styles from "./MenuEdit.module.css";

// ── Manage Categories Modal ────────────────────────────────────────────────────
function ManageCategoriesModal({ onClose, categories, onCategoryCreated, onCategoryUpdated, onCategoryDeleted }) {
  const [newName, setNewName]       = useState("");
  const [createBusy, setCreateBusy] = useState(false);
  const [createError, setCreateError] = useState("");

  const [editingId, setEditingId]   = useState(null);
  const [editName, setEditName]     = useState("");
  const [editBusy, setEditBusy]     = useState(false);
  const [editError, setEditError]   = useState("");

  const [deletingId, setDeletingId] = useState(null);
  const [deleteError, setDeleteError] = useState("");

  useEscapeKey(true, onClose);

  // ── Create ──
  async function handleCreate(e) {
    e.preventDefault();
    setCreateError("");
    const trimmed = newName.trim();
    if (!trimmed) { setCreateError("Enter a category name."); return; }

    const existing = categories.find(
      (c) => c.name.trim().toLowerCase() === trimmed.toLowerCase()
    );
    if (existing) { setCreateError("That category already exists."); return; }

    setCreateBusy(true);
    try {
      const created = await createCategory({ name: trimmed });
      if (!created?.id) throw new Error("No ID returned.");
      onCategoryCreated(created);
      setNewName("");
    } catch (err) {
      setCreateError(err.message || "Failed to create.");
    } finally {
      setCreateBusy(false);
    }
  }

  // ── Edit ──
  function startEdit(cat) {
    setEditingId(cat.id);
    setEditName(cat.name);
    setEditError("");
    setDeleteError("");
  }

  function cancelEdit() {
    setEditingId(null);
    setEditName("");
    setEditError("");
  }

  async function handleUpdate(id) {
    setEditError("");
    const trimmed = editName.trim();
    if (!trimmed) { setEditError("Name cannot be empty."); return; }

    const duplicate = categories.find(
      (c) => c.id !== id && c.name.trim().toLowerCase() === trimmed.toLowerCase()
    );
    if (duplicate) { setEditError("Another category has that name."); return; }

    setEditBusy(true);
    try {
      const updated = await updateCategory(id, { name: trimmed });
      onCategoryUpdated({ ...updated, id });
      setEditingId(null);
    } catch (err) {
      setEditError(err.message || "Failed to update.");
    } finally {
      setEditBusy(false);
    }
  }

  // ── Delete ──
  async function handleDelete(id) {
    setDeleteError("");
    setDeletingId(id);
    try {
      await deleteCategory(id);
      onCategoryDeleted(id);
      if (editingId === id) cancelEdit();
    } catch (err) {
      setDeleteError(err.message || "Failed to delete.");
      setDeletingId(null);
    }
  }

  return (
    <div className={styles.modalOverlay} onClick={onClose} aria-modal="true" role="dialog">
      <div className={styles.modalBox} onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className={styles.modalHeader}>
          <div className={styles.modalTitleGroup}>
            <span className={styles.modalIcon}>🏷️</span>
            <h3 className={styles.modalTitle}>Manage Categories</h3>
          </div>
          <button type="button" className={styles.closeX} onClick={onClose} aria-label="Close">×</button>
        </div>

        {/* Existing categories list */}
        <div className={styles.catList}>
          {categories.length === 0 && (
            <p className={styles.emptyMsg}>No categories yet. Add one below.</p>
          )}

          {categories.map((cat) => (
            <div key={cat.id} className={styles.catRow}>
              {editingId === cat.id ? (
                /* ── Edit mode ── */
                <div className={styles.catEditRow}>
                  <input
                    className={styles.catEditInput}
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleUpdate(cat.id);
                      if (e.key === "Escape") cancelEdit();
                    }}
                    autoFocus
                  />
                  <button
                    className={`${styles.catActionBtn} ${styles.catSaveBtn}`}
                    onClick={() => handleUpdate(cat.id)}
                    disabled={editBusy || !editName.trim()}
                    title="Save"
                  >
                    {editBusy ? "…" : "✓"}
                  </button>
                  <button
                    className={`${styles.catActionBtn} ${styles.catCancelBtn}`}
                    onClick={cancelEdit}
                    title="Cancel"
                  >
                    ✕
                  </button>
                </div>
              ) : (
                /* ── View mode ── */
                <div className={styles.catViewRow}>
                  <span className={styles.catDot} />
                  <span className={styles.catName}>{cat.name}</span>
                  <div className={styles.catActions}>
                    <button
                      className={`${styles.catActionBtn} ${styles.catEditBtn}`}
                      onClick={() => startEdit(cat)}
                      title="Rename"
                    >
                      ✏️
                    </button>
                    <button
                      className={`${styles.catActionBtn} ${styles.catDeleteBtn}`}
                      onClick={() => handleDelete(cat.id)}
                      disabled={deletingId === cat.id}
                      title="Delete"
                    >
                      {deletingId === cat.id ? "…" : "🗑️"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}

          {(editError || deleteError) && (
            <p className={styles.inlineError} role="alert">{editError || deleteError}</p>
          )}
        </div>

        {/* Divider */}
        <div className={styles.catDivider} />

        {/* Add new category */}
        <form onSubmit={handleCreate} noValidate className={styles.catAddForm}>
          <p className={styles.catAddLabel}>Add new category</p>
          <div className={styles.catAddRow}>
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="e.g. Desserts"
              autoComplete="off"
              className={styles.catAddInput}
            />
            <button
              type="submit"
              className={`${styles.catActionBtn} ${styles.catCreateBtn}`}
              disabled={createBusy || !newName.trim()}
            >
              {createBusy ? "…" : "+ Add"}
            </button>
          </div>
          {createError && (
            <p className={styles.inlineError} role="alert">{createError}</p>
          )}
        </form>

        {/* Footer close */}
        <div className={styles.modalFooter}>
          <Button type="button" className={styles.saveBtn} onClick={onClose}>Done</Button>
        </div>
      </div>
    </div>
  );
}

// ── New Category Modal (quick-create from drawer) ──────────────────────────────
function NewCategoryModal({ onClose, onCreated, categories }) {
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEscapeKey(true, onClose);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    const trimmed = name.trim();
    if (!trimmed) { setError("Please enter a category name."); return; }

    const existing = categories.find(
      (c) => String(c.name ?? "").trim().toLowerCase() === trimmed.toLowerCase()
    );
    if (existing) { onCreated(existing); onClose(); return; }

    setBusy(true);
    try {
      const created = await createCategory({ name: trimmed });
      if (!created?.id) throw new Error("No category ID returned.");
      onCreated(created);
      onClose();
    } catch (err) {
      setError(err.message || "Failed to create category.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={styles.modalOverlay} onClick={onClose} aria-modal="true" role="dialog">
      <div className={styles.modalBox} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div className={styles.modalTitleGroup}>
            <span className={styles.modalIcon}>🏷️</span>
            <h3 className={styles.modalTitle}>New Category</h3>
          </div>
          <button type="button" className={styles.closeX} onClick={onClose} aria-label="Close">×</button>
        </div>
        <form onSubmit={handleSubmit} noValidate>
          <label className={styles.inputSection}>
            <span className={styles.label}>Category name</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Desserts"
              autoFocus
              autoComplete="off"
            />
          </label>
          {error && <p className={styles.inlineError} role="alert">{error}</p>}
          <div className={styles.footer}>
            <Button type="button" className={styles.cancelBtn} onClick={onClose}>Cancel</Button>
            <Button type="submit" className={styles.saveBtn} disabled={busy || !name.trim()}>
              {busy ? "Creating…" : "Create"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── MenuEdit ───────────────────────────────────────────────────────────────────
function MenuEdit({
  isDrawerOpen,
  handleCloseDrawer,
  selectedItem,
  handleSaveItem,
  categories = [],
  existingItems = [],
  onCategoryCreated,
  onCategoryUpdated,   // ← new prop: (updatedCategory) => void
  onCategoryDeleted,   // ← new prop: (categoryId)     => void
}) {
  const [name, setName]               = useState("");
  const [categorySelectValue, setCategorySelectValue] = useState("");
  const [saveBusy, setSaveBusy]       = useState(false);
  const [saveError, setSaveError]     = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice]             = useState("");
  const [availability, setAvailability] = useState(true);
  const [ingredients, setIngredients] = useState("");
  const [imageFile, setImageFile]     = useState(null);
  const [imagePreview, setImagePreview] = useState("");

  const [showNewCatModal, setShowNewCatModal]       = useState(false);
  const [showManageCatModal, setShowManageCatModal] = useState(false);

  const anyModalOpen = showNewCatModal || showManageCatModal;
  const firstCategoryId = categories[0]?.id ?? "";

  useEffect(() => {
    if (selectedItem) {
      setName(selectedItem.name ?? "");
      setCategorySelectValue(
        selectedItem.categoryId != null
          ? String(selectedItem.categoryId)
          : firstCategoryId ? String(firstCategoryId) : ""
      );
      setDescription(selectedItem.description ?? "");
      setPrice(selectedItem.price != null && selectedItem.price !== "" ? String(selectedItem.price) : "");
      setAvailability(!!selectedItem.availability);
      setIngredients(selectedItem.ingredients ?? "");
      setImageFile(null);
      setImagePreview(selectedItem.image_url || selectedItem.image || "");
    } else {
      setName("");
      setCategorySelectValue(firstCategoryId ? String(firstCategoryId) : "");
      setDescription("");
      setPrice("");
      setAvailability(true);
      setIngredients("");
      setImageFile(null);
      setImagePreview("");
    }
  }, [selectedItem, firstCategoryId]);

  useEffect(() => {
    return () => { if (imagePreview?.startsWith("blob:")) URL.revokeObjectURL(imagePreview); };
  }, [imagePreview]);

  useEscapeKey(isDrawerOpen && !anyModalOpen, handleCloseDrawer);

  function handleImageChange(e) {
    const file = e.target.files?.[0] || null;
    setImageFile(file);
    if (imagePreview?.startsWith("blob:")) URL.revokeObjectURL(imagePreview);
    setImagePreview(file ? URL.createObjectURL(file) : (selectedItem?.image_url || selectedItem?.image || ""));
  }

  function handleCategoryCreated(created) {
    if (typeof onCategoryCreated === "function") onCategoryCreated(created);
    setCategorySelectValue(String(created.id));
  }

  function handleCategoryDeleted(id) {
    if (typeof onCategoryDeleted === "function") onCategoryDeleted(id);
    // If the deleted category was selected, fall back to first remaining
    if (categorySelectValue === String(id)) {
      const remaining = categories.filter((c) => c.id !== id);
      setCategorySelectValue(remaining[0] ? String(remaining[0].id) : "");
    }
  }

  async function handleSave(e) {
    e?.preventDefault();
    setSaveError("");
    if (!name.trim())            { setSaveError("Please enter an item name.");              return; }
    const desc = description.trim();
    if (!desc)                   { setSaveError("Please enter a description.");             return; }
    const priceStr = String(price).trim();
    if (priceStr === "")         { setSaveError("Please enter a price.");                   return; }
    const priceNum = Number(priceStr);
    if (!Number.isFinite(priceNum) || priceNum <= 0) { setSaveError("Enter a valid price."); return; }
    const resolvedCategoryId = Number(categorySelectValue);
    if (!Number.isFinite(resolvedCategoryId)) { setSaveError("Choose a category.");         return; }

    const nameNorm = name.trim().toLowerCase();
    const duplicate = existingItems.find(
      (it) => String(it.name ?? "").trim().toLowerCase() === nameNorm && (!selectedItem || it.id !== selectedItem.id)
    );
    if (duplicate) { setSaveError("An item with this name already exists."); return; }

    const formData = new FormData();
    formData.append("name", name.trim());
    formData.append("description", desc);
    formData.append("price", String(priceNum));
    formData.append("category", String(resolvedCategoryId));
    formData.append("availability", String(availability));
    formData.append("ingredients", ingredients.trim());
    if (imageFile) formData.append("image", imageFile);

    setSaveBusy(true);
    try   { await handleSaveItem(formData); }
    catch (err) { setSaveError(err.message || "Save failed."); }
    finally     { setSaveBusy(false); }
  }

  const previewSrc = imagePreview || "/image.png";

  return (
    <>
      {showNewCatModal && (
        <NewCategoryModal
          categories={categories}
          onClose={() => setShowNewCatModal(false)}
          onCreated={handleCategoryCreated}
        />
      )}

      {showManageCatModal && (
        <ManageCategoriesModal
          categories={categories}
          onClose={() => setShowManageCatModal(false)}
          onCategoryCreated={handleCategoryCreated}
          onCategoryUpdated={(cat) => { if (typeof onCategoryUpdated === "function") onCategoryUpdated(cat); }}
          onCategoryDeleted={handleCategoryDeleted}
        />
      )}

      <div className={styles.container}>
        <div
          className={`${styles.backdrop} ${isDrawerOpen ? styles.backdropShow : styles.backdropHide}`}
          onClick={handleCloseDrawer}
          aria-hidden
        />

        <aside
          className={`${styles.editDrawer} ${isDrawerOpen ? styles.drawerOpen : styles.drawerClose}`}
          aria-label="Edit menu item"
        >
          <div className={styles.drawerHeader}>
            <h2 className={styles.drawerTitle}>{selectedItem ? "Edit Menu Item" : "Add New Item"}</h2>
            <button type="button" className={styles.closeX} onClick={handleCloseDrawer} aria-label="Close">×</button>
          </div>

          <form className={styles.editForm} onSubmit={handleSave} noValidate>
            <div className={styles.imagePreviewWrap}>
              <img className={styles.imagePreview} src={previewSrc} alt="Preview"
                onError={(e) => { e.target.src = "/image.png"; }} />
            </div>

            <label className={styles.inputSection}>
              {/* <span className={styles.label}>Upload Image</span> */}
              <div className={styles.uploadWrapper}>
                <label className={styles.uploadBox}>
                  <input type="file" accept="image/*" onChange={handleImageChange} hidden />
                  <span className={styles.uploadText}>{imageFile ? imageFile.name : "Upload Image"}</span>
                </label>
              </div>
            </label>

            <label className={styles.inputSection}>
              <span className={styles.label}>Item name</span>
              <input value={name} onChange={(e) => setName(e.target.value)}
                autoComplete="off" required aria-invalid={!name.trim()} />
            </label>

            {saveError && <p className={styles.inlineError} role="alert">{saveError}</p>}

            {/* ── Category row ── */}
            <div className={styles.inputSection}>
              <span className={styles.label}>Category</span>

              <div className={styles.categoryRow}>
                <select
                  value={categorySelectValue}
                  onChange={(e) => setCategorySelectValue(e.target.value)}
                >
                  {categories.length === 0 && <option value="" disabled>No categories yet</option>}
                  {categories.map((c) => (
                    <option key={c.id} value={String(c.id)}>
                      {c.name}
                    </option>
                  ))}
                </select>

                <button
                  type="button"
                  className={styles.addCategoryBtn}
                  onClick={() => setShowManageCatModal(true)}
                  title="Manage categories"
                >
                  Manage
                </button>
              </div>
            </div>

            <label className={styles.inputSection}>
              <span className={styles.label}>Price</span>
              <div className={styles.priceField}>
                <span className={styles.rsPrefix}>Rs</span>
                <input type="number" min="0.01" step="0.01" required value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  aria-invalid={price !== "" && (!Number.isFinite(Number(price)) || Number(price) <= 0)} />
              </div>
            </label>

            <label className={styles.inputSection}>
              <span className={styles.label}>Description</span>
              <textarea value={description} onChange={(e) => setDescription(e.target.value)}
                rows={5} required placeholder="Describe the dish for customers"
                aria-invalid={!description.trim()} />
            </label>

            <label className={styles.inputSection}>
              <span className={styles.label}>Ingredients</span>
              <textarea value={ingredients} onChange={(e) => setIngredients(e.target.value)} rows={3} />
            </label>

            <label className={styles.toggleRow}>
              <span className={styles.label}>Available</span>
              <input type="checkbox" className={styles.bigCheckbox}
                checked={availability} onChange={(e) => setAvailability(e.target.checked)} />
            </label>

            <div className={styles.footer}>
              <Button type="button" className={styles.cancelBtn} onClick={handleCloseDrawer}>Cancel</Button>
              <Button
                type="submit"
                className={styles.saveBtn}
                disabled={
                  saveBusy || !name.trim() || !description.trim() ||
                  String(price).trim() === "" || !Number.isFinite(Number(price)) ||
                  Number(price) <= 0 || !categorySelectValue
                }
              >
                {saveBusy ? "Saving…" : "Save changes"}
              </Button>
            </div>
          </form>
        </aside>
      </div>
    </>
  );
}

export default MenuEdit;