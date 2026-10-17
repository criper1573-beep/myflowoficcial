import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { useEffect, useRef } from "react";
import { useBoardActions } from "./BoardContext";
import { cardRole, readCardText } from "./scriptModel";

function AuthorBadge({ author, edited }: { author: string; edited: boolean }) {
  const tone = author === "Алексей" ? "human" : "bot";
  return (
    <span className="card-author">
      <span className={`badge badge--${tone}`}>{author}</span>
      {edited ? <span className="edited-mark">изменено</span> : null}
    </span>
  );
}

export function ScriptCard({ id, data, type, selected }: NodeProps<Node>) {
  const role = cardRole({ type, data });
  const actions = useBoardActions();
  const meta = actions.metaFor(id);
  const text = readCardText(data);
  const areaRef = useRef<HTMLTextAreaElement>(null);
  const answer = role === "answer";
  const busy = actions.pendingId === id;

  useEffect(() => {
    const area = areaRef.current;
    if (!area) return;
    area.style.height = "0px";
    area.style.height = `${Math.min(area.scrollHeight, 160)}px`;
  }, [text]);

  return (
    <article className={`script-card script-card--${role}${selected ? " is-selected" : ""}`}>
      <Handle type="target" position={Position.Left} />
      <div className="card-top">
        <span className="card-kind">
          <span className="kind-mark" aria-hidden="true" />
          {answer ? "Наш ответ" : "Сообщение клиента"}
        </span>
        <AuthorBadge author={meta.author} edited={meta.edited} />
      </div>
      <textarea
        ref={areaRef}
        className="card-text nodrag nopan"
        value={text}
        placeholder={answer ? "Текст ответа" : "Текст сообщения"}
        aria-label={answer ? "Текст ответа" : "Текст сообщения клиента"}
        onChange={(event) => actions.onText(id, event.target.value)}
      />
      <div className="card-actions">
        {answer ? (
          <>
            <button
              type="button"
              className="card-btn nodrag nopan"
              disabled={busy}
              onClick={() => actions.onGenerate(id)}
            >
              {busy ? "…" : "Сгенерировать ответ"}
            </button>
            <button
              type="button"
              className="card-btn nodrag nopan"
              disabled={busy || !text.trim()}
              onClick={() => actions.onImprove(id)}
            >
              Улучшить текст
            </button>
          </>
        ) : null}
        <button
          type="button"
          className="card-btn nodrag nopan"
          disabled={!text.trim()}
          onClick={() => actions.onCopy(text)}
        >
          Копировать
        </button>
      </div>
      {actions.error?.id === id ? <p className="card-error">{actions.error.message}</p> : null}
      <Handle type="source" position={Position.Right} />
    </article>
  );
}

export const nodeTypes = {
  client: ScriptCard,
  clientMessage: ScriptCard,
  message: ScriptCard,
  incoming: ScriptCard,
  answer: ScriptCard,
  reply: ScriptCard,
  ourAnswer: ScriptCard,
  our_answer: ScriptCard,
  response: ScriptCard,
  outgoing: ScriptCard,
  assistant: ScriptCard,
  default: ScriptCard,
};
