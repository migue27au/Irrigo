import { shareSystem } from "../../services/systems.api";
import { useState } from "react";

export default function SystemDetail({ system, onDelete }) {
  const [userId, setUserId] = useState("");

  if (!system) {
    return <div className="text-muted">Select a system</div>;
  }

  const handleShare = async () => {
    await shareSystem(system.id, {
      user_id: Number(userId),
      role: "viewer",
    });
    alert("System shared");
  };

  return (
    <div>
      <h2 className="text-success">{system.alias}</h2>

      <p className="text-muted">{system.description}</p>

      <hr />

      <p><b>ID:</b> {system.id}</p>
      <p><b>Firmware:</b> {system.firmware_version || "N/A"}</p>
      <p><b>Last seen:</b> {system.last_seen_at || "Never"}</p>

      <hr />

      <button
        className="btn btn-danger me-2"
        onClick={() => onDelete(system.id)}
      >
        Delete
      </button>

      <hr />

      <h5>Share system</h5>

      <input
        className="form-control mb-2"
        placeholder="User ID"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
      />

      <button className="btn btn-success" onClick={handleShare}>
        Share
      </button>
    </div>
  );
}