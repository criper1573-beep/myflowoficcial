# Docker — КонтентЗавод

Один образ для всех блоков; нужный блок задаётся командой при запуске. Секреты в образ не попадают: используйте `.env` и при необходимости тома для конфигов.

---

## Нужно ли что-то менять на сервере?

**Нет.** Текущий деплой на VPS (Beget и др.) работает как раньше: `git pull`, `pip install -r docs/config/requirements.txt`, systemd запускает `python -m blocks.spambot` и другие сервисы. Docker — **альтернативный** способ запуска (локально или на любой машине с Docker), а не замена существующему сценарию.

**Если захочешь запускать приложение в Docker на сервере** — тогда на VPS нужно: установить Docker (и при необходимости Docker Compose), в каталоге проекта выполнить `docker build -t contentzavod .`, создать/скопировать `.env` и запускать контейнеры вместо или вместе с systemd. Такой сценарий можно оформить отдельно (например, в docs/scripts/deploy_beget/ или в этом гайде).

---

## Требования

- Docker (и Docker Compose v2 при использовании `docker compose`)
- Файл `.env` в корне проекта (скопируйте из `docs/config/.env.example`, заполните ключи)

### Если команда `docker` не найдена (Windows)

1. **Установка:** в PowerShell выполните:  
   `winget install --id Docker.DockerDesktop -e --accept-package-agreements --accept-source-agreements`  
   Подтвердите UAC, дождитесь окончания. Если **сбой с кодом выхода 3** — см. ниже.
2. **Запуск:** откройте **Docker Desktop** из меню Пуск, дождитесь полного запуска (иконка в трее).
3. **PATH:** закройте и снова откройте терминал/Cursor (или перезагрузите ПК), затем проверьте: `docker --version`, `docker compose version`.

### Сбой установки с кодом выхода 3 (winget)

Код 3 часто означает конфликт с уже установленной версией или сбой тихой установки.

- **Вариант A — ручная установка:** скачайте установщик с https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe и запустите его (двойной клик). Пройдите шаги мастера, при необходимости включите WSL 2 по подсказкам установщика.
- **Вариант B — если Docker уже стоял:** удалите старую версию через «Параметры → Приложения → Docker Desktop → Удалить». Затем установите заново (winget или установщик с сайта).
- **Вариант C — логи:** при повторной установке через winget можно посмотреть логи в `%LocalAppData%\Docker\` или запустить скачанный установщик вручную с ключом логирования (см. [документацию Docker](https://docs.docker.com/desktop/setup/install/enterprise-deployment/faq/)).

### «Virtualization support not detected» в Docker Desktop

Ошибка появляется, когда в Windows не включены компоненты для виртуализации (Docker использует WSL 2 или Hyper-V). Процессор может поддерживать виртуализацию, но нужны **включённые компоненты ОС**.

**Шаг 1 — Включить компоненты Windows (от имени администратора):**

1. Откройте **PowerShell от имени администратора** (правый клик по Пуск → «Терминал (администратор)» или «Windows PowerShell (администратор)»).
2. Выполните по очереди (после каждой команды дождитесь окончания):

   ```powershell
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   ```

3. **Перезагрузите компьютер.**

**Шаг 2 — Установить/обновить WSL 2 (после перезагрузки, снова от администратора):**

```powershell
wsl --install
```

Если WSL уже установлен, обновите ядро и переведите дистрибутивы на WSL 2:

```powershell
wsl --update
wsl --set-default-version 2
```

При необходимости снова перезагрузите ПК.

**Шаг 3 — Проверить виртуализацию:**

- Откройте **Диспетчер задач** → вкладка **Производительность** → **ЦП**. Внизу должно быть указано **«Виртуализация: Включено»**.
- Если там «Отключено» — зайдите в **BIOS/UEFI** при загрузке (обычно F2, Del или F12) и включите **Intel Virtualization Technology (VT-x)** или **AMD-V** (название зависит от производителя).

**Шаг 4 — Запустить Docker Desktop** после перезагрузки и дождаться полной инициализации.

Краткая справка Microsoft: https://aka.ms/enablevirtualization

---

## Сборка образа

Из **корня проекта** (где лежат `Dockerfile` и `blocks/`):

```bash
docker build -t contentzavod .
```

---

## Запуск одного контейнера

Передавайте переменные из `.env` через `--env-file`. **Файл `.env` должен быть в текущей директории** или укажите полный путь, например:  
`--env-file "C:\Users\Имя\Desktop\КонтентЗавод\.env"`.  
Удобнее всего запускать команды **из корня проекта** (где лежит `.env`):  
`cd путь\к\КонтентЗавод`, затем `docker run ... --env-file .env ...`.  
Рабочая директория в контейнере — `/app`, поэтому `python -m blocks.*` работает без доп. настроек.

### Spambot (NewsBot)

```bash
docker run --rm -it --env-file .env contentzavod python -m blocks.spambot --project flowcabinet
```

Список проектов:

```bash
docker run --rm -it --env-file .env contentzavod python -m blocks.spambot --list-projects
```

### Post FLOW

```bash
docker run --rm -it --env-file .env contentzavod python -m blocks.post_flow.bot
```

### MCP-сервер

```bash
docker run --rm -it --env-file .env -p 8765:8765 contentzavod python -m blocks.mcp_server
```

### Конфиги проектов (YAML)

Если в образе нет актуальных `blocks/projects/data/*.yaml` с токенами, смонтируйте папку с хоста:

**Linux/macOS:**

```bash
docker run --rm -it --env-file .env \
  -v "$(pwd)/blocks/projects/data:/app/blocks/projects/data:ro" \
  contentzavod python -m blocks.spambot --project flowcabinet
```

**Windows (PowerShell):**

```powershell
docker run --rm -it --env-file .env `
  -v "${PWD}/blocks/projects/data:/app/blocks/projects/data:ro" `
  contentzavod python -m blocks.spambot --project flowcabinet
```

---

## Docker Compose

В корне проекта есть `docker-compose.yml` с примерами сервисов **spambot** и **post_flow**. Используется общий образ, у каждого сервиса свой `command`.

Запуск:

```bash
docker compose up -d spambot
# или
docker compose up -d post_flow
```

Остановка:

```bash
docker compose down
```

Конфиги проектов монтируются из `./blocks/projects/data` (read-only). Добавить другой блок можно, скопировав сервис и изменив `command` (см. закомментированный пример `mcp_server` в `docker-compose.yml`).

---

## Секреты и .env

- В образ **не копируется** `.env` (он в `.dockerignore`).
- Всегда передавайте переменные при запуске: `--env-file .env` или `env_file: .env` в compose.
- Токены и ключи храните только в `.env` и при необходимости в `blocks/projects/data/*.yaml` на хосте, не в коде и не в образе.

---

## Ограничения

### Playwright (autopost_zen и др.)

Блоки с браузерной автоматизацией (например `blocks/autopost_zen`) требуют установленный браузер. Текущий образ на базе `python:3.12-slim` **не содержит** Playwright/Chromium.

Варианты:

- Запускать такие блоки на хосте (вне Docker).
- Собрать отдельный образ с установкой Playwright и браузера (отдельная задача/расширение).

### Windows и тома

При монтировании каталогов на Windows используйте формат Docker: `C:\path\to\project\blocks\projects\data:/app/blocks/projects/data:ro`. В PowerShell удобно задать путь так: `-v "${PWD}/blocks/projects/data:/app/blocks/projects/data:ro"` (запуск из корня проекта).

---

## Типичные проблемы

- **ModuleNotFoundError: No module named 'blocks'** — убедитесь, что запускаете контейнер с образом, собранным из корня проекта (где есть `blocks/` и `docs/`), и что в Dockerfile задан `WORKDIR /app` и копируются `blocks/` и `docs/`.
- **Нет доступа к Telegram/API** — проверьте, что передан `--env-file .env` и в `.env` заданы нужные ключи и `PROJECT_ID` (или проект в `command`).
- **Конфиг проекта не найден** — при использовании проектов из YAML смонтируйте том `./blocks/projects/data:/app/blocks/projects/data:ro`.
