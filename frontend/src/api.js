import axios from "axios";

// Vite сам подставит значение из frontend/.env
const BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: BASE,
});

// Вешаем/снимаем Authorization
export function setAuthToken(token) {
  if (token) api.defaults.headers.common.Authorization = `Bearer ${token}`;
  else delete api.defaults.headers.common.Authorization;
}

// При загрузке страницы подтянуть токен из localStorage
setAuthToken(localStorage.getItem("token") || null);

// ==== AUTH ====
export async function login(email, password) {
  const form = new URLSearchParams();
  form.append("grant_type", "password");
  form.append("username", email);
  form.append("password", password);
  form.append("scope", "");
  form.append("client_id", "");
  form.append("client_secret", "");

  const res = await api.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  const { access_token } = res.data || {};
  if (access_token) {
    localStorage.setItem("token", access_token);
    setAuthToken(access_token);
  }
  return res.data;
}

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ==== EVENTS ====
export async function listEvents({ from, to }) {
  const res = await api.get("/events", { params: { from, to } });
  return res.data;
}

export async function createEvent(body) {
  const res = await api.post("/events", body);
  return res.data;
}

// --- добавляем ---
export async function deleteEvent(id) {
  const res = await api.delete(`/events/${id}`);
  return res.data;
}

export async function updateEvent(id, body) {
  const res = await api.put(`/events/${id}`, body);
  return res.data;
}

export async function getEvent(id) {
  const res = await api.get(`/events/${id}`);
  return res.data;
}

export async function listReminders(eventId) {
  const res = await api.get(`/events/${eventId}/reminders`);
  return res.data; // ожидаем [{id, event_id, remind_at, sent}, ...]
}

// ➕ НОВОЕ: регистрация
export async function register({ name, email, password }) {
  const body = { name, email, password };
  const res = await api.post("/auth/register", body);
  return res.data; // { id, name, email }
}

export async function startTelegramLink() {
  const res = await api.post("/telegram/link/start");
  return res.data; // { code, message }
}

export async function telegramLinkStatus() {
  try {
    const res = await api.get("/telegram/link/status");
    return res.data;         // { linked, telegram_id }
  } catch {
    return { linked: false, telegram_id: null };
  }
}

export async function getMe() {
  const res = await api.get('/auth/me');
  return res.data; // {id, name, email, telegram_id}
}



