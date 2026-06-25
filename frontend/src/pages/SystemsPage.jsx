import { useEffect, useState } from "react";
import api from "../api/api";
import { useToast } from "../context/ToastContext";

export default function SystemsPage() {
  const [systems, setSystems] = useState([]);
  const [selected, setSelected] = useState(null);

  const { error, success, warning } = useToast();

  const [apiKey, setApiKey] = useState("");
  const [loadingApiKey, setLoadingApiKey] = useState(false);

  const [editAlias, setEditAlias] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const [shareUsername, setShareUsername] = useState("");
  const [shareRole, setShareRole] = useState("viewer");
  const [sharing, setSharing] = useState(false);

  const [sharedUsers, setSharedUsers] = useState([]);
  const [loadingSharedUsers, setLoadingSharedUsers] = useState(false);

  const [sensors, setSensors] = useState([]);
  const [editingSensors, setEditingSensors] = useState({});
  
  const [actuators, setActuators] = useState([]);
  const [newActuator, setNewActuator] = useState({
    name: "",
    channel: 0,
  });
  const [editingActuators, setEditingActuators] = useState({});

  // -----------------------------
  // SYSTEM LIST
  // -----------------------------
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

  // -----------------------------
  // LOAD FULL SYSTEM (IMPORTANT FIX)
  // -----------------------------
  const loadSystem = async (systemId) => {
    try {
      const res = await api.get(`/irrigation-systems/${systemId}`);
      setSelected(res.data);
    } catch (err) {
      error(err?.response?.data?.detail || "Failed to load system");
    }
  };

  useEffect(() => {
    if (!selected) return;

    setEditAlias(selected.alias || "");
    setEditDescription(selected.description || "");

    loadApiKey(selected.id, selected.role);
    loadSharedUsers(selected.id, selected.role);
    loadSensors(selected.id);
    loadActuators(selected.id);

  }, [selected]);

  // -----------------------------
  // SENSORS
  // -----------------------------
  const loadSensors = async (systemId) => {
    try {
      const res = await api.get(`/irrigation-systems/${systemId}/sensors`);
      setSensors(res.data);
    } catch (err) {
      setSensors([]);
      error("Failed to load sensors");
    }
  };

  const updateSensorName = async (sensor) => {
    try {
      await api.put(`/sensors/${sensor.id}`, {
        name: editingSensors[sensor.id],
      });

      success("Sensor updated");

      setSensors((prev) =>
        prev.map((s) =>
          s.id === sensor.id
            ? { ...s, name: editingSensors[sensor.id] }
            : s
        )
      );
    } catch (err) {
      error("Failed to update sensor");
    }
  };
  
  // -----------------------------
  // ACTUATORS
  // -----------------------------

  const loadActuators = async (systemId) => {
    try {
      const res = await api.get(`/irrigation-systems/${systemId}/actuators`);
      setActuators(res.data);
    } catch (err) {
      setActuators([]);
      error("Failed to load actuators");
    }
  };

  const createActuator = async () => {
    try {
      const res = await api.post("/actuators/", {
        system_id: selected.id,
        name: newActuator.name,
        channel: newActuator.channel,
      });

      setActuators((prev) => [res.data, ...prev]);

      setNewActuator({
        name: "",
        channel: 0,
      });

      success("Actuator created");
    } catch (err) {
      error(err?.response?.data?.detail || "Failed to create actuator");
    }
  };

  const updateActuator = async (actuator) => {
    try {
      const res = await api.put(`/actuators/${actuator.id}`, {
        name: editingActuators[actuator.id],
      });

      setActuators((prev) =>
        prev.map((a) => (a.id === actuator.id ? res.data : a))
      );

      success("Actuator updated");
    } catch (err) {
      error("Failed to update actuator");
    }
  };

  const toggleActuator = async (actuator, value) => {
    try {
      const res = await api.put(`/actuators/${actuator.id}`, {
        enabled: value,
      });

      setActuators((prev) =>
        prev.map((x) => (x.id === actuator.id ? res.data : x))
      );

      success("State updated");
    } catch (err) {
      error(err?.response?.data?.detail || "Failed to update state");
    }
  };

  const deleteActuator = async (actuator) => {
    const previous = actuators;

    try {
      setActuators((prev) =>
        prev.filter((a) => a.id !== actuator.id)
      );

      await api.delete(`/actuators/${actuator.id}`);

      success("Actuator deleted");
    } catch (err) {
      // If fail, rollback to previous
      setActuators(previous);

      error(err?.response?.data?.detail || "Failed to delete actuator");
    }
  };


  // -----------------------------
  // API KEY
  // -----------------------------
  const loadApiKey = async (systemId, role) => {
    if (role !== "owner"){
      setApiKey("");
      return;
    }
    try {
      setLoadingApiKey(true);

      const res = await api.get(
        `/irrigation-systems/${systemId}/apikey`
      );

      setApiKey(res.data.api_key);
    } catch (err) {
      setApiKey("");

      error("Failed to load API key");
    } finally {
      setLoadingApiKey(false);
    }
  };

  const regenerateApiKey = async () => {
    try {
      await api.post(
        `/irrigation-systems/${selected.id}/apikey/regenerate`
      );

      success("API key regenerated");
      await loadApiKey(selected.id);
    } catch (err) {
      error(
        err?.response?.data?.detail ||
          "Failed to regenerate API key"
      );
    }
  };

  const copyApiKey = async () => {
    try {
      await navigator.clipboard.writeText(apiKey);
      success("API key copied");
    } catch {
      error("Failed to copy API key");
    }
  };

  // -----------------------------
  // SHARED USERS
  // -----------------------------
  const loadSharedUsers = async (systemId, role) => {
    if (!["owner", "maintainer"].includes(role)){
      setSharedUsers([]);
      return;
    }
    try {
      setLoadingSharedUsers(true);

      const res = await api.get(
        `/irrigation-systems/${systemId}/shared-users`
      );

      setSharedUsers(res.data);
    } catch (err) {
      setSharedUsers([]);
      error("Failed to load shared users");
    } finally {
      setLoadingSharedUsers(false);
    }
  };

  const unshareUser = async (userId) => {
    try {
      await api.delete(
        `/irrigation-systems/${selected.id}/share/${userId}`
      );

      success("User removed from system");

      setSharedUsers((prev) =>
        prev.filter((u) => u.user_id !== userId)
      );
    } catch (err) {
      error(err?.response?.data?.detail || "Failed to remove user");
    }
  };

  const shareSystem = async () => {
    if (!selected) return;

    try {
      setSharing(true);

      await api.post(
        `/irrigation-systems/${selected.id}/share`,
        {
          username: shareUsername,
          role: shareRole,
        }
      );

      success("System shared successfully");

      setShareUsername("");
      setShareRole("viewer");

      await loadSharedUsers(selected.id);
    } catch (err) {
      error(err?.response?.data?.detail || "Failed to share system");
    } finally {
      setSharing(false);
    }
  };

  // -----------------------------
  // SYSTEM CRUD
  // -----------------------------
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

      if (selected?.id === id) {
        setSelected(null);
        setSharedUsers([]);
      }
    } catch (err) {
      error(err?.response?.data?.detail || "Delete failed");
    }
  };

  const saveSystem = async () => {
    try {
      const res = await api.put(
        `/irrigation-systems/${selected.id}`,
        {
          alias: editAlias,
          description: editDescription,
        }
      );

      setSystems((prev) =>
        prev.map((s) =>
          s.id === selected.id ? res.data : s
        )
      );

      setSelected(res.data);

      success("System updated");
    } catch (err) {
      error(err?.response?.data?.detail || "Update failed");
    }
  };

  // -----------------------------
  // UI
  // -----------------------------
  return (
    <div className="systems-layout">

      {/* LEFT SIDEBAR */}
      <div className="systems-sidebar">
        <div className="d-flex justify-content-between mb-2">
          <h5>Systems</h5>

          <button
            className="btn btn-sm btn-success"
            onClick={createSystem}
          >
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
              onClick={() => loadSystem(s.id)}
            >
              {s.alias}
            </button>
          ))}
        </div>
      </div>

      {/* CENTER CONTENT */}
      <div className="systems-content">
        {!selected ? (
          <div>Select a system</div>
        ) : (
          <>
            {/* EDIT */}
            <div className="mb-3">
              <label className="form-label">Alias</label>
              <input
                className="form-control"
                value={editAlias}
                onChange={(e) => setEditAlias(e.target.value)}
              />
            </div>

            <div className="mb-3">
              <label className="form-label">Owner</label>
              <input
                className="form-control"
                value={selected?.owner_username || "Unknown"}
                readOnly
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Firmware version</label>
              <input
                className="form-control"
                value={selected?.firmware_version || "Unknown"}
                readOnly
              />
            </div>
            

            <div className="mb-3">
              <label className="form-label">Role</label>
              <input
                className="form-control"
                value={selected?.role || "Unknown"}
                readOnly
              />
            </div>

            <div className="mb-3">
              <label className="form-label">Description</label>
              <textarea
                className="form-control"
                rows="4"
                value={editDescription}
                onChange={(e) =>
                  setEditDescription(e.target.value)
                }
              />
            </div>

            {/* API KEY */}
            <div className="mb-4">
              <label className="form-label">API Key</label>

              <div className="input-group">
                <input
                  className="form-control"
                  readOnly
                  value={
                    loadingApiKey ? "Loading..." : apiKey
                  }
                />

                <button
                  className="btn btn-outline-secondary"
                  onClick={copyApiKey}
                >
                  Copy
                </button>

                <button
                  className="btn btn-outline-warning"
                  onClick={regenerateApiKey}
                >
                  Regenerate
                </button>
              </div>
            </div>

            {/* SHARE */}
            <div className="mb-4">
              <label className="form-label">Share system</label>

              <div className="input-group">
                <input
                  className="form-control"
                  placeholder="Username"
                  value={shareUsername}
                  onChange={(e) =>
                    setShareUsername(e.target.value)
                  }
                />

                <select
                  className="form-select"
                  value={shareRole}
                  onChange={(e) =>
                    setShareRole(e.target.value)
                  }
                  style={{ maxWidth: "140px" }}
                >
                  <option value="viewer">Viewer</option>
                  <option value="maintainer">Maintainer</option>
                </select>

                <button
                  className="btn btn-primary"
                  onClick={shareSystem}
                  disabled={!shareUsername || sharing}
                >
                  {sharing ? "Sharing..." : "Share"}
                </button>
              </div>
            </div>

            {/* SHARED USERS */}
            <div className="mb-4">
              <label className="form-label">Shared users</label>

              {loadingSharedUsers ? (
                <div>Loading...</div>
              ) : (
                <ul className="list-group">
                  {sharedUsers.map((u) => (
                    <li
                      key={u.user_id}
                      className="list-group-item d-flex justify-content-between align-items-center"
                    >
                      <div>
                        <strong>{u.username}</strong>{" "}
                        <span className="text-muted">
                          ({u.role})
                        </span>
                      </div>

                      {u.role !== "owner" && (
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() =>
                            unshareUser(u.user_id)
                          }
                        >
                          Remove
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* ACTIONS */}
            <div className="d-flex gap-2">
              <button
                className="btn btn-success"
                onClick={saveSystem}
              >
                Save
              </button>

              <button
                className="btn btn-danger"
                onClick={() =>
                  deleteSystem(selected.id)
                }
              >
                Delete
              </button>
            </div>

            {/* SENSORS TABLE */}
            <h5>Sensors</h5>

            <table className="table table-dark table-striped">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Key</th>
                  <th>Name</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {sensors.map((s) => (
                  <tr key={s.id}>
                    <td>{s.id}</td>
                    <td>{s.sensor_key}</td>

                    <td>
                      <input
                        className="form-control"
                        value={
                          editingSensors[s.id] ?? s.name
                        }
                        onChange={(e) =>
                          setEditingSensors((prev) => ({
                            ...prev,
                            [s.id]: e.target.value,
                          }))
                        }
                      />
                    </td>

                    <td>
                      <button
                        className="btn btn-sm btn-success"
                        onClick={() => updateSensorName(s)}
                      >
                        Save
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* ACTUATORS TABLE */}
            <h5>Actuators</h5>

            <table className="table table-dark table-striped">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Channel</th>
                  <th>Name</th>
                  <th>Enabled</th>
                  <th>Last change</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {/* CREATE NEW ACTUATOR */}
                <tr>
                  <td>New</td>

                  <td>
                    <input
                      className="form-control"
                      type="number"
                      min={0}
                      max={3}
                      value={newActuator.channel}
                      onChange={(e) =>
                        setNewActuator((prev) => ({
                          ...prev,
                          channel: Number(e.target.value),
                        }))
                      }
                    />
                  </td>

                  <td>
                    <input
                      className="form-control"
                      placeholder="Name"
                      value={newActuator.name}
                      onChange={(e) =>
                        setNewActuator((prev) => ({
                          ...prev,
                          name: e.target.value,
                        }))
                      }
                    />
                  </td>

                  <td colSpan={2}></td>

                  <td>
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={createActuator}
                      disabled={!newActuator.name}
                    >
                      Add
                    </button>
                  </td>
                </tr>

                {/* EXISTING ACTUATORS */}
                {actuators.map((a) => (
                  <tr key={a.id}>
                    <td>{a.id}</td>

                    <td>{a.channel}</td>

                    <td>
                      <input
                        className="form-control"
                        value={editingActuators[a.id] ?? a.name}
                        onChange={(e) =>
                          setEditingActuators((prev) => ({
                            ...prev,
                            [a.id]: e.target.value,
                          }))
                        }
                      />
                    </td>

                    <td>
                      <input
                        type="checkbox"
                        checked={a.enabled}
                        onChange={(e) => toggleActuator(a, e.target.checked)}
                      />
                    </td>

                    <td>
                      {a.last_changed_at
                        ? new Date(a.last_changed_at).toLocaleString()
                        : "-"}
                    </td>

                    <td>
                      <div className="d-flex gap-2">
                        <button
                          className="btn btn-sm btn-success"
                          onClick={() => updateActuator(a)}
                        >
                          Save
                        </button>

                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => deleteActuator(a)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>
    </div>
  );
}