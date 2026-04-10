// import { useState } from "react";

// import MenuItem from "./MenuItem";
// import Button from "./Button";
// import MenuEdit from "./MenuEdit";

// import styles from "./Menu.module.css";

// import { FaSearch } from "react-icons/fa";
// import { FaPlus } from "react-icons/fa";

// const initialMenuItems = [
//   {
//     id: 1,
//     name: "Chicken Fried Rice",
//     category: "Main Course",
//     description:
//       "Fragrant fried rice with tender chicken, vegetables, and soy seasoning.",
//     price: 1200,
//     availability: true,

//   },
//   {
//     id: 2,
//     name: "Egg Kottu",
//     category: "Sri Lankan",
//     description:
//       "Chopped roti stir-fried with egg, vegetables, and signature spices.",
//     price: 950,
//     availability: true,
//   },
//   {
//     id: 3,
//     name: "Margherita Pizza",
//     category: "Italian",
//     description:
//       "Classic pizza topped with mozzarella, tomato sauce, and fresh basil.",
//     price: 1800,
//     availability: false,
//   },
//   {
//     id: 4,
//     name: "Chicken Burger",
//     category: "Fast Food",
//     description: "Grilled chicken patty with lettuce, cheese, and house sauce.",
//     price: 850,
//     availability: true,
//   },
//   {
//     id: 5,
//     name: "Chocolate Milkshake",
//     category: "Beverages",
//     description:
//       "Creamy milkshake blended with rich chocolate syrup and ice cream.",
//     price: 650,
//     availability: true,
//   },
//   {
//     id: 6,
//     name: "Caesar Salad",
//     category: "Salads",
//     description:
//       "Fresh lettuce with croutons, parmesan cheese, and Caesar dressing.",
//     price: 900,
//     availability: false,
//   },
// ];

// function Menu() {
//   const [menuItems, setMenuItems] = useState(initialMenuItems);
//   const [searchWord, setSearchWord] = useState("");

//   const [isDrawerVisible, setIsDrawerVisible] = useState(false);
//   const [isDrawerOpen, setIsDrawerOpen] = useState(false);
//   const [selectedItem, setSelectedItem] = useState(null);

//   const [isAddItemDrawerVisible, setIsAddItemDrawerVisible] = useState(false);

//   function handleEdit(item) {
//     setSelectedItem(item);
//     setIsAddItemDrawerVisible(false);
//     setIsDrawerVisible(true);

//     setTimeout(() => {
//       setIsDrawerOpen(true);
//     }, 100);
//   }

//   function handleCloseDrawer() {
//     setIsDrawerOpen(false);
//     setIsAddItemDrawerVisible(false);

//     setTimeout(() => {
//       setIsDrawerVisible(false);
//       setSelectedItem(null);
//     }, 300);
//   }

//   function handleSaveItem(updatedItem) {
//     if (isAddItemDrawerVisible) {
//       const newItem = { ...updatedItem, id: Date.now() };
//       setMenuItems([...menuItems, newItem]);
//     } else {
//       setMenuItems((prevMenuItems) =>
//         prevMenuItems.map((el) =>
//           el.id === updatedItem.id ? updatedItem : el,
//         ),
//       );
//     }
//   }

//   const filteredItems =
//     searchWord !== ""
//       ? menuItems.filter((el) =>
//           el.name.toLowerCase().includes(searchWord.toLowerCase()),
//         )
//       : null;

//   function handleDeleteItem(item) {
//     const remainingItems = menuItems.filter((el) => el.id !== item.id);

//     setMenuItems(remainingItems);
//     handleCloseDrawer();
//   }

//   function handleAddItem(item) {
//     setSelectedItem(null);
//     setIsAddItemDrawerVisible(true);
//     setIsDrawerVisible(true);

//     setTimeout(() => {
//       setIsDrawerOpen(true);
//     }, 10);

//     // setMenuItems(...menuItems, item);
//   }

//   return (
//     <div>
//       <div className={styles.topSection}>
//         <div className={styles.searchSection}>
//           <FaSearch className={styles.searchIcon} />
//           <input
//             className={styles.userInput}
//             type="text"
//             value={searchWord}
//             placeholder={`Search Menu Item`}
//             onChange={(e) => setSearchWord(e.target.value)}
//           />
//         </div>

//         <Button className={styles.addBtn} onClick={handleAddItem}>
//           <FaPlus className={styles.addBtnIcon} />
//           <p>Add Item</p>
//         </Button>

//         {isAddItemDrawerVisible && (
//           <MenuEdit
//             isDrawerOpen={isDrawerOpen}
//             handleCloseDrawer={handleCloseDrawer}
//             selectedItem={selectedItem}
//             handleSaveItem={handleSaveItem}
//           />
//         )}
//       </div>

//       <div className={styles.container}>
//         <div className={styles.menuHeadings}>
//           <p>Item</p>
//           <p>Price</p>
//           <p>Availability</p>
//           <p>Edit</p>
//         </div>

//         {searchWord === ""
//           ? menuItems.map((el) => (
//               <MenuItem
//                 name={el.name}
//                 category={el.category}
//                 description={el.description}
//                 price={el.price}
//                 availability={el.availability}
//                 onEdit={() => handleEdit(el)}
//               />
//             ))
//           : filteredItems.map((el) => (
//               <MenuItem
//                 name={el.name}
//                 category={el.category}
//                 description={el.description}
//                 price={el.price}
//                 availability={el.availability}
//                 setIsEditOpen={setIsDrawerOpen}
//                 onEdit={() => handleEdit(el)}
//               />
//             ))}

//         {isDrawerVisible && (
//           <MenuEdit
//             isDrawerOpen={isDrawerOpen}
//             handleCloseDrawer={handleCloseDrawer}
//             selectedItem={selectedItem}
//             handleSaveItem={handleSaveItem}
//             onDelete={() => handleDeleteItem(selectedItem)}
//           />
//         )}
//       </div>
//     </div>
//   );
// }

// export default Menu;

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
} from "../repository/menu";

import styles from "./Menu.module.css";

import { FaSearch } from "react-icons/fa";
import { FaPlus } from "react-icons/fa";

// const initialMenuItems = [
//   {
//     id: 1,
//     name: "Chicken Fried Rice",
//     category: "Main Course",
//     description:
//       "Fragrant fried rice with tender chicken, vegetables, and soy seasoning.",
//     price: 1200,
//     availability: true,
//     image: "/Fired-rice.jpg",
//   },
//   {
//     id: 2,
//     name: "Egg Kottu",
//     category: "Sri Lankan",
//     description:
//       "Chopped roti stir-fried with egg, vegetables, and signature spices.",
//     price: 950,
//     availability: true,
//     image: "/Fired-rice.jpg",
//   },
//   {
//     id: 3,
//     name: "Margherita Pizza",
//     category: "Italian",
//     description:
//       "Classic pizza topped with mozzarella, tomato sauce, and fresh basil.",
//     price: 1800,
//     availability: false,
//     image: "/Fired-rice.jpg",
//   },
//   {
//     id: 4,
//     name: "Chicken Burger",
//     category: "Fast Food",
//     description: "Grilled chicken patty with lettuce, cheese, and house sauce.",
//     price: 850,
//     availability: true,
//     image: "/Fired-rice.jpg",
//   },
//   {
//     id: 5,
//     name: "Chocolate Milkshake",
//     category: "Beverages",
//     description:
//       "Creamy milkshake blended with rich chocolate syrup and ice cream.",
//     price: 650,
//     availability: true,
//     image: "/Fired-rice.jpg",
//   },
//   {
//     id: 6,
//     name: "Caesar Salad",
//     category: "Salads",
//     description:
//       "Fresh lettuce with croutons, parmesan cheese, and Caesar dressing.",
//     price: 900,
//     availability: false,
//     image: "/Fired-rice.jpg",
//   },
// ];

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
      const m = new Map(cats.map((c) => [c.id, c.name]));
      const raw = await fetchMenuItems();
      setMenuItems(raw.map((row) => mapMenuItemFromApi(row, m)));
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

  async function handleSaveItem(draft) {
    setMutationError("");
    const body = {
      name: draft.name,
      description: draft.description || "",
      price: draft.price,
      category: draft.categoryId,
      availability: draft.availability,
      image_url: "",
      ingredients: draft.ingredients || "",
    };
    try {
      if (!selectedItem) {
        const created = await createMenuItem(body);
        setMenuItems((prev) => [
          ...prev,
          mapMenuItemFromApi(created, categoryMap),
        ]);
      } else {
        const saved = await updateMenuItem(selectedItem.id, body);
        const mapped = mapMenuItemFromApi(saved, categoryMap);
        setMenuItems((prev) =>
          prev.map((el) => (el.id === mapped.id ? mapped : el)),
        );
      }
      handleCloseDrawer();
    } catch (e) {
      setMutationError(e.message || "Save failed.");
    }
  }

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
      if (selectedItem?.id === item.id) handleCloseDrawer();
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
        />
      )}
    </div>
  );
}

export default Menu;
