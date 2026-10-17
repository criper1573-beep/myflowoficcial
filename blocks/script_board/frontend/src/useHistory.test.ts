import { act, createElement } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it } from "vitest";
import { useHistory, type HistoryItem } from "./useHistory";

describe("useHistory", () => {
  it("returns an empty list and is not loading", async () => {
    (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
    const host = document.createElement("div");
    document.body.appendChild(host);
    let snapshot: { items: HistoryItem[]; loading: boolean } | null = null;

    function Probe({ id }: { id: string }) {
      snapshot = useHistory(id);
      return null;
    }

    const root = createRoot(host);
    await act(async () => {
      root.render(createElement(Probe, { id: "project-1" }));
    });
    expect(snapshot).toEqual({ items: [], loading: false });
    await act(async () => {
      root.unmount();
    });
    host.remove();
  });
});
