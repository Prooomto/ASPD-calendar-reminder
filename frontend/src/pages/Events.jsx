import { useEffect, useState } from "react";
import { addDays, formatISO } from "date-fns";
import {
  listEvents,
  createEvent,
  deleteEvent,
  startTelegramLink,
  getEvent,
  updateEvent,
  listReminders,
  telegramLinkStatus,
  getMe,
  apiListCompanies,            // ⬅️ добавили импорт
} from "../api";
import { formatLocal } from "../helpers/date";

// ISO/UTC -> значение для <input type="datetime-local">
function toInputLocalValue(isoLike) {
  const d = new Date(isoLike);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export default function Events() {
  // шапка
  const [me, setMe] = useState(null);
  // статус Telegram
  const [tg, setTg] = useState({ linked: false, telegram_id: null });

  // данные
  const [events, setEvents] = useState([]);
  const [error, setError] = useState(null);

  // компании (новое)
  const [companies, setCompanies] = useState([]); // [{id, name, ...}]
  const [companyId, setCompanyId] = useState(""); // строка из <select>, конвертим в число при отправке

  // привязка TG
  const [linkInfo, setLinkInfo] = useState(null);
  const [linkErr, setLinkErr] = useState(null);

  // форма
  const [title, setTitle] = useState("");
  const [dt, setDt] = useState("");
  const [desc, setDesc] = useState("");
  const [recurrence, setRecurrence] = useState("");
  const [rem, setRem] = useState({ m5: false, m30: false, h1: false, d1: false });

  // редактирование
  const [editId, setEditId] = useState(null);
  const isEdit = editId !== null;

  // просмотр напоминаний
  const [openRemindersFor, setOpenRemindersFor] = useState(null);
  const [reminders, setReminders] = useState([]);

  useEffect(() => {
    document.title = "NotifyMe";
  }, []);

  useEffect(() => {
    // одна, аккуратная загрузка всего
    (async () => {
      setError(null);
      try {
        const [meResp, tgResp, companiesResp] = await Promise.all([
          getMe().catch(() => null),
          telegramLinkStatus().catch(() => ({ linked: false, telegram_id: null })),
          apiListCompanies().catch(() => []), // ⬅️ загрузили компании
        ]);
        if (meResp) setMe(meResp);
        setTg(tgResp || { linked: false, telegram_id: null });
        setCompanies(Array.isArray(companiesResp) ? companiesResp : []);

        const from = formatISO(new Date());
        const to = formatISO(addDays(new Date(), 7));
        const data = await listEvents({ from, to });
        setEvents(Array.isArray(data) ? data : []);
      } catch (e) {
        setError(e?.response?.data?.detail || "Ошибка загрузки");
      }
    })();
  }, []);

  async function refreshTgStatus() {
    try {
      const status = await telegramLinkStatus();
      setTg(status || { linked: false, telegram_id: null });
    } catch {
      setTg({ linked: false, telegram_id: null });
    }
  }

  function collectReminders() {
    const arr = [];
    if (rem.m5) arr.push(5);
    if (rem.m30) arr.push(30);
    if (rem.h1) arr.push(60);
    if (rem.d1) arr.push(24 * 60);
    return arr.length ? arr : null;
  }

  function resetForm() {
    setTitle("");
    setDt("");
    setDesc("");
    setRecurrence("");
    setRem({ m5: false, m30: false, h1: false, d1: false });
    setCompanyId(""); // ⬅️ сбрасываем выбор компании
    setEditId(null);
  }

  async function reloadEvents() {
    try {
      const from = formatISO(new Date());
      const to = formatISO(addDays(new Date(), 7));
      const data = await listEvents({ from, to });
      setEvents(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e?.response?.data?.detail || "Ошибка загрузки");
    }
  }

  async function addOrSave() {
    if (!title.trim() || !dt) return;
    const payload = {
      title: title.trim(),
      description: desc.trim() || null,
      start_time: new Date(dt).toISOString(), // сервер хранит в UTC
      recurrence: recurrence || null,
      reminders_minutes_before: collectReminders(),
      company_id: companyId ? Number(companyId) : null, // ⬅️ главное изменение
    };
    try {
      if (isEdit) await updateEvent(editId, payload);
      else await createEvent(payload);
      resetForm();
      reloadEvents();
    } catch (e) {
      alert(e?.response?.data?.detail || (isEdit ? "Не удалось сохранить событие" : "Не удалось создать событие"));
    }
  }

  async function onDelete(id) {
    if (!confirm("Удалить событие?")) return;
    try {
      await deleteEvent(id);
      if (editId === id) resetForm();
      reloadEvents();
    } catch (e) {
      alert(e?.response?.data?.detail || "Не удалось удалить событие");
    }
  }

  async function onEdit(id) {
    try {
      const ev = await getEvent(id);
      setEditId(id);
      setTitle(ev.title || "");
      setDesc(ev.description || "");
      setRecurrence(ev.recurrence || "");
      setDt(toInputLocalValue(ev.start_time));
      setCompanyId(ev.company_id ? String(ev.company_id) : ""); // ⬅️ подставляем выбранную компанию
      const mins = ev.reminders_minutes_before || [];
      setRem({
        m5: mins.includes(5),
        m30: mins.includes(30),
        h1: mins.includes(60),
        d1: mins.includes(24 * 60),
      });
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      alert(e?.response?.data?.detail || "Не удалось загрузить событие");
    }
  }

  async function toggleReminders(eventId) {
    if (openRemindersFor === eventId) {
      setOpenRemindersFor(null);
      setReminders([]);
      return;
    }
    try {
      const data = await listReminders(eventId);
      setReminders(Array.isArray(data) ? data : []);
      setOpenRemindersFor(eventId);
    } catch (e) {
      alert(e?.response?.data?.detail || "Не удалось получить напоминания");
    }
  }

  async function linkTelegram() {
    setLinkErr(null);
    try {
      const data = await startTelegramLink(); // { code, message }
      setLinkInfo(data);
    } catch (e) {
      setLinkErr(e?.response?.data?.detail || e?.message || "Не удалось получить код привязки");
    }
  }

  // вспомогательно: имя компании по id для списка событий
  function companyNameById(id) {
    const c = companies.find((x) => x.id === id);
    return c ? c.name : null;
  }

  return (
    <div className="wrap">
      <header className="topbar">
        <div className="brand">NotifyMe</div>
        <div className="userchip" title="Текущий пользователь">
          <span className="dot" />
          {me?.name || me?.email || "Пользователь"}
        </div>
      </header>

      <main>
        <h2>Мои события (7 дней)</h2>

        <section className="panel">
          <div className="panel-row">
            <b>Telegram</b>
            <span className={`badge ${tg.linked ? "ok" : "warn"}`} title={tg.telegram_id ? `ID: ${tg.telegram_id}` : ""}>
              {tg.linked ? "Привязан" : "Не привязан"}
            </span>
          </div>
          <div className="panel-row gap">
            <button onClick={linkTelegram}>Привязать Telegram</button>
            <button className="ghost" onClick={refreshTgStatus}>Проверить</button>
            {linkErr && <span className="error">{linkErr}</span>}
          </div>
          {linkInfo && (
            <div className="hint">
              Код: <code>{linkInfo.code}</code>
              <div className="muted">Открой бота и отправь: <code>/link {linkInfo.code}</code>, затем нажми «Проверить».</div>
            </div>
          )}
        </section>

        <section className="panel">
          <div className="grid2">
            <input
              placeholder={isEdit ? "Редактирование: заголовок" : "Заголовок"}
              value={title}
              onChange={e => setTitle(e.target.value)}
            />
            <input type="datetime-local" value={dt} onChange={e => setDt(e.target.value)} />
          </div>

          {/* выбор компании */}
          <div className="form-row">
            <label>Компания:</label>
            <select value={companyId} onChange={(e)=>setCompanyId(e.target.value)}>
              <option value="">(личное событие)</option>
              {companies.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <textarea
            placeholder="Описание (необязательно)"
            value={desc}
            onChange={e => setDesc(e.target.value)}
            rows={4}
          />

          <div className="form-row">
            <label>Повтор:</label>
            <select value={recurrence} onChange={e => setRecurrence(e.target.value)}>
              <option value="">Нет</option>
              <option value="DAILY">Ежедневно</option>
              <option value="WEEKLY">Еженедельно</option>
              <option value="MONTHLY">Ежемесячно</option>
            </select>

            <span className="spacer" />
            <span>Напомнить за:</span>
            <label><input type="checkbox" checked={rem.m5} onChange={e => setRem({ ...rem, m5: e.target.checked })} /> 5 мин</label>
            <label><input type="checkbox" checked={rem.m30} onChange={e => setRem({ ...rem, m30: e.target.checked })} /> 30 мин</label>
            <label><input type="checkbox" checked={rem.h1} onChange={e => setRem({ ...rem, h1: e.target.checked })} /> 1 час</label>
            <label><input type="checkbox" checked={rem.d1} onChange={e => setRem({ ...rem, d1: e.target.checked })} /> 1 день</label>

            <span className="spacer" />
            <button onClick={addOrSave}>{isEdit ? "Сохранить" : "Добавить"}</button>
            {isEdit ? <button className="ghost" onClick={resetForm}>Отмена</button> : <button className="ghost" onClick={reloadEvents}>Обновить</button>}
          </div>
        </section>

        {error && <div className="error">{error}</div>}

        <ul className="list">
          {events.map(ev => (
            <li key={ev.id} className="item">
              <div className="item-main">
                <div className="item-title">
                  {ev.title}
                  {ev.company_id ? (
                    <span className="badge" style={{ marginLeft: 8 }}>
                      {companyNameById(ev.company_id) || `company #${ev.company_id}`}
                    </span>
                  ) : null}
                </div>
                <div className="item-sub">
                  {formatLocal(ev.start_time)}
                  {ev.description ? " — " + ev.description : ""}
                  {ev.recurrence ? ` — [${ev.recurrence}]` : ""}
                </div>

                {openRemindersFor === ev.id && (
                  <div className="reminders">
                    <div className="muted">Напоминания:</div>
                    {reminders.length === 0 ? (
                      <div>Нет записей</div>
                    ) : (
                      <ul>
                        {reminders.map(r => (
                          <li key={r.id}>{formatLocal(r.remind_at)} {r.sent ? "✓" : ""}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>

              <div className="item-actions">
                <button className="ghost" onClick={() => onEdit(ev.id)}>Редактировать</button>
                <button className="ghost" onClick={() => toggleReminders(ev.id)}>Напоминания</button>
                <button className="danger" onClick={() => onDelete(ev.id)}>Удалить</button>
              </div>
            </li>
          ))}
          {events.length === 0 && <li className="muted">Пока пусто</li>}
        </ul>
      </main>
    </div>
  );
}
