(function () {
  const API = '/api';
  const CHANNEL_NAMES = {
    '': 'Главная',
    telegram: 'Телеграм канал',
    site: 'Сайт',
    zen: 'Дзен',
    vk: 'VK',
    vc_ru: 'VC.ru',
    generation: 'Generation',
  };
  const INITIAL_RUNS_VISIBLE = 3;
  const INITIAL_SERVICES_VISIBLE = 10;

  let currentProject = 'flow';
  let currentChannel = '';
  let allRuns = [];
  let allServices = [];
  let timelineChart = null;
  let channelTimelineChart = null;
  let genChart = null;
  let genLinksChart = null;
  let currentGenPill = 'images'; // 'images' | 'links'

  var PROJECT_IDS = { FLOW: 'flow', FULFILMENT: 'fulfilment' };
  function appendProjectParam(path, project) {
    project = (project != null && project !== '') ? String(project).toLowerCase() : currentProject;
    if (project === 'fulfillment') project = 'fulfilment';
    var q = 'project=' + encodeURIComponent(project);
    if (path.indexOf('?') >= 0) {
      return path + '&' + q;
    }
    return path + '?' + q;
  }

  async function fetchJson(path, options) {
    options = options || {};
    var project = options.project != null ? options.project : currentProject;
    if (project === 'fulfillment') project = 'fulfilment';
    var url = API + appendProjectParam(path, project);
    var r = await fetch(url, { cache: 'no-store', headers: { 'X-Requested-Project': project } });
    if (!r.ok) throw new Error(r.statusText);
    return r.json();
  }

  function setChannel(channel) {
    currentChannel = channel || '';
    document.querySelectorAll('.nav-channel').forEach(function (a) {
      var ch = a.getAttribute('data-channel') || '';
      if (ch === 'generation' && currentProject !== 'flow') {
        a.classList.add('hidden');
        return;
      }
      if (ch === 'generation') a.classList.remove('hidden');
      var isActive = ch === currentChannel;
      a.classList.toggle('bg-blue-600', isActive);
      a.classList.toggle('text-white', isActive);
      a.classList.toggle('bg-gray-800/50', !isActive);
      a.classList.toggle('text-gray-300', !isActive);
    });
    const pageMain = document.getElementById('page-main');
    const pageChannel = document.getElementById('page-channel');
    const pageGeneration = document.getElementById('page-generation');
    if (!pageMain || !pageChannel) return;
    if (pageGeneration) pageGeneration.classList.add('hidden');
    if (currentChannel === '') {
      pageMain.classList.remove('hidden');
      pageChannel.classList.add('hidden');
      loadMain();
    } else if (currentChannel === 'generation') {
      pageMain.classList.add('hidden');
      pageChannel.classList.add('hidden');
      if (pageGeneration) pageGeneration.classList.remove('hidden');
      loadGeneration();
    } else {
      pageMain.classList.add('hidden');
      pageChannel.classList.remove('hidden');
      document.getElementById('channel-title').textContent = CHANNEL_NAMES[currentChannel] || currentChannel;
      loadChannel(currentChannel);
    }
  }

  function renderSummary(stats, containerId) {
    const wrap = containerId ? document.getElementById(containerId) : null;
    const totalEl = document.getElementById('stat-total');
    const completedEl = document.getElementById('stat-completed');
    const failedEl = document.getElementById('stat-failed');
    const todayEl = document.getElementById('stat-today');
    if (wrap) {
      wrap.innerHTML =
        '<div class="card bg-gray-800 rounded-lg p-4 border border-gray-700"><div class="text-gray-400 text-xs sm:text-sm uppercase tracking-wide">Всего запусков</div><div class="text-2xl font-bold text-white">' +
        (stats.total ?? '—') +
        '</div></div>' +
        '<div class="card bg-gray-800 rounded-lg p-4 border border-gray-700"><div class="text-gray-400 text-xs sm:text-sm uppercase tracking-wide">Успешных</div><div class="text-2xl font-bold text-green-400">' +
        (stats.completed ?? '—') +
        '</div></div>' +
        '<div class="card bg-gray-800 rounded-lg p-4 border border-gray-700"><div class="text-gray-400 text-xs sm:text-sm uppercase tracking-wide">С ошибками</div><div class="text-2xl font-bold text-red-400">' +
        (stats.failed ?? '—') +
        '</div></div>' +
        '<div class="card bg-gray-800 rounded-lg p-4 border border-gray-700"><div class="text-gray-400 text-xs sm:text-sm uppercase tracking-wide">Сегодня</div><div class="text-2xl font-bold text-blue-400">' +
        (stats.today ?? '—') +
        '</div></div>';
      return;
    }
    if (totalEl) totalEl.textContent = stats.total ?? '—';
    if (completedEl) completedEl.textContent = stats.completed ?? '—';
    if (failedEl) failedEl.textContent = stats.failed ?? '—';
    if (todayEl) todayEl.textContent = stats.today ?? '—';
  }

  function renderTimeline(data, days, chartElId) {
    const el = document.getElementById(chartElId || 'timeline-chart');
    if (!el) return;
    const categories = (data || []).map(function (d) {
      return d.day;
    });
    const series = [{ name: 'Запусков', data: (data || []).map(function (d) {
      return d.count;
    }) }];
    const opts = {
      chart: { type: 'area', height: 220, toolbar: { show: false }, background: 'transparent', fontFamily: 'inherit' },
      series: series,
      theme: { mode: 'dark' },
      colors: ['#3b82f6'],
      dataLabels: { enabled: false },
      stroke: { curve: 'smooth', width: 2 },
      fill: { type: 'gradient', gradient: { shadeIntensity: 0.3, opacityFrom: 0.5, opacityTo: 0.1 } },
      xaxis: { categories, labels: { style: { colors: '#9ca3af' } } },
      yaxis: { labels: { style: { colors: '#9ca3af' } } },
      grid: { borderColor: '#374151', strokeDashArray: 4 },
      tooltip: { theme: 'dark' },
    };
    if (chartElId === 'channel-timeline-chart') {
      if (channelTimelineChart) channelTimelineChart.destroy();
      channelTimelineChart = new ApexCharts(el, opts);
      channelTimelineChart.render();
    } else {
      if (timelineChart) timelineChart.destroy();
      timelineChart = new ApexCharts(el, opts);
      timelineChart.render();
    }
  }

  function stepDotClass(status) {
    return 'step-dot ' + (status || 'pending');
  }

  function openErrorPanel(label, message) {
    document.getElementById('error-panel-label').textContent = label;
    document.getElementById('error-panel-message').textContent = message || 'Нет описания';
    document.getElementById('error-panel').classList.remove('hidden');
    document.getElementById('error-panel').setAttribute('aria-hidden', 'false');
  }

  function closeErrorPanel() {
    document.getElementById('error-panel').classList.add('hidden');
    document.getElementById('error-panel').setAttribute('aria-hidden', 'true');
  }

  document.getElementById('error-panel').querySelectorAll('[data-close="error-panel"]').forEach(function (btn) {
    btn.addEventListener('click', closeErrorPanel);
  });

  var copyBtn = document.getElementById('error-panel-copy');
  if (copyBtn) {
    copyBtn.addEventListener('click', function () {
      var pre = document.getElementById('error-panel-message');
      if (!pre) return;
      navigator.clipboard.writeText(pre.textContent).then(
        function () { copyBtn.textContent = 'Скопировано'; setTimeout(function () { copyBtn.textContent = 'Скопировать'; }, 1500); },
        function () { copyBtn.textContent = 'Не удалось'; setTimeout(function () { copyBtn.textContent = 'Скопировать'; }, 1500); }
      );
    });
  }

  function getRunErrorText(run) {
    var steps = run.steps || [];
    for (var i = 0; i < steps.length; i++) {
      if (steps[i].status === 'failed' && (steps[i].error_message || '').trim()) {
        return { label: steps[i].label || steps[i].name || 'Шаг', message: steps[i].error_message };
      }
    }
    if (run.status === 'failed') return { label: 'Запуск', message: 'Запуск завершился с ошибкой (детали в шагах выше)' };
    return null;
  }

  function renderRuns(runs, options) {
    options = options || {};
    var visibleCount = options.visibleCount != null ? options.visibleCount : runs.length;
    var showMoreWrap = document.getElementById('runs-more-wrap');
    var container = document.getElementById('runs-items');
    var loading = document.getElementById('runs-loading');
    if (!container) return;
    if (loading) loading.classList.add('hidden');
    var toShow = runs.slice(0, visibleCount);
    if (!runs || runs.length === 0) {
      container.innerHTML = '<p class="text-gray-500 py-6 text-center">Нет запусков</p>';
      if (showMoreWrap) showMoreWrap.classList.add('hidden');
      return;
    }
    var hasMore = runs.length > INITIAL_RUNS_VISIBLE;
    var isExpanded = visibleCount >= runs.length;
    if (showMoreWrap) {
      showMoreWrap.classList.toggle('hidden', !hasMore);
      var runBtn = document.getElementById('btn-runs-more');
      if (runBtn) runBtn.textContent = isExpanded ? 'Скрыть' : 'Показать больше';
    }
    container.innerHTML = toShow
      .map(function (run) {
        var topic = (run.topic || '').slice(0, 60) + (run.topic && run.topic.length > 60 ? '…' : '');
        var steps = run.steps || [];
        var stepsHtml = steps
          .map(function (s) {
            var isFailedClickable = s.status === 'failed' && (s.error_message || '').length > 0;
            var dataAttrs = isFailedClickable
              ? ' data-error-label="' + escapeAttr(s.label || s.name) + '" data-error-message="' + escapeAttr(s.error_message || '') + '" role="button" tabindex="0" class="step-failed-clickable cursor-pointer"'
              : '';
            return '<span class="flex items-center gap-1" title="' + escapeAttr(s.label || s.name) + '"' + dataAttrs + '><span class="' + stepDotClass(s.status) + '" aria-label="' + escapeAttr(s.label || s.name) + ': ' + s.status + '"></span><span class="text-xs text-gray-500 truncate max-w-[80px] sm:max-w-[120px]">' + escapeHtml(s.label || s.name) + '</span></span>';
          })
          .join('');
        var runError = getRunErrorText(run);
        var errorBtnHtml = runError
          ? '<button type="button" class="run-show-error mt-2 px-3 py-1.5 rounded bg-red-900/50 text-red-300 text-sm hover:bg-red-800/50" data-error-label="' + escapeAttr(runError.label) + '" data-error-message="' + escapeAttr(runError.message) + '">Показать ошибку</button>'
          : '';
        return (
          '<div class="run-card bg-gray-800 rounded-lg p-4 border border-gray-700" data-run-id="' +
          run.id +
          '">' +
          '<div class="flex flex-wrap items-center gap-2 mb-2">' +
          '<span class="font-semibold text-white">Запуск #' + run.id + '</span>' +
          '<span class="text-xs px-2 py-0.5 rounded ' +
          (run.status === 'completed' ? 'bg-green-900/50 text-green-300' : run.status === 'failed' ? 'bg-red-900/50 text-red-300' : 'bg-gray-600 text-gray-300') +
          '">' + (run.status === 'running' ? 'выполняется' : run.status === 'completed' ? 'успех' : 'ошибка') + '</span>' +
          '</div>' +
          '<p class="text-gray-400 text-sm mb-3">' + escapeHtml(topic) + '</p>' +
          '<div class="flex flex-wrap gap-2 sm:gap-3 items-center">' + stepsHtml + '</div>' +
          errorBtnHtml +
          '</div>'
        );
      })
      .join('');

    container.querySelectorAll('.run-show-error').forEach(function (btn) {
      btn.addEventListener('click', function () {
        openErrorPanel(btn.getAttribute('data-error-label'), btn.getAttribute('data-error-message'));
      });
    });
    container.querySelectorAll('.step-failed-clickable').forEach(function (el) {
      el.addEventListener('click', function () {
        openErrorPanel(el.getAttribute('data-error-label') || 'Ошибка', el.getAttribute('data-error-message') || '');
      });
      el.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') openErrorPanel(el.getAttribute('data-error-label') || 'Ошибка', el.getAttribute('data-error-message') || '');
      });
    });
  }

  function escapeHtml(s) {
    if (!s) return '';
    var div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function escapeAttr(s) {
    if (!s) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  async function loadTimeline(days, channel, chartElId) {
    var path = '/stats/timeline?days=' + (days || 30);
    if (channel) path += '&channel=' + encodeURIComponent(channel);
    var data = await fetchJson(path);
    renderTimeline(data, days, chartElId);
  }

  function renderServerServices(services, visibleCount) {
    if (visibleCount == null) visibleCount = services.length;
    var wrap = document.getElementById('services-items');
    var loading = document.getElementById('services-loading');
    var moreWrap = document.getElementById('services-more-wrap');
    if (!wrap) return;
    if (loading) loading.classList.add('hidden');
    if (!services || services.length === 0) {
      wrap.innerHTML = '<p class="text-gray-500 col-span-full">Нет данных о сервисах (только на Linux-сервере)</p>';
      if (moreWrap) moreWrap.classList.add('hidden');
      return;
    }
    var activeFirst = services.filter(function (s) { return s.active_state === 'active'; });
    var naServices = services.filter(function (s) { return s.active_state === 'n/a'; });
    var rest = services.filter(function (s) { return s.active_state !== 'active' && s.active_state !== 'n/a'; });
    var ordered = activeFirst.concat(naServices).concat(rest);
    var toShow = ordered.slice(0, visibleCount);
    var hasMore = ordered.length > INITIAL_SERVICES_VISIBLE;
    var isExpanded = visibleCount >= ordered.length;
    if (moreWrap) {
      moreWrap.classList.toggle('hidden', !hasMore);
      var btn = document.getElementById('btn-services-more');
      if (btn) btn.textContent = isExpanded ? 'Скрыть' : 'Показать больше';
    }
    wrap.innerHTML = toShow
      .map(function (s) {
        var isActive = (s.active_state && String(s.active_state).toLowerCase()) === 'active';
        var isLocal = s.active_state === 'n/a';
        var bg = isActive ? 'bg-gray-800 border-2 border-green-500' : (isLocal ? 'bg-gray-800 border border-gray-600' : 'bg-gray-800 border-2 border-red-500');
        var dot = isActive ? 'bg-green-500 shadow-sm shadow-green-500/50' : (isLocal ? 'bg-gray-500' : 'bg-red-500');
        var rawState = isActive ? (s.sub_state || 'работает') : (isLocal ? (s.sub_state || 'локальный режим') : (s.active_state || 'остановлен'));
        var stateText = (rawState === 'running') ? 'работает' : rawState;
        var pid = s.pid && s.pid !== '0' ? 'PID ' + s.pid : '';
        var desc = (s.description || '').trim();
        return (
          '<div class="rounded-lg p-4 border ' +
          bg +
          '">' +
          '<div class="flex items-center gap-2 mb-1">' +
          '<span class="w-2 h-2 rounded-full ' +
          dot +
          '"></span>' +
          '<span class="font-medium text-white">' +
          (s.label || s.unit) +
          '</span>' +
          '</div>' +
          (desc ? '<p class="text-sm text-gray-400 mt-1 mb-2">' + escapeHtml(desc) + '</p>' : '') +
          '<div class="text-sm text-gray-400">' +
          stateText +
          (pid ? ' · ' + pid : '') +
          '</div>' +
          '<div class="text-xs text-gray-500 mt-1">' +
          s.unit +
          '</div>' +
          '</div>'
        );
      })
      .join('');
  }

  async function loadServerServices() {
    try {
      var data = await fetchJson('/server-services');
      allServices = data.services || [];
      renderServerServices(allServices, INITIAL_SERVICES_VISIBLE);
      var noteEl = document.getElementById('services-note');
      if (noteEl) {
        noteEl.textContent = data.note || '';
        noteEl.classList.toggle('hidden', !data.note);
      }
    } catch (e) {
      var wrap = document.getElementById('services-items');
      var loading = document.getElementById('services-loading');
      if (loading) loading.classList.add('hidden');
      if (wrap) wrap.innerHTML = '<p class="text-gray-500 col-span-full">Не удалось загрузить сервисы</p>';
    }
  }

  function loadMain(project) {
    project = project != null ? project : currentProject;
    document.getElementById('stat-total') && (document.getElementById('stat-total').textContent = '—');
    document.getElementById('stat-completed') && (document.getElementById('stat-completed').textContent = '—');
    document.getElementById('stat-failed') && (document.getElementById('stat-failed').textContent = '—');
    document.getElementById('stat-today') && (document.getElementById('stat-today').textContent = '—');
    var runsLoading = document.getElementById('runs-loading');
    if (runsLoading) {
      runsLoading.textContent = 'Загрузка…';
      runsLoading.classList.remove('hidden');
    }
    var runsItems = document.getElementById('runs-items');
    if (runsItems) runsItems.innerHTML = '';
    Promise.all([
      fetchJson('/stats', { project: project }),
      fetchJson('/runs?limit=50', { project: project }),
      fetchJson('/stats/timeline?days=30', { project: project }),
    ]).then(function (results) {
      var stats = results[0];
      var runs = results[1];
      var timeline = results[2];
      renderSummary(stats);
      renderTimeline(timeline, 30);
      allRuns = runs;
      renderRuns(runs, { visibleCount: INITIAL_RUNS_VISIBLE });
    }).catch(function (e) {
      var loading = document.getElementById('runs-loading');
      if (loading) {
        loading.textContent = 'Ошибка загрузки: ' + e.message;
        loading.classList.remove('hidden');
      }
    });
    loadServerServices();
  }

  async function loadChannel(channel, project) {
    project = project != null ? project : currentProject;
    try {
      var statsPath = '/stats';
      if (channel) statsPath += '?channel=' + encodeURIComponent(channel);
      var timelinePath = '/stats/timeline?days=30&channel=' + encodeURIComponent(channel);
      var funnelPath = '/stats/funnel?channel=' + encodeURIComponent(channel);
      var stats = await fetchJson(statsPath, { project: project });
      var timeline = await fetchJson(timelinePath, { project: project });
      var funnel = await fetchJson(funnelPath, { project: project });
      renderSummary(stats, 'channel-summary');
      renderTimeline(timeline, 30, 'channel-timeline-chart');
      var funnelContent = document.getElementById('channel-funnel-content');
      if (funnelContent) {
        if (funnel.stages && funnel.stages.length) {
          funnelContent.innerHTML = funnel.stages.map(function (s) { return '<div>' + escapeHtml(s.name || s.label) + ': ' + (s.value ?? '—') + '</div>'; }).join('');
        } else {
          funnelContent.textContent = funnel.note || 'Данные воронки пока не собираются для этого канала.';
        }
      }
    } catch (e) {
      var funnelContent = document.getElementById('channel-funnel-content');
      if (funnelContent) funnelContent.textContent = 'Ошибка загрузки: ' + e.message;
    }
  }

  function renderGenChart(data, chartElId) {
    var el = document.getElementById(chartElId);
    var emptyEl = document.getElementById(chartElId === 'gen-links-chart' ? 'gen-links-chart-empty' : 'gen-chart-empty');
    if (!el) return;
    var byDay = (data && data.byDay) ? data.byDay.slice().reverse() : [];
    if (chartElId === 'gen-links-chart') {
      if (genLinksChart) { genLinksChart.destroy(); genLinksChart = null; }
    } else {
      if (genChart) { genChart.destroy(); genChart = null; }
    }
    if (byDay.length === 0) {
      if (emptyEl) emptyEl.classList.remove('hidden');
      el.innerHTML = '';
      return;
    }
    if (emptyEl) emptyEl.classList.add('hidden');
    var categories = byDay.map(function (d) { return d.day; });
    var series = [{ name: currentGenPill === 'images' ? 'Генераций' : 'Ссылок', data: byDay.map(function (d) { return d.count; }) }];
    var opts = {
      chart: { type: 'area', height: 220, toolbar: { show: false }, background: 'transparent', fontFamily: 'inherit' },
      series: series,
      theme: { mode: 'dark' },
      colors: ['#3b82f6'],
      dataLabels: { enabled: false },
      stroke: { curve: 'smooth', width: 2 },
      fill: { type: 'gradient', gradient: { shadeIntensity: 0.3, opacityFrom: 0.5, opacityTo: 0.1 } },
      xaxis: { categories, labels: { style: { colors: '#9ca3af' } } },
      yaxis: { labels: { style: { colors: '#9ca3af' } } },
      grid: { borderColor: '#374151', strokeDashArray: 4 },
      tooltip: { theme: 'dark' },
    };
    var render = function () {
      if (chartElId === 'gen-links-chart') {
        genLinksChart = new ApexCharts(el, opts);
        genLinksChart.render();
      } else {
        genChart = new ApexCharts(el, opts);
        genChart.render();
      }
    };
    if (el.offsetParent === null) setTimeout(render, 150);
    else render();
  }

  async function loadGeneration() {
    var path = currentGenPill === 'images' ? '/generation/images/summary' : '/generation/links/summary';
    var totalEl = currentGenPill === 'images' ? document.getElementById('gen-stat-total') : document.getElementById('gen-links-stat-total');
    var chartElId = currentGenPill === 'images' ? 'gen-chart' : 'gen-links-chart';
    var listEl = currentGenPill === 'images' ? document.getElementById('gen-users-list') : document.getElementById('gen-links-users-list');
    if (totalEl) totalEl.textContent = '—';
    if (listEl) listEl.innerHTML = '<p class="text-gray-500">Загрузка…</p>';
    try {
      var data = await fetch(API + path).then(function (r) { if (!r.ok) throw new Error(r.statusText); return r.json(); });
      if (totalEl) totalEl.textContent = data.total ?? 0;
      renderGenChart(data, chartElId);
      var users = data.users || [];
      if (!listEl) return;
      if (users.length === 0) {
        listEl.innerHTML = '<p class="text-gray-500">Нет данных</p>';
        return;
      }
      listEl.innerHTML = users.map(function (u) {
        var displayName = (u.name != null && u.name !== '') ? u.name : ('ID ' + u.telegramId);
        return '<div class="gen-user-row flex items-center justify-between py-2 px-3 rounded-lg bg-gray-800 border border-gray-700 cursor-pointer hover:bg-gray-700" data-tid="' + escapeAttr(u.telegramId) + '" data-name="' + escapeAttr(u.name != null && u.name !== '' ? u.name : '') + '">' +
          '<span class="text-white font-medium">' + escapeHtml(displayName) + '</span>' +
          '<span class="text-gray-400">' + (u.count || 0) + '</span>' +
          '</div>';
      }).join('');
      listEl.querySelectorAll('.gen-user-row').forEach(function (row) {
        row.addEventListener('click', function () {
          var tid = row.getAttribute('data-tid');
          var name = row.getAttribute('data-name') || '';
          if (currentGenPill === 'images') openGenUserPopup(tid, name);
          else openGenLinksUserPopup(tid, name);
        });
      });
    } catch (e) {
      if (listEl) listEl.innerHTML = '<p class="text-gray-500">Ошибка: ' + escapeHtml(e.message) + '</p>';
    }
  }

  function openGenUserPopup(tid, displayName) {
    var titleEl = document.getElementById('gen-user-popup-title');
    if (titleEl) titleEl.textContent = (displayName && displayName.trim()) ? (displayName.trim() + ' (ID ' + tid + ')') : ('ID ' + tid);
    document.getElementById('gen-user-popup').classList.remove('hidden');
    document.getElementById('gen-user-popup').setAttribute('aria-hidden', 'false');
    var listEl = document.getElementById('gen-user-popup-list');
    listEl.innerHTML = '<p class="text-gray-500 col-span-full">Загрузка…</p>';
    fetch(API + '/generation/images/user/' + encodeURIComponent(tid))
      .then(function (r) { if (!r.ok) throw new Error(r.statusText); return r.json(); })
      .then(function (data) {
        var items = data.items || [];
        if (items.length === 0) {
          listEl.innerHTML = '<p class="text-gray-500 col-span-full">Нет генераций</p>';
          return;
        }
        listEl.innerHTML = items.map(function (item) {
          var promptShort = (item.prompt || '').slice(0, 80) + ((item.prompt || '').length > 80 ? '…' : '');
          return '<div class="bg-gray-900 rounded-lg p-3 border border-gray-700">' +
            '<img src="' + escapeAttr(item.imageProxyUrl) + '" alt="" class="w-full h-32 object-cover rounded mb-2" loading="lazy" />' +
            '<p class="text-gray-400 text-xs mb-1">' + escapeHtml(item.date || '') + '</p>' +
            '<p class="text-gray-300 text-sm truncate mb-2" title="' + escapeAttr(item.prompt || '') + '">' + escapeHtml(promptShort) + '</p>' +
            '<div class="flex gap-2">' +
            '<button type="button" class="gen-copy-prompt px-2 py-1 rounded bg-gray-700 text-gray-300 text-xs hover:bg-gray-600" data-prompt="' + escapeAttr(item.prompt || '') + '">Скопировать промпт</button>' +
            '<a href="' + escapeAttr(item.downloadUrl) + '" target="_blank" rel="noopener" class="px-2 py-1 rounded bg-gray-700 text-gray-300 text-xs hover:bg-gray-600">Скачать</a>' +
            '</div></div>';
        }).join('');
        listEl.querySelectorAll('.gen-copy-prompt').forEach(function (btn) {
          btn.addEventListener('click', function () {
            var prompt = btn.getAttribute('data-prompt') || '';
            navigator.clipboard.writeText(prompt).then(function () {
              var t = btn.textContent;
              btn.textContent = 'Скопировано';
              setTimeout(function () { btn.textContent = t; }, 1500);
            });
          });
        });
      })
      .catch(function (e) {
        listEl.innerHTML = '<p class="text-gray-500 col-span-full">Ошибка: ' + escapeHtml(e.message) + '</p>';
      });
  }

  function openGenLinksUserPopup(tid, displayName) {
    var titleEl = document.getElementById('gen-links-user-popup-title');
    if (titleEl) titleEl.textContent = (displayName && displayName.trim()) ? (displayName.trim() + ' (ID ' + tid + ')') : ('ID ' + tid);
    document.getElementById('gen-links-user-popup').classList.remove('hidden');
    document.getElementById('gen-links-user-popup').setAttribute('aria-hidden', 'false');
    var listEl = document.getElementById('gen-links-user-popup-list');
    listEl.innerHTML = '<p class="text-gray-500 col-span-full">Загрузка…</p>';
    fetch(API + '/generation/links/user/' + encodeURIComponent(tid))
      .then(function (r) { if (!r.ok) throw new Error(r.statusText); return r.json(); })
      .then(function (data) {
        var items = data.items || [];
        if (items.length === 0) {
          listEl.innerHTML = '<p class="text-gray-500 col-span-full">Нет ссылок</p>';
          return;
        }
        listEl.innerHTML = items.map(function (item) {
          return '<div class="bg-gray-900 rounded-lg p-3 border border-gray-700">' +
            '<img src="' + escapeAttr(item.fullUrl) + '" alt="" class="w-full h-32 object-cover rounded mb-2" loading="lazy" />' +
            '<p class="text-gray-400 text-xs mb-2">' + escapeHtml(item.date || '') + '</p>' +
            '<button type="button" class="gen-copy-link w-full px-2 py-1 rounded bg-gray-700 text-gray-300 text-xs hover:bg-gray-600" data-url="' + escapeAttr(item.fullUrl || '') + '">Скопировать ссылку</button>' +
            '</div>';
        }).join('');
        listEl.querySelectorAll('.gen-copy-link').forEach(function (btn) {
          btn.addEventListener('click', function () {
            var url = btn.getAttribute('data-url') || '';
            navigator.clipboard.writeText(url).then(function () {
              var t = btn.textContent;
              btn.textContent = 'Скопировано';
              setTimeout(function () { btn.textContent = t; }, 1500);
            });
          });
        });
      })
      .catch(function (e) {
        listEl.innerHTML = '<p class="text-gray-500 col-span-full">Ошибка: ' + escapeHtml(e.message) + '</p>';
      });
  }

  function closeGenUserPopup() {
    document.getElementById('gen-user-popup').classList.add('hidden');
    document.getElementById('gen-user-popup').setAttribute('aria-hidden', 'true');
  }
  function closeGenLinksUserPopup() {
    document.getElementById('gen-links-user-popup').classList.add('hidden');
    document.getElementById('gen-links-user-popup').setAttribute('aria-hidden', 'true');
  }

  document.getElementById('gen-user-popup-close') && document.getElementById('gen-user-popup-close').addEventListener('click', closeGenUserPopup);
  document.getElementById('gen-links-user-popup-close') && document.getElementById('gen-links-user-popup-close').addEventListener('click', closeGenLinksUserPopup);
  document.querySelectorAll('[data-close="gen-user-popup"]').forEach(function (el) { el.addEventListener('click', closeGenUserPopup); });
  document.querySelectorAll('[data-close="gen-links-user-popup"]').forEach(function (el) { el.addEventListener('click', closeGenLinksUserPopup); });

  document.getElementById('gen-pill-images') && document.getElementById('gen-pill-images').addEventListener('click', function () {
    currentGenPill = 'images';
    document.getElementById('gen-pill-images').classList.add('bg-blue-600', 'text-white');
    document.getElementById('gen-pill-images').classList.remove('bg-gray-700', 'text-gray-300');
    document.getElementById('gen-pill-links').classList.remove('bg-blue-600', 'text-white');
    document.getElementById('gen-pill-links').classList.add('bg-gray-700', 'text-gray-300');
    document.getElementById('gen-content-images').classList.remove('hidden');
    document.getElementById('gen-content-links').classList.add('hidden');
    loadGeneration();
  });
  document.getElementById('gen-pill-links') && document.getElementById('gen-pill-links').addEventListener('click', function () {
    currentGenPill = 'links';
    document.getElementById('gen-pill-links').classList.add('bg-blue-600', 'text-white');
    document.getElementById('gen-pill-links').classList.remove('bg-gray-700', 'text-gray-300');
    document.getElementById('gen-pill-images').classList.remove('bg-blue-600', 'text-white');
    document.getElementById('gen-pill-images').classList.add('bg-gray-700', 'text-gray-300');
    document.getElementById('gen-content-links').classList.remove('hidden');
    document.getElementById('gen-content-images').classList.add('hidden');
    loadGeneration();
  });

  document.querySelectorAll('.timeline-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var days = parseInt(btn.getAttribute('data-days'), 10);
      loadTimeline(days);
    });
  });

  document.querySelectorAll('.channel-timeline-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (!currentChannel) return;
      var days = parseInt(btn.getAttribute('data-days'), 10);
      loadTimeline(days, currentChannel, 'channel-timeline-chart');
    });
  });

  document.querySelectorAll('.nav-channel').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      setChannel(a.getAttribute('data-channel') || '');
    });
  });

  var btnServicesMore = document.getElementById('btn-services-more');
  if (btnServicesMore) {
    btnServicesMore.addEventListener('click', function () {
      var isExpanded = btnServicesMore.textContent === 'Скрыть';
      renderServerServices(allServices, isExpanded ? INITIAL_SERVICES_VISIBLE : allServices.length);
    });
  }

  var btnRunsMore = document.getElementById('btn-runs-more');
  if (btnRunsMore) {
    btnRunsMore.addEventListener('click', function () {
      var isExpanded = btnRunsMore.textContent === 'Скрыть';
      renderRuns(allRuns, { visibleCount: isExpanded ? INITIAL_RUNS_VISIBLE : allRuns.length });
    });
  }

  var PROJECT_LABELS = { flow: 'FLOW', fulfilment: 'Фулфилмент' };
  function updateProjectTriggerLabel() {
    var el = document.getElementById('project-trigger-label');
    if (el) el.textContent = PROJECT_LABELS[currentProject] || currentProject;
  }
  function openProjectDropdown() {
    var dd = document.getElementById('project-dropdown');
    var trigger = document.getElementById('project-trigger');
    if (dd) dd.classList.remove('hidden');
    if (trigger) trigger.setAttribute('aria-expanded', 'true');
  }
  function closeProjectDropdown() {
    var dd = document.getElementById('project-dropdown');
    var trigger = document.getElementById('project-trigger');
    if (dd) dd.classList.add('hidden');
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
  }
  function switchProject(project) {
    currentProject = project;
    localStorage.setItem('analytics_project', currentProject);
    updateProjectTriggerLabel();
    closeProjectDropdown();
    if (currentChannel === 'generation' && currentProject !== 'flow') {
      setChannel('');
      return;
    }
    setChannel(currentChannel);
  }
  (function initProjectSwitcher() {
    var saved = localStorage.getItem('analytics_project');
    if (saved === 'flow' || saved === 'fulfilment') currentProject = saved;
    updateProjectTriggerLabel();
  })();
  var triggerEl = document.getElementById('project-trigger');
  if (triggerEl) {
    triggerEl.addEventListener('click', function (e) {
      e.stopPropagation();
      var dd = document.getElementById('project-dropdown');
      if (dd && dd.classList.contains('hidden')) openProjectDropdown();
      else closeProjectDropdown();
    });
  }
  var dropdownEl = document.getElementById('project-dropdown');
  if (dropdownEl) {
    dropdownEl.addEventListener('click', function (e) {
      var opt = e.target && e.target.closest && e.target.closest('.project-option');
      if (!opt) return;
      var project = opt.getAttribute('data-project') || 'flow';
      switchProject(project);
    });
  }
  document.addEventListener('click', function () {
    closeProjectDropdown();
  });
  document.getElementById('project-switcher-wrap') && document.getElementById('project-switcher-wrap').addEventListener('click', function (e) {
    e.stopPropagation();
  });

  setChannel('');
})();
