# -*- coding: utf-8 -*-
"""JSON-хранилище доски: атомарная запись, блокировка, ревизии, история."""
from __future__ import annotations

import copy
import fcntl
import json
import os
import re
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")

CARD_TYPES = ("client", "our_response")


class StoreError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, extra: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.extra = extra or {}

    def detail(self) -> dict:
        body = {"code": self.code, "message": self.message}
        body.update(self.extra)
        return body


class RevisionConflict(StoreError):
    def __init__(self, revision: int, message: str, card_revision: int | None = None):
        extra: dict[str, Any] = {"revision": revision}
        if card_revision is not None:
            extra["cardRevision"] = card_revision
        super().__init__("revision_conflict", message, 409, extra)


class NotFound(StoreError):
    def __init__(self, message: str = "Не найдено"):
        super().__init__("not_found", message, 404)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _parse_dt(value: str) -> datetime:
    text = value.strip()
    if text.isdigit():
        return datetime.fromtimestamp(int(text) / 1000.0, tz=timezone.utc)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _as_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise StoreError("bad_request", f"{field} должен быть целым числом")
    if value < 0:
        raise StoreError("bad_request", f"{field} не может быть отрицательным")
    return value


def _check_id(value: Any, field: str = "id") -> str:
    if not isinstance(value, str) or not ID_RE.match(value):
        raise StoreError("bad_id", f"{field} должен соответствовать [A-Za-z0-9_-]+")
    return value


def _deep(value: Any) -> Any:
    return copy.deepcopy(value)


class BoardStore:
    def __init__(self, root: str | Path | None = None):
        if root is None:
            env = os.getenv("SCRIPT_BOARD_STORAGE")
            if env:
                root = env
            else:
                root = Path(__file__).resolve().parent / "storage"
        self.root = Path(root)
        self.projects_path = self.root / "projects.json"
        self.history_dir = self.root / "history"
        self.lock_path = self.root / ".store.lock"
        self._seq = 0

    @contextmanager
    def _locked(self) -> Iterator[None]:
        self.root.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        handle = open(self.lock_path, "a+", encoding="utf-8")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()

    def _atomic_write(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    def _read(self) -> dict:
        if not self.projects_path.exists():
            return {}
        raw = self.projects_path.read_text(encoding="utf-8")
        if not raw.strip():
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise StoreError("corrupt", "projects.json повреждён, запись остановлена", 500) from exc
        if not isinstance(data, dict):
            raise StoreError("corrupt", "projects.json должен быть объектом", 500)
        return data

    def _write(self, data: dict) -> None:
        text = json.dumps(data, ensure_ascii=False, indent=2)
        self._atomic_write(self.projects_path, text + "\n")

    def _append_history(self, project_id: str, event: dict) -> None:
        path = self.history_dir / f"{project_id}.jsonl"
        line = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
        fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
        try:
            os.write(fd, line.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)

    def _history_path(self, project_id: str) -> Path:
        return self.history_dir / f"{project_id}.jsonl"

    def _read_history(self, project_id: str) -> list[dict]:
        path = self._history_path(project_id)
        if not path.exists():
            return []
        events: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict) and item.get("id"):
                events.append(item)
        return events

    def _migrate(self, data: dict) -> tuple[dict, bool]:
        """Добавляет revision и пустые коллекции. Существующие nodes/edges/comments не трогает."""
        changed = False
        for project in data.values():
            if not isinstance(project, dict):
                continue
            if "name" not in project:
                project["name"] = ""
                changed = True
            if "scriptDescription" not in project:
                project["scriptDescription"] = ""
                changed = True
            if not isinstance(project.get("nodes"), list):
                project["nodes"] = []
                changed = True
            if not isinstance(project.get("edges"), list):
                project["edges"] = []
                changed = True
            if not isinstance(project.get("comments"), list):
                project["comments"] = []
                changed = True
            if "revision" not in project:
                project["revision"] = 0
                changed = True
            for node in project["nodes"]:
                if isinstance(node, dict) and "revision" not in node:
                    node["revision"] = 0
                    changed = True
        return data, changed

    def _load_migrated(self) -> tuple[dict, bool]:
        data = self._read()
        return self._migrate(data)

    def _new_id(self, prefix: str, taken: set[str]) -> str:
        for _ in range(20):
            self._seq += 1
            candidate = f"{prefix}-{time.time_ns() // 1_000_000}-{self._seq}"
            if candidate not in taken:
                return candidate
        raise StoreError("id_exhausted", "Не удалось выдать id", 500)

    def _event(
        self,
        *,
        author: str,
        type_: str,
        revision: int,
        card_id: str | None = None,
        edge_id: str | None = None,
        comment_id: str | None = None,
        before: Any = None,
        after: Any = None,
    ) -> dict:
        self._seq += 1
        return {
            "id": f"evt-{time.time_ns()}-{os.getpid()}-{self._seq}",
            "ts": now_iso(),
            "author": author or "unknown",
            "type": type_,
            "cardId": card_id,
            "edgeId": edge_id,
            "commentId": comment_id,
            "before": _deep(before),
            "after": _deep(after),
            "revision": revision,
        }

    def _require(self, data: dict, project_id: str, *, allow_archived: bool = False) -> dict:
        project_id = _check_id(project_id, "project id")
        project = data.get(project_id)
        if not isinstance(project, dict):
            raise NotFound("Проект не найден")
        if project.get("archived") and not allow_archived:
            raise NotFound("Проект в архиве")
        return project

    def _check_project_revision(self, project: dict, expected: Any) -> int:
        current = int(project.get("revision") or 0)
        given = _as_int(expected, "revision")
        if given != current:
            raise RevisionConflict(current, "Устаревшая ревизия проекта")
        return current

    def _check_card_revision(self, node: dict, expected: Any, project_revision: int) -> int:
        current = int(node.get("revision") or 0)
        given = _as_int(expected, "revision")
        if given != current:
            raise RevisionConflict(
                project_revision,
                "Устаревшая ревизия карточки",
                card_revision=current,
            )
        return current

    def _check_type(self, value: Any) -> str:
        if value not in CARD_TYPES:
            raise StoreError("bad_request", "type должен быть client или our_response")
        return value

    def _check_position(self, value: Any) -> dict:
        if not isinstance(value, dict) or "x" not in value or "y" not in value:
            raise StoreError("bad_request", "position должен содержать x и y")
        try:
            x = float(value["x"])
            y = float(value["y"])
        except (TypeError, ValueError) as exc:
            raise StoreError("bad_request", "position.x и position.y должны быть числами") from exc
        position = _deep(value)
        position["x"] = x
        position["y"] = y
        return position

    def _normalize_node(self, raw: Any, revision: int) -> dict:
        if not isinstance(raw, dict):
            raise StoreError("bad_request", "Карточка должна быть объектом")
        node = _deep(raw)
        node.pop("selected", None)
        node.pop("dragging", None)
        node["id"] = _check_id(node.get("id"), "card id")
        node["type"] = self._check_type(node.get("type"))
        node["position"] = self._check_position(node.get("position"))
        data = node.get("data")
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise StoreError("bad_request", "data карточки должен быть объектом")
        data = _deep(data)
        if not isinstance(data.get("title", ""), str):
            data["title"] = str(data.get("title") or "")
        data.setdefault("title", "")
        if not isinstance(data.get("text", ""), str):
            data["text"] = str(data.get("text") or "")
        data.setdefault("text", "")
        node["data"] = data
        node["revision"] = revision
        return node

    def _normalize_edge(self, raw: Any) -> dict:
        if not isinstance(raw, dict):
            raise StoreError("bad_request", "Связь должна быть объектом")
        edge = _deep(raw)
        edge.pop("selected", None)
        edge["id"] = _check_id(edge.get("id"), "edge id")
        edge["source"] = _check_id(edge.get("source"), "edge source")
        edge["target"] = _check_id(edge.get("target"), "edge target")
        if edge["source"] == edge["target"]:
            raise StoreError("bad_request", "Связь не может замыкаться на ту же карточку")
        return edge

    def _normalize_comment(self, raw: Any) -> dict:
        if not isinstance(raw, dict):
            raise StoreError("bad_request", "Комментарий должен быть объектом")
        comment = _deep(raw)
        comment["id"] = _check_id(comment.get("id"), "comment id")
        try:
            comment["x"] = float(comment["x"])
            comment["y"] = float(comment["y"])
        except (KeyError, TypeError, ValueError) as exc:
            raise StoreError("bad_request", "Комментарий должен содержать числовые x и y") from exc
        text = comment.get("text", "")
        if not isinstance(text, str):
            text = str(text or "")
        comment["text"] = text
        return comment

    def _canonical_node(self, node: dict) -> str:
        normalized = self._normalize_node(node, 0)
        normalized.pop("revision", None)
        position = normalized.get("position") or {}
        position["x"] = round(float(position.get("x", 0)), 2)
        position["y"] = round(float(position.get("y", 0)), 2)
        return json.dumps(normalized, ensure_ascii=False, sort_keys=True, default=str)

    def _canonical_edge(self, edge: dict) -> str:
        normalized = self._normalize_edge(edge)
        return json.dumps(normalized, ensure_ascii=False, sort_keys=True, default=str)

    def _canonical_comment(self, comment: dict) -> str:
        normalized = self._normalize_comment(comment)
        normalized["x"] = round(float(normalized["x"]), 2)
        normalized["y"] = round(float(normalized["y"]), 2)
        return json.dumps(normalized, ensure_ascii=False, sort_keys=True, default=str)

    def _touch(self, project: dict, revision: int) -> None:
        project["revision"] = revision
        project["updatedAt"] = now_iso()

    def _commit(self, project_id: str | None, mutate) -> Any:
        with self._locked():
            data, migrated = self._load_migrated()
            if migrated:
                self._write(data)
            result, events = mutate(data)
            if events:
                self._write(data)
                target = project_id
                if target is None:
                    raise StoreError("bad_request", "Не указан проект для истории", 500)
                for event in events:
                    self._append_history(target, event)
            return result

    def list_projects(self, *, include_archived: bool = False) -> list[dict]:
        with self._locked():
            data, migrated = self._load_migrated()
            if migrated:
                self._write(data)
            items = []
            for project_id, project in data.items():
                if not isinstance(project, dict):
                    continue
                archived = bool(project.get("archived"))
                if archived and not include_archived:
                    continue
                item = {
                    "id": project_id,
                    "name": project.get("name") or "",
                    "revision": int(project.get("revision") or 0),
                }
                if include_archived:
                    item["archived"] = archived
                items.append(item)
            return items

    def get_project(self, project_id: str, *, include_archived: bool = False) -> dict:
        with self._locked():
            data, migrated = self._load_migrated()
            if migrated:
                self._write(data)
            project = self._require(data, project_id, allow_archived=include_archived)
            payload = _deep(project)
            payload["id"] = project_id
            return payload

    def _public(self, project_id: str, project: dict) -> dict:
        payload = _deep(project)
        payload["id"] = project_id
        return payload

    def create_project(
        self,
        *,
        name: str,
        script_description: str = "",
        nodes: list | None = None,
        edges: list | None = None,
        comments: list | None = None,
        author: str,
        project_id: str | None = None,
    ) -> dict:
        if not isinstance(name, str) or not name.strip():
            raise StoreError("bad_request", "Нужно название проекта")
        if not isinstance(script_description, str):
            raise StoreError("bad_request", "scriptDescription должен быть строкой")

        with self._locked():
            data, migrated = self._load_migrated()
            if migrated:
                self._write(data)
            taken = set(data)
            if project_id:
                pid = _check_id(project_id, "project id")
                if pid in data:
                    raise StoreError("conflict", "Проект с таким id уже есть", 409)
            else:
                pid = self._new_id("project", taken)
            project = self._build_new_project(
                name=name.strip(),
                script_description=script_description,
                nodes=nodes or [],
                edges=edges or [],
                comments=comments or [],
            )
            data[pid] = project
            event = self._event(
                author=author,
                type_="project.create",
                revision=1,
                before=None,
                after=self._public(pid, project),
            )
            self._write(data)
            self._append_history(pid, event)
            return {"id": pid, "revision": 1}

    def _build_new_project(
        self,
        *,
        name: str,
        script_description: str,
        nodes: list,
        edges: list,
        comments: list,
    ) -> dict:
        node_ids: set[str] = set()
        built_nodes = []
        for raw in nodes:
            prepared = _deep(raw)
            if not prepared.get("id"):
                prepared["id"] = self._new_id("node", node_ids)
            node = self._normalize_node(prepared, 1)
            if node["id"] in node_ids:
                raise StoreError("conflict", f"Карточка {node['id']} уже есть", 409)
            node_ids.add(node["id"])
            built_nodes.append(node)
        edge_ids: set[str] = set()
        built_edges = []
        for raw in edges:
            prepared = _deep(raw)
            if not prepared.get("id"):
                source = str(prepared.get("source") or "src")
                target = str(prepared.get("target") or "dst")
                prepared["id"] = f"e-{source}-{target}"
                if prepared["id"] in edge_ids:
                    prepared["id"] = self._new_id("e", edge_ids)
            edge = self._normalize_edge(prepared)
            if edge["id"] in edge_ids:
                raise StoreError("conflict", f"Связь {edge['id']} уже есть", 409)
            edge_ids.add(edge["id"])
            built_edges.append(edge)
        comment_ids: set[str] = set()
        built_comments = []
        for raw in comments:
            prepared = _deep(raw)
            if not prepared.get("id"):
                prepared["id"] = self._new_id("comment", comment_ids)
            comment = self._normalize_comment(prepared)
            if comment["id"] in comment_ids:
                raise StoreError("conflict", f"Комментарий {comment['id']} уже есть", 409)
            comment_ids.add(comment["id"])
            built_comments.append(comment)
        ts = now_iso()
        return {
            "name": name,
            "scriptDescription": script_description,
            "nodes": built_nodes,
            "edges": built_edges,
            "comments": built_comments,
            "revision": 1,
            "archived": False,
            "createdAt": ts,
            "updatedAt": ts,
        }

    def replace_project(self, project_id: str, body: dict, author: str) -> dict:
        project_id = _check_id(project_id, "project id")
        if not isinstance(body, dict):
            raise StoreError("bad_request", "Тело должно быть объектом проекта")

        with self._locked():
            data, migrated = self._load_migrated()
            if migrated:
                self._write(data)
            if project_id not in data:
                name = body.get("name")
                if not isinstance(name, str) or not name.strip():
                    raise StoreError("bad_request", "Нужно название проекта")
                description = body.get("scriptDescription") or ""
                if not isinstance(description, str):
                    raise StoreError("bad_request", "scriptDescription должен быть строкой")
                project = self._build_new_project(
                    name=name.strip(),
                    script_description=description,
                    nodes=body.get("nodes") or [],
                    edges=body.get("edges") or [],
                    comments=body.get("comments") or [],
                )
                data[project_id] = project
                event = self._event(
                    author=author,
                    type_="project.create",
                    revision=1,
                    before=None,
                    after=self._public(project_id, project),
                )
                self._write(data)
                self._append_history(project_id, event)
                return {"success": True, "revision": 1, "project": self._public(project_id, project)}

            project = self._require(data, project_id)
            if "revision" not in body:
                raise RevisionConflict(int(project.get("revision") or 0), "В полной записи нужна ревизия проекта")
            self._check_project_revision(project, body.get("revision"))
            updated, events = self._diff_replace(project_id, project, body, author)
            if events:
                data[project_id] = updated
                self._write(data)
                for event in events:
                    self._append_history(project_id, event)
                project = updated
            return {
                "success": True,
                "revision": int(project.get("revision") or 0),
                "project": self._public(project_id, project),
            }

    def _diff_replace(self, project_id: str, project: dict, body: dict, author: str) -> tuple[dict, list]:
        name = body.get("name", project.get("name"))
        if not isinstance(name, str) or not name.strip():
            raise StoreError("bad_request", "Нужно название проекта")
        description = body.get("scriptDescription", project.get("scriptDescription") or "")
        if not isinstance(description, str):
            raise StoreError("bad_request", "scriptDescription должен быть строкой")
        if not isinstance(body.get("nodes", []), list) or not isinstance(body.get("edges", []), list):
            raise StoreError("bad_request", "nodes и edges должны быть массивами")
        if "comments" in body and not isinstance(body.get("comments"), list):
            raise StoreError("bad_request", "comments должен быть массивом")

        old_nodes = {node["id"]: node for node in project.get("nodes") or [] if isinstance(node, dict) and node.get("id")}
        new_nodes = []
        seen_nodes: set[str] = set()
        node_events_spec: list[tuple] = []
        for raw in body.get("nodes") or []:
            if not isinstance(raw, dict):
                raise StoreError("bad_request", "Карточка должна быть объектом")
            node_id = _check_id(raw.get("id"), "card id")
            if node_id in seen_nodes:
                raise StoreError("conflict", f"Карточка {node_id} уже есть", 409)
            seen_nodes.add(node_id)
            previous = old_nodes.get(node_id)
            if previous is None:
                node = self._normalize_node(raw, 1)
                node_events_spec.append(("card.create", node_id, None, node))
            elif self._canonical_node(previous) == self._canonical_node(raw):
                node = self._normalize_node(raw, int(previous.get("revision") or 0))
            else:
                node = self._normalize_node(raw, int(previous.get("revision") or 0) + 1)
                node_events_spec.append(("card.update", node_id, previous, node))
            new_nodes.append(node)
        for node_id, previous in old_nodes.items():
            if node_id not in seen_nodes:
                node_events_spec.append(("card.delete", node_id, previous, None))

        old_edges = {edge["id"]: edge for edge in project.get("edges") or [] if isinstance(edge, dict) and edge.get("id")}
        new_edges = []
        seen_edges: set[str] = set()
        edge_events_spec: list[tuple] = []
        for raw in body.get("edges") or []:
            edge = self._normalize_edge(raw)
            if edge["id"] in seen_edges:
                raise StoreError("conflict", f"Связь {edge['id']} уже есть", 409)
            seen_edges.add(edge["id"])
            previous = old_edges.get(edge["id"])
            if previous is None:
                edge_events_spec.append(("edge.create", edge["id"], None, edge))
            elif self._canonical_edge(previous) == self._canonical_edge(edge):
                pass
            else:
                edge_events_spec.append(("edge.update", edge["id"], previous, edge))
            new_edges.append(edge)
        for edge_id, previous in old_edges.items():
            if edge_id not in seen_edges:
                edge_events_spec.append(("edge.delete", edge_id, previous, None))

        old_comments = {
            item["id"]: item for item in project.get("comments") or [] if isinstance(item, dict) and item.get("id")
        }
        incoming_comments = body.get("comments", project.get("comments") or [])
        new_comments = []
        seen_comments: set[str] = set()
        comment_events_spec: list[tuple] = []
        for raw in incoming_comments:
            comment = self._normalize_comment(raw)
            if comment["id"] in seen_comments:
                raise StoreError("conflict", f"Комментарий {comment['id']} уже есть", 409)
            seen_comments.add(comment["id"])
            previous = old_comments.get(comment["id"])
            if previous is None:
                comment_events_spec.append(("comment.create", comment["id"], None, comment))
            elif self._canonical_comment(previous) == self._canonical_comment(comment):
                pass
            else:
                comment_events_spec.append(("comment.update", comment["id"], previous, comment))
            new_comments.append(comment)
        for comment_id, previous in old_comments.items():
            if comment_id not in seen_comments:
                comment_events_spec.append(("comment.delete", comment_id, previous, None))

        meta_events: list[tuple] = []
        if name.strip() != (project.get("name") or ""):
            meta_events.append(("project.rename", {"name": project.get("name")}, {"name": name.strip()}))
        if description != (project.get("scriptDescription") or ""):
            meta_events.append(
                (
                    "project.description",
                    {"scriptDescription": project.get("scriptDescription") or ""},
                    {"scriptDescription": description},
                )
            )

        if not node_events_spec and not edge_events_spec and not comment_events_spec and not meta_events:
            return project, []

        updated = _deep(project)
        updated["name"] = name.strip()
        updated["scriptDescription"] = description
        updated["nodes"] = new_nodes
        updated["edges"] = new_edges
        updated["comments"] = new_comments
        next_revision = int(project.get("revision") or 0) + 1
        self._touch(updated, next_revision)
        events = []
        for event_type, before, after in meta_events:
            events.append(
                self._event(author=author, type_=event_type, revision=next_revision, before=before, after=after)
            )
        for event_type, card_id, before, after in node_events_spec:
            events.append(
                self._event(
                    author=author,
                    type_=event_type,
                    revision=next_revision,
                    card_id=card_id,
                    before=before,
                    after=after,
                )
            )
        for event_type, edge_id, before, after in edge_events_spec:
            events.append(
                self._event(
                    author=author,
                    type_=event_type,
                    revision=next_revision,
                    edge_id=edge_id,
                    before=before,
                    after=after,
                )
            )
        for event_type, comment_id, before, after in comment_events_spec:
            events.append(
                self._event(
                    author=author,
                    type_=event_type,
                    revision=next_revision,
                    comment_id=comment_id,
                    before=before,
                    after=after,
                )
            )
        return updated, events

    def update_project_meta(
        self,
        project_id: str,
        *,
        revision: Any,
        author: str,
        name: str | None = None,
        script_description: str | None = None,
    ) -> dict:
        if name is None and script_description is None:
            raise StoreError("bad_request", "Нечего обновлять: укажите name или scriptDescription")

        def mutate(data: dict):
            project = self._require(data, project_id)
            self._check_project_revision(project, revision)
            events = []
            next_revision = int(project.get("revision") or 0) + 1
            changed = False
            if name is not None:
                if not isinstance(name, str) or not name.strip():
                    raise StoreError("bad_request", "Нужно название проекта")
                if name.strip() != (project.get("name") or ""):
                    before = {"name": project.get("name")}
                    project["name"] = name.strip()
                    changed = True
                    events.append(
                        self._event(
                            author=author,
                            type_="project.rename",
                            revision=next_revision,
                            before=before,
                            after={"name": project["name"]},
                        )
                    )
            if script_description is not None:
                if not isinstance(script_description, str):
                    raise StoreError("bad_request", "scriptDescription должен быть строкой")
                if script_description != (project.get("scriptDescription") or ""):
                    before = {"scriptDescription": project.get("scriptDescription") or ""}
                    project["scriptDescription"] = script_description
                    changed = True
                    events.append(
                        self._event(
                            author=author,
                            type_="project.description",
                            revision=next_revision,
                            before=before,
                            after={"scriptDescription": script_description},
                        )
                    )
            if changed:
                self._touch(project, next_revision)
            return self._public(project_id, project), events

        project = self._commit(project_id, mutate)
        return {"success": True, "revision": project["revision"], "project": project}

    def archive_project(self, project_id: str, revision: Any, author: str) -> dict:
        def mutate(data: dict):
            project = self._require(data, project_id)
            self._check_project_revision(project, revision)
            next_revision = int(project.get("revision") or 0) + 1
            before = {"archived": bool(project.get("archived"))}
            project["archived"] = True
            project["archivedAt"] = now_iso()
            self._touch(project, next_revision)
            event = self._event(
                author=author,
                type_="project.archive",
                revision=next_revision,
                before=before,
                after={"archived": True},
            )
            return {"success": True, "revision": next_revision, "archived": True}, [event]

        return self._commit(project_id, mutate)

    def restore_project(self, project_id: str, revision: Any, author: str) -> dict:
        def mutate(data: dict):
            project = self._require(data, project_id, allow_archived=True)
            if not project.get("archived"):
                raise StoreError("bad_request", "Проект не в архиве")
            self._check_project_revision(project, revision)
            next_revision = int(project.get("revision") or 0) + 1
            project["archived"] = False
            project.pop("archivedAt", None)
            self._touch(project, next_revision)
            event = self._event(
                author=author,
                type_="project.restore",
                revision=next_revision,
                before={"archived": True},
                after={"archived": False},
            )
            return {"success": True, "revision": next_revision, "project": self._public(project_id, project)}, [event]

        return self._commit(project_id, mutate)

    def create_card(self, project_id: str, body: dict, author: str) -> dict:
        def mutate(data: dict):
            project = self._require(data, project_id)
            self._check_project_revision(project, body.get("projectRevision"))
            raw = {key: value for key, value in body.items() if key != "projectRevision"}
            if not raw.get("id"):
                taken = {node.get("id") for node in project.get("nodes") or []}
                raw["id"] = self._new_id("node", {item for item in taken if isinstance(item, str)})
            node = self._normalize_node(raw, 1)
            if any(item.get("id") == node["id"] for item in project.get("nodes") or []):
                raise StoreError("conflict", "Карточка с таким id уже есть", 409, {"revision": project["revision"]})
            project.setdefault("nodes", []).append(node)
            next_revision = int(project.get("revision") or 0) + 1
            self._touch(project, next_revision)
            event = self._event(
                author=author,
                type_="card.create",
                revision=next_revision,
                card_id=node["id"],
                before=None,
                after=node,
            )
            return {"node": _deep(node), "projectRevision": next_revision}, [event]

        return self._commit(project_id, mutate)

    def update_card(self, project_id: str, card_id: str, body: dict, author: str) -> dict:
        card_id = _check_id(card_id, "card id")

        def mutate(data: dict):
            project = self._require(data, project_id)
            nodes = project.get("nodes") or []
            index = next((i for i, node in enumerate(nodes) if node.get("id") == card_id), None)
            if index is None:
                raise NotFound("Карточка не найдена")
            current = nodes[index]
            self._check_card_revision(current, body.get("revision"), int(project.get("revision") or 0))
            updated = _deep(current)
            if "type" in body:
                updated["type"] = self._check_type(body["type"])
            if "position" in body:
                updated["position"] = self._check_position(body["position"])
            if "data" in body:
                if not isinstance(body["data"], dict):
                    raise StoreError("bad_request", "data карточки должен быть объектом")
                merged = dict(updated.get("data") or {})
                merged.update(body["data"])
                updated["data"] = merged
            for key in ("width", "height", "measured", "style", "className", "parentId"):
                if key in body:
                    updated[key] = _deep(body[key])
            updated = self._normalize_node(updated, int(current.get("revision") or 0))
            if self._canonical_node(current) == self._canonical_node(updated):
                return {"node": _deep(current), "projectRevision": int(project.get("revision") or 0)}, []
            updated["revision"] = int(current.get("revision") or 0) + 1
            nodes[index] = updated
            project["nodes"] = nodes
            next_revision = int(project.get("revision") or 0) + 1
            self._touch(project, next_revision)
            event = self._event(
                author=author,
                type_="card.update",
                revision=next_revision,
                card_id=card_id,
                before=current,
                after=updated,
            )
            return {"node": _deep(updated), "projectRevision": next_revision}, [event]

        return self._commit(project_id, mutate)

    def delete_card(self, project_id: str, card_id: str, revision: Any, author: str) -> dict:
        card_id = _check_id(card_id, "card id")

        def mutate(data: dict):
            project = self._require(data, project_id)
            nodes = project.get("nodes") or []
            current = next((node for node in nodes if node.get("id") == card_id), None)
            if current is None:
                raise NotFound("Карточка не найдена")
            self._check_card_revision(current, revision, int(project.get("revision") or 0))
            next_revision = int(project.get("revision") or 0) + 1
            project["nodes"] = [node for node in nodes if node.get("id") != card_id]
            removed_edges = [
                edge
                for edge in project.get("edges") or []
                if edge.get("source") == card_id or edge.get("target") == card_id
            ]
            project["edges"] = [
                edge
                for edge in project.get("edges") or []
                if edge.get("source") != card_id and edge.get("target") != card_id
            ]
            self._touch(project, next_revision)
            events = [
                self._event(
                    author=author,
                    type_="card.delete",
                    revision=next_revision,
                    card_id=card_id,
                    before=current,
                    after=None,
                )
            ]
            for edge in removed_edges:
                events.append(
                    self._event(
                        author=author,
                        type_="edge.delete",
                        revision=next_revision,
                        edge_id=edge.get("id"),
                        before=edge,
                        after=None,
                    )
                )
            return {"success": True, "projectRevision": next_revision}, events

        return self._commit(project_id, mutate)

    def create_edge(self, project_id: str, body: dict, author: str) -> dict:
        def mutate(data: dict):
            project = self._require(data, project_id)
            self._check_project_revision(project, body.get("projectRevision"))
            raw = {key: value for key, value in body.items() if key != "projectRevision"}
            node_ids = {node.get("id") for node in project.get("nodes") or []}
            if raw.get("source") not in node_ids or raw.get("target") not in node_ids:
                raise StoreError("bad_request", "source и target должны быть id существующих карточек")
            if not raw.get("id"):
                raw["id"] = f"e-{raw.get('source')}-{raw.get('target')}"
                taken = {edge.get("id") for edge in project.get("edges") or []}
                if raw["id"] in taken:
                    raw["id"] = self._new_id("e", {item for item in taken if isinstance(item, str)})
            edge = self._normalize_edge(raw)
            if any(item.get("id") == edge["id"] for item in project.get("edges") or []):
                raise StoreError("conflict", "Связь с таким id уже есть", 409, {"revision": project["revision"]})
            if any(
                item.get("source") == edge["source"] and item.get("target") == edge["target"]
                for item in project.get("edges") or []
            ):
                raise StoreError("conflict", "Такая связь уже есть", 409, {"revision": project["revision"]})
            project.setdefault("edges", []).append(edge)
            next_revision = int(project.get("revision") or 0) + 1
            self._touch(project, next_revision)
            event = self._event(
                author=author,
                type_="edge.create",
                revision=next_revision,
                edge_id=edge["id"],
                before=None,
                after=edge,
            )
            return {"edge": _deep(edge), "projectRevision": next_revision}, [event]

        return self._commit(project_id, mutate)

    def delete_edge(self, project_id: str, edge_id: str, project_revision: Any, author: str) -> dict:
        edge_id = _check_id(edge_id, "edge id")

        def mutate(data: dict):
            project = self._require(data, project_id)
            self._check_project_revision(project, project_revision)
            edges = project.get("edges") or []
            current = next((edge for edge in edges if edge.get("id") == edge_id), None)
            if current is None:
                raise NotFound("Связь не найдена")
            project["edges"] = [edge for edge in edges if edge.get("id") != edge_id]
            next_revision = int(project.get("revision") or 0) + 1
            self._touch(project, next_revision)
            event = self._event(
                author=author,
                type_="edge.delete",
                revision=next_revision,
                edge_id=edge_id,
                before=current,
                after=None,
            )
            return {"success": True, "projectRevision": next_revision}, [event]

        return self._commit(project_id, mutate)

    def create_comment(self, project_id: str, body: dict, author: str) -> dict:
        def mutate(data: dict):
            project = self._require(data, project_id)
            self._check_project_revision(project, body.get("projectRevision"))
            raw = {key: value for key, value in body.items() if key != "projectRevision"}
            if not raw.get("id"):
                taken = {item.get("id") for item in project.get("comments") or []}
                raw["id"] = self._new_id("comment", {item for item in taken if isinstance(item, str)})
            comment = self._normalize_comment(raw)
            if any(item.get("id") == comment["id"] for item in project.get("comments") or []):
                raise StoreError("conflict", "Комментарий с таким id уже есть", 409, {"revision": project["revision"]})
            project.setdefault("comments", []).append(comment)
            next_revision = int(project.get("revision") or 0) + 1
            self._touch(project, next_revision)
            event = self._event(
                author=author,
                type_="comment.create",
                revision=next_revision,
                comment_id=comment["id"],
                before=None,
                after=comment,
            )
            return {"comment": _deep(comment), "projectRevision": next_revision}, [event]

        return self._commit(project_id, mutate)

    def update_comment(self, project_id: str, comment_id: str, body: dict, author: str) -> dict:
        comment_id = _check_id(comment_id, "comment id")

        def mutate(data: dict):
            project = self._require(data, project_id)
            self._check_project_revision(project, body.get("projectRevision"))
            comments = project.get("comments") or []
            index = next((i for i, item in enumerate(comments) if item.get("id") == comment_id), None)
            if index is None:
                raise NotFound("Комментарий не найден")
            current = comments[index]
            updated = _deep(current)
            if "text" in body:
                if not isinstance(body["text"], str):
                    raise StoreError("bad_request", "text должен быть строкой")
                updated["text"] = body["text"]
            if "x" in body:
                updated["x"] = body["x"]
            if "y" in body:
                updated["y"] = body["y"]
            updated = self._normalize_comment(updated)
            if self._canonical_comment(current) == self._canonical_comment(updated):
                return {"comment": _deep(current), "projectRevision": int(project.get("revision") or 0)}, []
            comments[index] = updated
            project["comments"] = comments
            next_revision = int(project.get("revision") or 0) + 1
            self._touch(project, next_revision)
            event = self._event(
                author=author,
                type_="comment.update",
                revision=next_revision,
                comment_id=comment_id,
                before=current,
                after=updated,
            )
            return {"comment": _deep(updated), "projectRevision": next_revision}, [event]

        return self._commit(project_id, mutate)

    def delete_comment(self, project_id: str, comment_id: str, project_revision: Any, author: str) -> dict:
        comment_id = _check_id(comment_id, "comment id")

        def mutate(data: dict):
            project = self._require(data, project_id)
            self._check_project_revision(project, project_revision)
            comments = project.get("comments") or []
            current = next((item for item in comments if item.get("id") == comment_id), None)
            if current is None:
                raise NotFound("Комментарий не найден")
            project["comments"] = [item for item in comments if item.get("id") != comment_id]
            next_revision = int(project.get("revision") or 0) + 1
            self._touch(project, next_revision)
            event = self._event(
                author=author,
                type_="comment.delete",
                revision=next_revision,
                comment_id=comment_id,
                before=current,
                after=None,
            )
            return {"success": True, "projectRevision": next_revision}, [event]

        return self._commit(project_id, mutate)

    def get_history(
        self,
        project_id: str,
        *,
        since: str | None = None,
        author: str | None = None,
        exclude_author: str | None = None,
    ) -> dict:
        project_id = _check_id(project_id, "project id")
        with self._locked():
            data, migrated = self._load_migrated()
            if migrated:
                self._write(data)
            if project_id not in data or not isinstance(data.get(project_id), dict):
                raise NotFound("Проект не найден")
            project = data[project_id]
            events = self._read_history(project_id)
            filtered = self._filter_events(events, since=since, author=author, exclude_author=exclude_author)
            return {
                "projectId": project_id,
                "revision": int(project.get("revision") or 0),
                "events": filtered,
            }

    def _filter_events(
        self,
        events: list[dict],
        *,
        since: str | None,
        author: str | None,
        exclude_author: str | None,
    ) -> list[dict]:
        selected = list(events)
        if since:
            token = since.strip()
            if token.startswith("evt-") or any(item.get("id") == token for item in events):
                indexes = [index for index, item in enumerate(events) if item.get("id") == token]
                if not indexes:
                    raise StoreError("bad_request", "Событие since не найдено")
                selected = events[indexes[0] + 1 :]
            else:
                try:
                    bound = _parse_dt(token)
                except (ValueError, OSError) as exc:
                    raise StoreError("bad_request", "since должен быть ISO-временем, epoch ms или id события") from exc
                kept = []
                for item in selected:
                    try:
                        moment = _parse_dt(str(item.get("ts") or ""))
                    except (ValueError, OSError):
                        continue
                    if moment > bound:
                        kept.append(item)
                selected = kept
        if author:
            needle = author.strip().lower()
            selected = [item for item in selected if str(item.get("author") or "").lower() == needle]
        if exclude_author:
            banned = exclude_author.strip().lower()
            selected = [item for item in selected if str(item.get("author") or "").lower() != banned]
        return selected
