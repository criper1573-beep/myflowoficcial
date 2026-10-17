import { useEffect, useId, useState } from "react";
import type { ProjectListItem } from "./projectsStorage";

interface ProjectPickerModalProps {
  open: boolean;
  projects: ProjectListItem[];
  onCreateProject: (name: string) => void;
  onSelectProject: (id: string) => void;
  onClose: () => void;
}

export function ProjectPickerModal({
  open,
  projects,
  onCreateProject,
  onSelectProject,
  onClose,
}: ProjectPickerModalProps) {
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const titleId = useId();

  useEffect(() => {
    if (!open) {
      setCreating(false);
      setName("");
    }
  }, [open]);

  if (!open) return null;

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <div
        className="modal modal--projects"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="panel-head">
          <h2 id={titleId}>Выбрать проект</h2>
          <button type="button" className="panel-close" onClick={onClose} aria-label="Закрыть">
            ×
          </button>
        </div>
        <div className="modal__body">
          {creating ? (
            <form
              className="create-form"
              onSubmit={(event) => {
                event.preventDefault();
                if (!name.trim()) return;
                onCreateProject(name.trim());
              }}
            >
              <label className="field-label" htmlFor="project-name">
                Название проекта
              </label>
              <input
                id="project-name"
                className="field-input"
                value={name}
                autoFocus
                onChange={(event) => setName(event.target.value)}
              />
              <div className="create-form__actions">
                <button type="button" className="ghost-btn" onClick={() => setCreating(false)}>
                  Назад
                </button>
                <button type="submit" className="solid-btn" disabled={!name.trim()}>
                  Создать
                </button>
              </div>
            </form>
          ) : (
            <>
              {projects.length === 0 ? (
                <p className="project-list__empty">Проектов пока нет</p>
              ) : (
                <ul className="project-list">
                  {projects.map((project) => (
                    <li key={project.id}>
                      <button
                        type="button"
                        className="project-list__item"
                        onClick={() => onSelectProject(project.id)}
                      >
                        {project.name}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              <button type="button" className="solid-btn create-project" onClick={() => setCreating(true)}>
                Создать проект
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
