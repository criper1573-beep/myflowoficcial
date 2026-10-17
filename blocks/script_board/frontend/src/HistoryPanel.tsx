import { useEffect, useMemo, useState } from "react";
import { useHistory } from "./useHistory";
import type { HistoryEvent, HistoryEventType } from "./types";

const TYPE_LABEL: Record<HistoryEventType, string> = {
  "project.create": "Проект создан",
  "project.rename": "Проект переименован",
  "project.description": "Описание изменено",
  "project.archive": "Проект в архиве",
  "project.restore": "Проект восстановлен",
  "card.create": "Карточка создана",
  "card.update": "Карточка изменена",
  "card.delete": "Карточка удалена",
  "edge.create": "Связь создана",
  "edge.update": "Связь изменена",
  "edge.delete": "Связь удалена",
  "comment.create": "Комментарий создан",
  "comment.update": "Комментарий изменён",
  "comment.delete": "Комментарий удалён",
  "goal.create": "Цель добавлена",
  "goal.update": "Цель изменена",
  "goal.delete": "Цель удалена",
  "goal.reorder": "Порядок целей изменён",
};

function formatTime(ts: string): string {
  const date = new Date(ts);
  if (Number.isNaN(date.getTime())) return ts;
  return date.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Последний автор карточки. Без имени показываем, что карточку уже меняли. */
export function cardBadges(events: HistoryEvent[]): Record<string, string> {
  const badges: Record<string, string> = {};
  for (const event of events) {
    if (!event.cardId) continue;
    if (event.type === "card.delete") {
      delete badges[event.cardId];
      continue;
    }
    if (event.type !== "card.create" && event.type !== "card.update") continue;
    const author = event.author.trim();
    badges[event.cardId] = author && author.toLowerCase() !== "unknown" ? author : "изменено";
  }
  return badges;
}

interface HistoryPanelProps {
  projectId: string | null;
  onCardBadges: (badges: Record<string, string>) => void;
}

export default function HistoryPanel({ projectId, onCardBadges }: HistoryPanelProps) {
  const [hideSonya, setHideSonya] = useState(false);
  const { events, loading, error } = useHistory(projectId, {
    excludeAuthor: hideSonya ? "sonya" : undefined,
    pollMs: 12000,
  });
  const authored = useHistory(projectId, { pollMs: 12000 });
  const badges = useMemo(() => cardBadges(authored.events), [authored.events]);

  useEffect(() => {
    onCardBadges(badges);
  }, [badges, onCardBadges]);

  const shown = [...events].reverse();

  return (
    <>
      <label className="history__filter">
        <input
          type="checkbox"
          checked={hideSonya}
          onChange={(event) => setHideSonya(event.target.checked)}
        />
        правки не от sonya
      </label>
      {error ? <p className="history__note">{error}</p> : null}
      {loading && shown.length === 0 ? <p className="history__note">Загрузка…</p> : null}
      {!loading && !error && shown.length === 0 ? <p className="history__note">Пока нет записей</p> : null}
      <ul className="history__list">
        {shown.map((event) => (
          <li key={event.id} className="history__item">
            <span className="history__author">{event.author || "unknown"}</span>
            <time dateTime={event.ts}>{formatTime(event.ts)}</time>
            <span className="history__type">{TYPE_LABEL[event.type] ?? event.type}</span>
          </li>
        ))}
      </ul>
    </>
  );
}
