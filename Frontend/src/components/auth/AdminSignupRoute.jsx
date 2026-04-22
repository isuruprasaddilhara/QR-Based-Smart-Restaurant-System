import { Navigate } from "react-router-dom";

import { getAccessToken, getStoredRole } from "../../repository/auth";

function AdminSignupRoute({ children }) {
  const token = getAccessToken();
  const role = getStoredRole();

  if (!token) {
    return <Navigate to="/login" replace state={{ from: "/signup" }} />;
  }
  if (role !== "admin") {
    return <Navigate to="/home" replace />;
  }
  return children;
}

export default AdminSignupRoute;