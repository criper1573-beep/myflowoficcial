# КонтентЗавод (ContentZavod) — один образ для всех блоков
# Запуск: docker run --env-file .env -it contentzavod
# Или с переопределением команды: docker run --env-file .env -it contentzavod python -m blocks.post_flow.bot

FROM python:3.12-slim

WORKDIR /app

# Зависимости: requirements-docker.txt (без mcp — конфликт httpx с googletrans; MCP на хосте)
COPY docs/config/requirements-docker.txt docs/config/requirements-docker.txt
RUN pip install --no-cache-dir -r docs/config/requirements-docker.txt

# Код приложения (.env не копируется — передавать через --env-file при запуске)
COPY blocks/ blocks/
COPY docs/ docs/

# По умолчанию — Spambot для проекта flowcabinet (переопределяется в docker run / compose)
CMD ["python", "-m", "blocks.spambot", "--project", "flowcabinet"]
