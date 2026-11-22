// Member 4's API helper. Everyone on the team imports from here.
//
// BASE_URL:
//  - Browser on the same laptop as the backend:  http://127.0.0.1:8000
//  - Phone / Expo Go: use your laptop's Wi-Fi IP, e.g. http://192.168.1.5:8000
//    (find it with `ipconfig` on Windows; run uvicorn with --host 0.0.0.0)
export const BASE_URL = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API ${path} failed with status ${res.status}`);
  }
  return res.json();
}

// ---- Member 1 screens (CycloneAlert, SafetyCheckIn) ----
export const getActiveCyclone = () => request("/cyclone/active");

// ---- Preparedness screen ----
export const getPrecautions = () => request("/cyclone/precautions");

// ---- SafetyCheckIn callbacks ----
// response must be exactly: "Safe" | "NeedHelp" | "Unresponsive"
export const sendCheckIn = ({ userId, response, latitude, longitude, scenarioId }) =>
  request("/checkins", {
    method: "POST",
    body: JSON.stringify({
      user_id: userId,
      response,
      latitude,
      longitude,
      scenario_id: scenarioId,
    }),
  });

// ---- SOS (Member 2: direct SOS button and offline sync) ----
export const sendSos = (sos) =>
  request("/sos", { method: "POST", body: JSON.stringify(sos) });

// Upload SOS requests that were saved on the phone while offline
export const syncOfflineSos = (requests) =>
  request("/sos/sync", { method: "POST", body: JSON.stringify({ requests }) });

// ---- Users and family (Member 2: call these at sign-up / contacts screen) ----
export const registerUser = ({ userId, name, phone, pushToken }) =>
  request("/users", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, name, phone, push_token: pushToken }),
  });

export const addContact = (userId, { name, phone, relation }) =>
  request(`/users/${encodeURIComponent(userId)}/contacts`, {
    method: "POST",
    body: JSON.stringify({ name, phone, relation }),
  });

export const getContacts = (userId) =>
  request(`/users/${encodeURIComponent(userId)}/contacts`);

// Save the phone's Expo push token (used later to send real notifications)
export const savePushToken = (userId, pushToken) =>
  request(`/users/${encodeURIComponent(userId)}/push-token`, {
    method: "PUT",
    body: JSON.stringify({ push_token: pushToken }),
  });

// Family member checking on their person (phone must be one of the person's contacts)
export const getFamilyStatus = (userId, myPhone) =>
  request(`/family/${encodeURIComponent(userId)}/status?phone=${encodeURIComponent(myPhone)}`);

// ---- Rescuer dashboard ----
export const listSos = (status) =>
  request(status ? `/sos?status=${encodeURIComponent(status)}` : "/sos");

export const updateSosStatus = (sosId, status) =>
  request(`/sos/${sosId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
