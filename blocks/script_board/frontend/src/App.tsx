import { ReactFlowProvider, addEdge, useEdgesState, useNodesState, type Connection, type Edge, type Node } from "@xyflow/react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { BoardProvider, type BoardActions } from "./BoardContext";
import { BoardCanvas } from "./BoardCanvas";
import { readProjectMeta, writeCardMeta, type CardMeta } from "./cardMeta";
import { DescriptionPanel } from "./DescriptionPanel";
import { HistoryPanel } from "./HistoryPanel";
import { exportScriptPdf } from "./pdfExport";
import { ProjectPickerModal } from "./ProjectPickerModal";
import {
  createProject,
  getCurrentProjectId,
  getProjectName,
  listProjects,
  loadProject,
  saveProject,
  setCurrentProjectId,
  type ProjectListItem,
} from "./projectsStorage";
import {
  linearizeScript,
  normalizeEdges,
  normalizeNodes,
  toStoredRecord,
  writeCardText,
} from "./scriptModel";
import { Toolbar } from "./Toolbar";
import { useHistory } from "./useHistory";
import { useMediaQuery } from "./useMediaQuery";

interface ProjectState {
  id: string;
  name: string;
  nodes: Node[];
  edges: Edge[];
  scriptDescription: string;
}

function getInitialProjectState(): ProjectState {
  const current = getCurrentProjectId();
  if (current) {
    const project = loadProject(current);
    if (project) {
      return {
        id: current,
        name: project.name,
        nodes: normalizeNodes(project.nodes),
        edges: normalizeEdges(project.edges),
        scriptDescription: project.scriptDescription,
      };
    }
  }
  const existing = listProjects();
  if (existing.length > 0) {
    const first = existing[0];
    const project = loadProject(first.id);
    setCurrentProjectId(first.id);
    return {
      id: first.id,
      name: project?.name ?? first.name,
      nodes: normalizeNodes(project?.nodes ?? []),
      edges: normalizeEdges(project?.edges ?? []),
      scriptDescription: project?.scriptDescription ?? "",
    };
  }
  const id = createProject("Проект 1");
  setCurrentProjectId(id);
  return { id, name: "Проект 1", nodes: [], edges: [], scriptDescription: "" };
}

function nextCardPosition(nodes: Node[], edges: Edge[], selected: Node | undefined): { x: number; y: number } {
  if (!selected) {
    if (nodes.length === 0) return { x: 80, y: 120 };
    const maxX = nodes.reduce((max, node) => Math.max(max, node.position.x), 0);
    return { x: maxX + 280, y: 120 };
  }
  const siblings = edges.filter((edge) => edge.source === selected.id).length;
  return { x: selected.position.x + 280, y: selected.position.y + siblings * 156 };
}

export default function App() {
  const initial = useRef(getInitialProjectState()).current;
  const [currentProjectId, setProjectId] = useState(initial.id);
  const [projectName, setProjectName] = useState(initial.name);
  const [projects, setProjects] = useState<ProjectListItem[]>(() => listProjects());
  const [projectPickerOpen, setProjectPickerOpen] = useState(false);
  const [nodes, setNodes, onNodesChange] = useNodesState(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initial.edges);
  const [scriptDescription, setScriptDescription] = useState(initial.scriptDescription);
  const [meta, setMeta] = useState<Record<string, CardMeta>>(() => readProjectMeta(initial.id));
  const [toast, setToast] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const isMobile = useMediaQuery("(max-width: 760px)");
  const [descOpen, setDescOpen] = useState(() => !isMobile);
  const [histOpen, setHistOpen] = useState(() => !isMobile);
  const history = useHistory(currentProjectId);
  const skipSave = useRef(true);
  const wasMobile = useRef(isMobile);

  useEffect(() => {
    if (wasMobile.current === isMobile) return;
    wasMobile.current = isMobile;
    if (isMobile) {
      setDescOpen(false);
      setHistOpen(false);
    }
  }, [isMobile]);

  useEffect(() => {
    if (skipSave.current) {
      skipSave.current = false;
      return;
    }
    const timer = window.setTimeout(() => {
      saveProject(
        currentProjectId,
        getProjectName(currentProjectId) || projectName,
        nodes.map((node) => toStoredRecord(node)),
        edges.map((edge) => toStoredRecord(edge)),
        scriptDescription,
      );
    }, 200);
    return () => window.clearTimeout(timer);
  }, [nodes, edges, scriptDescription, currentProjectId, projectName]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 1600);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const applyProject = useCallback((id: string) => {
    const project = loadProject(id);
    if (!project) return;
    skipSave.current = true;
    setCurrentProjectId(id);
    setProjectId(id);
    setProjectName(project.name);
    setNodes(normalizeNodes(project.nodes));
    setEdges(normalizeEdges(project.edges));
    setScriptDescription(project.scriptDescription);
    setMeta(readProjectMeta(id));
    setProjects(listProjects());
    setProjectPickerOpen(false);
  }, [setEdges, setNodes]);

  const handleSelectProject = useCallback((id: string) => {
    applyProject(id);
  }, [applyProject]);

  const handleCreateProject = useCallback((name: string) => {
    const id = createProject(name);
    setCurrentProjectId(id);
    applyProject(id);
  }, [applyProject]);

  const onConnect = useCallback((connection: Connection) => {
    setEdges((current) => addEdge({ ...connection, type: "smoothstep" }, current));
  }, [setEdges]);

  const addCard = useCallback((role: "client" | "answer") => {
    const selected = nodes.find((node) => node.selected);
    const id = crypto.randomUUID();
    const position = nextCardPosition(nodes, edges, selected);
    const node: Node = {
      id,
      type: role,
      position,
      data: { text: "" },
      selected: true,
    };
    setNodes((current) => {
      const next: Node[] = current.map((item) => ({ ...item, selected: false }));
      next.push(node);
      return next;
    });
    if (selected) {
      setEdges((current) =>
        addEdge({ source: selected.id, target: id, sourceHandle: null, targetHandle: null }, current),
      );
    }
    setMeta(writeCardMeta(currentProjectId, id, { author: "Алексей", edited: false }));
  }, [currentProjectId, edges, nodes, setEdges, setNodes]);

  const deleteSelected = useCallback(() => {
    const selectedIds = new Set(nodes.filter((node) => node.selected).map((node) => node.id));
    if (selectedIds.size === 0 && !edges.some((edge) => edge.selected)) return;
    setNodes((current) => current.filter((node) => !node.selected));
    setEdges((current) =>
      current.filter((edge) => !edge.selected && !selectedIds.has(edge.source) && !selectedIds.has(edge.target)),
    );
  }, [edges, nodes, setEdges, setNodes]);

  const onText = useCallback((id: string, text: string) => {
    setNodes((current) =>
      current.map((node) => (node.id === id ? { ...node, data: writeCardText(node.data, text) } : node)),
    );
    setMeta(writeCardMeta(currentProjectId, id, { author: "Алексей", edited: true }));
  }, [currentProjectId, setNodes]);

  const onCopy = useCallback(async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setToast("Скопировано");
    } catch {
      setToast("Не удалось скопировать");
    }
  }, []);

  const onExport = useCallback(async () => {
    setExporting(true);
    try {
      await exportScriptPdf({
        name: projectName,
        scriptDescription,
        lines: linearizeScript(nodes, edges),
      });
    } catch {
      setToast("Не удалось собрать PDF");
    } finally {
      setExporting(false);
    }
  }, [edges, nodes, projectName, scriptDescription]);

  const toggleDesc = useCallback(() => {
    setDescOpen((open) => {
      const next = !open;
      if (next && isMobile) setHistOpen(false);
      return next;
    });
  }, [isMobile]);

  const toggleHist = useCallback(() => {
    setHistOpen((open) => {
      const next = !open;
      if (next && isMobile) setDescOpen(false);
      return next;
    });
  }, [isMobile]);

  const actions = useMemo<BoardActions>(() => ({
    metaFor: (cardId) => meta[cardId] ?? { author: "Соня", edited: false },
    onText,
    onCopy: (text) => {
      void onCopy(text);
    },
  }), [meta, onCopy, onText]);

  const sheetOpen = isMobile && (descOpen || histOpen);

  return (
    <ReactFlowProvider>
      <BoardProvider value={actions}>
        <div className="app">
          <h1 className="visually-hidden">Доска скриптов</h1>
          <Toolbar
            projectName={projectName}
            descOpen={descOpen}
            histOpen={histOpen}
            canDelete={nodes.some((node) => node.selected) || edges.some((edge) => edge.selected)}
            onOpenProjects={() => {
              setProjects(listProjects());
              setProjectPickerOpen(true);
            }}
            onAddClient={() => addCard("client")}
            onAddAnswer={() => addCard("answer")}
            onDelete={deleteSelected}
            onExport={() => {
              void onExport();
            }}
            exporting={exporting}
            onToggleDesc={toggleDesc}
            onToggleHist={toggleHist}
          />
          <div className="workspace">
            <DescriptionPanel
              open={descOpen}
              value={scriptDescription}
              onChange={setScriptDescription}
              onClose={() => setDescOpen(false)}
            />
            <BoardCanvas
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
            />
            <HistoryPanel
              open={histOpen}
              items={history.items}
              loading={history.loading}
              onClose={() => setHistOpen(false)}
            />
          </div>
          {sheetOpen ? (
            <button
              type="button"
              className="sheet-backdrop"
              aria-label="Закрыть панель"
              onClick={() => {
                setDescOpen(false);
                setHistOpen(false);
              }}
            />
          ) : null}
          <ProjectPickerModal
            open={projectPickerOpen}
            projects={projects}
            onCreateProject={handleCreateProject}
            onSelectProject={handleSelectProject}
            onClose={() => setProjectPickerOpen(false)}
          />
          {toast ? <div className="toast" role="status">{toast}</div> : null}
        </div>
      </BoardProvider>
    </ReactFlowProvider>
  );
}
