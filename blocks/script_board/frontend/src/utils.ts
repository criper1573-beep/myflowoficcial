import type { Node, Edge } from "@xyflow/react";

/** Константы для расстановки карточек (без наложения и для «Упорядочить»). */
export const CARD_LAYOUT = {
  width: 280,
  height: 100,
  hGap: 40,
  /** Зазор между карточками в ряду, если у всех в ряду нет детей. */
  hGapLeaves: 20,
  vGap: 120,
  /** Шаг по горизонтали между карточками. */
  stepX: 280 + 40,
} as const;

function getChildren(nodeId: string, edges: Edge[]): string[] {
  return edges.filter((e) => e.source === nodeId).map((e) => e.target);
}

function getParents(nodeId: string, edges: Edge[]): string[] {
  return edges.filter((e) => e.target === nodeId).map((e) => e.source);
}

/** Ширина поддерева (для размещения): сумма ширин детей + зазоры, минимум одна карточка. Если все дети — листья, зазор 20px. */
function subtreeWidth(
  nodeId: string,
  edges: Edge[],
  cache: Map<string, number>,
): number {
  const cached = cache.get(nodeId);
  if (cached !== undefined) return cached;
  const children = getChildren(nodeId, edges);
  if (children.length === 0) {
    cache.set(nodeId, CARD_LAYOUT.width);
    return CARD_LAYOUT.width;
  }
  const sum = children.reduce(
    (acc, c) => acc + subtreeWidth(c, edges, cache),
    0,
  );
  const allLeaves = children.every((c) => getChildren(c, edges).length === 0);
  const gap = allLeaves ? CARD_LAYOUT.hGapLeaves : CARD_LAYOUT.hGap;
  const total = sum + (children.length - 1) * gap;
  cache.set(nodeId, Math.max(CARD_LAYOUT.width, total));
  return cache.get(nodeId)!;
}

/**
 * Вычисляет позиции (x, y) для всех нод: корни в одну линию,
 * дети под родителем, центр группы детей под центром родителя.
 */
export function computeLayoutPositions(
  nodes: Node[],
  edges: Edge[],
): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  const widthCache = new Map<string, number>();
  const nodeById = new Map(nodes.map((node) => [node.id, node]));

  const roots = nodes.filter((n) => getParents(n.id, edges).length === 0);
  const sortedRoots = [...roots].sort((a, b) => a.id.localeCompare(b.id));

  function placeNode(nodeId: string, left: number, y: number): void {
    const w = subtreeWidth(nodeId, edges, widthCache);
    const x = left + w / 2 - CARD_LAYOUT.width / 2;
    positions.set(nodeId, { x, y });

    const children = getChildren(nodeId, edges);
    if (children.length === 0) return;

    const node = nodeById.get(nodeId);
    const childY = y + (node?.measured?.height ?? CARD_LAYOUT.height) + CARD_LAYOUT.vGap;
    const allLeaves = children.every((c) => getChildren(c, edges).length === 0);
    const gap = allLeaves ? CARD_LAYOUT.hGapLeaves : CARD_LAYOUT.hGap;
    const childWidths = children.map((c) => subtreeWidth(c, edges, widthCache));
    let childLeft = left;
    for (let i = 0; i < children.length; i++) {
      placeNode(children[i], childLeft, childY);
      childLeft += childWidths[i] + gap;
    }
  }

  let rootLeft = 0;
  for (const r of sortedRoots) {
    placeNode(r.id, rootLeft, 0);
    const rootIsLeaf = getChildren(r.id, edges).length === 0;
    const rootGap = rootIsLeaf ? CARD_LAYOUT.hGapLeaves : CARD_LAYOUT.hGap;
    rootLeft += subtreeWidth(r.id, edges, widthCache) + rootGap;
  }

  const placed = new Set(positions.keys());
  const orphans = nodes.filter((n) => !placed.has(n.id));
  if (orphans.length > 0) {
    let orphanX = 0;
    for (const n of orphans) {
      positions.set(n.id, {
        x: orphanX,
        y: 0,
      });
      orphanX += CARD_LAYOUT.width + CARD_LAYOUT.hGapLeaves;
    }
  }

  /**
   * Каждая ветка — на одной вертикальной оси: середина ширины каждого уровня
   * совпадает с серединой карточки-родителя выше.
   * Проход снизу вверх: для каждого узла с детьми ставим его x так, чтобы
   * центр карточки (x + width/2) совпадал с центром ширины детей.
   */
  const depthByNode = new Map<string, number>();
  const stack: { id: string; depth: number }[] = sortedRoots.map((r) => ({ id: r.id, depth: 0 }));
  while (stack.length) {
    const { id, depth } = stack.pop()!;
    if (depthByNode.has(id)) continue;
    depthByNode.set(id, depth);
    for (const c of getChildren(id, edges)) stack.push({ id: c, depth: depth + 1 });
  }
  const byDepthDesc = [...depthByNode.entries()].sort((a, b) => b[1] - a[1]);
  for (const [nodeId] of byDepthDesc) {
    const children = getChildren(nodeId, edges);
    if (children.length === 0) continue;
    const childPositions = children.map((c) => positions.get(c)!).filter(Boolean);
    if (childPositions.length === 0) continue;
    const minX = Math.min(...childPositions.map((p) => p.x));
    const maxX = Math.max(...childPositions.map((p) => p.x));
    const rightEdgeLast = maxX + CARD_LAYOUT.width;
    const centerChildrenBbox = (minX + rightEdgeLast) / 2;
    positions.set(nodeId, {
      x: centerChildrenBbox - CARD_LAYOUT.width / 2,
      y: positions.get(nodeId)!.y,
    });
  }

  /** Вертикальный центр всей диаграммы: сдвигаем все узлы по Y так, чтобы центр диаграммы был на одной линии. */
  let diagramMinY = Infinity;
  let diagramMaxY = -Infinity;
  for (const pos of positions.values()) {
    if (pos.y < diagramMinY) diagramMinY = pos.y;
    if (pos.y > diagramMaxY) diagramMaxY = pos.y;
  }
  const diagramCenterY = (diagramMinY + diagramMaxY) / 2;
  for (const id of positions.keys()) {
    const pos = positions.get(id)!;
    positions.set(id, { x: pos.x, y: pos.y - diagramCenterY });
  }

  return positions;
}

/** Все предки ноды (обход рёбер назад), затем топологический порядок от корней. */
export function getAncestorIds(nodeId: string, _nodes: Node[], edges: Edge[]): string[] {
  const incoming = new Map<string, string[]>();
  for (const e of edges) {
    if (e.target === nodeId) {
      const list = incoming.get(e.target) ?? [];
      list.push(e.source);
      incoming.set(e.target, list);
    }
  }
  const visited = new Set<string>();
  const stack: string[] = [nodeId];
  while (stack.length) {
    const cur = stack.pop()!;
    if (visited.has(cur)) continue;
    visited.add(cur);
    const sources = edges.filter((e) => e.target === cur).map((e) => e.source);
    for (const s of sources) stack.push(s);
  }
  visited.delete(nodeId);
  const ancestorList = Array.from(visited);
  return topologicalSort(ancestorList, edges);
}

function topologicalSort(ids: string[], edges: Edge[]): string[] {
  const outdeg = new Map<string, string[]>();
  for (const e of edges) {
    if (!ids.includes(e.source) || !ids.includes(e.target)) continue;
    const list = outdeg.get(e.source) ?? [];
    list.push(e.target);
    outdeg.set(e.source, list);
  }
  const indeg = new Map<string, number>();
  for (const id of ids) indeg.set(id, 0);
  for (const [, targets] of outdeg) for (const t of targets) indeg.set(t, (indeg.get(t) ?? 0) + 1);
  const queue = ids.filter((id) => indeg.get(id) === 0);
  const result: string[] = [];
  while (queue.length) {
    const u = queue.shift()!;
    result.push(u);
    for (const v of outdeg.get(u) ?? []) {
      let d = indeg.get(v)! - 1;
      indeg.set(v, d);
      if (d === 0) queue.push(v);
    }
  }
  return result;
}

/** Порядок всех нод для PDF: топологическая сортировка по графу, затем по Y, X. */
export function orderNodesForPdf(nodes: Node[], edges: Edge[]): Node[] {
  const ids = nodes.map((n) => n.id);
  const sorted = topologicalSort(ids, edges);
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const ordered: Node[] = [];
  for (const id of sorted) {
    const n = byId.get(id);
    if (n) ordered.push(n);
  }
  const remaining = nodes.filter((n) => !sorted.includes(n.id));
  remaining.sort((a, b) => {
    const ya = a.position?.y ?? 0;
    const yb = b.position?.y ?? 0;
    if (ya !== yb) return ya - yb;
    return (a.position?.x ?? 0) - (b.position?.x ?? 0);
  });
  return [...ordered, ...remaining];
}
