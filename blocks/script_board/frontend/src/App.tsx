import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  type Connection,
  type EdgeChange,
  type Node,
  type NodeChange,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { ApiError, api } from "./api";
import { BoardContext, CardNode } from "./CardNode";
import { useHistory } from "./useHistory";
import type { CardData, Project, ProjectListItem, ScriptEdge, ScriptNode } from "./types";

const nodeTypes = { client: CardNode, our_response: CardNode };
const CURRENT_KEY = "script_board_current";

function toPayload(project: Project): Project {
  return {
    ...project,
    nodes: project.nodes.map((node) => {
      const copy: ScriptNode = { ...node };
      delete copy.selected;
      delete copy.dragging;
      return copy;
    }),
    edges: project.edges.map((edge) => {
      const copy: ScriptEdge = { ...edge };
      delete copy.selected;
      return copy;
    }),
  };
}

export default function App() {
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [banner, setBanner] = useState<string | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [draftName, setDraftName] = useState("");

  const projectRef = useRef<Project | null>(null);
  const projectIdRef = useRef<string | null>(null);
  const dirtyRef = useRef(false);
  const savingRef = useRef(false);
  const genRef = useRef(0);

  const history = useHistory(projectId, { pollMs: 12000 });

  useEffect(() => {
    projectRef.current = project;
  }, [project]);
  useEffect(() => {
    projectIdRef.current = projectId;
  }, [projectId]);

  const markSaved = useCallback((next: Project) => {
    projectRef.current = next;
    dirtyRef.current = false;
    genRef.current += 1;
    setProject(next);
    setDirty(false);
  }, []);

  const edit = useCallback((mutator: (current: Project) => Project) => {
    setProject((prev) => {
      if (!prev) return prev;
      const next = mutator(prev);
      projectRef.current = next;
      return next;
    });
    genRef.current += 1;
    dirtyRef.current = true;
    setDirty(true);
  }, []);

  const refreshList = useCallback(async () => {
    const items = await api.listProjects();
    setProjects(items);
    return items;
  }, []);

  const openProject = useCallback(async (id: string) => {
    const fresh = await api.getProject(id);
    projectRef.current = fresh;
    dirtyRef.current = false;
    genRef.current += 1;
    setProject(fresh);
    setProjectId(id);
    setDirty(false);
    setBanner(null);
    window.localStorage.setItem(CURRENT_KEY, id);
  }, []);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const items = await refreshList();
        if (cancelled) return;
        const stored = window.localStorage.getItem(CURRENT_KEY);
        const initial = items.find((item) => item.id === stored)?.id ?? items[0]?.id;
        if (initial) await openProject(initial);
      } catch (error) {
        if (!cancelled) setBanner(error instanceof Error ? error.message : "Не удалось загрузить проекты");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [openProject, refreshList]);

  const flush = useCallback(async () => {
    if (savingRef.current) return;
    const snapshot = projectRef.current;
    const id = projectIdRef.current;
    if (!snapshot || !id || !dirtyRef.current) return;
    if (!snapshot.name.trim()) {
      setBanner("У проекта должно быть название");
      return;
    }
    const genAtStart = genRef.current;
    savingRef.current = true;
    setSaving(true);
    try {
      const result = await api.replaceProject(id, toPayload(snapshot));
      if (genRef.current !== genAtStart) {
        setProject((prev) => {
          if (!prev) return prev;
          const next = { ...prev, revision: result.revision };
          projectRef.current = next;
          return next;
        });
        return;
      }
      markSaved(result.project);
      setBanner(null);
      void refreshList();
    } catch (error) {
      if (error instanceof ApiError && error.status === 409 && projectIdRef.current) {
        try {
          const fresh = await api.getProject(projectIdRef.current);
          markSaved(fresh);
          setBanner("Проект изменился на сервере. Показана актуальная версия, это сохранение отменено.");
        } catch {
          setBanner("Конфликт ревизии, и не удалось перечитать проект.");
        }
      } else {
        setBanner(error instanceof Error ? error.message : "Не удалось сохранить");
      }
    } finally {
      savingRef.current = false;
      setSaving(false);
    }
  }, [markSaved, refreshList]);

  useEffect(() => {
    if (!dirty || !projectId) return;
    const timer = window.setTimeout(() => {
      void flush();
    }, 400);
    return () => window.clearTimeout(timer);
  }, [dirty, project, projectId, flush]);

  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    const pull = async () => {
      if (dirtyRef.current || savingRef.current) return;
      try {
        const fresh = await api.getProject(projectId);
        if (cancelled || dirtyRef.current || savingRef.current) return;
        setProject((prev) => {
          if (!prev || prev.revision === fresh.revision) return prev;
          projectRef.current = fresh;
          return fresh;
        });
      } catch {
        /* следующий тик попробует снова */
      }
    };
    const timer = window.setInterval(() => {
      void pull();
    }, 12000);
    const onFocus = () => {
      void pull();
    };
    const onVisible = () => {
      if (document.visibilityState === "visible") void pull();
    };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [projectId]);

  const updateCardData = useCallback((id: string, patch: Partial<CardData>) => {
    edit((current) => ({
      ...current,
      nodes: current.nodes.map((node) =>
        node.id === id ? { ...node, data: { ...node.data, ...patch } } : node,
      ),
    }));
  }, [edit]);

  const actions = useMemo(() => ({ updateCardData }), [updateCardData]);

  const onNodesChange = useCallback((changes: NodeChange[]) => {
    const commitChange = changes.some((change) => {
      if (change.type === "position") return change.dragging === false;
      return change.type === "remove" || change.type === "add";
    });
    setProject((prev) => {
      if (!prev) return prev;
      const next = {
        ...prev,
        nodes: applyNodeChanges(changes, prev.nodes as unknown as Node[]) as unknown as ScriptNode[],
      };
      projectRef.current = next;
      return next;
    });
    if (commitChange) {
      genRef.current += 1;
      dirtyRef.current = true;
      setDirty(true);
    }
  }, []);

  const onEdgesChange = useCallback((changes: EdgeChange[]) => {
    const commitChange = changes.some((change) => change.type === "remove" || change.type === "add");
    setProject((prev) => {
      if (!prev) return prev;
      const next = {
        ...prev,
        edges: applyEdgeChanges(changes, prev.edges) as ScriptEdge[],
      };
      projectRef.current = next;
      return next;
    });
    if (commitChange) {
      genRef.current += 1;
      dirtyRef.current = true;
      setDirty(true);
    }
  }, []);

  const onConnect = useCallback((connection: Connection) => {
    if (!connection.source || !connection.target || connection.source === connection.target) return;
    edit((current) => ({
      ...current,
      edges: addEdge(
        { ...connection, id: `e-${connection.source}-${connection.target}` },
        current.edges,
      ) as ScriptEdge[],
    }));
  }, [edit]);

  function addCard(type: "client" | "our_response") {
    edit((current) => {
      const index = current.nodes.length;
      const node: ScriptNode = {
        id: `node-${Date.now()}`,
        type,
        position: { x: 80 + (index % 3) * 40, y: 80 + index * 30 },
        data: { title: type === "client" ? "Сообщение клиента" : "Наш ответ", text: "" },
        revision: 0,
      };
      return { ...current, nodes: [...current.nodes, node] };
    });
  }

  function addComment() {
    edit((current) => ({
      ...current,
      comments: [
        ...current.comments,
        { id: `comment-${Date.now()}`, x: 24, y: 24 + current.comments.length * 28, text: "" },
      ],
    }));
  }

  function deleteSelected() {
    edit((current) => {
      const selected = new Set(current.nodes.filter((node) => node.selected).map((node) => node.id));
      return {
        ...current,
        nodes: current.nodes.filter((node) => !node.selected),
        edges: current.edges.filter(
          (edge) => !edge.selected && !selected.has(edge.source) && !selected.has(edge.target),
        ),
      };
    });
  }

  async function createProject() {
    const name = draftName.trim();
    if (!name) return;
    const created = await api.createProject({ name, scriptDescription: "" });
    setDraftName("");
    setPickerOpen(false);
    await refreshList();
    await openProject(created.id);
  }

  async function archiveCurrent() {
    if (!project || !projectId) return;
    if (!window.confirm(`Архивировать «${project.name}»?`)) return;
    await flush();
    const revision = projectRef.current?.revision ?? project.revision;
    await api.archiveProject(projectId, revision);
    const items = await refreshList();
    if (items[0]) await openProject(items[0].id);
    else {
      setProject(null);
      setProjectId(null);
      window.localStorage.removeItem(CURRENT_KEY);
    }
  }

  const status = saving ? "Сохранение…" : dirty ? "Есть несохранённые правки" : "Сохранено";

  return (
    <div className="app">
      <header className="topbar">
        <h1>Доска скриптов</h1>
        <input
          type="text"
          aria-label="Название проекта"
          value={project?.name ?? ""}
          disabled={!project}
          onChange={(event) => {
            const value = event.target.value;
            setProject((prev) => {
              if (!prev) return prev;
              const next = { ...prev, name: value };
              projectRef.current = next;
              return next;
            });
            if (value.trim()) {
              genRef.current += 1;
              dirtyRef.current = true;
              setDirty(true);
            }
          }}
        />
        <button type="button" onClick={() => setPickerOpen(true)}>Выбрать проект</button>
        <button type="button" onClick={() => void archiveCurrent()} disabled={!project}>В архив</button>
        <span className="status">
          {project ? `ревизия ${project.revision}` : "нет проекта"} · {project ? status : ""}
        </span>
      </header>
      {banner ? (
        <div className="banner" role="status">
          {banner}
          <button type="button" onClick={() => setBanner(null)}>Скрыть</button>
        </div>
      ) : null}
      <div className="toolbar">
        <button type="button" onClick={() => addCard("client")} disabled={!project}>Сообщение клиента</button>
        <button type="button" onClick={() => addCard("our_response")} disabled={!project}>Наш ответ</button>
        <button type="button" onClick={addComment} disabled={!project}>Комментарий</button>
        <button type="button" onClick={deleteSelected} disabled={!project}>Удалить выбранное</button>
      </div>
      <div className="workspace">
        <div className="canvas">
          <BoardContext.Provider value={actions}>
            <ReactFlow
              key={projectId ?? "empty"}
              nodes={(project?.nodes ?? []) as unknown as Node[]}
              edges={project?.edges ?? []}
              nodeTypes={nodeTypes}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              fitView
              deleteKeyCode={null}
            >
              <Background />
              <Controls />
              <MiniMap />
            </ReactFlow>
          </BoardContext.Provider>
        </div>
        <aside className="side">
          <h2>Контекст для Сони</h2>
          <textarea
            rows={6}
            value={project?.scriptDescription ?? ""}
            disabled={!project}
            placeholder="О чём скрипт, тон, цель переписки"
            onChange={(event) => edit((current) => ({ ...current, scriptDescription: event.target.value }))}
          />
          <h2>Комментарии</h2>
          {(project?.comments ?? []).map((comment) => (
            <div className="comment" key={comment.id}>
              <input
                type="text"
                value={comment.text}
                onChange={(event) =>
                  edit((current) => ({
                    ...current,
                    comments: current.comments.map((item) =>
                      item.id === comment.id ? { ...item, text: event.target.value } : item,
                    ),
                  }))
                }
              />
              <button
                type="button"
                onClick={() =>
                  edit((current) => ({
                    ...current,
                    comments: current.comments.filter((item) => item.id !== comment.id),
                  }))
                }
              >
                Удалить
              </button>
            </div>
          ))}
          {(project?.comments.length ?? 0) === 0 ? <p className="project-list__empty">Нет комментариев</p> : null}
          <h2>История</h2>
          {history.loading ? <p className="project-list__empty">Загрузка…</p> : null}
          {history.error ? <p className="project-list__empty">{history.error}</p> : null}
          <ul className="history">
            {history.events.slice(-20).reverse().map((event) => (
              <li key={event.id}>
                <span className="who">{event.author}</span> · {event.type}
                {event.cardId ? ` · ${event.cardId}` : ""}
                <br />
                <time dateTime={event.ts}>{event.ts}</time>
              </li>
            ))}
          </ul>
        </aside>
      </div>
      {pickerOpen ? (
        <div className="modal-back" onClick={() => setPickerOpen(false)}>
          <div className="modal modal--projects" onClick={(event) => event.stopPropagation()}>
            <h2>Выбрать проект</h2>
            {projects.length === 0 ? <p className="project-list__empty">Пока нет проектов</p> : null}
            <ul className="project-list">
              {projects.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    className="project-list__item"
                    onClick={() => {
                      setPickerOpen(false);
                      void openProject(item.id);
                    }}
                  >
                    {item.name}
                  </button>
                </li>
              ))}
            </ul>
            <div className="modal__row">
              <input
                type="text"
                value={draftName}
                placeholder="Название проекта"
                onChange={(event) => setDraftName(event.target.value)}
              />
              <button type="button" onClick={() => void createProject()}>Создать</button>
            </div>
            <button type="button" onClick={() => setPickerOpen(false)}>Закрыть</button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
