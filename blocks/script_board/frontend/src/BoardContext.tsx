import { createContext, useContext } from "react";
import type { CardMeta } from "./cardMeta";

export interface BoardActions {
  metaFor: (cardId: string) => CardMeta;
  onText: (id: string, text: string) => void;
  onCopy: (text: string) => void;
}

const BoardContext = createContext<BoardActions | null>(null);

export const BoardProvider = BoardContext.Provider;

export function useBoardActions(): BoardActions {
  const value = useContext(BoardContext);
  if (!value) throw new Error("Карточка вне доски");
  return value;
}
