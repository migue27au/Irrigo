import { createContext, useContext, useState, useEffect } from "react";
import api from "../api/api";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [user, setUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(false);

  // -----------------------------
  // Fetch real user from backend
  // -----------------------------
  const fetchUser = async () => {
    try {
      setLoadingUser(true);

      const res = await api.get("/users/me");
      setUser(res.data);
    } catch (err) {
      console.error("Failed to fetch user:", err);
      setUser(null);
    } finally {
      setLoadingUser(false);
    }
  };

  // -----------------------------
  // Sync token -> backend user
  // -----------------------------
  useEffect(() => {
    if (!token) {
      setUser(null);
      return;
    }

    // opcional: seguir usando decode JWT como fallback rápido
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      setUser(payload);
    } catch {
      setUser({});
    }

    // pero SIEMPRE sincronizar con backend
    fetchUser();
  }, [token]);

  // -----------------------------
  // LOGIN
  // -----------------------------
  const login = (jwt) => {
    localStorage.setItem("token", jwt);
    setToken(jwt);
  };

  // -----------------------------
  // LOGOUT
  // -----------------------------
  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        login,
        logout,
        loadingUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}