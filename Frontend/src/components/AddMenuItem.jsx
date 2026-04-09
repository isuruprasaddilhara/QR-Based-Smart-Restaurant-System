import axios from "axios";
import { useEffect, useState } from "react";
// import { getMenu } from "../api/menuAPI";
function AddItem() {
  const [name, setName] = useState("");

  const submit = () => {
    axios.defaults.headers.common["Authorization"] =
    "Bearer " + localStorage.getItem("token");
    axios.post("http://127.0.0.1:8000/menu/items/", {
      name: name
    });
  };

  return (
    <div>
      <input onChange={(e) => setName(e.target.value)} />
      <button onClick={submit}>Add</button>
    </div>
  );
}