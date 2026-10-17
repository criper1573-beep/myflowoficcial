import { selectHistory, type HistoryEntry } from "./history";

/** Пустой список в сборке, пример — только в `vite` dev. Бэкенд заменит тело хука. */
export function useHistory(): HistoryEntry[] {
  return selectHistory(import.meta.env.DEV);
}
