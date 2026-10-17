import { describe, expect, it } from "vitest";
import {
  cardRole,
  chainTo,
  linearizeScript,
  readCardText,
  toStoredRecord,
  writeCardText,
} from "./scriptModel";

const nodes = [
  { id: "c1", type: "client", position: { x: 0, y: 100 }, data: { text: "Цена?" } },
  { id: "a2", type: "answer", position: { x: 200, y: 100 }, data: { content: "От 390 000" } },
  { id: "c3", type: "clientMessage", position: { x: 400, y: 20 }, data: { text: "Мебель?" } },
  { id: "a4", type: "ourAnswer", position: { x: 600, y: 20 }, data: { text: "Базовая входит" } },
  { id: "c5", type: "client", position: { x: 400, y: 220 }, data: { text: "К 20 мая?" } },
  { id: "a6", type: "answer", position: { x: 600, y: 220 }, data: { text: "Успеем" } },
];

const edges = [
  { source: "c1", target: "a2" },
  { source: "a2", target: "c3" },
  { source: "c3", target: "a4" },
  { source: "a2", target: "c5" },
  { source: "c5", target: "a6" },
];

describe("scriptModel", () => {
  it("различает карточку клиента и наш ответ, включая старые type", () => {
    expect(cardRole({ type: "client" })).toBe("client");
    expect(cardRole({ type: "ourAnswer" })).toBe("answer");
    expect(cardRole({ type: "reply" })).toBe("answer");
    expect(cardRole({ type: "custom", data: { kind: "answer" } })).toBe("answer");
  });

  it("пишет текст в уже существующее поле", () => {
    expect(readCardText({ content: "было" })).toBe("было");
    expect(writeCardText({ content: "было", keep: 1 }, "стало")).toEqual({ content: "стало", keep: 1 });
    expect(writeCardText({}, "новый")).toEqual({ text: "новый" });
  });

  it("обходит две ветки сверху вниз", () => {
    expect(linearizeScript(nodes, edges).map((line) => line.text)).toEqual([
      "Цена?",
      "От 390 000",
      "Мебель?",
      "Базовая входит",
      "К 20 мая?",
      "Успеем",
    ]);
  });

  it("собирает цепочку только своей ветки", () => {
    expect(chainTo("a6", nodes, edges).map((line) => line.text)).toEqual([
      "Цена?",
      "От 390 000",
      "К 20 мая?",
      "Успеем",
    ]);
  });

  it("не сохраняет служебные поля доски", () => {
    expect(toStoredRecord({ id: "n", selected: true, dragging: false, data: { text: "а" } })).toEqual({
      id: "n",
      data: { text: "а" },
    });
  });
});
