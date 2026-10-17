const NYAN_GIF =
  "https://assets.codepen.io/16327/nyan_cat.gif";

interface ImproveTextModalProps {
  open: boolean;
  loading: boolean;
  resultText: string | null;
  error: string | null;
  onUseResult: (text: string) => void;
  onClose: () => void;
}

export default function ImproveTextModal({
  open,
  loading,
  resultText,
  error,
  onUseResult,
  onClose,
}: ImproveTextModalProps) {
  if (!open) return null;

  return (
    <div className="modal-overlay modal-overlay--top" onClick={onClose}>
      <div
        className="modal modal--improve"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal__header">
          <span>Улучшить текст</span>
          <button type="button" className="modal__close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="modal__body">
          {loading && (
            <>
              <p className="improve-loading__text">Идёт генерация</p>
              <img
                src={NYAN_GIF}
                alt=""
                className="improve-loading__gif"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                  const fallback = (e.target as HTMLImageElement).nextElementSibling;
                  if (fallback) (fallback as HTMLElement).classList.remove("hidden");
                }}
              />
              <div className="improve-loading__fallback hidden">🐱 ✨</div>
            </>
          )}
          {!loading && error && (
            <p className="improve-error">{error}</p>
          )}
          {!loading && resultText !== null && !error && (
            <>
              <label className="modal__label">Новый вариант текста</label>
              <textarea
                className="modal__textarea"
                value={resultText}
                readOnly
                rows={12}
              />
              <div className="modal__footer">
                <button type="button" onClick={onClose}>
                  Отмена
                </button>
                <button
                  type="button"
                  className="modal__btn-primary"
                  onClick={() => onUseResult(resultText)}
                >
                  Использовать этот вариант
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
