import type { HistoryQuery, HistoryResponse } from "./types";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly revision: number | null;
  readonly cardRevision: number | null;

  constructor(status: number, payload: unknown) {
    const detail = unwrapDetail(payload);
    super(messageOf(detail, status));
    this.name = "ApiError";
    this.status = status;
    this.code = isRecord(detail) && typeof detail.code === "string" ? detail.code : "";
    this.revision = isRecord(detail) && typeof detail.revision === "number" ? detail.revision : null;
    this.cardRevision = isRecord(detail) && typeof detail.cardRevision === "number" ? detail.cardRevision : null;
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

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers);
  if (options?.body != null && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  let response: Response;
  try {
    response = await fetch(path, { ...options, headers });
  } catch (error) {
    throw new ApiError(0, error instanceof Error ? error.message : "Сервер недоступен");
  }
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

function historyQuery(query?: HistoryQuery): string {
  const params = new URLSearchParams();
  if (query?.since) params.set("since", query.since);
  if (query?.author) params.set("author", query.author);
  if (query?.excludeAuthor) params.set("exclude_author", query.excludeAuthor);
  const text = params.toString();
  return text ? `?${text}` : "";
}

/** Клиент для панели истории и точечных правок. Лена импортирует его вместе с useHistory. */
export const api = {
  history(projectId: string, query?: HistoryQuery): Promise<HistoryResponse> {
    return request(`/api/projects/${encodeURIComponent(projectId)}/history${historyQuery(query)}`);
  },
};
