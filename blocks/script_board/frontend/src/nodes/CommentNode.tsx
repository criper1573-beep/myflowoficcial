import { memo, useState } from "react";
import type { NodeProps } from "@xyflow/react";

export interface CommentNodeData {
  text?: string;
  onOpen?: (commentId: string) => void;
}

function CommentNode({ id, data }: NodeProps) {
  const d = (data ?? {}) as CommentNodeData;
  const [hover, setHover] = useState(false);
  const text = (d.text ?? "").trim() || "(пусто)";

  return (
    <div
      className="comment-marker-wrap"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {hover && (
        <div className="comment-marker-tooltip" role="tooltip">
          <div className="comment-marker-tooltip__text">{text}</div>
          <span className="comment-marker-tooltip__hint">Иконка — открыть; полоска — перетащить</span>
        </div>
      )}
      {/* Ручка перетаскивания — перетаскивание только отсюда */}
      <div className="comment-marker-drag-handle" title="Перетащить" aria-hidden>
        <span className="comment-marker-drag-handle__grip">⋮⋮</span>
      </div>
      {/* Иконка — только клик для открытия окна (nodrag, чтобы не конкурировать с панорамой) */}
      <button
        type="button"
        className="comment-marker nodrag"
        onClick={(e) => {
          e.stopPropagation();
          e.preventDefault();
          d.onOpen?.(id);
        }}
        onPointerDown={(e) => e.stopPropagation()}
        aria-label="Открыть комментарий"
      >
        <span className="comment-marker__icon" aria-hidden>✉</span>
      </button>
    </div>
  );
}

export default memo(CommentNode);
