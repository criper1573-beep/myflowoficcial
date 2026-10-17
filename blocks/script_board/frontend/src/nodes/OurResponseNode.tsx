import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { CardData } from "../types";

const firstLine = (t: string) => (t || "").trim().split("\n")[0] || "Без текста";

function authorLabel(data: CardData): string {
  const value = data["author"];
  return typeof value === "string" ? value.trim() : "";
}

function OurResponseNode({ id, data }: NodeProps) {
  const d = data as CardData;
  const title = d.title || "Наш ответ";
  const preview = firstLine(d.text);
  const author = authorLabel(d);

  return (
    <div className="script-card script-card--our">
      <Handle type="target" position={Position.Top} />
      <div className="script-card__top">
        <span className="script-card__kind">
          <i className="script-card__mark" aria-hidden />
          <input
            type="text"
            className="script-card__header-input nodrag"
            value={title}
            onChange={(e) => d.onTitleChange?.(id, e.target.value)}
            onClick={(e) => e.stopPropagation()}
            placeholder="Название"
          />
        </span>
        {author ? (
          <span className="script-card__who">
            <span className="script-card__badge">{author}</span>
          </span>
        ) : null}
      </div>
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
          Текст
        </button>
        <button
          type="button"
          className="script-card__btn"
          onClick={() => d.onCopy?.(id)}
          title="Копировать текст"
        >
          Копия
        </button>
        <button
          type="button"
          className="script-card__btn"
          onClick={() => d.onDuplicate?.(id)}
          title="Дублировать карточку (Alt+D)"
        >
          Дубль
        </button>
        <button
          type="button"
          className="script-card__btn script-card__btn--delete"
          onClick={() => d.onDelete?.(id)}
          title="Удалить карточку (Delete)"
        >
          Удалить
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
