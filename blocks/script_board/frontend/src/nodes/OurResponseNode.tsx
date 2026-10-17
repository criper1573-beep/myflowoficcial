import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { CardData } from "../types";

const firstLine = (t: string) => (t || "").trim().split("\n")[0] || "Без текста";

function OurResponseNode({ id, data }: NodeProps) {
  const d = data as CardData;
  const title = d.title || "Наш ответ";
  const preview = firstLine(d.text);
  const loading = d.generating ?? false;

  const handleGenerate = () => {
    if (loading || !d.onGenerate) return;
    d.onGenerate(id);
  };

  return (
    <div
      className="script-card script-card--our"
      style={{ width: 280 }}
    >
      <Handle type="target" position={Position.Top} />
      <input
        type="text"
        className="script-card__header-input nodrag"
        value={title}
        onChange={(e) => d.onTitleChange?.(id, e.target.value)}
        onClick={(e) => e.stopPropagation()}
        placeholder="Название"
      />
      <div
        className="script-card__preview script-card__preview--clickable nodrag"
        onClick={() => d.onOpenTextEditor?.(id)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && d.onOpenTextEditor?.(id)}
        title="Нажмите, чтобы открыть редактор текста"
      >
        {preview}
      </div>
      <div className="script-card__actions">
        <button
          type="button"
          className="script-card__btn"
          onClick={() => d.onOpenTextEditor?.(id)}
          title="Редактировать текст"
        >
          ✎
        </button>
        <button
          type="button"
          className="script-card__btn"
          onClick={() => d.onCopy?.(id)}
          title="Копировать текст"
        >
          ⎘
        </button>
        <button
          type="button"
          className="script-card__btn"
          onClick={() => d.onDuplicate?.(id)}
          title="Дублировать карточку (Alt+D)"
        >
          ⧉
        </button>
        <button
          type="button"
          className="script-card__btn script-card__btn--delete"
          onClick={() => d.onDelete?.(id)}
          title="Удалить карточку (Delete)"
        >
          🗑
        </button>
        <button
          type="button"
          className="script-card__btn script-card__btn--generate"
          onClick={handleGenerate}
          disabled={loading}
          title="Сгенерировать ответ по ветке"
        >
          {loading ? "…" : "◇"}
        </button>
      </div>
      <div className="script-card__add-buttons nodrag">
        <button
          type="button"
          className="script-card__add-btn"
          onClick={() => d.onAddChild?.(id, "client")}
          title="Добавить сообщение клиента со связью"
        >
          Сообщение
        </button>
        <button
          type="button"
          className="script-card__add-btn"
          onClick={() => d.onAddChild?.(id, "our_response")}
          title="Добавить наш ответ со связью"
        >
          Ответ
        </button>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

export default memo(OurResponseNode);
