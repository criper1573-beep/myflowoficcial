/**
 * Кнопки «Сгенерировать ответ» и «Улучшить текст».
 * Вызовы изолированы здесь, чтобы не плодить новые маршруты по коду.
 * История изменений сюда не ходит — для неё отдельный хук useHistory.
 */

export interface AiRequest {
  text: string;
  scriptDescription: string;
  context: string;
}

function readAiText(data: unknown): string {
  if (typeof data === "string" && data.trim()) return data.trim();
  if (!data || typeof data !== "object") {
    throw new Error("Пустой ответ сервера");
  }
  const record = data as Record<string, unknown>;
  for (const key of ["text", "reply", "answer", "improved", "result", "content", "message"]) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  throw new Error("Пустой ответ сервера");
}

async function postAi(path: string, body: AiRequest): Promise<string> {
  const response = await fetch(path, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      text: body.text,
      scriptDescription: body.scriptDescription,
      script_description: body.scriptDescription,
      context: body.context,
    }),
  });
  if (!response.ok) {
    throw new Error(`Сервер ответил ${response.status}`);
  }
  const payload: unknown = await response.json().catch(() => null);
  return readAiText(payload);
}

export function generateReply(body: AiRequest): Promise<string> {
  return postAi("/api/generate", body);
}

export function improveText(body: AiRequest): Promise<string> {
  return postAi("/api/improve", body);
}
