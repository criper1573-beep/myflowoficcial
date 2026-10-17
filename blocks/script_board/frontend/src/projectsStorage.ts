/** Ключи и форма проекта зафиксированы в docs/guides/PATCHES.md (script-board-project-picker). */
export const PROJECTS_KEY = "script_board_projects";
export const CURRENT_KEY = "script_board_current";

export interface ProjectData {
  name: string;
  nodes: unknown[];
  edges: unknown[];
  scriptDescription: string;
}

export interface ProjectListItem {
  id: string;
  name: string;
}

function readMap(): Record<string, ProjectData> {
  try {
    const raw = localStorage.getItem(PROJECTS_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
    return parsed as Record<string, ProjectData>;
  } catch {
    return {};
  }
}

function writeMap(map: Record<string, ProjectData>): void {
  localStorage.setItem(PROJECTS_KEY, JSON.stringify(map));
}

export function getCurrentProjectId(): string | null {
  return localStorage.getItem(CURRENT_KEY);
}

export function setCurrentProjectId(id: string): void {
  localStorage.setItem(CURRENT_KEY, id);
}

export function listProjects(): ProjectListItem[] {
  return Object.entries(readMap()).map(([id, project]) => ({
    id,
    name: typeof project?.name === "string" && project.name ? project.name : "Без названия",
  }));
}

export function loadProject(id: string): ProjectData | null {
  const project = readMap()[id];
  if (!project || typeof project !== "object") return null;
  return {
    name: typeof project.name === "string" && project.name ? project.name : "Без названия",
    nodes: Array.isArray(project.nodes) ? project.nodes : [],
    edges: Array.isArray(project.edges) ? project.edges : [],
    scriptDescription: typeof project.scriptDescription === "string" ? project.scriptDescription : "",
  };
}

export function saveProject(
  id: string,
  name: string,
  nodes: unknown[],
  edges: unknown[],
  scriptDescription: string,
): void {
  const map = readMap();
  map[id] = { name, nodes, edges, scriptDescription };
  writeMap(map);
}

export function createProject(name: string): string {
  const id = crypto.randomUUID();
  const title = name.trim() || "Без названия";
  saveProject(id, title, [], [], "");
  return id;
}

export function getProjectName(id: string): string {
  return loadProject(id)?.name ?? "";
}
