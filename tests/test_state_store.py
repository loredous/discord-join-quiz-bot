import datetime
import json
from pathlib import Path

import state_store


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    state_path = tmp_path / "nested" / "state.json"
    now = datetime.datetime.now(datetime.timezone.utc)
    quizees = {111: {222: {"count": 2, "last_quiz": now}}}

    state_store.save_state(quizees, str(state_path))
    loaded = state_store.load_state(str(state_path))

    assert loaded == {111: {222: {"count": 2, "last_quiz": now}}}


def test_save_creates_parent_directories(tmp_path: Path) -> None:
    state_path = tmp_path / "a" / "b" / "c" / "state.json"
    state_store.save_state({}, str(state_path))
    assert state_path.is_file()


def test_save_does_not_leave_temp_file_behind(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state_store.save_state({}, str(state_path))
    remaining = list(tmp_path.iterdir())
    assert remaining == [state_path]


def test_load_missing_file_returns_empty_dict(tmp_path: Path) -> None:
    state_path = tmp_path / "does_not_exist.json"
    assert state_store.load_state(str(state_path)) == {}


def test_load_corrupt_file_returns_empty_dict(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text("not valid json{{{")
    assert state_store.load_state(str(state_path)) == {}


def test_saved_file_uses_string_keys_for_json_compatibility(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    now = datetime.datetime.now(datetime.timezone.utc)
    state_store.save_state({111: {222: {"count": 1, "last_quiz": now}}}, str(state_path))

    with open(state_path) as f:
        raw = json.load(f)

    assert raw["version"] == state_store.STATE_VERSION
    assert raw["quizees"]["111"]["222"]["count"] == 1
    assert raw["quizees"]["111"]["222"]["last_quiz"] == now.isoformat()
