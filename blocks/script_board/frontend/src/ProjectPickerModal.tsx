import { useState } from "react";

interface ProjectPickerModalProps {
  open: boolean;
  projects: { id: string; name: string }[];
  onCreateProject: (name: string) => void;
  onSelectProject: (id: string) => void;
  onClose: () => void;
}

export default function ProjectPickerModal({
  open,
  projects,
  onCreateProject,
  onSelectProject,
  onClose,
}: ProjectPickerModalProps) {
  const [newName, setNewName] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  if (!open) return null;

  const handleCreate = () => {
    const name = newName.trim() || "Новый проект";
    onCreateProject(name);
    setNewName("");
    setShowCreate(false);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal--projects" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <span className="modal__title">Выбрать проект</span>
          <button type="button" className="modal__close" onClick={onClose} aria-label="Закрыть">
            ×
          </button>
        </div>
        <div className="modal__body">
          {!showCreate ? (
            <>
              <ul className="project-list">
                {projects.length === 0 ? (
                  <li className="project-list__empty">Нет проектов. Создайте первый.</li>
                ) : (
                  projects.map((p) => (
                    <li key={p.id}>
                      <button
                        type="button"
                        className="project-list__item"
                        onClick={() => {
                          onSelectProject(p.id);
                          onClose();
                        }}
                      >
                        {p.name}
                      </button>
                    </li>
                  ))
                )}
              </ul>
              <div className="modal__footer">
                <button
                  type="button"
                  className="modal__btn-primary"
                  onClick={() => setShowCreate(true)}
                >
                  Создать проект
                </button>
              </div>
            </>
          ) : (
            <>
              <label className="modal__label">Название проекта</label>
              <input
                type="text"
                className="modal__input"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Новый проект"
                autoFocus
              />
              <div className="modal__footer">
                <button type="button" onClick={() => setShowCreate(false)}>
                  Отмена
                </button>
                <button type="button" className="modal__btn-primary" onClick={handleCreate}>
                  Создать
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
