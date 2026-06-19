export default function SystemsSidebar({ systems, onSelect, onCreate }) {
  return (
    <div className="bg-black text-light border-end"
         style={{ width: "280px", overflowY: "auto" }}>

      <div className="p-3 border-bottom">
        <button
          className="btn btn-success w-100"
          onClick={onCreate}
        >
          + New System
        </button>
      </div>

      {systems.map((sys) => (
        <div
          key={sys.id}
          className="p-3 border-bottom system-item"
          style={{ cursor: "pointer" }}
          onClick={() => onSelect(sys.id)}
        >
          <div className="fw-bold text-success">
            {sys.alias}
          </div>

          <small className="text-muted">
            {sys.description || "No description"}
          </small>
        </div>
      ))}
    </div>
  );
}