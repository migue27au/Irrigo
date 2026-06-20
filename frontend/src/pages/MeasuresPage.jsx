import { useEffect, useState } from "react";
import api from "../api/api";
import { useToast } from "../context/ToastContext";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

export default function MeasurePage() {
  const { error } = useToast();

  const [systems, setSystems] = useState([]);
  const [selectedSystem, setSelectedSystem] = useState(null);

  const [sensors, setSensors] = useState([]);
  const [selectedSensors, setSelectedSensors] = useState([]);

  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  const [data, setData] = useState([]);
  const [view, setView] = useState("chart");

  // -----------------------------
  // INIT TIME RANGE
  // -----------------------------
  useEffect(() => {
    const now = new Date();
    const yesterday = new Date(Date.now() - 86400000);

    setFrom(yesterday.toISOString().slice(0, 16));
    setTo(now.toISOString().slice(0, 16));
  }, []);

  // -----------------------------
  // LOAD SYSTEMS
  // -----------------------------
  const fetchSystems = async () => {
    try {
      const res = await api.get("/irrigation-systems/");
      setSystems(res.data);
    } catch {
      error("Failed to load systems");
    }
  };

  // -----------------------------
  // LOAD SENSORS
  // -----------------------------
  const fetchSensors = async (systemId) => {
    try {
      const res = await api.get(
        `/irrigation-systems/${systemId}/sensors`
      );
      setSensors(res.data);
      setSelectedSensors([]);
      setData([]);
    } catch {
      error("Failed to load sensors");
    }
  };

  // -----------------------------
  // LOAD DATA (MULTI SENSOR)
  // -----------------------------
  const fetchData = async () => {
    if (!selectedSensors.length) return;

    try {
      const ids = selectedSensors.join(",");

      const res = await api.get("/sensors/history", {
        params: {
          sensor_ids: ids,
          from_date: from,
          to_date: to,
        },
      });

      setData(res.data.data || []);
    } catch {
      error("Failed to load measures");
    }
  };

  // -----------------------------
  // LOAD SYSTEMS INIT
  // -----------------------------
  useEffect(() => {
    fetchSystems();
  }, []);

  useEffect(() => {
    if (selectedSystem) fetchSensors(selectedSystem.id);
  }, [selectedSystem]);

  // -----------------------------
  // TOGGLE SENSOR
  // -----------------------------
  const toggleSensor = (id) => {
    setSelectedSensors((prev) =>
      prev.includes(id)
        ? prev.filter((x) => x !== id)
        : [...prev, id]
    );
  };

  // -----------------------------
  // FIXED CHART DATA (REAL TIME AXIS)
  // -----------------------------
  const chartData = () => {
    const map = {};

    data.forEach((sensor) => {
      sensor.points.forEach((p) => {
        const t = new Date(p.t).getTime(); // 🔥 REAL TIME AXIS

        if (!map[t]) {
          map[t] = { time: t };
        }

        map[t][sensor.sensor_name] = p.v;
      });
    });

    return Object.values(map).sort((a, b) => a.time - b.time);
  };

  const sensorNames = data.map((s) => s.sensor_name);

  // -----------------------------
  // UI
  // -----------------------------
  return (
    <div className="systems-layout">

      {/* SIDEBAR */}
      <div className="systems-sidebar">
        <h5>Systems</h5>

        <div className="list-group">
          {systems.map((s) => (
            <button
              key={s.id}
              className={`list-group-item ${
                selectedSystem?.id === s.id ? "active" : ""
              }`}
              onClick={() => setSelectedSystem(s)}
            >
              {s.alias}
            </button>
          ))}
        </div>

        {selectedSystem && (
          <>
            <hr />
            <h6>Sensors</h6>

            <div className="list-group">
              {sensors.map((s) => (
                <label
                  key={s.id}
                  className="list-group-item d-flex align-items-center gap-2"
                >
                  <input
                    type="checkbox"
                    checked={selectedSensors.includes(s.id)}
                    onChange={() => toggleSensor(s.id)}
                  />
                  {s.name}
                </label>
              ))}
            </div>
          </>
        )}
      </div>

      {/* CONTENT */}
      <div className="systems-content">
        <h4>Measures</h4>

        {/* FILTERS */}
        <div className="d-flex gap-2 mb-3">
          <input
            type="datetime-local"
            className="form-control"
            value={from}
            onChange={(e) => setFrom(e.target.value)}
          />

          <input
            type="datetime-local"
            className="form-control"
            value={to}
            onChange={(e) => setTo(e.target.value)}
          />

          <button
            className="btn btn-primary"
            onClick={fetchData}
            disabled={!selectedSensors.length}
          >
            Reload
          </button>
        </div>

        {/* VIEW */}
        <div className="btn-group mb-3">
          <button
            className={`btn btn-outline-primary ${
              view === "chart" ? "active" : ""
            }`}
            onClick={() => setView("chart")}
          >
            Chart
          </button>

          <button
            className={`btn btn-outline-primary ${
              view === "table" ? "active" : ""
            }`}
            onClick={() => setView("table")}
          >
            Table
          </button>
        </div>

        {/* CHART */}
        {view === "chart" && (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData()}>
              <XAxis
                dataKey="time"
                type="number"
                domain={["dataMin", "dataMax"]}
                tickFormatter={(t) =>
                  new Date(t).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                }
              />

              <YAxis />
              <Tooltip
                labelFormatter={(t) =>
                  new Date(t).toLocaleString()
                }
              />
              <Legend />

              {sensorNames.map((name, i) => (
                <Line
                  key={name}
                  type="monotone"
                  dataKey={name}
                  stroke={`hsl(${i * 60}, 70%, 50%)`}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                  connectNulls={true}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}

        {/* TABLE */}
        {view === "table" && (
          <table className="table table-striped">
            <thead>
              <tr>
                <th>Time</th>
                {sensorNames.map((name) => (
                  <th key={name}>{name}</th>
                ))}
              </tr>
            </thead>

            <tbody>
              {chartData().map((row, i) => (
                <tr key={i}>
                  <td>
                    {new Date(row.time).toLocaleString()}
                  </td>

                  {sensorNames.map((name) => (
                    <td key={name}>{row[name] ?? "-"}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}