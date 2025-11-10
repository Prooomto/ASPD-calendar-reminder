import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  apiListCompanies,
  apiCreateCompany,
  apiDeleteCompany,
} from "../api";
import { formatLocal } from "../helpers/date";

export default function Companies() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [modal, setModal] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  async function load() {
    setLoading(true); setErr(null);
    try {
      const data = await apiListCompanies();
      setItems(Array.isArray(data) ? data : []);
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "Не удалось загрузить компании");
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { load(); }, []);

  async function create() {
    if (!name.trim()) return;
    try {
      await apiCreateCompany({ name: name.trim(), description: description.trim() || null });
      setName(""); setDescription(""); setModal(false);
      load();
    } catch (e) {
      alert(e?.response?.data?.detail || e?.message || "Не удалось создать компанию");
    }
  }

  async function remove(id) {
    if (!confirm("Удалить компанию?")) return;
    try { await apiDeleteCompany(id); load(); }
    catch (e) { alert(e?.response?.data?.detail || e?.message || "Не удалось удалить"); }
  }

  return (
    <div className="container">
      <div className="toolbar">
        <h1 className="text-2xl font-bold" style={{fontWeight:800}}>Мои компании</h1>
        <button className="btn dark" onClick={() => setModal(true)}>Создать</button>
      </div>

      {err && <div className="error" style={{marginBottom:12}}>{err}</div>}

      {loading ? (
        <div className="card">Загрузка…</div>
      ) : (
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Название</th>
                <th>Описание</th>
                <th>Создана</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map(c => (
                <tr key={c.id}>
                  <td>{c.id}</td>
                  <td><Link className="link" to={`/companies/${c.id}`}>{c.name}</Link></td>
                  <td>{c.description || "—"}</td>
                  <td>{formatLocal(c.created_at)}</td>
                  <td>
                    <button className="btn danger" onClick={() => remove(c.id)}>Удалить</button>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={5} style={{textAlign:"center", padding:20, color:"var(--muted)"}}>
                    Пока нет компаний
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {modal && (
        <div className="modal">
          <div className="card modal-card">
            <h2 className="text-xl" style={{fontWeight:700, marginBottom:8}}>Создать компанию</h2>
            <div style={{display:"grid", gap:10}}>
              <input className="field" placeholder="Название" value={name} onChange={e=>setName(e.target.value)} />
              <textarea className="field" placeholder="Описание" rows={4} value={description} onChange={e=>setDescription(e.target.value)} />
              <div style={{display:"flex", gap:8, justifyContent:"flex-end"}}>
                <button className="btn ghost" onClick={()=>setModal(false)}>Отмена</button>
                <button className="btn dark" onClick={create}>Создать</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
