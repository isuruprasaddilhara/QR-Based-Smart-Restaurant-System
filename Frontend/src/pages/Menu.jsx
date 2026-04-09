import { useEffect, useState } from "react";
import { getMenu } from "../api/menuAPI";

function Menu() {
  const [menu, setMenu] = useState([]);

  useEffect(() => {
    getMenu().then(res => setMenu(res.data));
  }, []);

  return (
    <div>
      <h2>Menu Page</h2>
      {menu.map(item => (
        <div key={item.id}>
          {item.name} - Rs {item.price}
        </div>
      ))}
    </div>
  );
}

function AddItem() {
  const [name, setName] = useState("");

  const submit = () => {
    axios.post("http://127.0.0.1:8000/menu/", {
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

export default Menu;
export { AddItem };