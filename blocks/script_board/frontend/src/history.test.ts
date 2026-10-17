import { describe, expect, it } from "vitest";
import { DEV_HISTORY, formatHistoryTime, selectHistory } from "./history";

describe("history", () => {
  it("в проде пусто, в dev отдаёт макет", () => {
    expect(selectHistory(false)).toEqual([]);
    expect(selectHistory(true)).toBe(DEV_HISTORY);
    expect(DEV_HISTORY.every((entry) => entry.author && entry.summary && entry.at)).toBe(true);
  });

  it("показывает московское время", () => {
    expect(formatHistoryTime("2026-10-17T06:14:00Z")).toBe("17.10.2026 09:14");
  });
});
