import { useMemo, useState } from "react";
import { ApiError, api } from "./api";
import type { Goal } from "./types";

interface GoalsPanelProps {
  projectId: string | null;
  projectRevision: number;
  goals: Goal[];
  onChange: (goals: Goal[], projectRevision: number) => void;
  onConflict: () => void;
}

export default function GoalsPanel({
  projectId,
  projectRevision,
  goals,
  onChange,
  onConflict,
}: GoalsPanelProps) {
  const [draft, setDraft] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [editNote, setEditNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [dragId, setDragId] = useState<string | null>(null);
  const sorted = useMemo(
    () => [...goals].sort((a, b) => a.order - b.order || a.id.localeCompare(b.id)),
    [goals],
  );

  const fail = (err: unknown) => {
    if (err instanceof ApiError && err.status === 409) {
      setEditingId(null);
      setError("Список целей изменился. Показана актуальная версия.");
      onConflict();
      return;
    }
    setError(err instanceof Error ? err.message : "Не удалось сохранить цель");
  };

  const addGoal = async () => {
    const text = draft.trim();
    if (!projectId || !text) return;
    try {
      const result = await api.goals.create(projectId, { projectRevision, text });
      onChange(result.goals, result.projectRevision);
      setDraft("");
      setError(null);
    } catch (err) {
      fail(err);
    }
  };

  const beginEdit = (goal: Goal) => {
    setEditingId(goal.id);
    setEditText(goal.text);
    setEditNote(goal.note ?? "");
    setError(null);
  };

  const commitEdit = async (goal: Goal) => {
    if (!projectId) return;
    const text = editText.trim();
    const note = editNote.trim();
    if (!text) {
      setError("У цели нужен текст");
      return;
    }
    if (text === goal.text && note === (goal.note ?? "")) {
      setEditingId(null);
      return;
    }
    try {
      const result = await api.goals.update(projectId, goal.id, {
        revision: goal.revision,
        text,
        note,
      });
      onChange(
        goals.map((item) => (item.id === goal.id ? result.goal : item)),
        result.projectRevision,
      );
      setEditingId(null);
      setError(null);
    } catch (err) {
      fail(err);
    }
  };

  const removeGoal = async (goal: Goal) => {
    if (!projectId) return;
    try {
      const result = await api.goals.remove(projectId, goal.id, goal.revision);
      onChange(result.goals, result.projectRevision);
      if (editingId === goal.id) setEditingId(null);
      setError(null);
    } catch (err) {
      fail(err);
    }
  };

  const dropOn = async (targetId: string) => {
    if (!projectId || !dragId || dragId === targetId) return;
    const ids = sorted.map((goal) => goal.id);
    const from = ids.indexOf(dragId);
    const to = ids.indexOf(targetId);
    if (from < 0 || to < 0) return;
    ids.splice(from, 1);
    ids.splice(to, 0, dragId);
    setDragId(null);
    try {
      const result = await api.goals.reorder(projectId, { projectRevision, ids });
      onChange(result.goals, result.projectRevision);
      setError(null);
    } catch (err) {
      fail(err);
    }
  };

  return (
    <div className="goals nowheel">
      <p className="goals__hint">Что нужно узнать у клиента, чтобы закрыть скрипт.</p>
      {error ? <p className="goals__note">{error}</p> : null}
      <ul className="goals__list">
        {sorted.map((goal) => (
          <li
            key={goal.id}
            className={dragId === goal.id ? "goals__item goals__item--drag" : "goals__item"}
            onDragOver={(event) => event.preventDefault()}
            onDrop={() => void dropOn(goal.id)}
          >
            <span
              className="goals__handle"
              draggable
              title="Перетащить"
              onDragStart={() => setDragId(goal.id)}
              onDragEnd={() => setDragId(null)}
            >
              ⋮⋮
            </span>
            {editingId === goal.id ? (
              <form
                className="goals__edit"
                onSubmit={(event) => {
                  event.preventDefault();
                  void commitEdit(goal);
                }}
              >
                <input
                  className="goals__input"
                  value={editText}
                  onChange={(event) => setEditText(event.target.value)}
                  aria-label="Текст цели"
                  autoFocus
                />
                <input
                  className="goals__input goals__input--note"
                  value={editNote}
                  onChange={(event) => setEditNote(event.target.value)}
                  placeholder="Заметка"
                  aria-label="Заметка к цели"
                />
                <button type="submit" className="goals__save">
                  Ок
                </button>
              </form>
            ) : (
              <button type="button" className="goals__text" onClick={() => beginEdit(goal)}>
                <span>{goal.text}</span>
                {goal.note ? <small>{goal.note}</small> : null}
              </button>
            )}
            <button type="button" className="goals__delete" onClick={() => void removeGoal(goal)} title="Удалить цель">
              ×
            </button>
          </li>
        ))}
      </ul>
      {sorted.length === 0 ? <p className="goals__note">Пока нет целей. Например: адрес, площадь, сроки, бюджет.</p> : null}
      <form
        className="goals__add"
        onSubmit={(event) => {
          event.preventDefault();
          void addGoal();
        }}
      >
        <input
          className="goals__input"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Новая цель"
          aria-label="Новая цель"
          disabled={!projectId}
        />
        <button type="submit" className="goals__save" disabled={!projectId || !draft.trim()}>
          Добавить
        </button>
      </form>
    </div>
  );
}
