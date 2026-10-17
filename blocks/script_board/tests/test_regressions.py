# -*- coding: utf-8 -*-
"""Запрещённые регрессии доски скриптов."""
import base64
import json
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from blocks.script_board.api import create_app
from blocks.script_board.store import BoardStore, RevisionConflict


@pytest.fixture
def storage_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def client(storage_dir: Path):
    app = create_app(storage_dir)
    with TestClient(app) as test_client:
        yield test_client


def _basic(user: str, password: str = "secret") -> dict:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _card(card_id: str, type_: str, title: str, text: str, x: int = 0, y: int = 0) -> dict:
    return {
        "id": card_id,
        "type": type_,
        "position": {"x": x, "y": y},
        "data": {"title": title, "text": text},
    }


def _create_two_cards(client: TestClient) -> str:
    response = client.post(
        "/api/projects",
        json={
            "name": "Авито",
            "scriptDescription": "контекст для Сони",
            "nodes": [
                _card("node-a", "client", "Клиент", "исходный A"),
                _card("node-b", "our_response", "Мы", "исходный B"),
            ],
            "edges": [{"id": "e-node-a-node-b", "source": "node-a", "target": "node-b"}],
            "comments": [{"id": "comment-1", "x": 10, "y": 20, "text": "заметка"}],
        },
        headers={"X-Remote-User": "sonya"},
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_parallel_same_card_second_gets_409_and_data_survives(storage_dir: Path, client: TestClient):
    project_id = _create_two_cards(client)
    store = BoardStore(storage_dir)
    barrier = threading.Barrier(2)
    outcomes: list[tuple] = []

    def worker(text: str):
        barrier.wait()
        try:
            result = store.update_card(
                project_id,
                "node-a",
                {"revision": 1, "data": {"text": text}},
                author="sonya" if text == "бот" else "alexey",
            )
            outcomes.append(("ok", text, result["node"]["data"]["text"]))
        except RevisionConflict as exc:
            outcomes.append(("conflict", text, exc.extra.get("cardRevision")))

    threads = [
        threading.Thread(target=worker, args=("бот",)),
        threading.Thread(target=worker, args=("человек",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(item[0] for item in outcomes) == ["conflict", "ok"]
    winner = next(item[1] for item in outcomes if item[0] == "ok")
    saved = store.get_project(project_id)
    texts = {node["id"]: node["data"]["text"] for node in saved["nodes"]}
    assert texts["node-a"] == winner
    assert texts["node-b"] == "исходный B"
    assert saved["comments"][0]["text"] == "заметка"
    assert saved["edges"][0]["id"] == "e-node-a-node-b"

    stale = client.patch(
        f"/api/projects/{project_id}/cards/node-a",
        json={"revision": 1, "data": {"text": "ещё одна попытка"}},
        headers={"X-Remote-User": "sonya"},
    )
    assert stale.status_code == 409
    again = store.get_project(project_id)
    assert {node["id"]: node["data"]["text"] for node in again["nodes"]}["node-a"] == winner
    raw = json.loads((storage_dir / "projects.json").read_text(encoding="utf-8"))
    assert raw[project_id]["nodes"]


def test_parallel_card_edits_do_not_clobber_each_other(storage_dir: Path, client: TestClient):
    project_id = _create_two_cards(client)
    store = BoardStore(storage_dir)
    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def worker(card_id: str, text: str, author: str):
        barrier.wait()
        try:
            store.update_card(
                project_id,
                card_id,
                {"revision": 1, "data": {"text": text}},
                author=author,
            )
        except BaseException as exc:  # noqa: BLE001 — тест должен увидеть любой сбой
            errors.append(exc)

    threads = [
        threading.Thread(target=worker, args=("node-a", "текст бота", "sonya")),
        threading.Thread(target=worker, args=("node-b", "текст человека", "alexey")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    saved = store.get_project(project_id)
    texts = {node["id"]: node["data"]["text"] for node in saved["nodes"]}
    assert texts == {"node-a": "текст бота", "node-b": "текст человека"}
    revisions = {node["id"]: node["revision"] for node in saved["nodes"]}
    assert revisions == {"node-a": 2, "node-b": 2}

    # Повтор по HTTP: ревизия карточки B не устарела из-за правки A и наоборот.
    fresh = client.get(f"/api/projects/{project_id}").json()
    card_a = next(node for node in fresh["nodes"] if node["id"] == "node-a")
    card_b = next(node for node in fresh["nodes"] if node["id"] == "node-b")
    left = client.patch(
        f"/api/projects/{project_id}/cards/node-a",
        json={"revision": card_a["revision"], "data": {"text": "бот ещё раз"}},
        headers={"X-Remote-User": "sonya"},
    )
    right = client.patch(
        f"/api/projects/{project_id}/cards/node-b",
        json={"revision": card_b["revision"], "data": {"text": "человек ещё раз"}},
        headers={"X-Remote-User": "alexey"},
    )
    assert left.status_code == 200, left.text
    assert right.status_code == 200, right.text
    final = client.get(f"/api/projects/{project_id}").json()
    final_texts = {node["id"]: node["data"]["text"] for node in final["nodes"]}
    assert final_texts == {"node-a": "бот ещё раз", "node-b": "человек ещё раз"}


def test_migration_preserves_nodes_edges_comments(storage_dir: Path):
    legacy = {
        "project-1771855166843": {
            "name": "Проект 1",
            "scriptDescription": "старый контекст",
            "nodes": [
                {
                    "id": "node-1",
                    "type": "client",
                    "position": {"x": 10, "y": 20},
                    "data": {"title": "Вопрос", "text": "Сколько стоит?"},
                    "width": 180,
                    "measured": {"width": 180, "height": 70},
                },
                {
                    "id": "node-2",
                    "type": "our_response",
                    "position": {"x": 10, "y": 200},
                    "data": {"title": "Ответ", "text": "Зависит от площади"},
                },
            ],
            "edges": [{"id": "e-node-1-node-2", "source": "node-1", "target": "node-2"}],
            "comments": [{"id": "comment-9", "x": 3, "y": 4, "text": "не удалять"}],
        },
        "project-1772813395846": {
            "name": "Вариант Леши",
            "scriptDescription": "",
            "nodes": [
                {
                    "id": "node-lesh",
                    "type": "client",
                    "position": {"x": 0, "y": 0},
                    "data": {"title": "Леша", "text": "вариант"},
                }
            ],
            "edges": [{"id": "e-dangling", "source": "node-lesh", "target": "node-missing"}],
            "comments": [
                {"id": "comment-a", "x": 1, "y": 2, "text": "первый"},
                {"id": "comment-b", "x": 5, "y": 6, "text": "второй"},
            ],
        },
    }
    path = storage_dir / "projects.json"
    path.write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")

    app = create_app(storage_dir)
    with TestClient(app) as test_client:
        listing = test_client.get("/api/projects")
        assert listing.status_code == 200
        names = {item["id"]: item["name"] for item in listing.json()}
        assert names["project-1771855166843"] == "Проект 1"
        assert names["project-1772813395846"] == "Вариант Леши"

        first = test_client.get("/api/projects/project-1771855166843").json()
        second = test_client.get("/api/projects/project-1772813395846").json()

    assert first["scriptDescription"] == "старый контекст"
    assert first["revision"] == 0
    assert [(node["id"], node["data"], node["type"], node["position"]) for node in first["nodes"]] == [
        ("node-1", {"title": "Вопрос", "text": "Сколько стоит?"}, "client", {"x": 10, "y": 20}),
        ("node-2", {"title": "Ответ", "text": "Зависит от площади"}, "our_response", {"x": 10, "y": 200}),
    ]
    assert first["nodes"][0]["width"] == 180
    assert first["nodes"][0]["measured"] == {"width": 180, "height": 70}
    assert first["nodes"][0]["revision"] == 0
    assert first["edges"] == legacy["project-1771855166843"]["edges"]
    assert first["comments"] == legacy["project-1771855166843"]["comments"]

    assert second["name"] == "Вариант Леши"
    assert second["nodes"][0]["data"]["text"] == "вариант"
    assert second["edges"] == legacy["project-1772813395846"]["edges"]
    assert second["comments"] == legacy["project-1772813395846"]["comments"]

    stored = json.loads(path.read_text(encoding="utf-8"))
    assert set(stored) == {"project-1771855166843", "project-1772813395846"}
    assert stored["project-1771855166843"]["nodes"][0]["data"]["text"] == "Сколько стоит?"
    assert stored["project-1772813395846"]["comments"][1]["text"] == "второй"


def test_history_records_author_and_exclude_author(client: TestClient):
    created = client.post("/api/projects", json={"name": "История", "scriptDescription": ""})
    assert created.status_code == 200, created.text
    project_id = created.json()["id"]
    assert created.json()["revision"] == 1

    no_header = client.get(f"/api/projects/{project_id}/history")
    assert no_header.status_code == 200
    assert no_header.json()["events"][0]["author"] == "unknown"
    assert no_header.json()["events"][0]["type"] == "project.create"

    renamed = client.patch(
        f"/api/projects/{project_id}",
        json={"revision": 1, "name": "История Алексея"},
        headers={"X-Remote-User": "alexey"},
    )
    assert renamed.status_code == 200, renamed.text
    revision = renamed.json()["revision"]

    described = client.patch(
        f"/api/projects/{project_id}",
        json={"revision": revision, "scriptDescription": "контекст"},
        headers=_basic("sonya", "from-env"),
    )
    assert described.status_code == 200, described.text

    # Заголовок nginx важнее Basic, если пришли оба.
    both = client.patch(
        f"/api/projects/{project_id}",
        json={"revision": described.json()["revision"], "name": "Снова Леша"},
        headers={**_basic("sonya"), "X-Remote-User": "alexey"},
    )
    assert both.status_code == 200, both.text

    history = client.get(f"/api/projects/{project_id}/history")
    authors = [event["author"] for event in history.json()["events"]]
    assert authors == ["unknown", "alexey", "sonya", "alexey"]
    assert history.json()["events"][1]["type"] == "project.rename"
    assert history.json()["events"][1]["before"] == {"name": "История"}
    assert history.json()["events"][1]["after"] == {"name": "История Алексея"}

    hidden = client.get(f"/api/projects/{project_id}/history?exclude_author=sonya")
    assert [event["author"] for event in hidden.json()["events"]] == ["unknown", "alexey", "alexey"]
    assert all(event["author"].lower() != "sonya" for event in hidden.json()["events"])

    only_sonya = client.get(f"/api/projects/{project_id}/history?author=Sonya")
    assert [event["author"] for event in only_sonya.json()["events"]] == ["sonya"]

    sonya_event = next(event for event in history.json()["events"] if event["author"] == "sonya")
    after_visit = client.get(
        f"/api/projects/{project_id}/history",
        params={"exclude_author": "sonya", "since": sonya_event["id"]},
    )
    assert after_visit.status_code == 200, after_visit.text
    assert [event["author"] for event in after_visit.json()["events"]] == ["alexey"]
    assert after_visit.json()["events"][0]["after"] == {"name": "Снова Леша"}

    by_time = client.get(
        f"/api/projects/{project_id}/history",
        params={"since": "2000-01-01T00:00:00Z", "author": "alexey"},
    )
    assert len(by_time.json()["events"]) == 2


def test_full_replace_endpoint_still_works_and_checks_revision(client: TestClient):
    created = client.post(
        "/api/projects",
        json={
            "name": "Полная запись",
            "scriptDescription": "до",
            "nodes": [_card("node-a", "client", "A", "старый")],
            "edges": [],
            "comments": [{"id": "comment-1", "x": 0, "y": 0, "text": "был"}],
        },
        headers={"X-Remote-User": "alexey"},
    )
    project_id = created.json()["id"]
    current = client.get(f"/api/projects/{project_id}").json()

    stale = client.put(
        f"/api/projects/{project_id}",
        json={
            "name": "затирание",
            "scriptDescription": "потеря",
            "revision": current["revision"] - 1,
            "nodes": [],
            "edges": [],
            "comments": [],
        },
        headers={"X-Remote-User": "sonya"},
    )
    assert stale.status_code == 409
    untouched = client.get(f"/api/projects/{project_id}").json()
    assert untouched["name"] == "Полная запись"
    assert untouched["nodes"][0]["data"]["text"] == "старый"
    assert untouched["comments"][0]["text"] == "был"

    replaced = client.put(
        f"/api/projects/{project_id}",
        json={
            "name": "Полная запись",
            "scriptDescription": "после",
            "revision": untouched["revision"],
            "nodes": [
                {**_card("node-a", "client", "A", "новый"), "revision": untouched["nodes"][0]["revision"]},
                _card("node-c", "our_response", "C", "добавлен", 0, 200),
            ],
            "edges": [{"id": "e-node-a-node-c", "source": "node-a", "target": "node-c"}],
            "comments": [{"id": "comment-1", "x": 0, "y": 0, "text": "стал"}],
        },
        headers={"X-Remote-User": "alexey"},
    )
    assert replaced.status_code == 200, replaced.text
    assert replaced.json()["success"] is True
    assert replaced.json()["revision"] == untouched["revision"] + 1
    body = replaced.json()["project"]
    assert body["scriptDescription"] == "после"
    texts = {node["id"]: node["data"]["text"] for node in body["nodes"]}
    assert texts == {"node-a": "новый", "node-c": "добавлен"}
    assert body["edges"][0]["target"] == "node-c"
    assert body["comments"][0]["text"] == "стал"

    # Совместимость: PUT нового id создаёт проект, как раньше.
    created_by_put = client.put(
        "/api/projects/project-manual",
        json={
            "name": "Создан PUT",
            "scriptDescription": "",
            "nodes": [_card("node-z", "client", "Z", "текст")],
            "edges": [],
            "comments": [],
        },
        headers={"X-Remote-User": "sonya"},
    )
    assert created_by_put.status_code == 200, created_by_put.text
    assert created_by_put.json()["success"] is True
    loaded = client.get("/api/projects/project-manual")
    assert loaded.status_code == 200
    assert loaded.json()["name"] == "Создан PUT"
    assert loaded.json()["nodes"][0]["id"] == "node-z"

    removed = client.delete(
        f"/api/projects/{project_id}",
        params={"revision": replaced.json()["revision"]},
        headers={"X-Remote-User": "alexey"},
    )
    assert removed.status_code == 200, removed.text
    assert client.get(f"/api/projects/{project_id}").status_code == 404
    listed = {item["id"] for item in client.get("/api/projects").json()}
    assert project_id not in listed
    archived = client.get("/api/projects", params={"include_archived": True}).json()
    assert any(item["id"] == project_id and item["archived"] for item in archived)


def test_cards_edges_comments_and_removed_ai_routes(client: TestClient):
    created = client.post(
        "/api/projects",
        json={"name": "Гранулярно", "scriptDescription": "для Сони"},
        headers={"X-Remote-User": "sonya"},
    )
    project_id = created.json()["id"]
    revision = created.json()["revision"]

    card = client.post(
        f"/api/projects/{project_id}/cards",
        json={
            "projectRevision": revision,
            "id": "node-q",
            "type": "client",
            "position": {"x": 0, "y": 0},
            "data": {"title": "Цена", "text": "Сколько стоит потолок?"},
        },
        headers={"X-Remote-User": "sonya"},
    )
    assert card.status_code == 200, card.text
    revision = card.json()["projectRevision"]
    answer = client.post(
        f"/api/projects/{project_id}/cards",
        json={
            "projectRevision": revision,
            "id": "node-a",
            "type": "our_response",
            "position": {"x": 0, "y": 180},
            "data": {"title": "Ответ", "text": "Зависит от площади"},
        },
        headers={"X-Remote-User": "sonya"},
    )
    assert answer.status_code == 200, answer.text
    revision = answer.json()["projectRevision"]
    edge = client.post(
        f"/api/projects/{project_id}/edges",
        json={"projectRevision": revision, "source": "node-q", "target": "node-a"},
        headers={"X-Remote-User": "sonya"},
    )
    assert edge.status_code == 200, edge.text
    assert edge.json()["edge"]["id"] == "e-node-q-node-a"
    revision = edge.json()["projectRevision"]
    comment = client.post(
        f"/api/projects/{project_id}/comments",
        json={"projectRevision": revision, "x": 12, "y": 24, "text": "развилка"},
        headers={"X-Remote-User": "sonya"},
    )
    assert comment.status_code == 200, comment.text
    revision = comment.json()["projectRevision"]
    comment_id = comment.json()["comment"]["id"]
    edited = client.patch(
        f"/api/projects/{project_id}/comments/{comment_id}",
        json={"projectRevision": revision, "text": "развилка по цене"},
        headers={"X-Remote-User": "alexey"},
    )
    assert edited.status_code == 200, edited.text

    for path, method in (
        ("/api/generate", "post"),
        ("/api/improve-text", "post"),
        ("/api/check-grs", "get"),
        ("/api/models", "get"),
    ):
        response = client.request(method, path, json={} if method == "post" else None)
        assert response.status_code == 404
