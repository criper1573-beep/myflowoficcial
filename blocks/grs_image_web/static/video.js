(function () {
  "use strict";

  const THEME_KEY = "grs_image_web_theme";
  const POLL_INTERVAL_MS = 4000;
  const POLL_MAX_ATTEMPTS = 120; // ~8 min

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

  function showScreen(screen) {
    document.getElementById("screen-login").classList.toggle("hidden", screen !== "login");
    document.getElementById("screen-main").classList.toggle("hidden", screen !== "main");
    if (screen === "main") {
      document.getElementById("btn-history").classList.remove("hidden");
      document.getElementById("btn-new-generation").classList.remove("hidden");
      document.getElementById("btn-logout").classList.remove("hidden");
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
    script.setAttribute("data-onauth", "onTelegramAuthVideo(user)");
    script.setAttribute("data-request-access", "write");
    document.getElementById("telegram-login-container").appendChild(script);
  }

  window.onTelegramAuthVideo = function (user) {
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

  // Model switch: show Sora or Veo options
  var modelSelect = document.getElementById("model-select");
  var optionsSora = document.getElementById("video-options-sora");
  var optionsVeo = document.getElementById("video-options-veo");
  function updateModelOptions() {
    var model = modelSelect && modelSelect.value ? modelSelect.value : "sora-2";
    if (model === "veo") {
      optionsSora.classList.add("hidden");
      optionsVeo.classList.remove("hidden");
    } else {
      optionsSora.classList.remove("hidden");
      optionsVeo.classList.add("hidden");
    }
  }
  modelSelect?.addEventListener("change", updateModelOptions);
  updateModelOptions();

  // Single ref: file input + preview + remove
  var refInput = document.getElementById("video-ref-input");
  var refPreviewWrap = document.getElementById("video-ref-preview-wrap");
  var refPreview = document.getElementById("video-ref-preview");
  var refRemove = document.getElementById("video-ref-remove");
  var refDataUrl = null;

  function readFileAsDataUrl(file) {
    return new Promise(function (resolve, reject) {
      var fr = new FileReader();
      fr.onload = function () { resolve(fr.result); };
      fr.onerror = reject;
      fr.readAsDataURL(file);
    });
  }

  refInput?.addEventListener("change", function () {
    var file = this.files && this.files[0];
    if (!file || !file.type.startsWith("image/")) {
      refPreviewWrap.classList.add("hidden");
      refPreview.src = "";
      refRemove.classList.add("hidden");
      refDataUrl = null;
      return;
    }
    refPreview.src = URL.createObjectURL(file);
    refPreview.onload = function () { URL.revokeObjectURL(refPreview.src); };
    refPreviewWrap.classList.remove("hidden");
    refRemove.classList.remove("hidden");
    readFileAsDataUrl(file).then(function (dataUrl) {
      refDataUrl = dataUrl;
    });
  });
  refRemove?.addEventListener("click", function () {
    refInput.value = "";
    refPreviewWrap.classList.add("hidden");
    refPreview.src = "";
    refRemove.classList.add("hidden");
    refDataUrl = null;
  });

  // Generate button
  var btnGenerate = document.getElementById("btn-generate-video");
  var loadingSection = document.getElementById("loading-section");
  var loadingStatus = document.getElementById("loading-status");
  var resultSection = document.getElementById("result-section");
  var resultVideo = document.getElementById("result-video");
  var btnDownload = document.getElementById("btn-download-video");
  var btnRetry = document.getElementById("btn-retry-video");

  function setLoadingStatus(text) {
    if (loadingStatus) loadingStatus.textContent = text || "";
  }

  function pollVideoResult(taskId) {
    var attempts = 0;
    function doPoll() {
      attempts++;
      setLoadingStatus("Ожидание результата… (" + attempts + ")");
      return api("/api/video-result", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: taskId }),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.success && data.videoUrl) {
            loadingSection.classList.add("hidden");
            resultVideo.src = data.videoUrl + "?t=" + Date.now();
            btnDownload.href = data.videoUrl;
            btnDownload.download = data.id || "video.mp4";
            resultSection.classList.remove("hidden");
            return;
          }
          if (data.pending && attempts < POLL_MAX_ATTEMPTS) {
            return new Promise(function (resolve) {
              setTimeout(function () {
                doPoll().then(resolve);
              }, POLL_INTERVAL_MS);
            });
          }
          loadingSection.classList.add("hidden");
          alert(data.error || "Генерация не завершилась");
        })
        .catch(function (e) {
          loadingSection.classList.add("hidden");
          alert(e.message || "Ошибка при получении результата");
        });
    }
    return doPoll();
  }

  btnGenerate?.addEventListener("click", function () {
    var promptEl = document.getElementById("video-prompt-input");
    var prompt = (promptEl && promptEl.value || "").trim();
    if (!prompt) {
      alert("Введите промпт.");
      return;
    }
    var model = (modelSelect && modelSelect.value) || "sora-2";
    var body = {
      prompt: prompt,
      model: model,
      ref: refDataUrl || null,
    };
    if (model === "sora-2") {
      body.aspect_ratio = (document.getElementById("video-aspect-sora") && document.getElementById("video-aspect-sora").value) || "9:16";
      body.duration = (document.getElementById("video-duration") && document.getElementById("video-duration").value) || "10";
      body.size = (document.getElementById("video-size") && document.getElementById("video-size").value) || "Small";
    } else {
      body.aspect_ratio = (document.getElementById("video-aspect-veo") && document.getElementById("video-aspect-veo").value) || "16:9";
    }

    loadingSection.classList.remove("hidden");
    resultSection.classList.add("hidden");
    setLoadingStatus("Отправка запроса…");

    api("/api/generate-video", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (r) {
        if (r.status === 401) throw new Error("Требуется авторизация через Telegram");
        if (!r.ok) return r.json().then(function (d) { throw new Error(d.detail || "Ошибка генерации"); });
        return r.json();
      })
      .then(function (data) {
        if (data.taskId) {
          setLoadingStatus("Генерация видео…");
          return pollVideoResult(data.taskId);
        }
        if (data.videoUrl) {
          loadingSection.classList.add("hidden");
          resultVideo.src = data.videoUrl + "?t=" + Date.now();
          btnDownload.href = data.videoUrl;
          btnDownload.download = data.id || "video.mp4";
          resultSection.classList.remove("hidden");
        } else {
          loadingSection.classList.add("hidden");
          alert("Не удалось получить видео");
        }
      })
      .catch(function (e) {
        loadingSection.classList.add("hidden");
        alert(e.message || "Ошибка генерации");
      });
  });

  btnRetry?.addEventListener("click", function () {
    resultSection.classList.add("hidden");
    btnGenerate.click();
  });

  document.getElementById("btn-new-generation")?.addEventListener("click", function () {
    resultSection.classList.add("hidden");
  });

  // History
  function openHistory() {
    document.getElementById("history-popup").classList.remove("hidden");
    document.getElementById("history-popup").setAttribute("aria-hidden", "false");
    api("/api/history/video")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var list = document.getElementById("history-list");
        var empty = document.getElementById("history-empty");
        if (empty) empty.classList.add("hidden");
        list.querySelectorAll(".history-item").forEach(function (n) { n.remove(); });
        if (!data.items || data.items.length === 0) {
          if (empty) {
            empty.classList.remove("hidden");
            empty.textContent = "Нет сохранённых генераций";
          }
          return;
        }
        data.items.forEach(function (item) {
          var div = document.createElement("div");
          div.className = "history-item flex items-center gap-3 p-2 rounded border border-divider";
          div.innerHTML =
            '<video src="' + item.url + '" class="w-20 h-14 object-cover rounded flex-shrink-0" preload="metadata" muted></video>' +
            '<div class="history-item-info flex-1 min-w-0">' +
              '<span class="text-sm truncate block input-label">' + (item.id || "video") + '</span>' +
            '</div>' +
            '<div class="history-item-actions flex items-center gap-2">' +
              '<a href="' + item.url + '" download="' + (item.id || "video.mp4") + '" class="download-btn py-1.5 px-3 rounded text-sm btn-secondary">Скачать</a>' +
            '</div>';
          list.appendChild(div);
          var vid = div.querySelector("video");
          if (vid) {
            div.addEventListener("click", function (e) {
              if (e.target.closest(".download-btn")) return;
              resultVideo.src = item.url + "?t=" + Date.now();
              btnDownload.href = item.url;
              btnDownload.download = item.id || "video.mp4";
              resultSection.classList.remove("hidden");
              document.getElementById("history-popup").classList.add("hidden");
              document.getElementById("history-popup").setAttribute("aria-hidden", "true");
            });
          }
        });
      })
      .catch(function () {
        var empty = document.getElementById("history-empty");
        if (empty) {
          empty.textContent = "Не удалось загрузить историю";
          empty.classList.remove("hidden");
        }
      });
  }

  document.getElementById("btn-history").addEventListener("click", openHistory);
  document.getElementById("history-close").addEventListener("click", function () {
    document.getElementById("history-popup").classList.add("hidden");
    document.getElementById("history-popup").setAttribute("aria-hidden", "true");
  });
  document.getElementById("history-popup").addEventListener("click", function (e) {
    if (e.target.id === "history-popup") document.getElementById("history-close").click();
  });

  checkAuth();
})();
