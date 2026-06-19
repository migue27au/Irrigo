import { useState } from "react";

export default function CreateSystemModal({ onClose, onCreate }) {
  const [alias, setAlias] = useState("");
  const [description, setDescription] = useState("");

  const submit = () => {
    onCreate({ alias, description });
  };

  return (
    <div className="modal d-block bg-dark bg-opacity-75">
      <div className="modal-dialog">
        <div className="modal-content p-3">

          <h5>Create System</h5>

          <input
            className="form-control mb-2"
            placeholder="Alias"
            value={alias}
            onChange={(e) => setAlias(e.target.value)}
          />

          <textarea
            className="form-control mb-2"
            placeholder="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          <div className="d-flex justify-content-end gap-2">
            <button className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button className="btn btn-success" onClick={submit}>
              Create
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}