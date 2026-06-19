import { createContext, useContext, useState } from "react";

const ToastContext = createContext();

export function ToastProvider({ children }) {
    const [toasts, setToasts] = useState([]);

    const removeToast = (id) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    };

    const addToast = (message, type = "info") => {
        const id = Date.now();

        setToasts((prev) => [
            ...prev,
            { id, message, type }
        ]);

        setTimeout(() => {
            removeToast(id);
        }, 4000);
    };

    const error = (msg) => addToast(msg, "error");
    const warning = (msg) => addToast(msg, "warning");
    const success = (msg) => addToast(msg, "success");
    const primary = (msg) => addToast(msg, "primary");
    const info = (msg) => addToast(msg, "info");

    return (
        <ToastContext.Provider
            value={{
                error,
                warning,
                success,
                primary,
                info
            }}
        >
            {children}

            <div className="toast-container position-fixed top-0 end-0 p-3">
                {toasts.map((t) => (
                    <div
                        key={t.id}
                        role="button"
                        onClick={() => removeToast(t.id)}
                        className={`toast show text-white mb-2 ${
                            t.type === "error"
                                ? "bg-danger"
                                : t.type === "warning"
                                ? "bg-warning text-dark"
                                : t.type === "success"
                                ? "bg-success"
                                : t.type === "primary"
                                ? "bg-primary"
                                : "bg-secondary"
                        }`}
                        style={{
                            cursor: "pointer"
                        }}
                    >
                        <div className="toast-body">
                            {t.message}
                        </div>
                    </div>
                ))}
            </div>
        </ToastContext.Provider>
    );
}

export const useToast = () => useContext(ToastContext);