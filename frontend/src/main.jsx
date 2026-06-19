import React from "react";
import ReactDOM from "react-dom/client";

import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import "./styles/theme.css";

import { BrowserRouter } from "react-router-dom";

import App from "./App";

import { AuthProvider } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";

ReactDOM.createRoot(
    document.getElementById("root")
).render(

    <BrowserRouter>
        <AuthProvider>
            <ToastProvider>
                <App />
            </ToastProvider>
        </AuthProvider>
    </BrowserRouter>
);