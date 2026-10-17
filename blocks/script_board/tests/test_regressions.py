# -*- coding: utf-8 -*-
"""Регрессии доски: параллельные правки, миграция, история, старый PUT, PDF."""
from __future__ import annotations

import base64
import json
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from blocks.script_board.api import app
from blocks.script_board.store import BoardStore, RevisionConflict

ROOT = Path(__file__).resolve().parents[3]
FRONTEND = ROOT / "blocks" / "script_board" / "frontend" / "src"


@pytest.fixture
def storage(tmp_path, monkeypatch):
    monkeypatch.setenv("SCRIPT_BOARD_STORAGE", str(tmp_path))
    return tmp_path


def _client() -> TestClient:
    return TestClient(app)


def _basic(user: str, password: str = "secret") -> dict[str, str]:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _seed_two_cards(store: BoardStore) -> str:
    created = store.create_project(
        name="Проект 1",
        script_description="контекст",
        author="unknown",
        nodes=[
            {
                "id": "card-a",
                "type": "client",
                "position": {"x": 1, "y": 2},
                "data": {"title": "A", "text": "старый A"},
            },
            {
                "id": "card-b",
                "type": "our_response",
                "position": {"x": 30, "y": 40},
                "data": {"title": "B", "text": "старый B"},
            },
        ],
        edges=[{"id": "xy-edge__card-a-card-b", "source": "card-a", "target": "card-b"}],
        comments=[{"id": "comment-1", "x": 5, "y": 6, "text": "заметка"}],
    )
    return created["id"]


def test_parallel_same_card_second_write_conflicts(storage):
    store = BoardStore(storage)
    project_id = _seed_two_cards(store)
    results: list[tuple] = []

    def write(text: str) -> None:
        try:
            saved = store.update_card(
                project_id,
                "card-a",
                {"revision": 1, "data": {"text": text}},
                "human",
            )
            results.append(("ok", saved["node"]["data"]["text"]))
        except RevisionConflict as exc:
            results.append(("conflict", exc.extra.get("cardRevision")))

    threads = [threading.Thread(target=write, args=(text,)) for text in ("альфа", "бета")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(item[0] for item in results) == ["conflict", "ok"]
    project = store.get_project(project_id)
    texts = {node["id"]: node["data"]["text"] for node in project["nodes"]}
    assert texts["card-a"] in {"альфа", "бета"}
    assert texts["card-b"] == "старый B"
    assert project["comments"][0]["text"] == "заметка"
    assert project["edges"][0]["id"] == "xy-edge__card-a-card-b"
    winner = texts["card-a"]

    response = _client().patch(
        f"/api/projects/{project_id}/cards/card-a",
        json={"revision": 1, "data": {"text": "опоздал"}},
    )
    assert response.status_code == 409
    again = store.get_project(project_id)
    kept = {node["id"]: node["data"]["text"] for node in again["nodes"]}
    assert kept["card-a"] == winner
    assert kept["card-b"] == "старый B"


def test_parallel_different_cards_do_not_clobber(storage):
    store = BoardStore(storage)
    project_id = _seed_two_cards(store)
    errors: list[BaseException] = []

    def write(card_id: str, text: str) -> None:
        try:
            store.update_card(project_id, card_id, {"revision": 1, "data": {"text": text}}, "editor")
        except BaseException as exc:  # noqa: BLE001 — тест должен увидеть любую гонку
            errors.append(exc)

    threads = [
        threading.Thread(target=write, args=("card-a", "бот A")),
        threading.Thread(target=write, args=("card-b", "человек B")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []

    project = store.get_project(project_id)
    by_id = {node["id"]: node for node in project["nodes"]}
    assert by_id["card-a"]["data"]["text"] == "бот A"
    assert by_id["card-b"]["data"]["text"] == "человек B"
    assert by_id["card-a"]["revision"] == 2
    assert by_id["card-b"]["revision"] == 2
    assert project["comments"][0]["text"] == "заметка"

    client = _client()
    for card_id, text in (("card-a", "бот A2"), ("card-b", "человек B2")):
        response = client.patch(
            f"/api/projects/{project_id}/cards/{card_id}",
            json={"revision": 2, "data": {"text": text}},
        )
        assert response.status_code == 200, response.text
    fresh = client.get(f"/api/projects/{project_id}").json()
    fresh_text = {node["id"]: node["data"]["text"] for node in fresh["nodes"]}
    assert fresh_text == {"card-a": "бот A2", "card-b": "человек B2"}


def test_migration_keeps_nodes_edges_and_comments(storage):
    legacy = {
        "project-1771855166843": {
            "name": "Проект 1",
            "scriptDescription": "контекст проекта",
            "nodes": [
                {
                    "id": "n1",
                    "type": "client",
                    "position": {"x": 12.5, "y": 40},
                    "width": 280,
                    "measured": {"width": 280, "height": 120},
                    "data": {"title": "Клиент", "text": "Здравствуйте"},
                }
            ],
            "edges": [{"id": "xy-edge__n1-gone", "source": "n1", "target": "gone"}],
            "comments": [{"id": "comment-1", "x": 8, "y": 9, "text": "заметка"}],
        },
        "project-1772813395846": {
            "name": "Вариант Леши",
            "nodes": [
                {
                    "id": "n2",
                    "type": "our_response",
                    "position": {"x": 1, "y": 2},
                    "data": {"title": "Ответ", "text": "Текст Леши"},
                }
            ],
            "edges": [],
            "comments": [{"id": "comment-2", "x": 0, "y": 1, "text": "коммент Леши"}],
        },
    }
    (storage / "projects.json").write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")

    client = _client()
    first = client.get("/api/projects/project-1771855166843")
    second = client.get("/api/projects/project-1772813395846")
    assert first.status_code == 200
    assert second.status_code == 200
    left = first.json()
    right = second.json()
    assert left["name"] == "Проект 1"
    assert right["name"] == "Вариант Леши"
    assert left["revision"] == 0
    assert right["revision"] == 0
    assert left["nodes"][0]["data"]["text"] == "Здравствуйте"
    assert left["nodes"][0]["width"] == 280
    assert left["nodes"][0]["measured"]["height"] == 120
    assert left["nodes"][0]["revision"] == 0
    assert left["edges"] == [{"id": "xy-edge__n1-gone", "source": "n1", "target": "gone"}]
    assert left["comments"][0]["text"] == "заметка"
    assert left["goals"] == []
    assert right["goals"] == []
    assert right["nodes"][0]["data"]["text"] == "Текст Леши"
    assert right["comments"][0]["text"] == "коммент Леши"

    stored = json.loads((storage / "projects.json").read_text(encoding="utf-8"))
    assert set(stored) == {"project-1771855166843", "project-1772813395846"}
    assert stored["project-1771855166843"]["nodes"][0]["width"] == 280
    assert stored["project-1771855166843"]["goals"] == []
    assert stored["project-1772813395846"]["goals"] == []
    history = client.get("/api/projects/project-1771855166843/history")
    assert history.status_code == 200
    assert history.json()["events"] == []


def test_history_author_header_and_exclude_author(storage):
    client = _client()
    created = client.post("/api/projects", json={"name": "Проект 1", "scriptDescription": "контекст"})
    assert created.status_code == 200, created.text
    project_id = created.json()["id"]
    assert created.json()["revision"] == 1

    opened = client.get(f"/api/projects/{project_id}/history")
    assert opened.json()["events"][0]["author"] == "unknown"
    assert opened.json()["events"][0]["type"] == "project.create"

    card = client.post(
        f"/api/projects/{project_id}/cards",
        headers={"X-Remote-User": "alexey"},
        json={
            "id": "card-a",
            "type": "client",
            "position": {"x": 0, "y": 0},
            "data": {"title": "A", "text": "черновик"},
            "projectRevision": 1,
        },
    )
    assert card.status_code == 200, card.text
    sonya = client.patch(
        f"/api/projects/{project_id}/cards/card-a",
        headers=_basic("sonya"),
        json={"revision": 1, "data": {"text": "от Сони"}},
    )
    assert sonya.status_code == 200, sonya.text
    both = client.patch(
        f"/api/projects/{project_id}/cards/card-a",
        headers={"X-Remote-User": "alexey", **_basic("sonya")},
        json={"revision": 2, "data": {"text": "правка Алексея"}},
    )
    assert both.status_code == 200, both.text

    events = client.get(f"/api/projects/{project_id}/history").json()["events"]
    authors = [(event["type"], event["author"]) for event in events]
    assert ("project.create", "unknown") in authors
    assert ("card.create", "alexey") in authors
    assert ("card.update", "sonya") in authors
    assert ("card.update", "alexey") in authors
    assert authors[-1] == ("card.update", "alexey")

    without_sonya = client.get(f"/api/projects/{project_id}/history?exclude_author=sonya").json()["events"]
    assert all(event["author"].lower() != "sonya" for event in without_sonya)
    assert any(event["author"] == "alexey" for event in without_sonya)

    only_sonya = client.get(f"/api/projects/{project_id}/history?author=Sonya").json()["events"]
    assert len(only_sonya) == 1
    assert only_sonya[0]["author"] == "sonya"
    sonya_id = only_sonya[0]["id"]

    after = client.get(
        f"/api/projects/{project_id}/history",
        params={"since": sonya_id, "exclude_author": "sonya"},
    )
    assert after.status_code == 200, after.text
    later = after.json()["events"]
    assert len(later) == 1
    assert later[0]["author"] == "alexey"
    assert later[0]["after"]["data"]["text"] == "правка Алексея"


def test_full_put_still_works_and_stale_revision_is_409(storage):
    client = _client()
    created = client.post("/api/projects", json={"name": "Проект 1"})
    project_id = created.json()["id"]

    missing = client.put(
        f"/api/projects/{project_id}",
        json={"name": "Затёрто", "nodes": [], "edges": [], "scriptDescription": "", "comments": []},
    )
    assert missing.status_code == 409
    assert client.get(f"/api/projects/{project_id}").json()["name"] == "Проект 1"

    stale = client.put(
        f"/api/projects/{project_id}",
        json={"name": "Затёрто", "revision": 0, "nodes": [], "edges": [], "scriptDescription": "", "comments": []},
    )
    assert stale.status_code == 409
    assert client.get(f"/api/projects/{project_id}").json()["revision"] == 1

    saved = client.put(
        f"/api/projects/{project_id}",
        json={
            "name": "Проект 1",
            "revision": 1,
            "scriptDescription": "для Сони",
            "nodes": [
                {
                    "id": "card-a",
                    "type": "client",
                    "position": {"x": 1, "y": 2},
                    "data": {"title": "A", "text": "один"},
                }
            ],
            "edges": [],
            "comments": [{"id": "comment-1", "x": 3, "y": 4, "text": "заметка"}],
        },
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["success"] is True
    assert saved.json()["revision"] == 2

    updated = client.put(
        f"/api/projects/{project_id}",
        json={
            "name": "Проект 1",
            "revision": 2,
            "scriptDescription": "для Сони",
            "nodes": [
                {
                    "id": "card-a",
                    "type": "client",
                    "position": {"x": 1, "y": 2},
                    "data": {"title": "A", "text": "один-новый"},
                },
                {
                    "id": "card-b",
                    "type": "our_response",
                    "position": {"x": 10, "y": 20},
                    "data": {"title": "B", "text": "два"},
                },
            ],
            "edges": [{"id": "e-card-a-card-b", "source": "card-a", "target": "card-b"}],
            "comments": [{"id": "comment-1", "x": 3, "y": 4, "text": "заметка обновлена"}],
        },
    )
    assert updated.status_code == 200, updated.text
    project = client.get(f"/api/projects/{project_id}").json()
    by_id = {node["id"]: node for node in project["nodes"]}
    assert by_id["card-a"]["data"]["text"] == "один-новый"
    assert by_id["card-b"]["data"]["text"] == "два"
    assert project["edges"][0]["target"] == "card-b"
    assert project["comments"][0]["text"] == "заметка обновлена"
    assert project["revision"] == 3

    same = client.put(
        f"/api/projects/{project_id}",
        json={
            "name": project["name"],
            "revision": project["revision"],
            "scriptDescription": project["scriptDescription"],
            "nodes": project["nodes"],
            "edges": project["edges"],
            "comments": project["comments"],
        },
    )
    assert same.status_code == 200, same.text
    assert same.json()["revision"] == 3

    manual = client.put(
        "/api/projects/project-manual",
        json={"name": "Ручной", "nodes": [], "edges": [], "scriptDescription": "", "comments": []},
    )
    assert manual.status_code == 200, manual.text
    assert manual.json()["revision"] == 1
    assert client.get("/api/projects/project-manual").json()["name"] == "Ручной"

    archived = client.delete(f"/api/projects/{project_id}?revision=3")
    assert archived.status_code == 200, archived.text
    listed = client.get("/api/projects").json()
    assert project_id not in {item["id"] for item in listed}
    assert "project-manual" in {item["id"] for item in listed}
    hidden = client.get("/api/projects?include_archived=true").json()
    assert project_id in {item["id"] for item in hidden}


def test_goals_keep_revision_conflict_and_author(storage):
    client = _client()
    created = client.post("/api/projects", json={"name": "Проект 1"})
    project_id = created.json()["id"]
    revision = created.json()["revision"]

    first = client.post(
        f"/api/projects/{project_id}/goals",
        headers={"X-Remote-User": "sonya"},
        json={"projectRevision": revision, "text": "Адрес объекта", "note": "город и улица"},
    )
    assert first.status_code == 200, first.text
    address = first.json()["goal"]
    assert address["revision"] == 1
    assert address["order"] == 0
    revision = first.json()["projectRevision"]

    second = client.post(
        f"/api/projects/{project_id}/goals",
        headers={"X-Remote-User": "alexey"},
        json={"projectRevision": revision, "text": "Бюджет"},
    )
    assert second.status_code == 200, second.text
    budget = second.json()["goal"]
    revision = second.json()["projectRevision"]

    stale = client.patch(
        f"/api/projects/{project_id}/goals/{address['id']}",
        json={"revision": 0, "text": "чужой адрес"},
    )
    assert stale.status_code == 409
    assert stale.json()["detail"]["goalRevision"] == 1
    kept = client.get(f"/api/projects/{project_id}").json()
    assert kept["goals"][0]["text"] == "Адрес объекта"

    edited = client.patch(
        f"/api/projects/{project_id}/goals/{address['id']}",
        headers={"X-Remote-User": "alexey"},
        json={"revision": 1, "text": "Адрес объекта", "note": "с номером дома"},
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["goal"]["revision"] == 2
    revision = edited.json()["projectRevision"]

    moved = client.post(
        f"/api/projects/{project_id}/goals/reorder",
        headers={"X-Remote-User": "alexey"},
        json={"projectRevision": revision, "ids": [budget["id"], address["id"]]},
    )
    assert moved.status_code == 200, moved.text
    assert [item["text"] for item in moved.json()["goals"]] == ["Бюджет", "Адрес объекта"]
    revision = moved.json()["projectRevision"]

    events = client.get(f"/api/projects/{project_id}/history").json()["events"]
    created_address = next(event for event in events if event["type"] == "goal.create" and event["goalId"] == address["id"])
    assert created_address["author"] == "sonya"
    assert any(event["type"] == "goal.update" and event["author"] == "alexey" for event in events)
    assert any(event["type"] == "goal.reorder" and event["author"] == "alexey" for event in events)

    project = client.get(f"/api/projects/{project_id}").json()
    untouched = client.put(
        f"/api/projects/{project_id}",
        json={
            "name": project["name"],
            "revision": project["revision"],
            "scriptDescription": project["scriptDescription"],
            "nodes": project["nodes"],
            "edges": project["edges"],
            "comments": project["comments"],
        },
    )
    assert untouched.status_code == 200, untouched.text
    assert [item["text"] for item in client.get(f"/api/projects/{project_id}").json()["goals"]] == [
        "Бюджет",
        "Адрес объекта",
    ]

    removed = client.delete(f"/api/projects/{project_id}/goals/{budget['id']}?revision=1")
    assert removed.status_code == 200, removed.text
    assert [item["text"] for item in removed.json()["goals"]] == ["Адрес объекта"]
    late = client.delete(f"/api/projects/{project_id}/goals/{budget['id']}?revision=1")
    assert late.status_code == 404

    store = BoardStore(storage)
    raced: list[tuple] = []

    def write(text: str) -> None:
        try:
            saved = store.update_goal(project_id, address["id"], {"revision": 2, "text": text}, "human")
            raced.append(("ok", saved["goal"]["text"]))
        except RevisionConflict:
            raced.append(("conflict", text))

    threads = [threading.Thread(target=write, args=(text,)) for text in ("адрес А", "адрес Б")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(item[0] for item in raced) == ["conflict", "ok"]
    winner = next(item[1] for item in raced if item[0] == "ok")
    final = store.get_project(project_id)
    assert final["goals"][0]["text"] == winner


def test_old_goal_without_revision_is_kept(storage):
    legacy = {
        "project-old": {
            "name": "Проект 1",
            "nodes": [],
            "edges": [],
            "comments": [],
            "goals": [{"id": "goal-area", "text": "Площадь", "order": 0}],
        }
    }
    (storage / "projects.json").write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
    project = _client().get("/api/projects/project-old").json()
    assert project["goals"][0]["text"] == "Площадь"
    assert project["goals"][0]["revision"] == 0
    assert project["goals"][0]["note"] == ""


def test_removed_ai_routes_are_404(storage):
    client = _client()
    assert client.post("/api/generate", json={"messages": []}).status_code == 404
    assert client.post("/api/improve-text", json={"text": "x"}).status_code == 404
    assert client.get("/api/check-grs").status_code == 404
    assert client.get("/api/models").status_code == 404
    source = (ROOT / "blocks" / "script_board" / "api.py").read_text(encoding="utf-8")
    assert "GRSAI" not in source
    assert "/api/generate" not in source
    assert "improve-text" not in source


def test_pdf_button_and_comments_remain():
    app_source = (FRONTEND / "App.tsx").read_text(encoding="utf-8")
    editor = (FRONTEND / "TextEditorModal.tsx").read_text(encoding="utf-8")
    response_node = (FRONTEND / "nodes" / "OurResponseNode.tsx").read_text(encoding="utf-8")
    settings = (FRONTEND / "SettingsModal.tsx").read_text(encoding="utf-8")
    storage = (FRONTEND / "projectsStorage.ts").read_text(encoding="utf-8")

    assert "handleDownloadPdf" in app_source
    assert "html2canvas" in app_source
    assert "jsPDF" in app_source
    assert "Скачать в PDF" in app_source
    assert "Режим комментирования" in app_source
    assert 'id="history-slot"' in app_source
    assert "data-history-hook" in app_source
    assert "История изменений" in app_source
    assert "AddCommentModal" in app_source
    assert "ViewCommentModal" in app_source
    assert "/api/generate" not in app_source
    assert "Улучшить текст" not in app_source
    assert "Сгенерировать ответ" not in app_source
    assert "Улучшить текст" not in editor
    assert "/api/improve-text" not in editor
    assert "Сгенерировать" not in response_node
    assert "onGenerate" not in response_node
    assert "контекст для Сони" in settings
    assert "генерац" not in settings.lower()
    assert "script_board_projects" not in storage
    assert "pendingSave" in storage
    assert not (FRONTEND / "ImproveTextModal.tsx").exists()
    assert "export function useHistory" in (FRONTEND / "useHistory.ts").read_text(encoding="utf-8")
    history_panel = (FRONTEND / "HistoryPanel.tsx").read_text(encoding="utf-8")
    assert "useHistory" in history_panel
    assert "правки не от sonya" in history_panel
    assert "excludeAuthor" in history_panel
    assert "export const api" in (FRONTEND / "api.ts").read_text(encoding="utf-8")
