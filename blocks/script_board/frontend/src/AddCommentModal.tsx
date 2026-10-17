import { useState, useRef, useEffect } from "react";

interface AddCommentModalProps {
  x: number;
  y: number;
  onSave: (text: string) => void;
  onClose: () => void;
}

export default function AddCommentModal({ onSave, onClose }: AddCommentModalProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleSave = () => {
    const t = text.trim();
    if (t) onSave(t);
    onClose();
  };

  return (
    <div className="modal-overlay nowheel" onClick={onClose} role="presentation">
      <div
        className="modal comment-modal comment-modal--add"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Добавить комментарий"
      >
        <div className="modal__header">
          <span className="modal__title">Новый комментарий</span>
          <button type="button" className="modal__close" onClick={onClose} aria-label="Закрыть">
            ×
          </button>
        </div>
        <div className="modal__body">
          <textarea
            ref={textareaRef}
            className="comment-modal__input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Введите комментарий…"
            rows={4}
          />
        </div>
        <div className="modal__footer">
          <button type="button" className="modal__btn modal__btn--primary" onClick={handleSave}>
            Сохранить
          </button>
          <button type="button" className="modal__btn" onClick={onClose}>
            Отмена
          </button>
        </div>
      </div>
    </div>
  );
}
