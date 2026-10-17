import { createContext, useContext } from "react";
import type { CardMeta } from "./cardMeta";

export interface CardError {
  id: string;
  message: string;
}

export interface BoardActions {
  metaFor: (cardId: string) => CardMeta;
  pendingId: string | null;
  error: CardError | null;
  onText: (id: string, text: string) => void;
  onCopy: (text: string) => void;
  onGenerate: (id: string) => void;
  onImprove: (id: string) => void;
}

const BoardContext = createContext<BoardActions | null>(null);

export const BoardProvider = BoardContext.Provider;

export function useBoardActions(): BoardActions {
  const value = useContext(BoardContext);
  if (!value) throw new Error("Карточка вне доски");
  return value;
}
