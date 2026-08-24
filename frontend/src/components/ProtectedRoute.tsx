import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Layout } from "./Layout";

export function ProtectedRoute() {
  const { session, loading } = useAuth();
  if (loading) {
    return (
      <div className="center-page">
        <p>Loading session...</p>
      </div>
    );
  }
  if (!session) {
    return <Navigate to="/login" replace />;
  }
  return (
    <Layout>
      <Outlet />
    </Layout>
  );
}
