(function () {
  "use strict";

  const FACTS = [
    "Нейросети для изображений часто используют архитектуру диффузии: картинка «проявляется» из шума шаг за шагом.",
    "Модель nano-banana умеет переносить лицо с референса в новую сцену, сохраняя узнаваемость.",
    "Чем конкретнее промпт, тем предсказуемее результат — добавьте стиль, освещение и композицию.",
    "Референсные фото помогают зафиксировать внешность человека или стиль объекта в сгенерированной сцене.",
    "GRS AI поддерживает несколько моделей: от быстрых до более детализированных, например flux.",
    "Генерация в высоком разрешении занимает больше времени, но даёт более чёткое изображение.",
    "Текстовые подсказки на английском часто дают более стабильный результат у международных моделей.",
    "Несколько референсов можно комбинировать: например, лицо с одного фото, поза — с другого.",
    "ИИ не хранит ваши референсы после генерации — они используются только в рамках одного запроса.",
    "Артефакты на руках или буквах часто исправляют повторной генерацией или уточнением промпта.",
    "Слова «фотореалистично», «высокое качество» в промпте могут усилить детализацию.",
    "Нейросети обучаются на миллионах изображений и комбинируют паттерны, а не копируют картинки целиком.",
    "Ограничение в 5 референсов помогает и балансу качества, и скорости ответа API.",
    "История генераций привязана к вашему аккаунту Telegram и не видна другим пользователям.",
    "Кнопка «Сделать заново» отправляет тот же промпт и референсы — результат может отличаться.",
    "Модели типа nano-banana оптимизированы под портреты и сцены с людьми по референсу.",
    "Промпты можно описывать и на русском: многие модели понимают несколько языков.",
    "Сохраняйте понравившиеся результаты через «Скачать» — они остаются только в вашей истории на сервере.",
    "Во время генерации можно читать факты о нейросетях — они меняются каждые 5 секунд.",
    "Telegram Login не передаёт пароль: авторизация идёт через подтверждение в приложении Telegram.",
    "Cookie сессии хранится 30 дней — не нужно входить при каждом визите.",
    "Размер 1024×1024 — стандарт для многих моделей; другие пропорции могут поддерживаться отдельно.",
    "Диффузионные модели «убирают шум» из случайной картинки, ориентируясь на текст и референсы.",
    "Чем больше деталей в промпте (фон, одежда, время суток), тем ближе результат к задумке.",
    "API GRS AI можно вызывать и из скриптов: например, для пакетной генерации обложек.",
    "Референс «лицо» обычно ставят первым в списке — так модель понимает, кого сохранять в сцене.",
    "Генерация занимает от нескольких секунд до минуты в зависимости от нагрузки и сложности.",
    "Все изображения сохраняются на сервере в папке, привязанной к вашему Telegram ID.",
    "Виджет «Войти через Telegram» проверяется по криптографической подписи — подделать данные нельзя.",
    "FLOW и flowcabinet.ru — проект, в котором используется эта страница генерации.",
  ];

  let factIndex = 0;
  let factTimer = null;
  let currentResultUrl = null;
  let useImprovedPrompt = false;
  const MAX_REFS = 5;
  const THEME_KEY = "grs_image_web_theme";
  const DRAFT_KEY = "grs_image_web_draft";
  const DRAFT_REFS_MAX_BYTES = 4 * 1024 * 1024; // ~4 MB на все референсы

  function getFactElement() {
    return document.getElementById("fact-text");
  }

  function showFact(index) {
    factIndex = ((index % FACTS.length) + FACTS.length) % FACTS.length;
    const el = getFactElement();
    if (el) el.textContent = FACTS[factIndex];
  }

  function startFactsCarousel() {
    showFact(factIndex);
    if (factTimer) clearInterval(factTimer);
    factTimer = setInterval(function () {
      showFact(factIndex + 1);
    }, 5000);
  }

  function stopFactsCarousel() {
    if (factTimer) {
      clearInterval(factTimer);
      factTimer = null;
    }
  }

  function resetFactsTimer() {
    if (factTimer) {
      clearInterval(factTimer);
      factTimer = setInterval(function () {
        showFact(factIndex + 1);
      }, 5000);
    }
  }

  document.getElementById("fact-prev")?.addEventListener("click", function () {
    showFact(factIndex - 1);
    resetFactsTimer();
  });
  document.getElementById("fact-next")?.addEventListener("click", function () {
    showFact(factIndex + 1);
    resetFactsTimer();
  });

  function api(path, options) {
    return fetch(path, { credentials: "include", ...options });
  }

  function getTheme() {
    try {
      return localStorage.getItem(THEME_KEY) || "dark";
    } catch (e) {
      return "dark";
    }
  }
  function setTheme(theme) {
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch (e) {}
    var html = document.getElementById("html-theme");
    if (html) {
      html.classList.remove("theme-dark", "theme-light");
      html.classList.add(theme === "light" ? "theme-light" : "theme-dark");
    }
    var btn = document.getElementById("btn-theme");
    if (btn) btn.textContent = theme === "light" ? "🌙" : "☀️";
  }
  document.getElementById("btn-theme")?.addEventListener("click", function () {
    var next = getTheme() === "light" ? "dark" : "light";
    setTheme(next);
  });
  setTheme(getTheme());

  function getEffectivePrompt() {
    var useNew = document.querySelector('input[name="prompt-source"][value="improved"]')?.checked;
    if (useNew) {
      var improved = document.getElementById("improved-prompt-input");
      if (improved && improved.value.trim()) return improved.value.trim();
    }
    var el = document.getElementById("prompt-input");
    return (el && el.value || "").trim();
  }

  function showScreen(screen) {
    document.getElementById("screen-login").classList.toggle("hidden", screen !== "login");
    document.getElementById("screen-main").classList.toggle("hidden", screen !== "main");
    if (screen === "main") {
      document.getElementById("btn-history").classList.remove("hidden");
      document.getElementById("btn-new-generation").classList.remove("hidden");
      document.getElementById("btn-logout").classList.remove("hidden");
      restoreDraft();
    }
  }

  function renderTelegramWidget(botUsername) {
    if (!botUsername) {
      document.getElementById("login-no-bot").classList.remove("hidden");
      return;
    }
    var script = document.createElement("script");
    script.async = true;
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute("data-telegram-login", botUsername);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    script.setAttribute("data-request-access", "write");
    document.getElementById("telegram-login-container").appendChild(script);
  }

  window.onTelegramAuth = function (user) {
    api("/api/auth/telegram", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(user),
    })
      .then(function (r) {
        if (!r.ok) return r.json().then(function (d) { throw new Error(d.detail || "Ошибка входа"); });
        return r.json();
      })
      .then(function () {
        document.getElementById("user-name").textContent = user.first_name || "User";
        document.getElementById("user-name").classList.remove("hidden");
        showScreen("main");
      })
      .catch(function (e) {
        alert("Ошибка входа: " + (e.message || e));
      });
  };

  function checkAuth() {
    api("/api/config")
      .then(function (r) { return r.json(); })
      .then(function (c) {
        if (c.require_auth === false) {
          document.getElementById("user-name").textContent = "Локальный режим";
          document.getElementById("user-name").classList.remove("hidden");
          document.getElementById("btn-logout").classList.add("hidden");
          showScreen("main");
          return;
        }
        api("/api/me")
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data.authenticated && data.user) {
              document.getElementById("user-name").textContent = "ID " + data.user.id;
              document.getElementById("user-name").classList.remove("hidden");
              document.getElementById("btn-logout").classList.remove("hidden");
              showScreen("main");
            } else {
              renderTelegramWidget(c.bot_username);
            }
          })
          .catch(function () { renderTelegramWidget(c.bot_username); });
      })
      .catch(function () {
        document.getElementById("user-name").textContent = "Локальный режим";
        document.getElementById("user-name").classList.remove("hidden");
        document.getElementById("btn-logout").classList.add("hidden");
        showScreen("main");
      });
  }

  document.getElementById("btn-logout").addEventListener("click", function () {
    api("/api/logout", { method: "POST", credentials: "include" }).then(function () {
      document.getElementById("user-name").classList.add("hidden");
      showScreen("login");
      document.getElementById("screen-login").classList.remove("hidden");
      document.getElementById("screen-main").classList.add("hidden");
      document.getElementById("btn-history").classList.add("hidden");
      document.getElementById("btn-logout").classList.add("hidden");
      checkAuth();
    });
  });

  // Добавление референса
  function getRefInputs() {
    return document.querySelectorAll("#refs-container .ref-input");
  }

  document.getElementById("btn-improve-prompt")?.addEventListener("click", function () {
    var promptEl = document.getElementById("prompt-input");
    var prompt = (promptEl && promptEl.value || "").trim();
    if (!prompt) {
      alert("Сначала введите промпт.");
      return;
    }
    var btn = document.getElementById("btn-improve-prompt");
    var panel = document.getElementById("improved-prompt-panel");
    var output = document.getElementById("improved-prompt-input");
    if (btn) btn.disabled = true;
    if (output) output.value = "Загрузка…";
    if (panel) panel.classList.remove("hidden");
    api("/api/improve-prompt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: prompt }),
    })
      .then(function (r) {
        if (!r.ok) return r.json().then(function (d) { throw new Error(d.detail || "Ошибка"); });
        return r.json();
      })
      .then(function (data) {
        if (output) output.value = (data.improved || "").trim() || prompt;
      })
      .catch(function (e) {
        if (output) output.value = "";
        alert("Ошибка: " + (e.message || e));
      })
      .finally(function () {
        if (btn) btn.disabled = false;
      });
  });
  document.querySelectorAll('input[name="prompt-source"]').forEach(function (radio) {
    radio.addEventListener("change", function () {
      useImprovedPrompt = document.querySelector('input[name="prompt-source"][value="improved"]')?.checked || false;
      persistDraft();
    });
  });

  function getRefRowTemplate() {
    return (
      '<div class="ref-preview-wrap hidden">' +
        '<img class="ref-preview hidden" alt="" />' +
        '<span class="ref-preview-placeholder input-label">—</span>' +
      '</div>' +
      '<input type="file" accept="image/*" class="ref-input text-sm file:mr-2 file:py-1.5 file:px-3 file:rounded file:border-0" />' +
      '<button type="button" class="ref-remove hidden" aria-label="Удалить референс">×</button>'
    );
  }

  function updateAddRefButtonVisibility() {
    var rows = document.querySelectorAll("#refs-container .ref-row");
    var hasAny = false;
    for (var i = 0; i < rows.length; i++) {
      if (rows[i].dataset.refUrl) { hasAny = true; break; }
      var input = rows[i].querySelector(".ref-input");
      if (input && input.files && input.files[0]) { hasAny = true; break; }
    }
    var btn = document.getElementById("btn-add-ref");
    if (btn) {
      if (hasAny) btn.classList.remove("hidden");
      else btn.classList.add("hidden");
    }
  }

  document.getElementById("btn-add-ref").addEventListener("click", function () {
    var container = document.getElementById("refs-container");
    if (getRefInputs().length >= MAX_REFS) return;
    var row = document.createElement("div");
    row.className = "ref-row flex items-center gap-3 flex-wrap";
    row.innerHTML = getRefRowTemplate();
    container.appendChild(row);
  });
  document.getElementById("refs-container").addEventListener("change", function (e) {
    if (!e.target.classList.contains("ref-input")) return;
    var row = e.target.closest(".ref-row");
    if (!row) return;
    var wrap = row.querySelector(".ref-preview-wrap");
    var img = row.querySelector(".ref-preview");
    var ph = row.querySelector(".ref-preview-placeholder");
    var file = e.target.files && e.target.files[0];
    if (!file || !file.type.startsWith("image/")) {
      if (wrap) wrap.classList.add("hidden");
      if (img) { img.classList.add("hidden"); img.src = ""; }
      if (ph) ph.classList.remove("hidden");
      delete row.dataset.refUrl;
      var removeBtn = row.querySelector(".ref-remove");
      if (removeBtn) removeBtn.classList.add("hidden");
      updateAddRefButtonVisibility();
      persistDraft();
      return;
    }
    var url = URL.createObjectURL(file);
    if (img) {
      img.onload = function () { URL.revokeObjectURL(url); };
      img.src = url;
      img.classList.remove("hidden");
    }
    if (ph) ph.classList.add("hidden");
    if (wrap) wrap.classList.remove("hidden");
    var removeBtn = row.querySelector(".ref-remove");
    if (removeBtn) removeBtn.classList.remove("hidden");
    readFileAsDataUrl(file).then(function (dataUrl) {
      row.dataset.refUrl = dataUrl;
      updateAddRefButtonVisibility();
      persistDraft();
    });
  });
  document.getElementById("refs-container").addEventListener("click", function (e) {
    if (!e.target.classList.contains("ref-remove")) return;
    var row = e.target.closest(".ref-row");
    if (!row) return;
    var wrap = row.querySelector(".ref-preview-wrap");
    var input = row.querySelector(".ref-input");
    var img = row.querySelector(".ref-preview");
    var ph = row.querySelector(".ref-preview-placeholder");
    if (wrap) wrap.classList.add("hidden");
    if (input) input.value = "";
    if (img) { if (img.src && img.src.indexOf("blob:") === 0) URL.revokeObjectURL(img.src); img.src = ""; img.classList.add("hidden"); }
    if (ph) ph.classList.remove("hidden");
    delete row.dataset.refUrl;
    var removeBtn = row.querySelector(".ref-remove");
    if (removeBtn) removeBtn.classList.add("hidden");
    var rows = document.querySelectorAll("#refs-container .ref-row");
    if (rows.length > 1) row.remove();
    updateAddRefButtonVisibility();
    persistDraft();
  });

  function readFileAsDataUrl(file) {
    return new Promise(function (resolve, reject) {
      var fr = new FileReader();
      fr.onload = function () { resolve(fr.result); };
      fr.onerror = reject;
      fr.readAsDataURL(file);
    });
  }

  function getDraftRefsDataUrls() {
    var rows = document.querySelectorAll("#refs-container .ref-row");
    var out = [];
    for (var i = 0; i < rows.length; i++) {
      var url = rows[i].dataset.refUrl;
      if (url) out.push(url);
    }
    return out;
  }

  function persistDraft() {
    try {
      var promptEl = document.getElementById("prompt-input");
      var improvedEl = document.getElementById("improved-prompt-input");
      var sourceRadio = document.querySelector('input[name="prompt-source"][value="improved"]');
      var refs = getDraftRefsDataUrls();
      var refsBytes = refs.reduce(function (sum, s) { return sum + (s.length * 2); }, 0);
      if (refsBytes > DRAFT_REFS_MAX_BYTES) refs = [];
      var formatEl = document.getElementById("format-select");
      var draft = {
        prompt: (promptEl && promptEl.value) || "",
        improvedPrompt: (improvedEl && improvedEl.value) || "",
        useImproved: sourceRadio ? sourceRadio.checked : false,
        refs: refs,
        format: (formatEl && formatEl.value) || "1024x1024",
      };
      localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
    } catch (err) {
      if (err && err.name === "QuotaExceededError") {
        try {
          var draft = JSON.parse(localStorage.getItem(DRAFT_KEY) || "{}");
          draft.refs = [];
          localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
        } catch (e) {}
      }
    }
  }

  function resetForNewGeneration() {
    var promptEl = document.getElementById("prompt-input");
    var improvedEl = document.getElementById("improved-prompt-input");
    var panel = document.getElementById("improved-prompt-panel");
    var mineRadio = document.querySelector('input[name="prompt-source"][value="mine"]');
    var formatEl = document.getElementById("format-select");
    var container = document.getElementById("refs-container");
    if (promptEl) promptEl.value = "";
    if (improvedEl) improvedEl.value = "";
    if (panel) panel.classList.add("hidden");
    if (mineRadio) mineRadio.checked = true;
    if (formatEl) formatEl.value = "1024x1024";
    if (container) {
      var rows = container.querySelectorAll(".ref-row");
      for (var i = 0; i < rows.length; i++) {
        var img = rows[i].querySelector(".ref-preview");
        if (img && img.src && img.src.indexOf("blob:") === 0) URL.revokeObjectURL(img.src);
      }
      container.innerHTML = "";
      var row = document.createElement("div");
      row.className = "ref-row flex items-center gap-3 flex-wrap";
      row.innerHTML = getRefRowTemplate();
      container.appendChild(row);
      updateAddRefButtonVisibility();
    }
    try { localStorage.setItem(DRAFT_KEY, JSON.stringify({ prompt: "", improvedPrompt: "", useImproved: false, refs: [], format: "1024x1024" })); } catch (e) {}
    document.getElementById("loading-section").classList.add("hidden");
    document.getElementById("result-section").classList.add("hidden");
  }

  function restoreDraft() {
    try {
      var raw = localStorage.getItem(DRAFT_KEY);
      if (!raw) return;
      var draft = JSON.parse(raw);
      var promptEl = document.getElementById("prompt-input");
      var improvedEl = document.getElementById("improved-prompt-input");
      if (promptEl && draft.prompt != null) promptEl.value = draft.prompt;
      if (improvedEl && draft.improvedPrompt != null) improvedEl.value = draft.improvedPrompt;
      var improvedRadio = document.querySelector('input[name="prompt-source"][value="improved"]');
      var mineRadio = document.querySelector('input[name="prompt-source"][value="mine"]');
      if (draft.useImproved && improvedRadio) improvedRadio.checked = true;
      else if (mineRadio) mineRadio.checked = true;
      var formatEl = document.getElementById("format-select");
      if (formatEl && draft.format) formatEl.value = draft.format;
      var refs = Array.isArray(draft.refs) ? draft.refs : [];
      var container = document.getElementById("refs-container");
      if (!container) return;
      container.innerHTML = "";
      if (refs.length === 0) {
        var row = document.createElement("div");
        row.className = "ref-row flex items-center gap-3 flex-wrap";
        row.innerHTML = getRefRowTemplate();
        container.appendChild(row);
        return;
      }
      for (var i = 0; i < refs.length; i++) {
        var row = document.createElement("div");
        row.className = "ref-row flex items-center gap-3 flex-wrap";
        row.innerHTML = getRefRowTemplate();
        var wrap = row.querySelector(".ref-preview-wrap");
        var img = row.querySelector(".ref-preview");
        var ph = row.querySelector(".ref-preview-placeholder");
        var removeBtn = row.querySelector(".ref-remove");
        row.dataset.refUrl = refs[i];
        img.src = refs[i];
        img.classList.remove("hidden");
        ph.classList.add("hidden");
        wrap.classList.remove("hidden");
        removeBtn.classList.remove("hidden");
        container.appendChild(row);
      }
      if (refs.length < MAX_REFS) {
        var row = document.createElement("div");
        row.className = "ref-row flex items-center gap-3 flex-wrap";
        row.innerHTML = getRefRowTemplate();
        container.appendChild(row);
      }
      updateAddRefButtonVisibility();
    } catch (e) {}
  }

  document.getElementById("prompt-input")?.addEventListener("input", persistDraft);
  document.getElementById("prompt-input")?.addEventListener("change", persistDraft);
  document.getElementById("improved-prompt-input")?.addEventListener("input", persistDraft);
  document.getElementById("improved-prompt-input")?.addEventListener("change", persistDraft);
  document.getElementById("format-select")?.addEventListener("change", persistDraft);

  document.getElementById("btn-new-generation")?.addEventListener("click", resetForNewGeneration);

  document.getElementById("btn-generate").addEventListener("click", function () {
    var prompt = getEffectivePrompt();
    if (!prompt) {
      alert("Введите промпт.");
      return;
    }
    var rows = document.querySelectorAll("#refs-container .ref-row");
    var refPromises = [];
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      if (r.dataset.refUrl) {
        refPromises.push(Promise.resolve(r.dataset.refUrl));
      } else {
        var input = r.querySelector(".ref-input");
        var f = input && input.files && input.files[0];
        if (f) refPromises.push(readFileAsDataUrl(f));
      }
    }
    Promise.all(refPromises).then(function (refs) {
      document.getElementById("loading-section").classList.remove("hidden");
      document.getElementById("result-section").classList.add("hidden");
      startFactsCarousel();

      var formatEl = document.getElementById("format-select");
      var formatValue = (formatEl && formatEl.value) ? formatEl.value : "1024x1024";
      api("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt, refs: refs, format: formatValue }),
      })
        .then(function (r) {
          if (r.status === 401) throw new Error("Требуется авторизация через Telegram");
          if (r.status === 413) throw new Error("Файлы референсов слишком большие. Выберите изображения меньшего размера или меньше файлов.");
          if (!r.ok) {
            return r.text().then(function (text) {
              try {
                var d = JSON.parse(text);
                throw new Error(d.detail || "Ошибка генерации");
              } catch (err) {
                if (err instanceof SyntaxError) throw new Error("Ошибка сервера. Попробуйте позже.");
                throw err;
              }
            });
          }
          return r.json();
        })
        .then(function (data) {
          document.getElementById("loading-section").classList.add("hidden");
          stopFactsCarousel();
          currentResultUrl = data.imageUrl;
          var preview = document.getElementById("result-preview");
          preview.src = data.imageUrl + "?t=" + Date.now();
          document.getElementById("btn-download").href = data.imageUrl;
          document.getElementById("btn-download").download = (data.id || "image.png");
          document.getElementById("result-section").classList.remove("hidden");
        })
        .catch(function (e) {
          document.getElementById("loading-section").classList.add("hidden");
          stopFactsCarousel();
          alert(e.message || "Ошибка генерации");
        });
    });
  });

  document.getElementById("btn-retry").addEventListener("click", function () {
    document.getElementById("btn-generate").click();
  });

  // История
  function openHistory() {
    document.getElementById("history-popup").classList.remove("hidden");
    document.getElementById("history-popup").setAttribute("aria-hidden", "false");
    api("/api/history")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var list = document.getElementById("history-list");
        var empty = document.getElementById("history-empty");
        empty.classList.add("hidden");
        list.querySelectorAll(".history-item").forEach(function (n) { n.remove(); });
        if (!data.items || data.items.length === 0) {
          empty.classList.remove("hidden");
          return;
        }
        data.items.forEach(function (item) {
          var div = document.createElement("div");
          div.className = "history-item";
          var promptText = (item.prompt || "").trim();
          var promptShort = promptText.length > 60 ? promptText.slice(0, 57) + "…" : promptText;
          var promptEsc = promptShort.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
          div.innerHTML =
            '<img src="' + item.url + '" alt="" />' +
            '<div class="history-item-info flex-1 min-w-0">' +
              '<span class="text-gray-400 text-sm truncate block">' + (item.name || item.id) + '</span>' +
              (promptShort ? '<p class="history-item-prompt text-sm mt-0.5 truncate" title="' + promptEsc + '">' + promptEsc + '</p>' : '') +
            '</div>' +
            '<div class="history-item-actions flex items-center gap-2">' +
              (promptText ? '<button type="button" class="history-copy-prompt-btn" title="Скопировать промпт">Скопировать промпт</button>' : '') +
              '<a href="' + item.url + '" download="' + (item.name || "image.png") + '" class="download-btn">Скачать</a>' +
            '</div>';
          list.appendChild(div);
          var copyBtn = div.querySelector(".history-copy-prompt-btn");
          if (copyBtn) {
            copyBtn._fullPrompt = promptText;
            copyBtn.addEventListener("click", function () {
              var p = this._fullPrompt || "";
              if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(p).then(function () {
                  var t = copyBtn.textContent;
                  copyBtn.textContent = "Скопировано";
                  setTimeout(function () { copyBtn.textContent = t; }, 1500);
                });
              }
            });
          }
        });
      })
      .catch(function () {
        document.getElementById("history-empty").textContent = "Не удалось загрузить историю";
        document.getElementById("history-empty").classList.remove("hidden");
      });
  }

  document.getElementById("btn-history").addEventListener("click", openHistory);
  document.getElementById("history-close").addEventListener("click", function () {
    document.getElementById("history-popup").classList.add("hidden");
    document.getElementById("history-popup").setAttribute("aria-hidden", "true");
  });
  document.getElementById("history-popup").addEventListener("click", function (e) {
    if (e.target.id === "history-popup") {
      document.getElementById("history-close").click();
    }
  });

  checkAuth();
})();
