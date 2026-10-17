import type {
  BoardComment,
  CardMutation,
  CardPatch,
  CardWrite,
  CommentMutation,
  EdgeMutation,
  HistoryQuery,
  HistoryResponse,
  Project,
  ProjectListItem,
  ReplaceResult,
} from "./types";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly detail: unknown;
  readonly revision: number | null;
  readonly cardRevision: number | null;

  constructor(status: number, payload: unknown) {
    const detail = unwrapDetail(payload);
    super(messageOf(detail, status));
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.code = isRecord(detail) && typeof detail.code === "string" ? detail.code : "";
    this.revision = isRecord(detail) && typeof detail.revision === "number" ? detail.revision : null;
    this.cardRevision =
      isRecord(detail) && typeof detail.cardRevision === "number" ? detail.cardRevision : null;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function unwrapDetail(payload: unknown): unknown {
  if (isRecord(payload) && "detail" in payload) return payload.detail;
  return payload;
}

function messageOf(detail: unknown, status: number): string {
  if (isRecord(detail) && typeof detail.message === "string") return detail.message;
  if (typeof detail === "string" && detail.trim()) return detail;
  return `HTTP ${status}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body != null && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(path, { ...init, headers });
  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text) as unknown;
    } catch {
      payload = text;
    }
  }
  if (!response.ok) throw new ApiError(response.status, payload);
  return payload as T;
}

function historyParams(query?: HistoryQuery): string {
  const params = new URLSearchParams();
  if (query?.since) params.set("since", query.since);
  if (query?.author) params.set("author", query.author);
  if (query?.excludeAuthor) params.set("exclude_author", query.excludeAuthor);
  const text = params.toString();
  return text ? `?${text}` : "";
}

export const api = {
  listProjects(includeArchived = false): Promise<ProjectListItem[]> {
    const query = includeArchived ? "?include_archived=true" : "";
    return request(`/api/projects${query}`);
  },

  getProject(id: string): Promise<Project> {
    return request(`/api/projects/${encodeURIComponent(id)}`);
  },

  createProject(body: {
    name: string;
    scriptDescription?: string;
    nodes?: Project["nodes"];
    edges?: Project["edges"];
    comments?: BoardComment[];
  }): Promise<{ id: string; revision: number }> {
    return request("/api/projects", { method: "POST", body: JSON.stringify(body) });
  },

  replaceProject(id: string, project: Project): Promise<ReplaceResult> {
    return request(`/api/projects/${encodeURIComponent(id)}`, {
      method: "PUT",
      body: JSON.stringify(project),
    });
  },

  updateProject(
    id: string,
    body: { revision: number; name?: string; scriptDescription?: string },
  ): Promise<{ success: true; revision: number; project: Project }> {
    return request(`/api/projects/${encodeURIComponent(id)}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  },

  archiveProject(id: string, revision: number): Promise<{ success: true; revision: number; archived: true }> {
    return request(`/api/projects/${encodeURIComponent(id)}?revision=${revision}`, { method: "DELETE" });
  },

  restoreProject(id: string, revision: number): Promise<{ success: true; revision: number; project: Project }> {
    return request(`/api/projects/${encodeURIComponent(id)}/restore`, {
      method: "POST",
      body: JSON.stringify({ revision }),
    });
  },

  createCard(projectId: string, body: CardWrite): Promise<CardMutation> {
    return request(`/api/projects/${encodeURIComponent(projectId)}/cards`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  updateCard(projectId: string, cardId: string, body: CardPatch): Promise<CardMutation> {
    return request(`/api/projects/${encodeURIComponent(projectId)}/cards/${encodeURIComponent(cardId)}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  },

  deleteCard(projectId: string, cardId: string, revision: number): Promise<{ success: true; projectRevision: number }> {
    return request(
      `/api/projects/${encodeURIComponent(projectId)}/cards/${encodeURIComponent(cardId)}?revision=${revision}`,
      { method: "DELETE" },
    );
  },

  createEdge(
    projectId: string,
    body: { projectRevision: number; id?: string; source: string; target: string },
  ): Promise<EdgeMutation> {
    return request(`/api/projects/${encodeURIComponent(projectId)}/edges`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  deleteEdge(
    projectId: string,
    edgeId: string,
    projectRevision: number,
  ): Promise<{ success: true; projectRevision: number }> {
    return request(
      `/api/projects/${encodeURIComponent(projectId)}/edges/${encodeURIComponent(edgeId)}?projectRevision=${projectRevision}`,
      { method: "DELETE" },
    );
  },

  createComment(
    projectId: string,
    body: { projectRevision: number; id?: string; x: number; y: number; text: string },
  ): Promise<CommentMutation> {
    return request(`/api/projects/${encodeURIComponent(projectId)}/comments`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  updateComment(
    projectId: string,
    commentId: string,
    body: { projectRevision: number; text?: string; x?: number; y?: number },
  ): Promise<CommentMutation> {
    return request(
      `/api/projects/${encodeURIComponent(projectId)}/comments/${encodeURIComponent(commentId)}`,
      { method: "PATCH", body: JSON.stringify(body) },
    );
  },

  deleteComment(
    projectId: string,
    commentId: string,
    projectRevision: number,
  ): Promise<{ success: true; projectRevision: number }> {
    return request(
      `/api/projects/${encodeURIComponent(projectId)}/comments/${encodeURIComponent(commentId)}?projectRevision=${projectRevision}`,
      { method: "DELETE" },
    );
  },

  history(projectId: string, query?: HistoryQuery): Promise<HistoryResponse> {
    return request(`/api/projects/${encodeURIComponent(projectId)}/history${historyParams(query)}`);
  },
};
