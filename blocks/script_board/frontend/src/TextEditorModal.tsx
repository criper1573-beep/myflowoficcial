import { useState, useEffect, useCallback } from "react";

const NYAN_GIF = "https://assets.codepen.io/16327/nyan_cat.gif";

interface TextEditorModalProps {
  nodeId: string | null;
  nodes: Array<{ id: string; data?: { title?: string; text?: string } }>;
  scriptDescription: string;
  onSave: (nodeId: string, text: string, title: string) => void;
  onClose: () => void;
}

export default function TextEditorModal({
  nodeId,
  nodes,
  scriptDescription,
  onSave,
  onClose,
}: TextEditorModalProps) {
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [improveLoading, setImproveLoading] = useState(false);
  const [improveResult, setImproveResult] = useState<string | null>(null);
  const [improveError, setImproveError] = useState<string | null>(null);

  const node = nodeId ? nodes.find((n) => n.id === nodeId) : null;

  useEffect(() => {
    if (node) {
      setTitle((node.data?.title as string) ?? "");
      setText((node.data?.text as string) ?? "");
    } else {
      setTitle("");
      setText("");
    }
    setImproveResult(null);
    setImproveError(null);
    setImproveLoading(false);
  }, [node]);

  const handleImprove = useCallback(() => {
    if (!nodeId) return;
    setImproveLoading(true);
    setImproveResult(null);
    setImproveError(null);
    fetch("/api/improve-text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        script_description: scriptDescription || null,
      }),
    })
      .then((r) => r.json())
      .then((data) => {
        setImproveLoading(false);
        if (data.success) setImproveResult(data.text ?? "");
        else setImproveError(data.error ?? "Ошибка генерации");
      })
      .catch(() => {
        setImproveLoading(false);
        setImproveError("Ошибка сети");
      });
  }, [nodeId, text, scriptDescription]);

  const handleUseResult = useCallback(() => {
    if (improveResult !== null) {
      setText(improveResult);
      setImproveResult(null);
      setImproveError(null);
    }
  }, [improveResult]);

  const handleDismissImprove = useCallback(() => {
    setImproveResult(null);
    setImproveError(null);
    setImproveLoading(false);
  }, []);

  if (!nodeId || !node) return null;

  const showImproveSection = improveLoading || improveResult !== null || improveError !== null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className={`modal modal--text ${showImproveSection ? "modal--text-expanded" : ""}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal__header">
          <span>Редактировать карточку</span>
          <button type="button" className="modal__close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="modal__body">
          <label className="modal__label">Название</label>
          <input
            type="text"
            className="modal__input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Название карточки"
          />

          <div className={`modal__text-columns ${showImproveSection ? "modal__text-columns--split" : ""}`}>
            <div className="modal__text-col">
              <label className="modal__label">Текст</label>
              <textarea
                className="modal__textarea"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Текст скрипта…"
                rows={12}
              />
            </div>

            {showImproveSection && (
              <div className="modal__text-col modal__text-col--improve">
                <div className="modal__label-row">
                  <label className="modal__label">Улучшенный вариант</label>
                  <button
                    type="button"
                    className="modal__dismiss-improve"
                    onClick={handleDismissImprove}
                    title="Закрыть"
                  >
                    ×
                  </button>
                </div>

                {improveLoading && (
                  <div className="improve-inline-loading">
                    <p className="improve-loading__text">Генерация…</p>
                    <img
                      src={NYAN_GIF}
                      alt=""
                      className="improve-loading__gif"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = "none";
                      }}
                    />
                  </div>
                )}

                {!improveLoading && improveError && (
                  <div className="improve-inline-error">
                    <p className="improve-error">{improveError}</p>
                    <button type="button" className="modal__btn-retry" onClick={handleImprove}>
                      Попробовать снова
                    </button>
                  </div>
                )}

                {!improveLoading && improveResult !== null && !improveError && (
                  <>
                    <textarea
                      className="modal__textarea"
                      value={improveResult}
                      readOnly
                      rows={12}
                    />
                    <button
                      type="button"
                      className="modal__btn-use-result"
                      onClick={handleUseResult}
                    >
                      ← Использовать этот вариант
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
        <div className="modal__footer">
          <button
            type="button"
            onClick={handleImprove}
            className="modal__btn-improve"
            disabled={improveLoading}
          >
            {improveLoading ? "Генерация…" : "✨ Улучшить текст"}
          </button>
          <button type="button" onClick={onClose}>
            Отмена
          </button>
          <button type="button" onClick={() => onSave(nodeId, text, title)}>
            Сохранить
          </button>
        </div>
      </div>
    </div>
  );
}
