interface DescriptionPanelProps {
  open: boolean;
  value: string;
  onChange: (value: string) => void;
  onClose: () => void;
}

export function DescriptionPanel({ open, value, onChange, onClose }: DescriptionPanelProps) {
  return (
    <aside className={`side-panel side-panel--desc${open ? " is-open" : ""}`} aria-hidden={!open}>
      <span className="sheet-handle" aria-hidden="true" />
      <div className="panel-head">
        <h2>Описание</h2>
        <button type="button" className="panel-close" onClick={onClose} aria-label="Свернуть описание">
          ×
        </button>
      </div>
      <textarea
        className="desc-input"
        value={value}
        placeholder="О чём скрипт, тон, ограничения"
        aria-label="Описание проекта"
        onChange={(event) => onChange(event.target.value)}
      />
    </aside>
  );
}
