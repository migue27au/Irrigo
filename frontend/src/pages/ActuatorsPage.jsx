import { useEffect, useState } from "react";
import api from "../api/api";
import { useToast } from "../context/ToastContext";

export default function ActuatorPage() {
  const { error, success } = useToast();

  const [systems, setSystems] = useState([]);
  const [selectedSystem, setSelectedSystem] = useState(null);

  const [actuators, setActuators] = useState([]);
  const [selectedActuator, setSelectedActuator] = useState(null);

  const [commands, setCommands] = useState([]);
  const [selectedCommand, setSelectedCommand] = useState(null);

  const [groups, setGroups] = useState([]);
  const [showRules, setShowRules] = useState(false);

  const [sensors, setSensors] = useState([]);

  const [editingGroupId, setEditingGroupId] = useState(null);
  const [editGroupForm, setEditGroupForm] = useState({
    name: "",
    description: "",
  });

  const [groupForm, setGroupForm] = useState({
    name: "",
    description: "",
  });

  const [conditionForms, setConditionForms] = useState({});

  const [form, setForm] = useState({
    intensity: "",
    duration_seconds: "",
    name: "",
  });

  // =========================
  // RESET RULES STATE
  // =========================
  const resetRules = () => {
    setSelectedCommand(null);
    setGroups([]);
    setShowRules(false);
    setConditionForms({});
    setEditingGroupId(null);
  };

  // =========================
  // SYSTEMS
  // =========================
  const fetchSystems = async () => {
    try {
      const res = await api.get("/irrigation-systems/");
      setSystems(res.data);
    } catch {
      error("Failed to load systems");
    }
  };

  // =========================
  // ACTUATORS
  // =========================
  const fetchActuators = async (systemId) => {
    try {
      const res = await api.get(
        `/irrigation-systems/${systemId}/actuators`
      );
      setActuators(res.data);

      setSelectedActuator(null);
      resetRules();
    } catch {
      error("Failed to load actuators");
    }
  };

  // =========================
  // SENSORS
  // =========================
  const getSensorName = (sensorId) => {
    const sensor = sensors.find(
      (s) => String(s.id) === String(sensorId)
    );
    return sensor ? sensor.name : sensorId;
  };

  const fetchSensors = async (systemId) => {
    try {
      const res = await api.get(
        `/irrigation-systems/${systemId}/sensors`
      );
      setSensors(res.data);
    } catch {
      error("Failed to load sensors");
    }
  };

  // =========================
  // COMMANDS
  // =========================
  const fetchCommands = async (actuatorId) => {
    try {
      const res = await api.get(
        `/actuators/${actuatorId}/commandsfromweb`
      );
      setCommands(res.data);
      resetRules();
    } catch {
      error("Failed to load commands");
    }
  };

  const createCommand = async (triggerType) => {
    try {
      const res = await api.post("/actuators/commands", {
        system_id: selectedSystem.id,
        actuator_id: selectedActuator,
        name: form.name || null,
        trigger_type: triggerType,
        intensity: form.intensity
          ? Number(form.intensity)
          : null,
        duration_seconds: form.duration_seconds
          ? Number(form.duration_seconds)
          : null,
      });

      setCommands((prev) => [res.data, ...prev]);
      setForm({
        intensity: "",
        duration_seconds: "",
        name: "",
      });

      success("Command created");
    } catch (err) {
      error(
        err?.response?.data?.detail ||
          "Failed to create command"
      );
    }
  };

  const deleteCommand = async (id) => {
    try {
      await api.delete(`/actuators/commands/${id}`);
      setCommands((prev) =>
        prev.filter((c) => c.id !== id)
      );
      resetRules();
      success("Command deleted");
    } catch {
      error("Failed to delete command");
    }
  };

  const toggleCommandEnabled = async (cmd) => {
    const updated = {
      ...cmd,
      enabled: !cmd.enabled,
    };

    setCommands((prev) =>
      prev.map((c) =>
        c.id === cmd.id ? updated : c
      )
    );

    try {
      const res = await api.put(
        `/actuators/commands/${cmd.id}`,
        {
          enabled: updated.enabled,
        }
      );

      setCommands((prev) =>
        prev.map((c) =>
          c.id === cmd.id ? res.data : c
        )
      );

      success("State updated");
    } catch {
      setCommands((prev) =>
        prev.map((c) =>
          c.id === cmd.id ? cmd : c
        )
      );
      error("Failed to update command");
    }
  };

  // =========================
  // RULES
  // =========================
  const loadRules = async (commandId) => {
    try {
      setSelectedCommand(commandId);
      setEditingGroupId(null);
      setConditionForms({});

      await fetchSensors(selectedSystem.id);

      const res = await api.get(
        `/rules/${commandId}/rulegroups`
      );

      setGroups(res.data);
      setShowRules(true);
    } catch {
      error("Failed to load rules");
    }
  };

  const createGroup = async () => {
    try {
      await api.post(
        `/rules/${selectedCommand}/rulegroups`,
        {
          name: groupForm.name?.trim(),
          description:
            groupForm.description?.trim() || null,
        }
      );

      setGroupForm({ name: "", description: "" });

      await loadRules(selectedCommand);
      success("Group created");
    } catch {
      error("Failed to create group");
    }
  };

  const updateGroup = async (groupId) => {
    try {
      const res = await api.put(
        `/rules/rulegroups/${groupId}`,
        {
          name: editGroupForm.name?.trim(),
          description:
            editGroupForm.description?.trim() || null,
        }
      );

      setGroups((prev) =>
        prev.map((g) =>
          g.id === groupId
            ? { ...g, ...res.data, id: groupId }
            : g
        )
      );

      setEditingGroupId(null);
      success("Group updated");
    } catch {
      error("Failed to update group");
    }
  };

  const deleteGroup = async (groupId) => {
    try {
      await api.delete(
        `/rules/rulegroups/${groupId}`
      );

      setGroups((prev) =>
        prev.filter((g) => g.id !== groupId)
      );

      success("Group deleted");
    } catch {
      error("Failed to delete group");
    }
  };

  const addCondition = async (groupId) => {
    const form = conditionForms[groupId];

    if (!form?.type) {
      error("Incomplete condition");
      return;
    }

    const payload = {
      type: form.type,
      sensor_id:
        form.type === "sensor" && form.sensor_id
          ? Number(form.sensor_id)
          : null,
      operator: form.operator || null,
      value:
        form.type === "sensor"
          ? Number(form.value)
          : null,
      cron:
        form.type === "time" ? form.value : null,
    };

    try {
      await api.post(
        `/rules/${selectedCommand}/rulegroups/${groupId}/conditions`,
        payload
      );

      setConditionForms((p) => ({
        ...p,
        [groupId]: {},
      }));

      await loadRules(selectedCommand);
      success("Condition added");
    } catch {
      error("Failed to add condition");
    }
  };

  const deleteCondition = async (
    groupId,
    conditionId
  ) => {
    try {
      await api.delete(
        `/rules/conditions/${conditionId}`
      );

      setGroups((prev) =>
        prev.map((g) =>
          g.id === groupId
            ? {
                ...g,
                conditions: g.conditions.filter(
                  (c) => c.id !== conditionId
                ),
              }
            : g
        )
      );

      success("Condition deleted");
    } catch {
      error("Failed to delete condition");
    }
  };

  const updateConditionForm = (
    groupId,
    key,
    value
  ) => {
    setConditionForms((prev) => ({
      ...prev,
      [groupId]: {
        ...prev[groupId],
        [key]: value,
      },
    }));
  };

  // =========================
  // EFFECTS
  // =========================
  useEffect(() => {
    fetchSystems();
  }, []);

  useEffect(() => {
    if (selectedSystem)
      fetchActuators(selectedSystem.id);
  }, [selectedSystem]);

  useEffect(() => {
    if (selectedActuator)
      fetchCommands(selectedActuator);
  }, [selectedActuator]);

  // =========================
  // UI
  // =========================
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
                selectedSystem?.id === s.id
                  ? "active"
                  : ""
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
            <h6>Actuators</h6>

            <div className="list-group">
              {actuators.map((a) => (
                <button
                  key={a.id}
                  className={`list-group-item ${
                    selectedActuator === a.id
                      ? "active"
                      : ""
                  }`}
                  onClick={() =>
                    setSelectedActuator(a.id)
                  }
                >
                  {a.name}
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {/* CONTENT */}
      <div className="systems-content">
        {!selectedActuator ? (
          <div>Select actuator</div>
        ) : (
          <>
            <h4>Commands</h4>

            {/* CREATE COMMAND */}
            <div className="card p-3 mb-3">
              <input
                className="form-control mb-2"
                placeholder="Name"
                value={form.name}
                onChange={(e) =>
                  setForm((p) => ({
                    ...p,
                    name: e.target.value,
                  }))
                }
              />

              <input
                className="form-control mb-2"
                placeholder="Intensity"
                type="number"
                value={form.intensity}
                onChange={(e) =>
                  setForm((p) => ({
                    ...p,
                    intensity: e.target.value,
                  }))
                }
              />

              <input
                className="form-control mb-2"
                placeholder="Duration"
                type="number"
                value={form.duration_seconds}
                onChange={(e) =>
                  setForm((p) => ({
                    ...p,
                    duration_seconds: e.target.value,
                  }))
                }
              />

              <div className="d-flex gap-2">
                <button
                  className="btn btn-primary"
                  onClick={() =>
                    createCommand("manual")
                  }
                >
                  Manual
                </button>

                <button
                  className="btn btn-warning"
                  onClick={() =>
                    createCommand("automatic")
                  }
                >
                  Automatic
                </button>
              </div>
            </div>

            {/* COMMAND TABLE */}
            <table className="table table-striped">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Enabled</th>
                  <th>Rules</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {commands.map((c) => (
                  <tr key={c.id}>
                    <td>{c.id}</td>
                    <td>{c.name || "-"}</td>
                    <td>{c.trigger_type}</td>

                    <td>
                      <input
                        type="checkbox"
                        checked={c.enabled}
                        onChange={() =>
                          toggleCommandEnabled(c)
                        }
                      />
                    </td>

                    <td>
                      {c.trigger_type ===
                        "automatic" && (
                        <button
                          className="btn btn-sm btn-outline-info"
                          onClick={() =>
                            loadRules(c.id)
                          }
                        >
                          Rules
                        </button>
                      )}
                    </td>

                    <td>
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() =>
                          deleteCommand(c.id)
                        }
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* RULES */}
            {showRules && (
              <div className="mt-4">
                <h5>Rule Groups</h5>

                {/* CREATE GROUP */}
                <div className="card p-3 mb-3">
                  <input
                    className="form-control mb-2"
                    placeholder="Group name"
                    value={groupForm.name}
                    onChange={(e) =>
                      setGroupForm((p) => ({
                        ...p,
                        name: e.target.value,
                      }))
                    }
                  />

                  <input
                    className="form-control mb-2"
                    placeholder="Description"
                    value={groupForm.description}
                    onChange={(e) =>
                      setGroupForm((p) => ({
                        ...p,
                        description:
                          e.target.value,
                      }))
                    }
                  />

                  <button
                    className="btn btn-success"
                    onClick={createGroup}
                  >
                    Add group
                  </button>
                </div>

                {/* GROUPS */}
                {groups.map((g) => (
                  <div
                    key={g.id}
                    className="card mb-3"
                  >
                    <div className="card-header d-flex justify-content-between">
                      <div>
                        <strong>{g.name}</strong>
                        <div className="text-muted small">
                          {g.description || "-"}
                        </div>
                      </div>

                      <div className="d-flex gap-2">
                        <button
                          className="btn btn-sm btn-outline-secondary"
                          onClick={() => {
                            setEditingGroupId(g.id);
                            setEditGroupForm({
                              name: g.name,
                              description:
                                g.description ||
                                "",
                            });
                          }}
                        >
                          Edit
                        </button>

                        <button
                          className="btn btn-sm btn-outline-danger"
                          onClick={() =>
                            deleteGroup(g.id)
                          }
                        >
                          Delete
                        </button>
                      </div>
                    </div>

                    {editingGroupId === g.id && (
                      <div className="p-3 border-top">
                        <input
                          className="form-control mb-2"
                          value={editGroupForm.name}
                          onChange={(e) =>
                            setEditGroupForm(
                              (p) => ({
                                ...p,
                                name:
                                  e.target.value,
                              })
                            )
                          }
                        />

                        <input
                          className="form-control mb-2"
                          value={
                            editGroupForm.description
                          }
                          onChange={(e) =>
                            setEditGroupForm(
                              (p) => ({
                                ...p,
                                description:
                                  e.target.value,
                              })
                            )
                          }
                        />

                        <button
                          className="btn btn-success btn-sm"
                          onClick={() =>
                            updateGroup(g.id)
                          }
                        >
                          Save
                        </button>
                      </div>
                    )}

                    <div className="card-body">
                      <table className="table table-sm">
                        <thead>
                          <tr>
                            <th>Type</th>
                            <th>Sensor</th>
                            <th>Operator</th>
                            <th>Value</th>
                            <th></th>
                          </tr>
                        </thead>

                        <tbody>
                          <tr>
                            <td>
                              <select
                                className="form-control"
                                value={conditionForms[g.id]?.type || ""}
                                onChange={(e) =>
                                  updateConditionForm(
                                    g.id,
                                    "type",
                                    e.target.value
                                  )
                                }
                              >
                                <option value="">
                                  Select
                                </option>

                                <option value="sensor">
                                  sensor
                                </option>

                                <option value="time">
                                  time
                                </option>
                              </select>
                            </td>

                            <td>
                              <select
                                className="form-control"
                                disabled={
                                  conditionForms[g.id]
                                    ?.type === "time"
                                }
                                value={
                                  conditionForms[g.id]
                                    ?.sensor_id || ""
                                }
                                onChange={(e) =>
                                  updateConditionForm(
                                    g.id,
                                    "sensor_id",
                                    e.target
                                      .value
                                  )
                                }
                              >
                                <option value="">
                                  Select
                                </option>
                                {sensors.map((s) => (
                                  <option
                                    key={s.id}
                                    value={s.id}
                                  >
                                    {s.name}
                                  </option>
                                ))}
                              </select>
                            </td>

                            <td>
                              <select
                                className="form-control"
                                value={conditionForms[g.id]?.operator || ""}
                                onChange={(e) =>
                                  updateConditionForm(
                                    g.id,
                                    "operator",
                                    e.target.value
                                  )
                                }
                              >
                                <option value="<">&lt;</option>
                                <option value=">">&gt;</option>
                                <option value="<=">&lt;=</option>
                                <option value=">=">&gt;=</option>
                                <option value="==">==</option>
                                <option value="!=">!=</option>
                              </select>
                            </td>

                            <td>
                              {conditionForms[g.id]?.type === "time" ? (
                                <input
                                  className="form-control"
                                  type="time"
                                  step="60"
                                  value={conditionForms[g.id]?.value || ""}
                                  onChange={(e) =>
                                    updateConditionForm(
                                      g.id,
                                      "value",
                                      e.target.value
                                    )
                                  }
                                />
                              ) : (
                                <input
                                  className="form-control"
                                  type="number"
                                  value={conditionForms[g.id]?.value || ""}
                                  onChange={(e) =>
                                    updateConditionForm(
                                      g.id,
                                      "value",
                                      e.target.value
                                    )
                                  }
                                />
                              )}
                            </td>

                            <td>
                              <button
                                className="btn btn-primary btn-sm"
                                onClick={() =>
                                  addCondition(g.id)
                                }
                              >
                                Add
                              </button>
                            </td>
                          </tr>

                          {g.conditions.map((c) => (
                            <tr key={c.id}>
                              <td>{c.type}</td>
                              <td>
                                {getSensorName(
                                  c.sensor_id
                                )}
                              </td>
                              <td>
                                {c.operator || "-"}
                              </td>
                              <td>
                                {c.value ||
                                  c.cron ||
                                  "-"}
                              </td>
                              <td>
                                <button
                                  className="btn btn-sm btn-danger"
                                  onClick={() =>
                                    deleteCondition(
                                      g.id,
                                      c.id
                                    )
                                  }
                                >
                                  Delete
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}