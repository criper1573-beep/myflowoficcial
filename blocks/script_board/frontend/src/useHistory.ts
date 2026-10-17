import { useCallback, useEffect, useState } from "react";

import { ApiError, api } from "./api";
import type { HistoryEvent, HistoryQuery } from "./types";

export interface UseHistoryResult {
  events: HistoryEvent[];
  revision: number | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/** История правок проекта. Лена подключает результат к панели и бейджам автора. */
export function useHistory(projectId: string | null, query?: HistoryQuery): UseHistoryResult {
  const [events, setEvents] = useState<HistoryEvent[]>([]);
  const [revision, setRevision] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const since = query?.since;
  const author = query?.author;
  const excludeAuthor = query?.excludeAuthor;
  const pollMs = query?.pollMs;

  const reload = useCallback(() => setTick((value) => value + 1), []);

  useEffect(() => {
    if (!projectId) {
      setEvents([]);
      setRevision(null);
      setError(null);
      setLoading(false);
      return;
    }
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      try {
        const response = await api.history(projectId, { since, author, excludeAuthor });
        if (cancelled) return;
        setEvents(response.events);
        setRevision(response.revision);
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : "Не удалось загрузить историю");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void load();
    if (!pollMs || pollMs <= 0) {
      return () => {
        cancelled = true;
      };
    }
    const timer = window.setInterval(() => {
      void load();
    }, pollMs);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [projectId, since, author, excludeAuthor, pollMs, tick]);

  return { events, revision, loading, error, reload };
}
