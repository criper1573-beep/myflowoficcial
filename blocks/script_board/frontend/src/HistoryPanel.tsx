import { formatHistoryTime, type HistoryEntry } from "./history";

interface HistoryPanelProps {
  open: boolean;
  entries: HistoryEntry[];
  onClose: () => void;
}

export function HistoryPanel({ open, entries, onClose }: HistoryPanelProps) {
  return (
    <aside className={`side-panel side-panel--history${open ? " is-open" : ""}`} aria-hidden={!open}>
      <span className="sheet-handle" aria-hidden="true" />
      <div className="panel-head">
        <h2>История изменений</h2>
        <button type="button" className="panel-close" onClick={onClose} aria-label="Свернуть историю">
          ×
        </button>
      </div>
      {entries.length === 0 ? (
        <p className="history-empty">Пока нет записей</p>
      ) : (
        <ol className="history-list">
          {entries.map((entry) => (
            <li key={entry.id} className="history-item">
              <div className="history-item__meta">
                <time dateTime={entry.at}>{formatHistoryTime(entry.at)}</time>
                <span className={`badge ${entry.author === "Алексей" ? "badge--human" : "badge--bot"}`}>
                  {entry.author}
                </span>
              </div>
              <p className="history-item__summary">{entry.summary}</p>
            </li>
          ))}
        </ol>
      )}
    </aside>
  );
}
