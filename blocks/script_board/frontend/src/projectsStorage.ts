import type { Node, Edge } from "@xyflow/react";
import type { CardData, Goal } from "./types";
import { ApiError, request } from "./api";

const CURRENT_KEY = "script_board_current";

export interface ProjectData {
  name: string;
  nodes: Array<{
    id: string;
    type?: string;
    position?: { x: number; y: number };
    data?: { title?: string; text?: string };
  }>;
  edges: Edge[];
  scriptDescription: string;
  comments?: CommentItem[];
  revision?: number;
}

export interface CommentItem {
  id: string;
  x: number;
  y: number;
  text: string;
}

export interface LoadedProject {
  nodes: Node<CardData>[];
  edges: Edge[];
  scriptDescription: string;
  name: string;
  comments: CommentItem[];
  goals: Goal[];
  revision: number;
}

interface PendingSave {
  id: string;
  name: string;
  nodes: Node<CardData>[];
  edges: Edge[];
  scriptDescription: string;
  comments: CommentItem[];
  revision: number;
  generation: number;
}

let pendingSave: PendingSave | null = null;
let saveGeneration = 0;

export function getCurrentProjectId(): string | null {
  return localStorage.getItem(CURRENT_KEY);
}

export function setCurrentProjectId(id: string) {
  localStorage.setItem(CURRENT_KEY, id);
}

export function hasPendingSave(): boolean {
  return pendingSave !== null;
}

function toPayload(
  name: string,
  nodes: Node<CardData>[],
  edges: Edge[],
  scriptDescription: string,
  comments: CommentItem[],
  revision: number,
) {
  return {
    name,
    revision,
    nodes: nodes.map((node) => ({
      id: node.id,
      type: node.type,
      position: node.position,
      data: { title: node.data?.title, text: node.data?.text },
      revision: typeof node.data?.revision === "number" ? node.data.revision : undefined,
    })),
    edges,
    scriptDescription,
    comments,
  };
}

function mapProject(project: {
  name?: string;
  nodes?: Array<{
    id: string;
    type?: string;
    position?: { x: number; y: number };
    data?: { title?: string; text?: string };
    revision?: number;
  }>;
  edges?: Edge[];
  scriptDescription?: string;
  comments?: CommentItem[];
  goals?: Goal[];
  revision?: number;
}): LoadedProject {
  const nodes: Node<CardData>[] = (project.nodes ?? []).map((node) => ({
    id: node.id,
    type: (node.type === "our_response" ? "our_response" : "client") as "client" | "our_response",
    position: node.position ?? { x: 0, y: 0 },
    data: {
      title: node.data?.title ?? "",
      text: node.data?.text ?? "",
      revision: node.revision,
    } as CardData,
  }));
  return {
    nodes,
    edges: project.edges ?? [],
    scriptDescription: project.scriptDescription ?? "",
    name: project.name ?? "Без названия",
    comments: project.comments ?? [],
    goals: [...(project.goals ?? [])].sort((a, b) => a.order - b.order),
    revision: project.revision ?? 0,
  };
}

/** Список проектов с сервера. При ошибке сети не подменяем его localStorage. */
export async function listProjects(): Promise<{ id: string; name: string; revision?: number }[]> {
  return request("/api/projects");
}

/** Загрузить проект с сервера. */
export async function loadProject(id: string): Promise<LoadedProject | null> {
  try {
    const project = await request<Parameters<typeof mapProject>[0]>(`/api/projects/${encodeURIComponent(id)}`);
    return mapProject(project);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

/**
 * Сохранить проект. Ревизия обязательна.
 * Если сервер недоступен, тело остаётся в памяти и уходит повторно с той же ревизией.
 * В localStorage проект не пишется: иначе следующий успешный заход затёр бы сервер.
 */
export async function saveProject(
  id: string,
  name: string,
  nodes: Node<CardData>[],
  edges: Edge[],
  scriptDescription: string,
  comments: CommentItem[] = [],
  revision: number,
): Promise<{ revision: number }> {
  const generation = ++saveGeneration;
  const payload = toPayload(name, nodes, edges, scriptDescription, comments, revision);
  try {
    const result = await request<{ success: boolean; revision: number }>(`/api/projects/${encodeURIComponent(id)}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    if (generation === saveGeneration) pendingSave = null;
    return { revision: result.revision };
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      if (generation === saveGeneration) pendingSave = null;
      throw error;
    }
    if (generation === saveGeneration) {
      pendingSave = { id, name, nodes, edges, scriptDescription, comments, revision, generation };
    }
    throw error;
  }
}

export async function retryPendingSave(): Promise<
  { status: "empty" } | { status: "saved"; revision: number } | { status: "conflict" } | { status: "error" }
> {
  const current = pendingSave;
  if (!current) return { status: "empty" };
  try {
    const result = await saveProject(
      current.id,
      current.name,
      current.nodes,
      current.edges,
      current.scriptDescription,
      current.comments,
      current.revision,
    );
    return { status: "saved", revision: result.revision };
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) return { status: "conflict" };
    return { status: "error" };
  }
}

/** Создать проект на сервере. Без сети id в localStorage не выдаём. */
export async function createProject(name: string): Promise<{ id: string; revision: number }> {
  return request("/api/projects", {
    method: "POST",
    body: JSON.stringify({ name: name.trim() || "Новый проект" }),
  });
}

export async function getProjectName(id: string): Promise<string> {
  const project = await request<{ name?: string }>(`/api/projects/${encodeURIComponent(id)}`);
  return project.name ?? "Без названия";
}
