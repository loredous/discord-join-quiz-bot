import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

import state_store
from quiz import Quiz, QuizeeList


def test_quizeelist_save_and_load_round_trip(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    quizees = QuizeeList()
    now = datetime.datetime.now(datetime.timezone.utc)
    quizees.quizees = {111: {222: {"count": 3, "last_quiz": now}}}

    quizees.save(str(state_path))

    reloaded = QuizeeList()
    reloaded.load(str(state_path))
    assert reloaded.quizees == {111: {222: {"count": 3, "last_quiz": now}}}


def test_quiz_loads_existing_state_on_init(quiz_config_file: Path, tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    now = datetime.datetime.now(datetime.timezone.utc)
    state_store.save_state({111: {222: {"count": 5, "last_quiz": now}}}, str(state_path))

    quiz = Quiz(str(quiz_config_file), MagicMock(), state_path=str(state_path))

    assert quiz.quizees.quizees == {111: {222: {"count": 5, "last_quiz": now}}}


def test_quiz_without_state_path_starts_empty(quiz_config_file: Path) -> None:
    quiz = Quiz(str(quiz_config_file), MagicMock())
    assert quiz.quizees.quizees == {}


def test_quiz_save_state_writes_to_configured_path(quiz_config_file: Path, tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    quiz = Quiz(str(quiz_config_file), MagicMock(), state_path=str(state_path))
    quiz.quizees.quizees = {111: {222: {"count": 1, "last_quiz": datetime.datetime.now(datetime.timezone.utc)}}}

    quiz.save_state()

    assert state_path.is_file()


def test_quiz_save_state_is_noop_without_state_path(quiz_config_file: Path) -> None:
    quiz = Quiz(str(quiz_config_file), MagicMock())
    # Should not raise even though no state_path was configured.
    quiz.save_state()


def test_quiz_save_state_logs_and_swallows_write_errors(quiz_config_file: Path, tmp_path: Path) -> None:
    # A directory can't be written to as if it were a file, forcing save() to raise.
    state_path = tmp_path / "not_writable"
    state_path.mkdir()
    quiz = Quiz(str(quiz_config_file), MagicMock(), state_path=str(state_path))

    quiz.save_state()  # Should not raise.


@pytest.mark.asyncio
async def test_requiz_member_removes_success_banish_and_moderator_roles(quiz_config_file: Path) -> None:
    quiz = Quiz(str(quiz_config_file), MagicMock())
    quiz._run_quiz = AsyncMock()

    success_role = MagicMock(name="success_role")
    banish_role = MagicMock(name="banish_role")
    moderator_role = MagicMock(name="moderator_role")

    def get_role(role_id: int):
        return {10: success_role, 20: banish_role, 30: moderator_role}[role_id]

    guild = MagicMock()
    guild.id = 111
    guild.get_role.side_effect = get_role

    member = MagicMock()
    member.id = 222
    member.remove_roles = AsyncMock()

    await quiz.requiz_member(member, guild)

    member.remove_roles.assert_awaited_once_with(success_role, banish_role, moderator_role)
    quiz._run_quiz.assert_awaited_once()


@pytest.mark.asyncio
async def test_requiz_member_skips_duplicate_role_when_moderator_role_matches_banish_role(
    quiz_config_file: Path,
) -> None:
    quiz = Quiz(str(quiz_config_file), MagicMock())
    quiz.config.quizzes[0].moderator_banish_role_id = quiz.config.quizzes[0].banish_role_id
    quiz._run_quiz = AsyncMock()

    success_role = MagicMock(name="success_role")
    banish_role = MagicMock(name="banish_role")

    guild = MagicMock()
    guild.id = 111
    guild.get_role.side_effect = lambda role_id: {10: success_role, 20: banish_role}[role_id]

    member = MagicMock()
    member.id = 222
    member.remove_roles = AsyncMock()

    await quiz.requiz_member(member, guild)

    member.remove_roles.assert_awaited_once_with(success_role, banish_role)
