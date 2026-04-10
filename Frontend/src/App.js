import { BrowserRouter, Route, Routes } from "react-router-dom";

import Homepage from "./pages/Home";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Welcome from "./pages/Welcome";
import AdminSignupRoute from "./components/AdminSignupRoute";

import "./App.css";

function App() {
  return (
    <div className="App">
      {/* <header className="App-header">
        <p>Scan2Serve</p>
      </header> */}
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Homepage />} />
          <Route path="/home" element={<Homepage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/welcome" element={<Welcome />} />
          <Route
            path="/signup"
            element={
              <AdminSignupRoute>
                <Signup />
              </AdminSignupRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
