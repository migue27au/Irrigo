const API = "http://localhost:8000";

function authHeaders() {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export async function getSystems() {
  const res = await fetch(`${API}/irrigation-systems/`, {
    headers: authHeaders(),
  });
  return res.json();
}

export async function getSystem(id) {
  const res = await fetch(`${API}/irrigation-systems/${id}`, {
    headers: authHeaders(),
  });
  return res.json();
}

export async function createSystem(data) {
  const res = await fetch(`${API}/irrigation-systems/`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function updateSystem(id, data) {
  const res = await fetch(`${API}/irrigation-systems/${id}`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function deleteSystem(id) {
  return fetch(`${API}/irrigation-systems/${id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}

export async function shareSystem(id, data) {
  return fetch(`${API}/irrigation-systems/${id}/share`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
}