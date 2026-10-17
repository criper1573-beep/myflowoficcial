import type { HistoryItem } from "./useHistory";

interface HistoryPanelProps {
  open: boolean;
  items: HistoryItem[];
  loading: boolean;
  onClose: () => void;
}

const moscowDate = new Intl.DateTimeFormat("ru-RU", {
  timeZone: "Europe/Moscow",
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

const moscowTime = new Intl.DateTimeFormat("ru-RU", {
  timeZone: "Europe/Moscow",
  hour: "2-digit",
  minute: "2-digit",
});

function formatWhen(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return `${moscowDate.format(date)} ${moscowTime.format(date)}`;
}

export function HistoryPanel({ open, items, loading, onClose }: HistoryPanelProps) {
  return (
    <aside className={`side-panel side-panel--history${open ? " is-open" : ""}`} aria-hidden={!open}>
      <span className="sheet-handle" aria-hidden="true" />
      <div className="panel-head">
        <h2>История изменений</h2>
        <button type="button" className="panel-close" onClick={onClose} aria-label="Свернуть историю">
          ×
        </button>
      </div>
      {loading ? (
        <p className="history-empty">Загрузка…</p>
      ) : items.length === 0 ? (
        <p className="history-empty">Пока нет записей</p>
      ) : (
        <ol className="history-list">
          {items.map((item) => (
            <li key={item.id} className="history-item">
              <div className="history-item__meta">
                <time dateTime={item.at}>{formatWhen(item.at)}</time>
                <span className={`badge ${item.author === "Алексей" ? "badge--human" : "badge--bot"}`}>
                  {item.author}
                </span>
              </div>
              <p className="history-item__summary">{item.action}</p>
            </li>
          ))}
        </ol>
      )}
    </aside>
  );
}
