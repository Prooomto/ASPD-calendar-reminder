import { useState } from "react";
import { login } from "../api";                // setAuthToken уже вызывается внутри login()
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [pwd, setPwd] = useState("");
  const [err, setErr] = useState(null);
  const nav = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    setErr(null);
    try {
      const data = await login(email, pwd);         // { access_token, token_type }
      const jwt = data?.access_token;
      if (!jwt) {
        setErr("Сервер вернул 200, но без access_token");
        return;
      }
      // Токен уже сохранён и повешен в axios в api.login()
      nav("/events");
    } catch (e) {
      const msg =
        e?.response?.data?.detail ||
        e?.response?.data?.message ||
        e?.message ||
        "Не удалось войти";
      setErr(String(msg));
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "40px auto", padding: 16 }}>
      <h2>Вход</h2>
      <form onSubmit={onSubmit} style={{ display: "grid", gap: 8 }}>
        <input
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
        />
        <input
          type="password"
          placeholder="Пароль"
          value={pwd}
          onChange={e => setPwd(e.target.value)}
        />
        {err && <div style={{ color: "crimson", fontSize: 14 }}>{err}</div>}
        <button>Войти</button>
      </form>
    </div>
  );
}