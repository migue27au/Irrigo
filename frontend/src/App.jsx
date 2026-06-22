import { Navigate } from "react-router-dom";
import { Routes, Route } from "react-router-dom";

import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import SystemsPage from "./pages/SystemsPage";
import MeasuresPage from "./pages/MeasuresPage";
import ActuatorsPage from "./pages/ActuatorsPage";

import AppNavbar from "./components/AppNavbar";
import ProtectedRoute from "./components/ProtectedRoute";

import { useAuth } from "./context/AuthContext";

import "./App.css";

function App() {
    const { token } = useAuth();

    return (
        <>
            {token && <AppNavbar />}

            <Routes>
                {/* PUBLIC */}
                <Route path="/" element={<LandingPage />} />

                <Route
                    path="/login"
                    element={
                        token ? (
                            <Navigate to="/dashboard" replace />
                        ) : (
                            <LoginPage />
                        )
                    }
                />

                {/* PROTECTED */}
                <Route
                    path="/dashboard"
                    element={
                        <ProtectedRoute>
                            <DashboardPage />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/systems"
                    element={
                        <ProtectedRoute>
                            <SystemsPage />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/measures"
                    element={
                        <ProtectedRoute>
                            <MeasuresPage />
                        </ProtectedRoute>
                    }
                />
                
                <Route
                    path="/actuators"
                    element={
                        <ProtectedRoute>
                            <ActuatorsPage />
                        </ProtectedRoute>
                    }
                />

            </Routes>
        </>
    );
}

export default App;