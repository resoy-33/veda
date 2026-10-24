import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./auth/ProtectedRoute.jsx";
import { Layout } from "./components/Layout.jsx";
import { Account } from "./pages/Account.jsx";
import { Deposits } from "./pages/Deposits.jsx";
import { FilingDetail } from "./pages/FilingDetail.jsx";
import { Login } from "./pages/Login.jsx";
import { NewDeposit } from "./pages/NewDeposit.jsx";
import { NotFound } from "./pages/NotFound.jsx";
import { Operations } from "./pages/Operations.jsx";
import { Verification } from "./pages/Verification.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/depots" replace />} />
          <Route path="/depots" element={<Deposits />} />
          <Route path="/depots/nouveau" element={<NewDeposit />} />
          <Route path="/depots/:id" element={<FilingDetail />} />
          <Route path="/verification" element={<Verification />} />
          <Route path="/operations" element={<Operations />} />
          <Route path="/compte" element={<Account />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
