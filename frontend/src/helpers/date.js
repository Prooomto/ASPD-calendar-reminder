// helpers/date.js
export function formatLocal(ts) {
  // ts может быть Date или ISO-строкой
  const hasTZ = typeof ts === "string" && /[zZ]|[+-]\d{2}:?\d{2}$/.test(ts);
  const d = ts instanceof Date ? ts : new Date(hasTZ ? ts : ts + "Z"); // трактуем без зоны как UTC

  try {
    // нормальный путь: современные браузеры
    return d.toLocaleString(undefined, {
      dateStyle: "short",
      timeStyle: "short",
      timeZoneName: "short",
    });
  } catch {
    // фолбэк для старых движков (где нет dateStyle/timeStyle)
    const fmt = new Intl.DateTimeFormat(undefined, {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
    return fmt.format(d);
  }
}
