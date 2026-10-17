import type { Node } from "@xyflow/react";
import type { CardData } from "./types";
import type { Edge } from "@xyflow/react";

const PROJECTS_KEY = "script_board_projects";
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
}

// --- Только текущий проект в localStorage (какой проект открыт на этом устройстве) ---
export function getCurrentProjectId(): string | null {
  return localStorage.getItem(CURRENT_KEY);
}

export function setCurrentProjectId(id: string) {
  localStorage.setItem(CURRENT_KEY, id);
}

// --- Серверное хранилище (API) ---

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || `HTTP ${res.status}`);
  }
  return res.json();
}

/** Список проектов с сервера. */
export async function listProjects(): Promise<{ id: string; name: string }[]> {
  try {
    return await api<{ id: string; name: string }[]>("/api/projects");
  } catch {
    return listProjectsFromStorage();
  }
}

export interface CommentItem {
  id: string;
  x: number;
  y: number;
  text: string;
}

/** Загрузить проект с сервера. */
export async function loadProject(
  id: string,
): Promise<{ nodes: Node<CardData>[]; edges: Edge[]; scriptDescription: string; name: string; comments: CommentItem[] } | null> {
  try {
    const p = await api<{
      name?: string;
      nodes?: Array<{ id: string; type?: string; position?: { x: number; y: number }; data?: { title?: string; text?: string } }>;
      edges?: Edge[];
      scriptDescription?: string;
      comments?: CommentItem[];
    }>(`/api/projects/${encodeURIComponent(id)}`);
    const nodes: Node<CardData>[] = (p.nodes ?? []).map((n) => ({
      id: n.id,
      type: (n.type === "our_response" ? "our_response" : "client") as "client" | "our_response",
      position: n.position ?? { x: 0, y: 0 },
      data: { title: n.data?.title ?? "", text: n.data?.text ?? "" } as CardData,
    }));
    return {
      nodes,
      edges: p.edges ?? [],
      scriptDescription: p.scriptDescription ?? "",
      name: p.name ?? "Без названия",
      comments: p.comments ?? [],
    };
  } catch {
    const loaded = loadProjectFromStorage(id);
    if (!loaded) return null;
    return { ...loaded, name: getProjectNameFromStorage(id), comments: loaded.comments ?? [] };
  }
}

/** Сохранить проект на сервер. */
export async function saveProject(
  id: string,
  name: string,
  nodes: Node<CardData>[],
  edges: Edge[],
  scriptDescription: string,
  comments: CommentItem[] = [],
): Promise<void> {
  const payload = {
    name,
    nodes: nodes.map((n) => ({
      id: n.id,
      type: n.type,
      position: n.position,
      data: { title: n.data?.title, text: n.data?.text },
    })),
    edges,
    scriptDescription,
    comments,
  };
  try {
    await api(`/api/projects/${encodeURIComponent(id)}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  } catch {
    saveProjectToStorage(id, name, nodes, edges, scriptDescription, comments);
  }
}

/** Создать проект на сервере, вернуть id. */
export async function createProject(name: string): Promise<string> {
  try {
    const { id } = await api<{ id: string }>("/api/projects", {
      method: "POST",
      body: JSON.stringify({ name: name.trim() || "Новый проект" }),
    });
    return id;
  } catch {
    return createProjectInStorage(name);
  }
}

/** Имя проекта (для отображения). Если уже загружали — передавать name из state; иначе можно запросить с сервера. */
export async function getProjectName(id: string): Promise<string> {
  try {
    const p = await api<{ name?: string }>(`/api/projects/${encodeURIComponent(id)}`);
    return p.name ?? "Без названия";
  } catch {
    return getProjectNameFromStorage(id);
  }
}

// --- Fallback: localStorage (офлайн / старая версия) ---

function getProjectsFromStorage(): Record<string, ProjectData> {
  try {
    const raw = localStorage.getItem(PROJECTS_KEY);
    if (!raw) return {};
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function setProjectsToStorage(projects: Record<string, ProjectData>) {
  try {
    localStorage.setItem(PROJECTS_KEY, JSON.stringify(projects));
  } catch {
    // ignore
  }
}

function listProjectsFromStorage(): { id: string; name: string }[] {
  const projects = getProjectsFromStorage();
  return Object.entries(projects).map(([id, p]) => ({ id, name: p.name || "Без названия" }));
}

function loadProjectFromStorage(
  id: string,
): { nodes: Node<CardData>[]; edges: Edge[]; scriptDescription: string; comments: CommentItem[] } | null {
  const projects = getProjectsFromStorage();
  const p = projects[id];
  if (!p) return null;
  const nodes: Node<CardData>[] = (p.nodes ?? []).map((n) => ({
    id: n.id,
    type: (n.type === "our_response" ? "our_response" : "client") as "client" | "our_response",
    position: n.position ?? { x: 0, y: 0 },
    data: { title: n.data?.title ?? "", text: n.data?.text ?? "" } as CardData,
  }));
  return {
    nodes,
    edges: p.edges ?? [],
    scriptDescription: p.scriptDescription ?? "",
    comments: p.comments ?? [],
  };
}

function saveProjectToStorage(
  id: string,
  name: string,
  nodes: Node<CardData>[],
  edges: Edge[],
  scriptDescription: string,
  comments: CommentItem[] = [],
) {
  const projects = getProjectsFromStorage();
  projects[id] = {
    name,
    nodes: nodes.map((n) => ({
      id: n.id,
      type: n.type,
      position: n.position,
      data: { title: n.data?.title, text: n.data?.text },
    })),
    edges,
    scriptDescription,
    comments,
  };
  setProjectsToStorage(projects);
}

function createProjectInStorage(name: string): string {
  const id = `project-${Date.now()}`;
  const projects = getProjectsFromStorage();
  projects[id] = {
    name: name.trim() || "Новый проект",
    nodes: [],
    edges: [],
    scriptDescription: "",
    comments: [],
  };
  setProjectsToStorage(projects);
  return id;
}

function getProjectNameFromStorage(id: string): string {
  const projects = getProjectsFromStorage();
  return projects[id]?.name ?? "Без названия";
}
