import { Route, Routes } from "react-router";

import { RequireAuth } from "./auth/RequireAuth";
import { HomePage } from "./pages/HomePage";

export function App() {
  return (
    <Routes>
      <Route element={<RequireAuth />}>
        <Route path="/" element={<HomePage />} />
      </Route>
    </Routes>
  );
}
