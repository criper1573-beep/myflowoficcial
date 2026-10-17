export type CardNodeType = "client" | "our_response";

export interface CardData extends Record<string, unknown> {
  title: string;
  text: string;
  revision?: number;
  onOpenTextEditor?: (nodeId: string) => void;
  onCopy?: (nodeId: string) => void;
  onDuplicate?: (nodeId: string) => void;
  onTitleChange?: (nodeId: string, title: string) => void;
  onAddChild?: (nodeId: string, type: "client" | "our_response") => void;
  onDelete?: (nodeId: string) => void;
}

export type HistoryEventType =
  | "project.create"
  | "project.rename"
  | "project.description"
  | "project.archive"
  | "project.restore"
  | "card.create"
  | "card.update"
  | "card.delete"
  | "edge.create"
  | "edge.update"
  | "edge.delete"
  | "comment.create"
  | "comment.update"
  | "comment.delete"
  | "goal.create"
  | "goal.update"
  | "goal.delete"
  | "goal.reorder";

export interface Goal {
  id: string;
  text: string;
  note?: string;
  order: number;
  revision: number;
}

export interface HistoryEvent {
  id: string;
  ts: string;
  author: string;
  type: HistoryEventType;
  cardId: string | null;
  edgeId: string | null;
  commentId: string | null;
  goalId?: string | null;
  before: unknown;
  after: unknown;
  revision: number;
}

export interface HistoryResponse {
  projectId: string;
  revision: number;
  events: HistoryEvent[];
}

export interface HistoryQuery {
  since?: string;
  author?: string;
  excludeAuthor?: string;
  pollMs?: number;
}
