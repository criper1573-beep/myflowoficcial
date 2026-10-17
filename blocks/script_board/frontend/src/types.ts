export type CardNodeType = "client" | "our_response";

export interface CardData extends Record<string, unknown> {
  title: string;
  text: string;
  generating?: boolean;
  onOpenTextEditor?: (nodeId: string) => void;
  onCopy?: (nodeId: string) => void;
  onGenerate?: (nodeId: string) => void;
  onDuplicate?: (nodeId: string) => void;
  onTitleChange?: (nodeId: string, title: string) => void;
  onAddChild?: (nodeId: string, type: "client" | "our_response") => void;
  onDelete?: (nodeId: string) => void;
}

export interface GenerateResponse {
  success: boolean;
  text?: string;
  error?: string;
}
