import axios from "axios";
import { useState } from "react";

function AddItem() {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [category, setCategory] = useState("");
  const [image_url, setImageUrl] = useState("");
  const [ingredients, setIngredients] = useState("");

  const submit = async () => {
    try {
      // store token manually for testing
      localStorage.setItem(
        "token",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc1NDY3NTI0LCJpYXQiOjE3NzU0NjM5MjQsImp0aSI6IjQ1Y2NkMWU2NzUyMjQzMjhhOGIyYmQ3NWM1MmE3NGJhIiwidXNlcl9pZCI6IjEifQ.5aX4BpXvqdmcuQD1wPwJ4J6UgF9yU8tMj4F2ndRnPy8"
      );

      const token = localStorage.getItem("token");

      const response = await axios.post(
        "http://127.0.0.1:8000/menu/items/",
        {
          name: name,
          description: description,
          price: price,
          category: category,
          availability: true,
          image_url: image_url,
          ingredients: ingredients,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      console.log("Item added:", response.data);
      alert("Item added successfully");
    } catch (error) {
      console.error("Error adding item:", error.response?.data || error.message);
      alert("Failed to add item");
    }
  };

  return (
    <div>
      <h2>Add Item</h2>

      <input
        type="text"
        placeholder="Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />

      <input
        type="text"
        placeholder="Description"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />

      <input
        type="number"
        placeholder="Price"
        value={price}
        onChange={(e) => setPrice(e.target.value)}
      />

      <input
        type="text"
        placeholder="Category ID"
        value={category}
        onChange={(e) => setCategory(e.target.value)}
      />

      <input
        type="text"
        placeholder="Image URL"
        value={image_url}
        onChange={(e) => setImageUrl(e.target.value)}
      />

      <input
        type="text"
        placeholder="Ingredients"
        value={ingredients}
        onChange={(e) => setIngredients(e.target.value)}
      />

      <button onClick={submit}>Add</button>
    </div>
  );
}

export default AddItem;