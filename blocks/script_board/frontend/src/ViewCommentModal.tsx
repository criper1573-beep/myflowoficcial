interface ViewCommentModalProps {
  text: string;
  onResolve: () => void;
  onClose: () => void;
}

export default function ViewCommentModal({ text, onResolve, onClose }: ViewCommentModalProps) {
  const handleResolve = () => {
    onResolve();
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="presentation">
      <div
        className="modal comment-modal comment-modal--view"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Комментарий"
      >
        <div className="modal__header">
          <span className="modal__title">Комментарий</span>
          <button type="button" className="modal__close" onClick={onClose} aria-label="Закрыть">
            ×
          </button>
        </div>
        <div className="modal__body">
          <div className="comment-modal__text">{text || "(пусто)"}</div>
        </div>
        <div className="modal__footer">
          <button
            type="button"
            className="modal__btn modal__btn--resolve"
            onClick={handleResolve}
          >
            Проблема решена
          </button>
          <button type="button" className="modal__btn" onClick={onClose}>
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
}
