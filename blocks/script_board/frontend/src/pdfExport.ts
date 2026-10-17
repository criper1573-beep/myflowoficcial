import type { ScriptLine } from "./scriptModel";

export interface PdfScript {
  name: string;
  scriptDescription: string;
  lines: ScriptLine[];
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function fileName(name: string): string {
  const safe = name.replace(/[^\p{L}\p{N}\-_ ]+/gu, "").trim() || "script";
  return `${safe}.pdf`;
}

export async function exportScriptPdf(script: PdfScript): Promise<void> {
  const host = document.createElement("div");
  host.style.position = "fixed";
  host.style.left = "-10000px";
  host.style.top = "0";
  host.style.width = "515px";
  host.style.background = "#ffffff";
  host.style.color = "#0a0a0a";
  host.style.fontFamily = '"Onest", "Inter Tight", sans-serif';
  host.style.padding = "8px 4px 24px";

  const rows = script.lines
    .map((line) => {
      const label = line.role === "client" ? "Сообщение клиента" : "Наш ответ";
      const rule = line.role === "answer" ? "border-left:2px solid #ff3c00;padding-left:10px;" : "border-left:2px solid #0a0a0a;padding-left:10px;";
      return `<div style="margin:0 0 12px;${rule}"><div style="font-family:'Inter Tight',sans-serif;font-size:10px;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:4px;">${label}</div><div style="font-size:13px;line-height:1.45;white-space:pre-wrap;">${escapeHtml(line.text) || "—"}</div></div>`;
    })
    .join("");

  host.innerHTML = `
    <div style="font-family:'Inter Tight',sans-serif;font-size:11px;letter-spacing:0.12em;margin-bottom:6px;">FLOW · ДОСКА СКРИПТОВ</div>
    <div style="font-family:'Inter Tight',sans-serif;font-size:18px;font-weight:600;margin-bottom:8px;">${escapeHtml(script.name)}</div>
    <div style="font-size:12px;line-height:1.45;color:#5c5c5c;margin-bottom:16px;white-space:pre-wrap;">${escapeHtml(script.scriptDescription) || "Без описания"}</div>
    ${rows || "<div style='font-size:13px;'>Нет карточек</div>"}
  `;
  document.body.appendChild(host);

  try {
    if (document.fonts?.ready) await document.fonts.ready;
    const { jsPDF } = await import("jspdf");
    const doc = new jsPDF({ unit: "pt", format: "a4" });
    await doc.html(host, {
      margin: [36, 40, 36, 40],
      autoPaging: "text",
      width: 515,
      windowWidth: 515,
      html2canvas: { scale: 2, backgroundColor: "#ffffff" },
    });
    doc.save(fileName(script.name));
  } finally {
    host.remove();
  }
}
