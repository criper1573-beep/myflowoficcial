import { useEffect, useRef } from "react";
import type { Node, Edge } from "@xyflow/react";
import { ApiError } from "./api";
import { hasPendingSave, loadProject, retryPendingSave, saveProject, type CommentItem } from "./projectsStorage";
import type { CardData } from "./types";

export interface AutosaveSnapshot {
  projectId: string | null;
  revision: number;
  name: string;
  nodes: Node<CardData>[];
  edges: Edge[];
  scriptDescription: string;
  comments: CommentItem[];
}

interface UseAutosaveOptions {
  enabled: boolean;
  snapshot: AutosaveSnapshot;
  onRevision: (revision: number) => void;
  onConflict: () => Promise<void>;
  onRemote: () => Promise<void>;
  onError: (message: string) => void;
  onClearError: () => void;
}

const POLL_MS = 12000;

/**
 * Автосохранение полного проекта с ревизией.
 * Пока сервер не ответил, правки остаются в памяти и повторяются с той же ревизией.
 * 409 не затирает сервер: вызывается onConflict, который перечитывает проект.
 */
export function useAutosave({
  enabled,
  snapshot,
  onRevision,
  onConflict,
  onRemote,
  onError,
  onClearError,
}: UseAutosaveOptions) {
  const snapshotRef = useRef(snapshot);
  snapshotRef.current = snapshot;
  const unsavedRef = useRef(false);
  const savingRef = useRef(false);
  const onRevisionRef = useRef(onRevision);
  const onConflictRef = useRef(onConflict);
  const onRemoteRef = useRef(onRemote);
  const onErrorRef = useRef(onError);
  const onClearErrorRef = useRef(onClearError);
  onRevisionRef.current = onRevision;
  onConflictRef.current = onConflict;
  onRemoteRef.current = onRemote;
  onErrorRef.current = onError;
  onClearErrorRef.current = onClearError;

  const flush = async () => {
    if (savingRef.current) return;
    const current = snapshotRef.current;
    if (!current.projectId || !unsavedRef.current) return;
    savingRef.current = true;
    let failed = false;
    try {
      const result = await saveProject(
        current.projectId,
        current.name,
        current.nodes,
        current.edges,
        current.scriptDescription,
        current.comments,
        current.revision,
      );
      unsavedRef.current = false;
      onRevisionRef.current(result.revision);
      onClearErrorRef.current();
    } catch (error) {
      failed = true;
      if (error instanceof ApiError && error.status === 409) {
        unsavedRef.current = false;
        await onConflictRef.current();
      } else {
        onErrorRef.current(
          error instanceof Error ? error.message : "Сервер недоступен. Правки повторим с той же ревизией.",
        );
      }
    } finally {
      savingRef.current = false;
      if (unsavedRef.current && !failed) {
        window.setTimeout(() => void flush(), 400);
      }
    }
  };

  useEffect(() => {
    if (!enabled || !snapshot.projectId) return;
    unsavedRef.current = true;
    const timer = window.setTimeout(() => void flush(), 400);
    return () => window.clearTimeout(timer);
    // revision намеренно не в зависимостях: её обновление после сохранения не должно слать проект заново
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, snapshot.projectId, snapshot.name, snapshot.nodes, snapshot.edges, snapshot.scriptDescription, snapshot.comments]);

  useEffect(() => {
    if (!enabled || !snapshot.projectId) return;
    let cancelled = false;
    const pull = async () => {
      if (cancelled) return;
      if (unsavedRef.current || savingRef.current || hasPendingSave()) {
        const retry = await retryPendingSave();
        if (retry.status === "saved") {
          unsavedRef.current = false;
          onRevisionRef.current(retry.revision);
          onClearErrorRef.current();
        } else if (retry.status === "conflict") {
          unsavedRef.current = false;
          await onConflictRef.current();
        }
        return;
      }
      try {
        const fresh = await loadProject(snapshotRef.current.projectId || "");
        if (cancelled || !fresh || unsavedRef.current || savingRef.current) return;
        if (fresh.revision !== snapshotRef.current.revision) {
          await onRemoteRef.current();
        }
      } catch {
        /* следующий тик */
      }
    };
    const timer = window.setInterval(() => void pull(), POLL_MS);
    const onFocus = () => void pull();
    const onVisible = () => {
      if (document.visibilityState === "visible") void pull();
    };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [enabled, snapshot.projectId]);
}
