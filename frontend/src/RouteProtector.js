import React from "react";
import { Navigate } from "react-router-dom";

function RouteProtector({ token, children }) {
  if (!token) {
    return <Navigate to="/login" />;
  }
  return children;
}

export default RouteProtector;
