import { Link } from "react-router-dom";

function DashboardPage() {
  return (
    <div className="container mt-4">

      <h1 className="mb-4" style={{ color: "#22c55e" }}>
        🌱 Irrigo Dashboard
      </h1>

      <div className="row g-3">

        <div className="col-md-4">
          <div className="card p-3">
            <h5>💧 Sistemas</h5>
            <p>Gestiona tus sistemas de riego</p>
            <Link className="btn btn-irrigation" to="/systems">
              Ver sistemas
            </Link>
          </div>
        </div>

        <div className="col-md-4">
          <div className="card p-3">
            <h5>📡 Sensores</h5>
            <p>Humedad, temperatura y estado</p>
          </div>
        </div>

        <div className="col-md-4">
          <div className="card p-3">
            <h5>⏱ Programación</h5>
            <p>Riegos automáticos</p>
          </div>
        </div>

      </div>
    </div>
  );
}

export default DashboardPage;