import { beforeEach, describe, expect, it } from "vitest";
import {
  CURRENT_KEY,
  PROJECTS_KEY,
  createProject,
  getCurrentProjectId,
  getProjectName,
  listProjects,
  loadProject,
  saveProject,
  setCurrentProjectId,
} from "./projectsStorage";

describe("projectsStorage", () => {
  beforeEach(() => localStorage.clear());

  it("создаёт проект и читает его по контракту", () => {
    const id = createProject("  Авито  ");
    expect(getProjectName(id)).toBe("Авито");
    expect(loadProject(id)).toEqual({
      name: "Авито",
      nodes: [],
      edges: [],
      scriptDescription: "",
    });
    setCurrentProjectId(id);
    expect(getCurrentProjectId()).toBe(id);
    expect(localStorage.getItem(CURRENT_KEY)).toBe(id);
  });

  it("хранит только name, nodes, edges и scriptDescription", () => {
    saveProject("p1", "Проект 1", [{ id: "n1" }], [{ id: "e1" }], "описание");
    const raw = JSON.parse(localStorage.getItem(PROJECTS_KEY) ?? "{}") as Record<string, object>;
    expect(Object.keys(raw.p1).sort()).toEqual(["edges", "name", "nodes", "scriptDescription"]);
    expect(listProjects()).toEqual([{ id: "p1", name: "Проект 1" }]);
  });

  it("возвращает null для неизвестного проекта и пустой список при битом JSON", () => {
    expect(loadProject("missing")).toBeNull();
    localStorage.setItem(PROJECTS_KEY, "{");
    expect(listProjects()).toEqual([]);
  });
});
