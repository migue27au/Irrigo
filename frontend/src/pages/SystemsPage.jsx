import { useEffect, useState } from "react";
import api from "../api/api";

function SystemsPage() {
  const [systems, setSystems] = useState([]);

  useEffect(() => {
    loadSystems();
  }, []);

  async function loadSystems() {
    try {
      const response = await api.get("/irrigation-systems");
      setSystems(response.data);
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div className="container mt-4">
      <h1 style={{ color: "#22c55e" }}>💧 Mis sistemas</h1>

      <div className="row mt-3">
        {systems.map((system) => (
          <div key={system.id} className="col-md-4 mb-3">
            <div className="card p-3">
              <h5>{system.alias}</h5>
              <p>{system.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SystemsPage;