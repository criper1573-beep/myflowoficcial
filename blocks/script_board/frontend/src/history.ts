/**
 * История изменений — только интерфейс.
 * Бэкенд подставит свой источник вместо `selectHistory`, не меняя тип записи.
 * Сюда не добавлять запросы к серверу.
 */
export interface HistoryEntry {
  id: string;
  /** ISO-8601 */
  at: string;
  author: string;
  /** Кто что изменил, одной короткой фразой */
  summary: string;
  cardId?: string;
}

/** Пример для локальной разработки и макета. В сборке хук возвращает []. */
export const DEV_HISTORY: HistoryEntry[] = [
  {
    id: "h1",
    at: "2026-10-17T08:42:00Z",
    author: "Алексей",
    summary: "Изменил текст карточки «Наш ответ» — мебель в стоимости",
    cardId: "a4",
  },
  {
    id: "h2",
    at: "2026-10-17T06:15:00Z",
    author: "Соня",
    summary: "Собрала ветку «Сроки» — вопрос про 20 мая и ответ",
  },
  {
    id: "h3",
    at: "2026-10-17T06:14:00Z",
    author: "Соня",
    summary: "Собрала ветку «Цена» — от 390 000 ₽ и бесплатный замер",
  },
  {
    id: "h4",
    at: "2026-10-17T06:14:00Z",
    author: "Соня",
    summary: "Создала скрипт по диалогу на Авито, объявление «кабинет 15 м²»",
  },
];

const EMPTY_HISTORY: HistoryEntry[] = [];

export function selectHistory(useMock: boolean): HistoryEntry[] {
  return useMock ? DEV_HISTORY : EMPTY_HISTORY;
}

const moscowDate = new Intl.DateTimeFormat("ru-RU", {
  timeZone: "Europe/Moscow",
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

const moscowTime = new Intl.DateTimeFormat("ru-RU", {
  timeZone: "Europe/Moscow",
  hour: "2-digit",
  minute: "2-digit",
});

export function formatHistoryTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return `${moscowDate.format(date)} ${moscowTime.format(date)}`;
}
