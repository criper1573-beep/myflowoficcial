interface SettingsModalProps {
  open: boolean;
  scriptDescription: string;
  onScriptDescriptionChange: (value: string) => void;
  onClose: () => void;
}

export default function SettingsModal({
  open,
  scriptDescription,
  onScriptDescriptionChange,
  onClose,
}: SettingsModalProps) {
  if (!open) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal--settings" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <span className="modal__title">Настройки скрипта</span>
          <button type="button" className="modal__close" onClick={onClose} aria-label="Закрыть">
            ×
          </button>
        </div>
        <div className="modal__body">
          <label className="modal__label">
            Описание проекта / скрипта (контекст для Сони)
          </label>
          <textarea
            className="modal__textarea"
            value={scriptDescription}
            onChange={(e) => onScriptDescriptionChange(e.target.value)}
            placeholder="Например: скрипт поддержки интернет-магазина, тон вежливый…"
            rows={6}
          />
        </div>
        <div className="modal__footer">
          <button type="button" onClick={onClose}>
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
}
