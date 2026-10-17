import { createContext, useContext } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";

import type { CardData, CardType } from "./types";

export interface BoardActions {
  updateCardData: (id: string, patch: Partial<CardData>) => void;
}

export const BoardContext = createContext<BoardActions>({
  updateCardData: () => undefined,
});

export function CardNode({ id, data, type }: NodeProps) {
  const actions = useContext(BoardContext);
  const cardType: CardType = type === "our_response" ? "our_response" : "client";
  const card = data as unknown as CardData;

  return (
    <article className={`card card--${cardType}`}>
      <Handle type="target" position={Position.Top} />
      <header className="card__kind">{cardType === "client" ? "Клиент" : "Наш ответ"}</header>
      <input
        className="card__title nodrag nopan"
        value={card.title ?? ""}
        placeholder="Заголовок"
        onChange={(event) => actions.updateCardData(id, { title: event.target.value })}
      />
      <textarea
        className="card__text nodrag nopan nowheel"
        value={card.text ?? ""}
        placeholder="Текст реплики"
        rows={4}
        onChange={(event) => actions.updateCardData(id, { text: event.target.value })}
      />
      <Handle type="source" position={Position.Bottom} />
    </article>
  );
}
