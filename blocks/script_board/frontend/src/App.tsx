import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ReactFlow,
  addEdge,
  useNodesState,
  useEdgesState,
  useReactFlow,
  type Connection,
  type Node,
  type Edge,
  type NodeTypes,
  type NodeChange,
  Controls,
  Background,
  BackgroundVariant,
} from "@xyflow/react";
import { nodeTypes } from "./nodes";
import { getAncestorIds, CARD_LAYOUT, computeLayoutPositions } from "./utils";
import type { CardData } from "./types";
import TextEditorModal from "./TextEditorModal";
import SettingsModal from "./SettingsModal";
import ProjectPickerModal from "./ProjectPickerModal";
import AddCommentModal from "./AddCommentModal";
import ViewCommentModal from "./ViewCommentModal";
import {
  getCurrentProjectId,
  setCurrentProjectId,
  listProjects,
  loadProject,
  saveProject,
  createProject,
} from "./projectsStorage";
import type { CommentItem } from "./projectsStorage";
import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";
import "@xyflow/react/dist/style.css";
import "./App.css";

type CardNode = Node<CardData>;

function buildMessages(
  nodeIds: string[],
  nodes: CardNode[],
): { role: "user" | "assistant"; content: string }[] {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const out: { role: "user" | "assistant"; content: string }[] = [];
  for (const id of nodeIds) {
    const n = byId.get(id);
    if (!n) continue;
    const role = n.type === "client" ? "user" : "assistant";
    out.push({ role, content: (n.data?.text as string) ?? "" });
  }
  return out;
}

function App() {
  const [loading, setLoading] = useState(true);
  const [currentProjectId, setCurrentProjectIdState] = useState<string | null>(null);
  const [projectName, setProjectName] = useState("");
  const [nodes, setNodes, builtInOnNodesChange] = useNodesState<CardNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [scriptDescription, setScriptDescription] = useState("");
  const [editingNodeId, setEditingNodeId] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [projectPickerOpen, setProjectPickerOpen] = useState(false);
  const [projectsList, setProjectsList] = useState<{ id: string; name: string }[]>([]);
  const [comments, setComments] = useState<CommentItem[]>([]);
  const [commentMode, setCommentMode] = useState(false);
  const [addCommentPosition, setAddCommentPosition] = useState<{ x: number; y: number } | null>(null);
  const [viewCommentId, setViewCommentId] = useState<string | null>(null);
  const { screenToFlowPosition } = useReactFlow();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const list = await listProjects();
      if (cancelled) return;
      let id = getCurrentProjectId();
      const exists = id && list.some((p) => p.id === id);
      if (!id || !exists) {
        if (list.length > 0) {
          id = list[0].id;
          setCurrentProjectId(id);
        } else {
          id = await createProject("Проект 1");
          setCurrentProjectId(id);
          setCurrentProjectIdState(id);
          setNodes([]);
          setEdges([]);
          setScriptDescription("");
          setProjectName("Проект 1");
          setLoading(false);
          return;
        }
      }
      setCurrentProjectIdState(id);
      const loaded = await loadProject(id);
      if (cancelled) return;
      if (loaded) {
        setNodes(loaded.nodes);
        setEdges(loaded.edges);
        setScriptDescription(loaded.scriptDescription);
        setProjectName(loaded.name);
        setComments(loaded.comments ?? []);
      }
      setLoading(false);
    })();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!currentProjectId || loading) return;
    const t = setTimeout(
      () =>
        saveProject(currentProjectId, projectName || "Без названия", nodes, edges, scriptDescription, comments),
      400,
    );
    return () => clearTimeout(t);
  }, [currentProjectId, projectName, nodes, edges, scriptDescription, comments, loading]);

  const handleSelectProject = useCallback(
    async (id: string) => {
      const loaded = await loadProject(id);
      if (!loaded) return;
      setCurrentProjectId(id);
      setCurrentProjectIdState(id);
      setNodes(loaded.nodes);
      setEdges(loaded.edges);
      setScriptDescription(loaded.scriptDescription);
      setProjectName(loaded.name);
      setComments(loaded.comments ?? []);
      setProjectPickerOpen(false);
    },
    [setNodes, setEdges],
  );

  const handleCreateProject = useCallback(
    async (name: string) => {
      const id = await createProject(name);
      setCurrentProjectId(id);
      setCurrentProjectIdState(id);
      setNodes([]);
      setEdges([]);
      setScriptDescription("");
      setProjectName(name.trim() || "Новый проект");
      setComments([]);
      setProjectPickerOpen(false);
    },
    [setNodes, setEdges],
  );

  const openProjectPicker = useCallback(() => {
    setProjectPickerOpen(true);
    listProjects().then(setProjectsList);
  }, []);

  const onConnect = useCallback(
    (conn: Connection) => setEdges((eds) => addEdge(conn, eds)),
    [setEdges],
  );

  const addNode = useCallback(
    (type: "client" | "our_response") => {
      const id = `node-${Date.now()}`;
      const title = type === "client" ? "Сообщение клиента" : "Наш ответ";
      setNodes((nds) => [
        ...nds,
        {
          id,
          type,
          position: {
            x: 100 + nds.length * CARD_LAYOUT.stepX,
            y: 100,
          },
          data: { title, text: "" } as CardData,
        } as CardNode,
      ]);
    },
    [setNodes],
  );

  const handleAddChild = useCallback(
    (sourceNodeId: string, type: "client" | "our_response") => {
      const source = nodes.find((n) => n.id === sourceNodeId);
      if (!source) return;
      const childCount = edges.filter((e) => e.source === sourceNodeId).length;
      const newId = `node-${Date.now()}`;
      const title = type === "client" ? "Сообщение клиента" : "Наш ответ";
      const sx = source.position?.x ?? 0;
      const sy = source.position?.y ?? 0;
      const parentCenterX = sx + CARD_LAYOUT.width / 2;
      const newY = sy + CARD_LAYOUT.height + CARD_LAYOUT.vGap;
      let newX: number;
      if (childCount === 0) {
        newX = parentCenterX - CARD_LAYOUT.width / 2;
      } else {
        const totalChildren = childCount + 1;
        const gap = CARD_LAYOUT.hGap;
        const totalWidth =
          totalChildren * CARD_LAYOUT.width + (totalChildren - 1) * gap;
        const startX = parentCenterX - totalWidth / 2;
        newX = startX + childCount * (CARD_LAYOUT.width + gap);
      }
      setNodes((nds) => [
        ...nds,
        {
          id: newId,
          type,
          position: { x: newX, y: newY },
          data: { title, text: "" } as CardData,
        } as CardNode,
      ]);
      setEdges((eds) => [
        ...eds,
        { id: `e-${sourceNodeId}-${newId}`, source: sourceNodeId, target: newId },
      ]);
    },
    [nodes, edges, setNodes, setEdges],
  );

  const handleOpenTextEditor = useCallback((nodeId: string) => setEditingNodeId(nodeId), []);

  const handleTitleChange = useCallback(
    (nodeId: string, title: string) => {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === nodeId ? { ...n, data: { ...n.data, title } } : n,
        ),
      );
    },
    [setNodes],
  );

  const handleDuplicate = useCallback(
    (nodeId: string) => {
      const node = nodes.find((n) => n.id === nodeId);
      if (!node) return;
      const newId = `node-${Date.now()}`;
      const newNode: CardNode = {
        ...node,
        id: newId,
        position: {
          x: (node.position?.x ?? 0) + CARD_LAYOUT.stepX,
          y: (node.position?.y ?? 0) + CARD_LAYOUT.vGap,
        },
        data: {
          ...node.data,
          title: (node.data?.title as string) ?? "",
          text: (node.data?.text as string) ?? "",
        } as CardData,
      };
      setNodes((nds) => [...nds, newNode]);
    },
    [nodes, setNodes],
  );

  const handleDelete = useCallback(
    (nodeId: string) => {
      setNodes((nds) => nds.filter((n) => n.id !== nodeId));
      setEdges((eds) =>
        eds.filter((e) => e.source !== nodeId && e.target !== nodeId),
      );
    },
    [setNodes, setEdges],
  );

  const handleCopy = useCallback(
    (nodeId: string) => {
      const n = nodes.find((n) => n.id === nodeId);
      const text = (n?.data?.text as string) ?? "";
      if (text) navigator.clipboard.writeText(text);
    },
    [nodes],
  );
  const handleGenerate = useCallback(
    async (nodeId: string) => {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === nodeId ? { ...n, data: { ...n.data, generating: true } } : n,
        ),
      );
      const ancestorIds = getAncestorIds(nodeId, nodes as Node[], edges);
      const orderedIds = [...ancestorIds, nodeId];
      const messages = buildMessages(orderedIds, nodes);
      try {
        const res = await fetch("/api/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            script_description: scriptDescription || null,
            messages,
          }),
        });
        const json = await res.json();
        setNodes((nds) =>
          nds.map((n) => {
            if (n.id !== nodeId) return n;
            return {
              ...n,
              data: {
                ...n.data,
                text: json.success ? json.text ?? "" : (n.data?.text as string) ?? "",
                generating: false,
              },
            };
          }),
        );
      } catch {
        setNodes((nds) =>
          nds.map((n) =>
            n.id === nodeId ? { ...n, data: { ...n.data, generating: false } } : n,
          ),
        );
      }
    },
    [nodes, edges, scriptDescription, setNodes],
  );

  const nodesWithCallbacks = useMemo(
    () =>
      nodes.map((n) => ({
        ...n,
        data: {
          ...n.data,
          onOpenTextEditor: handleOpenTextEditor,
          onTitleChange: handleTitleChange,
          onCopy: handleCopy,
          onDuplicate: handleDuplicate,
          onAddChild: handleAddChild,
          onDelete: handleDelete,
          onGenerate: n.type === "our_response" ? handleGenerate : undefined,
        } as CardData,
      })),
    [nodes, handleOpenTextEditor, handleTitleChange, handleCopy, handleDuplicate, handleAddChild, handleDelete, handleGenerate],
  );

  const commentNodes: Node[] = useMemo(
    () =>
      comments.map((c) => ({
        id: c.id,
        type: "comment",
        position: { x: c.x, y: c.y },
        data: { text: c.text, onOpen: (commentId: string) => setViewCommentId(commentId) },
        draggable: true,
      })),
    [comments],
  );

  const displayNodes = useMemo(
    () => [...nodesWithCallbacks, ...commentNodes],
    [nodesWithCallbacks, commentNodes],
  );

  const handleNodesChange = useCallback(
    (changes: NodeChange[]) => {
      const cardChanges = changes.filter(
        (c) => !(("id" in c) && typeof (c as { id?: string }).id === "string" && ((c as { id?: string }).id ?? "").startsWith("comment-")),
      );
      if (cardChanges.length > 0) {
        builtInOnNodesChange(cardChanges as NodeChange<CardNode>[]);
      }
      const commentPosChanges = changes.filter(
        (c) => c.type === "position" && ("id" in c) && ((c as { id?: string }).id ?? "").startsWith("comment-") && "position" in c,
      );
      if (commentPosChanges.length > 0) {
        setComments((prev) =>
          prev.map((cm) => {
            const ch = commentPosChanges.find((c) => (c as { id?: string }).id === cm.id);
            if (ch && "position" in ch) {
              const pos = (ch as { position?: { x: number; y: number } }).position;
              if (pos) return { ...cm, x: pos.x, y: pos.y };
            }
            return cm;
          }),
        );
      }
    },
    [builtInOnNodesChange],
  );

  const handlePaneClick = useCallback(
    (event: React.MouseEvent) => {
      if (!commentMode) return;
      const pos = screenToFlowPosition({ x: event.clientX, y: event.clientY });
      setAddCommentPosition({ x: pos.x, y: pos.y });
    },
    [commentMode, screenToFlowPosition],
  );

  const handleAddComment = useCallback((text: string) => {
    if (!addCommentPosition) return;
    const id = `comment-${Date.now()}`;
    setComments((prev) => [
      ...prev,
      { id, x: addCommentPosition.x, y: addCommentPosition.y, text },
    ]);
    setAddCommentPosition(null);
  }, [addCommentPosition]);

  const handleResolveComment = useCallback(() => {
    if (!viewCommentId) return;
    setComments((prev) => prev.filter((c) => c.id !== viewCommentId));
    setViewCommentId(null);
  }, [viewCommentId]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && (e.key === "d" || e.key === "D" || e.key === "в" || e.key === "В")) {
        e.preventDefault();
        const selected = nodes.filter((n) => n.selected);
        if (selected.length > 0) {
          selected.forEach((n) => handleDuplicate(n.id));
        }
      }
      if (e.key === "Delete" || e.key === "Backspace") {
        const target = e.target as HTMLElement;
        if (target.closest("input") || target.closest("textarea")) return;
        const selected = nodes.filter((n) => n.selected);
        if (selected.length > 0) {
          e.preventDefault();
          selected.forEach((n) => handleDelete(n.id));
        }
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [nodes, handleDuplicate, handleDelete]);

  const handleSaveText = useCallback(
    (nodeId: string, text: string, title: string) => {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === nodeId ? { ...n, data: { ...n.data, text, title } } : n,
        ),
      );
      setEditingNodeId(null);
    },
    [setNodes],
  );

  const flowContainerRef = useRef<HTMLDivElement>(null);

  const handleArrange = useCallback(() => {
    const layout = computeLayoutPositions(nodes, edges);
    setNodes((nds) =>
      nds.map((n) => {
        const pos = layout.get(n.id);
        if (!pos) return n;
        return { ...n, position: pos };
      }),
    );
  }, [nodes, edges, setNodes]);

  const handleDownloadPdf = useCallback(async () => {
    const el = flowContainerRef.current;
    if (!el) return;
    try {
      const canvas = await html2canvas(el, {
        useCORS: true,
        scale: 2,
        logging: false,
        backgroundColor: "#ffffff",
      });
      const imgData = canvas.toDataURL("image/png");
      const doc = new jsPDF({
        orientation: canvas.width > canvas.height ? "landscape" : "portrait",
        unit: "mm",
        format: "a4",
      });
      const pageW = doc.internal.pageSize.getWidth();
      const pageH = doc.internal.pageSize.getHeight();
      const margin = 10;
      const w = pageW - 2 * margin;
      const h = pageH - 2 * margin;
      const k = Math.min(w / canvas.width, h / canvas.height);
      const imgW = canvas.width * k;
      const imgH = canvas.height * k;
      doc.addImage(imgData, "PNG", margin, margin, imgW, imgH);
      doc.save("script-board.pdf");
    } catch (err) {
      console.error("PDF export failed:", err);
    }
  }, []);

  if (loading) {
    return (
      <div className="app app--loading">
        <div className="app__loading">Загрузка проектов…</div>
      </div>
    );
  }

  return (
    <div className="app">
      <input className="panel-toggle" type="checkbox" id="desc-open" defaultChecked />
      <input className="panel-toggle" type="checkbox" id="hist-open" defaultChecked />
      <header className="toolbar">
        <div className="brand">
          <span className="logo">
            FL<span className="logo-o">O</span>W
          </span>
          <span className="brand-name">Доска скриптов</span>
        </div>
        <span className="sep" />
        <button
          type="button"
          className="tool tool-project"
          onClick={openProjectPicker}
          title="Выбрать проект"
        >
          <span className="kicker">Выбрать проект</span>
          <span className="pname">{projectName || "Без названия"}</span>
        </button>
        <span className="sep" />
        <button
          type="button"
          className="tool"
          onClick={() => addNode("client")}
          title="Добавить сообщение клиента"
        >
          + Клиент
        </button>
        <button
          type="button"
          className="tool"
          onClick={() => addNode("our_response")}
          title="Добавить наш ответ"
        >
          + Ответ
        </button>
        <button
          type="button"
          className={commentMode ? "tool tool--active" : "tool"}
          onClick={() => setCommentMode((v) => !v)}
          title="Режим комментирования: клик по полю создаёт комментарий"
          aria-pressed={commentMode}
        >
          {commentMode ? "✓ Комментарии" : "Комментарии"}
        </button>
        <button
          type="button"
          className="tool"
          onClick={handleArrange}
          title="Выровнять карточки по уровням"
        >
          Упорядочить
        </button>
        <button type="button" className="tool" onClick={handleDownloadPdf} title="Скачать в PDF">
          PDF
        </button>
        <span className="spacer" />
        <label className="tool tool-desc" htmlFor="desc-open">
          Описание
        </label>
        <button type="button" className="tool" onClick={() => setSettingsOpen(true)} title="Настройки скрипта">
          Настройки
        </button>
        <label className="tool tool-hist" htmlFor="hist-open">
          История
        </label>
      </header>
      <div className="workspace">
        <aside className="panel panel-desc" aria-label="Описание проекта">
          <span className="panel__handle" aria-hidden />
          <div className="panel__head">
            <h2>Описание проекта</h2>
            <label className="panel__x" htmlFor="desc-open" aria-label="Свернуть описание">
              ×
            </label>
          </div>
          <textarea
            className="panel__desc"
            value={scriptDescription}
            onChange={(e) => setScriptDescription(e.target.value)}
            placeholder="Описание проекта / скрипта"
          />
        </aside>
        <div
          ref={flowContainerRef}
          className={commentMode ? "app__flow-wrap app__flow-wrap--comment" : "app__flow-wrap"}
        >
          <ReactFlow
            nodes={displayNodes}
            edges={edges}
            onNodesChange={handleNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onPaneClick={handlePaneClick}
            nodeTypes={nodeTypes as NodeTypes}
            panOnDrag
            panActivationKeyCode="Space"
            fitView
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={18}
              size={1}
              color="rgba(10,10,10,0.28)"
              bgColor="#f0ede6"
            />
            <Controls />
          </ReactFlow>
        </div>
        <aside className="panel panel-hist" aria-label="История изменений">
          <span className="panel__handle" aria-hidden />
          <div className="panel__head">
            <h2>История изменений</h2>
            <label className="panel__x" htmlFor="hist-open" aria-label="Свернуть историю">
              ×
            </label>
          </div>
          <div className="history" id="history-slot" data-history-hook="" />
        </aside>
        <label className="backdrop backdrop-desc" htmlFor="desc-open" aria-label="Закрыть описание" />
        <label className="backdrop backdrop-hist" htmlFor="hist-open" aria-label="Закрыть историю" />
      </div>

      <TextEditorModal
        nodeId={editingNodeId}
        nodes={nodes}
        scriptDescription={scriptDescription}
        onSave={handleSaveText}
        onClose={() => setEditingNodeId(null)}
      />
      <SettingsModal
        open={settingsOpen}
        scriptDescription={scriptDescription}
        onScriptDescriptionChange={setScriptDescription}
        onClose={() => setSettingsOpen(false)}
      />
      <ProjectPickerModal
        open={projectPickerOpen}
        projects={projectsList}
        onCreateProject={handleCreateProject}
        onSelectProject={handleSelectProject}
        onClose={() => setProjectPickerOpen(false)}
      />
      {addCommentPosition && (
        <AddCommentModal
          x={addCommentPosition.x}
          y={addCommentPosition.y}
          onSave={handleAddComment}
          onClose={() => setAddCommentPosition(null)}
        />
      )}
      {viewCommentId && (() => {
        const comment = comments.find((c) => c.id === viewCommentId);
        return comment ? (
          <ViewCommentModal
            text={comment.text}
            onResolve={handleResolveComment}
            onClose={() => setViewCommentId(null)}
          />
        ) : null;
      })()}
    </div>
  )
}

export default App;
