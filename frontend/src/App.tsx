import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAppStore } from "./store/useAppStore";
import LoginPage from "./pages/LoginPage";
import DashboardLayout from "./pages/DashboardLayout";
import ToastContainer from "./components/ToastContainer";
import ConfirmDialog from "./components/ConfirmDialog";

function RequireAuth({ children }: { children: JSX.Element }) {
  const token = useAppStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <RequireAuth>
              <DashboardLayout />
            </RequireAuth>
          }
        />
      </Routes>
      <ToastContainer />
      <ConfirmDialog />
    </BrowserRouter>
  );
}
