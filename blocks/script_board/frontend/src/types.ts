/** Единый файл типов доски и истории. Панель «История» импортирует их отсюда. */

export type CardType = "client" | "our_response";

export interface CardData {
  title: string;
  text: string;
  [key: string]: unknown;
}

export interface ScriptNode {
  id: string;
  type: CardType;
  position: { x: number; y: number };
  data: CardData;
  revision: number;
  selected?: boolean;
  dragging?: boolean;
  width?: number;
  height?: number;
  measured?: { width?: number; height?: number };
  style?: Record<string, unknown>;
  className?: string;
  parentId?: string;
}

export interface ScriptEdge {
  id: string;
  source: string;
  target: string;
  selected?: boolean;
  sourceHandle?: string | null;
  targetHandle?: string | null;
}

export interface BoardComment {
  id: string;
  x: number;
  y: number;
  text: string;
}

export interface Project {
  id?: string;
  name: string;
  scriptDescription: string;
  nodes: ScriptNode[];
  edges: ScriptEdge[];
  comments: BoardComment[];
  revision: number;
  archived?: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface ProjectListItem {
  id: string;
  name: string;
  revision: number;
  archived?: boolean;
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
  | "comment.delete";

export interface HistoryEvent {
  id: string;
  ts: string;
  author: string;
  type: HistoryEventType;
  cardId: string | null;
  edgeId: string | null;
  commentId: string | null;
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
  /** Период опроса в миллисекундах. 0 или отсутствие — один запрос. */
  pollMs?: number;
}

export interface CardWrite {
  projectRevision: number;
  id?: string;
  type: CardType;
  position: { x: number; y: number };
  data?: Partial<CardData>;
}

export interface CardPatch {
  revision: number;
  type?: CardType;
  position?: { x: number; y: number };
  data?: Partial<CardData>;
}

export interface MutationRevision {
  projectRevision: number;
}

export interface CardMutation extends MutationRevision {
  node: ScriptNode;
}

export interface EdgeMutation extends MutationRevision {
  edge: ScriptEdge;
}

export interface CommentMutation extends MutationRevision {
  comment: BoardComment;
}

export interface ReplaceResult {
  success: true;
  revision: number;
  project: Project;
}
