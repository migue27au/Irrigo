import { Routes, Route } from "react-router-dom";

import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import SystemsPage from "./pages/SystemsPage";

function App() {

    return (
        <Routes>

            <Route
                path="/"
                element={<LoginPage />}
            />

            <Route
                path="/dashboard"
                element={<DashboardPage />}
            />

            <Route
                path="/systems"
                element={<SystemsPage />}
            />

        </Routes>
    );
}

export default App;