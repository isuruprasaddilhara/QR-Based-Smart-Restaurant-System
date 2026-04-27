import { BrowserRouter, Route, Routes } from "react-router-dom";

import Homepage from "./pages/Home";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import AdminSignupRoute from "./components/auth/AdminSignupRoute";
import SessionHandler from "./components/shared/SessionHandler";
import PasswordResetConfirm from "./pages/PasswordResetConfirm";


import "./App.css";

function App() {
  return (
    <div className="App">
      {/* <header className="App-header">
        <p>Scan2Serve</p>
      </header> */}
      <BrowserRouter>
        <SessionHandler />
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/home" element={<Homepage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/reset-password-confirm" element={<PasswordResetConfirm />} />
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
