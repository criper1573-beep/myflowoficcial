import { useReactFlow, useStore } from "@xyflow/react";

interface ToolbarProps {
  projectName: string;
  descOpen: boolean;
  histOpen: boolean;
  canDelete: boolean;
  onOpenProjects: () => void;
  onAddClient: () => void;
  onAddAnswer: () => void;
  onDelete: () => void;
  onExport: () => void;
  exporting: boolean;
  onToggleDesc: () => void;
  onToggleHist: () => void;
}

export function Toolbar({
  projectName,
  descOpen,
  histOpen,
  canDelete,
  onOpenProjects,
  onAddClient,
  onAddAnswer,
  onDelete,
  onExport,
  exporting,
  onToggleDesc,
  onToggleHist,
}: ToolbarProps) {
  const { zoomIn, zoomOut, fitView } = useReactFlow();
  const zoom = useStore((state) => state.transform[2]);

  return (
    <header className="toolbar">
      <div className="brand">
        <span className="logo">
          FL<span className="logo-o">O</span>W
        </span>
        <span className="brand-name">Доска скриптов</span>
      </div>
      <span className="tool-sep" aria-hidden="true" />
      <button type="button" className="tool tool--project" onClick={onOpenProjects} title="Выбрать проект">
        <span className="tool-kicker">Выбрать проект</span>
        <span className="tool-project-name">{projectName}</span>
      </button>
      <span className="tool-sep" aria-hidden="true" />
      <button type="button" className="tool" onClick={onAddClient}>
        + Клиент
      </button>
      <button type="button" className="tool" onClick={onAddAnswer}>
        + Ответ
      </button>
      <button type="button" className="tool" onClick={onDelete} disabled={!canDelete}>
        Удалить
      </button>
      <span className="tool-sep" aria-hidden="true" />
      <div className="zoom" role="group" aria-label="Масштаб">
        <button type="button" onClick={() => zoomOut()} aria-label="Уменьшить">
          −
        </button>
        <span>{Math.round(zoom * 100)}%</span>
        <button type="button" onClick={() => zoomIn()} aria-label="Увеличить">
          +
        </button>
      </div>
      <button type="button" className="tool" onClick={() => fitView({ padding: 0.2, duration: 200 })}>
        Вписать
      </button>
      <button type="button" className="tool" onClick={onExport} disabled={exporting}>
        {exporting ? "PDF…" : "PDF"}
      </button>
      <span className="toolbar-spacer" />
      <button
        type="button"
        className={`tool${descOpen ? " is-active" : ""}`}
        aria-pressed={descOpen}
        onClick={onToggleDesc}
      >
        Описание
      </button>
      <button
        type="button"
        className={`tool${histOpen ? " is-active" : ""}`}
        aria-pressed={histOpen}
        onClick={onToggleHist}
      >
        История
      </button>
    </header>
  );
}
