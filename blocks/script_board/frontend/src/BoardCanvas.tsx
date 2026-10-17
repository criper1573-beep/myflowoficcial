import {
  Background,
  BackgroundVariant,
  MarkerType,
  ReactFlow,
  type Connection,
  type Edge,
  type Node,
  type OnEdgesChange,
  type OnNodesChange,
} from "@xyflow/react";
import { nodeTypes } from "./ScriptCard";

interface BoardCanvasProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: (connection: Connection) => void;
}

const marker = {
  type: MarkerType.ArrowClosed,
  width: 14,
  height: 14,
  color: "#0a0a0a",
};

export function BoardCanvas({ nodes, edges, onNodesChange, onEdgesChange, onConnect }: BoardCanvasProps) {
  const displayEdges = edges.map((edge) => ({
    ...edge,
    type: edge.type && edge.type !== "default" ? edge.type : "smoothstep",
    markerEnd: edge.markerEnd ?? marker,
    pathOptions: { borderRadius: 6 },
  }));

  return (
    <div className="canvas">
      <ReactFlow
        nodes={nodes}
        edges={displayEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.25}
        maxZoom={1.75}
        proOptions={{ hideAttribution: true }}
        deleteKeyCode={["Backspace", "Delete"]}
        selectionOnDrag={false}
        panOnScroll
        zoomOnPinch
        zoomOnDoubleClick={false}
        defaultEdgeOptions={{ type: "smoothstep", markerEnd: marker }}
        connectionLineStyle={{ stroke: "rgba(10,10,10,0.55)", strokeWidth: 1.25 }}
      >
        <Background variant={BackgroundVariant.Dots} gap={18} size={1.1} color="rgba(10,10,10,0.28)" />
      </ReactFlow>
      {nodes.length === 0 ? (
        <p className="board-empty">Нет карточек. Добавьте «Клиент» или «Ответ».</p>
      ) : null}
    </div>
  );
}
