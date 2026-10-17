import type { Edge, Node } from "@xyflow/react";

const TEXT_KEYS = ["text", "content", "body", "message", "label"] as const;
const ANSWER_TYPES = new Set([
  "answer",
  "reply",
  "ourAnswer",
  "our_answer",
  "response",
  "outgoing",
  "assistant",
]);

const EPHEMERAL = new Set(["selected", "dragging", "measured", "resizing", "positionAbsolute"]);

export interface ScriptLine {
  role: "client" | "answer";
  text: string;
}

export interface GraphPoint {
  id: string;
  type?: string | null;
  data?: unknown;
  position?: { x?: number; y?: number };
}

export interface GraphLink {
  source: string;
  target: string;
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export function readCardText(data: unknown): string {
  if (!isRecord(data)) return "";
  for (const key of TEXT_KEYS) {
    if (typeof data[key] === "string") return data[key];
  }
  return "";
}

export function writeCardText(data: unknown, text: string): Record<string, unknown> {
  const record = isRecord(data) ? { ...data } : {};
  const existing = TEXT_KEYS.find((key) => typeof record[key] === "string");
  record[existing ?? "text"] = text;
  return record;
}

export function cardRole(node: { type?: string | null; data?: unknown }): "client" | "answer" {
  const type = node.type ?? "";
  if (ANSWER_TYPES.has(type)) return "answer";
  if (isRecord(node.data)) {
    const kind = String(node.data.kind ?? node.data.role ?? node.data.cardType ?? "");
    if (ANSWER_TYPES.has(kind) || kind === "Наш ответ") return "answer";
  }
  const lower = type.toLowerCase();
  if (lower.includes("answer") || lower.includes("reply") || lower.includes("ответ")) return "answer";
  return "client";
}

export function toStoredRecord(entity: object): Record<string, unknown> {
  const stored: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(entity)) {
    if (EPHEMERAL.has(key)) continue;
    stored[key] = value;
  }
  return stored;
}

export function normalizeNodes(raw: unknown[]): Node[] {
  const nodes: Node[] = [];
  raw.forEach((item, index) => {
    if (!isRecord(item)) return;
    const id = typeof item.id === "string" && item.id ? item.id : `n-${index}`;
    const position = isRecord(item.position)
      ? { x: Number(item.position.x) || 0, y: Number(item.position.y) || 0 }
      : { x: 48 + (index % 4) * 40, y: 48 + index * 24 };
    const data = isRecord(item.data) ? item.data : {};
    const type = typeof item.type === "string" && item.type
      ? item.type
      : cardRole({ type: "", data });
    const { selected, dragging, measured, resizing, positionAbsolute, ...rest } = item;
    void selected;
    void dragging;
    void measured;
    void resizing;
    void positionAbsolute;
    nodes.push({ ...rest, id, position, data, type } as Node);
  });
  return nodes;
}

export function normalizeEdges(raw: unknown[]): Edge[] {
  const edges: Edge[] = [];
  raw.forEach((item, index) => {
    if (!isRecord(item)) return;
    if (typeof item.source !== "string" || typeof item.target !== "string") return;
    const id = typeof item.id === "string" && item.id ? item.id : `e-${index}`;
    const { selected, ...rest } = item;
    void selected;
    edges.push({ ...rest, id, source: item.source, target: item.target } as Edge);
  });
  return edges;
}

function yOf(node: GraphPoint | undefined): number {
  return node?.position?.y ?? 0;
}

export function linearizeScript(nodes: GraphPoint[], edges: GraphLink[]): ScriptLine[] {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const incoming = new Set(edges.map((edge) => edge.target));
  const children = new Map<string, string[]>();
  for (const edge of edges) {
    const list = children.get(edge.source) ?? [];
    list.push(edge.target);
    children.set(edge.source, list);
  }
  for (const list of children.values()) {
    list.sort((a, b) => yOf(byId.get(a)) - yOf(byId.get(b)));
  }
  const roots = nodes
    .filter((node) => !incoming.has(node.id))
    .sort((a, b) => yOf(a) - yOf(b));
  const lines: ScriptLine[] = [];
  const seen = new Set<string>();

  const visit = (id: string) => {
    if (seen.has(id)) return;
    seen.add(id);
    const node = byId.get(id);
    if (!node) return;
    lines.push({ role: cardRole(node), text: readCardText(node.data) });
    for (const child of children.get(id) ?? []) visit(child);
  };

  for (const root of roots) visit(root.id);
  for (const node of nodes) visit(node.id);
  return lines;
}

/** Цепочка от корня до карточки — контекст для генерации ответа в этой ветке. */
export function chainTo(nodeId: string, nodes: GraphPoint[], edges: GraphLink[]): ScriptLine[] {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const parents = new Map<string, string[]>();
  for (const edge of edges) {
    const list = parents.get(edge.target) ?? [];
    list.push(edge.source);
    parents.set(edge.target, list);
  }
  const path: string[] = [];
  const seen = new Set<string>();
  let current: string | undefined = nodeId;
  while (current && !seen.has(current)) {
    seen.add(current);
    path.push(current);
    const options = (parents.get(current) ?? []).slice().sort((a, b) => yOf(byId.get(a)) - yOf(byId.get(b)));
    current = options[0];
  }
  path.reverse();
  return path.flatMap((id) => {
    const node = byId.get(id);
    if (!node) return [];
    return [{ role: cardRole(node), text: readCardText(node.data) }];
  });
}

export function formatDialogue(lines: ScriptLine[]): string {
  return lines
    .filter((line) => line.text.trim())
    .map((line) => `${line.role === "client" ? "Клиент" : "Мы"}: ${line.text.trim()}`)
    .join("\n");
}
