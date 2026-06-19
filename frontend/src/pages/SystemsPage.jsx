import { useEffect, useState } from "react";
import api from "../api/api";
import { useToast } from "../context/ToastContext";

export default function SystemsPage() {
  const [systems, setSystems] = useState([]);
  const [selected, setSelected] = useState(null);
  const { error, success, warning } = useToast();

  const fetchSystems = async () => {
    try {
      const res = await api.get("/irrigation-systems/");
      setSystems(res.data);
    } catch (err) {
      error(err?.response?.data?.detail || "Error loading systems");
    }
  };

  useEffect(() => {
    fetchSystems();
  }, []);

  const createSystem = async () => {
    try {
      const res = await api.post("/irrigation-systems/", {
        alias: "New System",
        description: "Created from UI",
      });

      success("System created");
      setSystems((prev) => [...prev, res.data]);
    } catch (err) {
      error(err?.response?.data?.detail || "Create failed");
    }
  };

  const deleteSystem = async (id) => {
    try {
      await api.delete(`/irrigation-systems/${id}`);
      warning("System deleted");
      setSystems((prev) => prev.filter((s) => s.id !== id));
      if (selected?.id === id) setSelected(null);
    } catch (err) {
      error(err?.response?.data?.detail || "Delete failed");
    }
  };

  return (
    <div className="systems-layout">
      {/* LEFT SIDEBAR */}
      <div className="systems-sidebar">
        <div className="d-flex justify-content-between mb-2">
          <h5>Systems</h5>
          <button className="btn btn-sm btn-success" onClick={createSystem}>
            +
          </button>
        </div>

        <div className="list-group">
          {systems.map((s) => (
            <button
              key={s.id}
              className={`list-group-item list-group-item-action ${
                selected?.id === s.id ? "active" : ""
              }`}
              onClick={() => setSelected(s)}
            >
              {s.alias}
            </button>
          ))}
        </div>
      </div>

      {/* CENTER DETAIL */}
      <div className="systems-content">
        {!selected ? (
          <div>Select a system</div>
        ) : (
          <>
            <h3>{selected.alias}</h3>
            <p>{selected.description}</p>

            <button
              className="btn btn-danger btn-sm"
              onClick={() => deleteSystem(selected.id)}
            >
              Delete
            </button>
          </>
        )}
      </div>
    </div>
  );
}