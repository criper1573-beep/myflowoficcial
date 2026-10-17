const KEY = "script_board_right_panel";

export type SideTab = "goals" | "history";

export interface SidePanelState {
  open: boolean;
  tab: SideTab;
}

/** Открыта ли правая панель и какая вкладка. Только это, не содержимое целей. */
export function readSidePanel(): SidePanelState {
  const raw = localStorage.getItem(KEY);
  if (raw === "history") return { open: true, tab: "history" };
  if (raw === "closed") return { open: false, tab: "goals" };
  return { open: true, tab: "goals" };
}

export function writeSidePanel(state: SidePanelState) {
  localStorage.setItem(KEY, state.open ? state.tab : "closed");
}
