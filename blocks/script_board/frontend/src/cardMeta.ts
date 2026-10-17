/**
 * Автор карточки живёт отдельно от проекта.
 * В `{ name, nodes, edges, scriptDescription }` эти поля не пишутся.
 */
export const CARD_META_KEY = "script_board_card_meta";

export interface CardMeta {
  author: string;
  edited: boolean;
}

export const DEFAULT_CARD_META: CardMeta = { author: "Соня", edited: false };

type MetaMap = Record<string, Record<string, CardMeta>>;

function readMap(): MetaMap {
  try {
    const raw = localStorage.getItem(CARD_META_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
    return parsed as MetaMap;
  } catch {
    return {};
  }
}

function writeMap(map: MetaMap): void {
  localStorage.setItem(CARD_META_KEY, JSON.stringify(map));
}

export function readProjectMeta(projectId: string): Record<string, CardMeta> {
  const project = readMap()[projectId];
  if (!project || typeof project !== "object") return {};
  return project;
}

export function readCardMeta(projectId: string, cardId: string): CardMeta {
  const row = readProjectMeta(projectId)[cardId];
  if (!row || typeof row.author !== "string" || !row.author) return DEFAULT_CARD_META;
  return { author: row.author, edited: Boolean(row.edited) };
}

export function writeCardMeta(projectId: string, cardId: string, meta: CardMeta): Record<string, CardMeta> {
  const all = readMap();
  const project = { ...(all[projectId] ?? {}), [cardId]: meta };
  all[projectId] = project;
  writeMap(all);
  return project;
}
