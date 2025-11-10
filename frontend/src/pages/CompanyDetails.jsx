import { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  apiGetCompany,
  apiListMembers,
  apiAddMember,
  apiRemoveMember,
} from "../api";
import { getMe } from "../api";
import { formatLocal } from "../helpers/date";

// owner → admin (простой маппинг для показа)
function viewRole(role) {
  return role === "owner" ? "admin" : role;
}

export default function CompanyDetails() {
  const { id } = useParams();
  const companyId = Number(id);
  const nav = useNavigate();

  const [me, setMe] = useState(null);
  const [company, setCompany] = useState(null);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  const [email, setEmail] = useState("");

  const myMember = useMemo(
    () => members.find((m) => m.user?.email && me?.email && m.user.email === me.email),
    [members, me]
  );
  const myRole = viewRole(myMember?.role || "member"); // admin / member

  async function load() {
    setLoading(true);
    setErr(null);
    try {
      const [self, c, m] = await Promise.all([getMe(), apiGetCompany(companyId), apiListMembers(companyId)]);
      setMe(self || null);
      setCompany(c);
      setMembers(Array.isArray(m) ? m : []);
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "Не удалось загрузить данные");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [companyId]);

  async function addMember() {
    const val = email.trim();
    if (!val) return;
    try {
      await apiAddMember(companyId, val);
      setEmail("");
      load();
    } catch (e) {
      alert(e?.response?.data?.detail || e?.message || "Не удалось добавить участника");
    }
  }

  async function removeMember(memberId) {
    if (!confirm("Удалить участника?")) return;
    try {
      await apiRemoveMember(companyId, memberId);
      load();
    } catch (e) {
      alert(e?.response?.data?.detail || e?.message || "Не удалось удалить");
    }
  }

  return (
    <div className="container">
      <div className="toolbar">
        <div style={{display:"flex", alignItems:"center", gap:10}}>
          <button className="btn ghost" onClick={() => nav(-1)}>Назад</button>
          <h1 className="text-2xl" style={{fontWeight:800}}>Компания</h1>
        </div>
        <Link to="/companies" className="link">Все компании</Link>
      </div>

      {err && <div className="error" style={{marginBottom:12}}>{err}</div>}

      {loading || !company ? (
        <div className="card">Загрузка…</div>
      ) : (
        <>
          {/* Инфо о компании */}
          <div className="card" style={{marginBottom:12}}>
            <div style={{display:"grid", gap:4}}>
              <div style={{fontWeight:700, fontSize:18}}>{company.name}</div>
              <div style={{color:"var(--muted)"}}>{company.description || "—"}</div>
              <div style={{fontSize:13, color:"var(--muted)"}}>
                Создана: {formatLocal(company.created_at)}
              </div>
            </div>
          </div>

          {/* Управление участниками */}
          <div className="card" style={{display:"grid", gap:12}}>
            <div style={{fontWeight:700, fontSize:18}}>Участники</div>

            <div className="field-row">
              <input
                className="field"
                placeholder="Email пользователя"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={myRole !== "admin"}
              />
              <button
                className="btn dark"
                onClick={addMember}
                disabled={myRole !== "admin"}
                title={myRole !== "admin" ? "Добавлять участников может только админ" : ""}
              >
                Добавить
              </button>
            </div>

            <div style={{overflowX:"auto"}}>
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Имя</th>
                    <th>Email</th>
                    <th>Роль</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {members.map((m) => {
                    const isMe = me?.email && m.user?.email === me.email;
                    const role = viewRole(m.role);
                    const canAdmin = myRole === "admin";
                    const targetIsAdmin = role === "admin";

                    const showLeave = isMe && role === "member";
                    const showDelete = !isMe && canAdmin && !targetIsAdmin;

                    return (
                      <tr key={m.id}>
                        <td>{m.id}</td>
                        <td>{m.user?.name || "—"}</td>
                        <td>{m.user?.email || "—"}</td>
                        <td>
                          <span className={`role-chip ${role === "admin" ? "role-admin" : "role-member"}`}>
                            {role}
                          </span>
                        </td>
                        <td>
                          {showLeave && (
                            <button className="btn ghost" onClick={() => removeMember(m.id)}>
                              Выйти
                            </button>
                          )}
                          {showDelete && (
                            <button className="btn danger" onClick={() => removeMember(m.id)}>
                              Удалить
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                  {members.length === 0 && (
                    <tr>
                      <td colSpan={5} style={{textAlign:"center", padding:16, color:"var(--muted)"}}>
                        Нет участников
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
