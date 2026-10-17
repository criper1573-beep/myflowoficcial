export interface HistoryItem {
  id: string;
  author: string;
  action: string;
  cardId?: string;
  at: string;
}

/** Заглушка. Бэкенд заменит тело хука, сигнатуру оставить. */
export function useHistory(projectId: string): { items: HistoryItem[]; loading: boolean } {
  void projectId;
  return { items: [], loading: false };
}
