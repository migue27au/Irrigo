import { useState } from "react";
import api from "../api/api";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

function LoginPage() {
  const { token } = useAuth();

  if (token) {
      return <Navigate to="/dashboard" replace />;
  }

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const res = await api.post("/auth/login", {
        username,
        password,
      });

      login(res.data.access_token);
      navigate("/dashboard");
    } catch (err) {
      alert("Credenciales incorrectas");
    }
  };

  return (
    <div className="container d-flex justify-content-center align-items-center vh-100">
      <div className="card p-4 shadow-lg" style={{ width: "380px" }}>
        <h2 className="text-center mb-4" style={{ color: "#22c55e" }}>
          🌿 Irrigo
        </h2>

        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">Username</label>
            <input
              className="form-control"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="petitogrillo"
            />
          </div>

          <div className="mb-3">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          <button className="btn btn-irrigation w-100">
            Entrar
          </button>
        </form>
      </div>
    </div>
  );
}

export default LoginPage;