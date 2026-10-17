import { useState, useEffect } from "react";

interface TextEditorModalProps {
  nodeId: string | null;
  nodes: Array<{ id: string; data?: { title?: string; text?: string } }>;
  onSave: (nodeId: string, text: string, title: string) => void;
  onClose: () => void;
}

export default function TextEditorModal({
  nodeId,
  nodes,
  onSave,
  onClose,
}: TextEditorModalProps) {
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");

  const node = nodeId ? nodes.find((n) => n.id === nodeId) : null;

  useEffect(() => {
    if (node) {
      setTitle((node.data?.title as string) ?? "");
      setText((node.data?.text as string) ?? "");
    } else {
      setTitle("");
      setText("");
    }
  }, [node]);

  if (!nodeId || !node) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal--text" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <span>Редактировать карточку</span>
          <button type="button" className="modal__close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="modal__body">
          <label className="modal__label">Название</label>
          <input
            type="text"
            className="modal__input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Название карточки"
          />
          <label className="modal__label">Текст</label>
          <textarea
            className="modal__textarea"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Текст скрипта…"
            rows={12}
          />
        </div>
        <div className="modal__footer">
          <button type="button" onClick={onClose}>
            Отмена
          </button>
          <button type="button" onClick={() => onSave(nodeId, text, title)}>
            Сохранить
          </button>
        </div>
      </div>
    </div>
  );
}
