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
  Panel,
} from "@xyflow/react";
import { nodeTypes } from "./nodes";
import { CARD_LAYOUT, computeLayoutPositions } from "./utils";
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
  createProject,
} from "./projectsStorage";
import { useAutosave } from "./useAutosave";
import type { CommentItem } from "./projectsStorage";
import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";
import "@xyflow/react/dist/style.css";
import "./App.css";

type CardNode = Node<CardData>;

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
  const [revision, setRevision] = useState(0);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [commentMode, setCommentMode] = useState(false);
  const [addCommentPosition, setAddCommentPosition] = useState<{ x: number; y: number } | null>(null);
  const [viewCommentId, setViewCommentId] = useState<string | null>(null);
  const { screenToFlowPosition } = useReactFlow();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await listProjects();
        if (cancelled) return;
        let id = getCurrentProjectId();
        const exists = id && list.some((p) => p.id === id);
        if (!id || !exists) {
          if (list.length > 0) {
            id = list[0].id;
            setCurrentProjectId(id);
          } else {
            const created = await createProject("Проект 1");
            if (cancelled) return;
            setCurrentProjectId(created.id);
            setCurrentProjectIdState(created.id);
            setRevision(created.revision);
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
          setRevision(loaded.revision);
        }
        setLoading(false);
      } catch (error) {
        if (cancelled) return;
        setSyncMessage(error instanceof Error ? error.message : "Не удалось загрузить проекты");
        setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

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
      setRevision(loaded.revision);
      setProjectPickerOpen(false);
    },
    [setNodes, setEdges],
  );

  const handleCreateProject = useCallback(
    async (name: string) => {
      const created = await createProject(name);
      setCurrentProjectId(created.id);
      setCurrentProjectIdState(created.id);
      setRevision(created.revision);
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
        } as CardData,
      })),
    [nodes, handleOpenTextEditor, handleTitleChange, handleCopy, handleDuplicate, handleAddChild, handleDelete],
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

  const reloadFromServer = useCallback(async () => {
    if (!currentProjectId) return;
    const loaded = await loadProject(currentProjectId);
    if (!loaded) return;
    setNodes(loaded.nodes);
    setEdges(loaded.edges);
    setScriptDescription(loaded.scriptDescription);
    setProjectName(loaded.name);
    setComments(loaded.comments ?? []);
    setRevision(loaded.revision);
  }, [currentProjectId, setNodes, setEdges]);

  useAutosave({
    enabled: !loading && !!currentProjectId,
    snapshot: {
      projectId: currentProjectId,
      revision,
      name: projectName || "Без названия",
      nodes,
      edges,
      scriptDescription,
      comments,
    },
    onRevision: setRevision,
    onConflict: async () => {
      await reloadFromServer();
      setSyncMessage("Проект изменился на сервере. Показана актуальная версия, это сохранение отменено.");
    },
    onRemote: async () => {
      await reloadFromServer();
    },
    onError: setSyncMessage,
    onClearError: () => setSyncMessage(null),
  });

  if (loading) {
    return (
      <div className="app app--loading">
        <div className="app__loading">Загрузка проектов…</div>
      </div>
    );
  }

  return (
    <div className="app">
      <div ref={flowContainerRef} className="app__flow-wrap">
      {syncMessage && (
        <div className="app__sync" role="status">
          {syncMessage}
        </div>
      )}
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
        <Controls />
        <Panel position="top-left" className="toolbar">
          <button type="button" onClick={() => addNode("client")}>
            + Сообщение клиента
          </button>
          <button type="button" onClick={() => addNode("our_response")}>
            + Наш ответ
          </button>
          <button
            type="button"
            className={commentMode ? "toolbar__btn--active" : ""}
            onClick={() => setCommentMode((v) => !v)}
            title="Режим комментирования: клик по полю создаёт комментарий"
          >
            {commentMode ? "✓ Режим комментирования" : "Режим комментирования"}
          </button>
        </Panel>
        <Panel position="top-right" className="toolbar toolbar--right">
          <button type="button" onClick={openProjectPicker}>
            Выбрать проект
          </button>
          <button type="button" onClick={() => setSettingsOpen(true)}>
            Настройки скрипта
          </button>
          <button type="button" onClick={handleDownloadPdf}>
            Скачать в PDF
          </button>
        </Panel>
        <Panel position="bottom-right" className="toolbar toolbar--bottom-right">
          <button type="button" onClick={handleArrange} title="Выровнять карточки по уровням">
            Упорядочить
          </button>
        </Panel>
      </ReactFlow>
      </div>

      <TextEditorModal
        nodeId={editingNodeId}
        nodes={nodes}
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
