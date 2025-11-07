import { useState } from "react";
import { register } from "../api";
import { useNavigate, Link } from "react-router-dom";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [pwd, setPwd] = useState("");
  const [err, setErr] = useState(null);
  const nav = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    setErr(null);
    try {
      await register({ name: name.trim() || null, email: email.trim(), password: pwd });
      alert("Аккаунт создан! Теперь войдите.");
      nav("/login");
    } catch (e) {
      const msg =
        e?.response?.data?.detail ||
        e?.response?.data?.message ||
        e?.message ||
        "Не удалось создать пользователя";
      setErr(String(msg));
    }
  }

  return (
    <div style={{ maxWidth: 460, margin: "40px auto", padding: 16 }}>
      <h2>Регистрация</h2>
      <form onSubmit={onSubmit} style={{ display: "grid", gap: 8 }}>
        <input
          placeholder="Имя (необязательно)"
          value={name}
          onChange={e => setName(e.target.value)}
        />
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
        <button>Создать аккаунт</button>
      </form>

      <div style={{ marginTop: 12 }}>
        Уже есть аккаунт? <Link to="/login">Войти</Link>
      </div>
    </div>
  );
}
