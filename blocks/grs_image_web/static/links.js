(function () {
  "use strict";

  const THEME_KEY = "grs_image_web_theme";
  const DEFAULT_LIMIT = 10;
  let listOffset = 0;
  let listTotal = 0;
  let deleteTargetId = null;

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
      document.getElementById("btn-logout").classList.remove("hidden");
      loadLinks(0, DEFAULT_LIMIT, false);
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
          .catch(function () { renderTelegramWidget(null); });
      })
      .catch(function () {
        document.getElementById("user-name").textContent = "Локальный режим";
        document.getElementById("user-name").classList.remove("hidden");
        showScreen("main");
      });
  }

  document.getElementById("btn-logout")?.addEventListener("click", function () {
    api("/api/logout", { method: "POST" })
      .then(function () { window.location.href = "/links"; });
  });

  function buildItemEl(item) {
    var wrap = document.createElement("div");
    wrap.className = "link-item flex items-center gap-3 p-3 rounded-lg border border-divider";
    wrap.dataset.id = item.id;
    var img = document.createElement("img");
    img.src = item.fullUrl || (window.location.origin + item.url);
    img.alt = "";
    img.className = "w-16 h-16 object-cover rounded flex-shrink-0 bg-gray-800";
    img.loading = "lazy";
    var info = document.createElement("div");
    info.className = "flex-1 min-w-0";
    var actions = document.createElement("div");
    actions.className = "flex items-center gap-2 flex-shrink-0";
    var copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.className = "link-copy-btn px-3 py-1.5 rounded text-sm btn-secondary";
    copyBtn.textContent = "Скопировать ссылку";
    copyBtn.dataset.url = item.fullUrl || (window.location.origin + item.url);
    var delBtn = document.createElement("button");
    delBtn.type = "button";
    delBtn.className = "link-delete-btn px-3 py-1.5 rounded text-sm";
    delBtn.textContent = "Удалить с сервера";
    delBtn.dataset.id = item.id;
    actions.appendChild(copyBtn);
    actions.appendChild(delBtn);
    wrap.appendChild(img);
    wrap.appendChild(info);
    wrap.appendChild(actions);
    return wrap;
  }

  function renderList(items, append) {
    var list = document.getElementById("links-list");
    var empty = document.getElementById("links-empty");
    if (!append) {
      list.querySelectorAll(".link-item").forEach(function (n) { n.remove(); });
      if (empty) empty.classList.add("hidden");
    }
    if (items.length === 0 && !append) {
      if (empty) empty.classList.remove("hidden");
      return;
    }
    if (empty) empty.classList.add("hidden");
    items.forEach(function (item) {
      list.appendChild(buildItemEl(item));
    });
    list.querySelectorAll(".link-copy-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var url = btn.dataset.url;
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(function () {
            var t = btn.textContent;
            btn.textContent = "Скопировано";
            setTimeout(function () { btn.textContent = t; }, 1500);
          });
        } else {
          var inp = document.createElement("input");
          inp.value = url;
          document.body.appendChild(inp);
          inp.select();
          document.execCommand("copy");
          document.body.removeChild(inp);
          var t = btn.textContent;
          btn.textContent = "Скопировано";
          setTimeout(function () { btn.textContent = t; }, 1500);
        }
      });
    });
    list.querySelectorAll(".link-delete-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        deleteTargetId = btn.dataset.id;
        document.getElementById("delete-confirm-popup").classList.remove("hidden");
        document.getElementById("delete-confirm-popup").setAttribute("aria-hidden", "false");
      });
    });
    var showMore = document.getElementById("btn-show-more");
    if (showMore) {
      if (listOffset + items.length < listTotal) {
        showMore.classList.remove("hidden");
      } else {
        showMore.classList.add("hidden");
      }
    }
  }

  function loadLinks(offset, limit, append) {
    api("/api/links?limit=" + limit + "&offset=" + offset)
      .then(function (r) {
        if (!r.ok) return r.json().then(function (d) { throw new Error(d.detail || "Ошибка"); });
        return r.json();
      })
      .then(function (data) {
        listOffset = offset;
        listTotal = data.total || 0;
        renderList(data.items || [], append);
      })
      .catch(function (e) {
        alert(e.message || "Ошибка загрузки списка");
      });
  }

  document.getElementById("btn-show-more")?.addEventListener("click", function () {
    var nextOffset = listOffset + DEFAULT_LIMIT;
    loadLinks(nextOffset, 50, true);
  });

  document.getElementById("upload-form")?.addEventListener("submit", function (e) {
    e.preventDefault();
    var input = document.getElementById("link-file-input");
    var file = input.files && input.files[0];
    if (!file || !file.type.match(/^image\/(png|jpeg|jpg|gif|webp)$/)) {
      alert("Выберите изображение (PNG, JPG, GIF или WebP).");
      return;
    }
    var btn = document.getElementById("btn-upload");
    btn.disabled = true;
    var formData = new FormData();
    formData.append("file", file);
    api("/api/links/upload", {
      method: "POST",
      body: formData,
    })
      .then(function (r) {
        if (r.status === 413) throw new Error("Файл слишком большой. До 15 МБ.");
        if (!r.ok) return r.text().then(function (text) {
          try {
            var d = JSON.parse(text);
            throw new Error(d.detail || "Ошибка загрузки");
          } catch (err) {
            if (err instanceof SyntaxError) throw new Error("Ошибка сервера.");
            throw err;
          }
        });
        return r.json();
      })
      .then(function (data) {
        input.value = "";
        var item = {
          id: data.id,
          url: data.url,
          fullUrl: data.fullUrl,
          name: data.id,
        };
        var list = document.getElementById("links-list");
        var empty = document.getElementById("links-empty");
        if (empty) empty.classList.add("hidden");
        var newEl = buildItemEl(item);
        list.insertBefore(newEl, list.firstChild);
        listTotal += 1;
        newEl.querySelector(".link-copy-btn").addEventListener("click", function () {
          var url = this.dataset.url;
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(url).then(function () {
              var t = this.textContent;
              this.textContent = "Скопировано";
              var self = this;
              setTimeout(function () { self.textContent = t; }, 1500);
            }.bind(this));
          }
        });
        newEl.querySelector(".link-delete-btn").addEventListener("click", function () {
          deleteTargetId = this.dataset.id;
          document.getElementById("delete-confirm-popup").classList.remove("hidden");
          document.getElementById("delete-confirm-popup").setAttribute("aria-hidden", "false");
        });
      })
      .catch(function (e) {
        alert(e.message || "Ошибка загрузки");
      })
      .finally(function () {
        btn.disabled = false;
      });
  });

  document.getElementById("delete-cancel")?.addEventListener("click", function () {
    deleteTargetId = null;
    document.getElementById("delete-confirm-popup").classList.add("hidden");
    document.getElementById("delete-confirm-popup").setAttribute("aria-hidden", "true");
  });

  document.getElementById("delete-confirm")?.addEventListener("click", function () {
    if (!deleteTargetId) return;
    var id = deleteTargetId;
    deleteTargetId = null;
    document.getElementById("delete-confirm-popup").classList.add("hidden");
    document.getElementById("delete-confirm-popup").setAttribute("aria-hidden", "true");
    api("/api/links/" + encodeURIComponent(id), { method: "DELETE" })
      .then(function (r) {
        if (!r.ok) return r.json().then(function (d) { throw new Error(d.detail || "Ошибка"); });
        var el = document.querySelector('.link-item[data-id="' + id + '"]');
        if (el) el.remove();
        listTotal = Math.max(0, listTotal - 1);
        var list = document.getElementById("links-list");
        if (list.querySelectorAll(".link-item").length === 0) {
          document.getElementById("links-empty").classList.remove("hidden");
        }
        var showMoreBtn = document.getElementById("btn-show-more");
        if (list.querySelectorAll(".link-item").length < listTotal) {
          showMoreBtn.classList.remove("hidden");
        } else {
          showMoreBtn.classList.add("hidden");
        }
      })
      .catch(function (e) {
        alert(e.message || "Ошибка удаления");
      });
  });

  checkAuth();
})();
