import { beforeEach, describe, expect, it } from "vitest";
import { CARD_META_KEY, readCardMeta, readProjectMeta, writeCardMeta } from "./cardMeta";
import { PROJECTS_KEY, saveProject } from "./projectsStorage";

describe("cardMeta", () => {
  beforeEach(() => localStorage.clear());

  it("по умолчанию Соня и не пишет метаданные в проект", () => {
    expect(readCardMeta("p", "c")).toEqual({ author: "Соня", edited: false });
    writeCardMeta("p", "c", { author: "Алексей", edited: true });
    expect(readProjectMeta("p").c).toEqual({ author: "Алексей", edited: true });
    saveProject("p", "Проект", [{ id: "c", data: { text: "а" } }], [], "");
    const project = JSON.parse(localStorage.getItem(PROJECTS_KEY) ?? "{}") as { p: { nodes: object[] } };
    expect(JSON.stringify(project.p)).not.toContain("Алексей");
    expect(localStorage.getItem(CARD_META_KEY)).toContain("Алексей");
  });
});
