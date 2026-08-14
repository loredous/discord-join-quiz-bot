from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import bot


def _quiz(banish_role_id=20, moderator_banish_role_id=None):
    return SimpleNamespace(
        banish_role_id=banish_role_id,
        moderator_banish_role_id=moderator_banish_role_id,
        log_channel_id=None,
    )


def _set_quizconfig(monkeypatch, quiz):
    fake_quizconfig = SimpleNamespace(config=SimpleNamespace(get_quiz_by_guild=lambda guild_id: quiz))
    # bot.client.quizconfig is a property backed by _quizconfig; patch the
    # backing attribute directly so monkeypatch can cleanly restore it.
    monkeypatch.setattr(bot.client, "_quizconfig", fake_quizconfig, raising=False)
    return fake_quizconfig


def _guild_with_role(role_id, role):
    guild = MagicMock()
    guild.id = 111
    guild.default_role = MagicMock(name="default_role")
    guild.get_role.side_effect = lambda rid: role if rid == role_id else None
    return guild


def _member_with_roles(*roles):
    member = MagicMock()
    member.id = 222
    member.roles = list(roles)
    member.remove_roles = AsyncMock()
    member.add_roles = AsyncMock()
    return member


@pytest.mark.asyncio
async def test_banish_user_uses_fail_banish_role_when_no_moderator(monkeypatch) -> None:
    quiz = _quiz(banish_role_id=20, moderator_banish_role_id=30)
    _set_quizconfig(monkeypatch, quiz)
    role = MagicMock(name="banish_role", id=20)
    guild = _guild_with_role(20, role)
    member = _member_with_roles()

    await bot.banish_user(member, guild)

    member.add_roles.assert_awaited_once_with(role)


@pytest.mark.asyncio
async def test_banish_user_uses_moderator_role_when_set(monkeypatch) -> None:
    quiz = _quiz(banish_role_id=20, moderator_banish_role_id=30)
    _set_quizconfig(monkeypatch, quiz)
    moderator_role = MagicMock(name="moderator_role", id=30)
    guild = _guild_with_role(30, moderator_role)
    member = _member_with_roles()
    moderator = MagicMock(name="moderator")

    await bot.banish_user(member, guild, moderator=moderator)

    member.add_roles.assert_awaited_once_with(moderator_role)


@pytest.mark.asyncio
async def test_banish_user_moderator_falls_back_to_fail_banish_role_when_unset(monkeypatch) -> None:
    quiz = _quiz(banish_role_id=20, moderator_banish_role_id=None)
    _set_quizconfig(monkeypatch, quiz)
    role = MagicMock(name="banish_role", id=20)
    guild = _guild_with_role(20, role)
    member = _member_with_roles()
    moderator = MagicMock(name="moderator")

    await bot.banish_user(member, guild, moderator=moderator)

    member.add_roles.assert_awaited_once_with(role)


@pytest.mark.asyncio
async def test_banish_user_logs_and_returns_when_no_role_configured(monkeypatch) -> None:
    quiz = _quiz(banish_role_id=None, moderator_banish_role_id=None)
    _set_quizconfig(monkeypatch, quiz)
    guild = MagicMock()
    member = _member_with_roles()

    await bot.banish_user(member, guild)

    member.add_roles.assert_not_awaited()


@pytest.mark.asyncio
async def test_banish_command_defers_before_slow_work(monkeypatch) -> None:
    quiz = _quiz(banish_role_id=20, moderator_banish_role_id=None)
    _set_quizconfig(monkeypatch, quiz)
    role = MagicMock(name="banish_role", id=20)
    guild = _guild_with_role(20, role)
    member = _member_with_roles()
    member.display_name = "SomeUser"
    member.send = AsyncMock()

    ctx = MagicMock()
    ctx.guild = guild
    ctx.author = MagicMock(spec=[])
    ctx.respond = AsyncMock()
    ctx.defer = AsyncMock()

    await bot.banish.callback(ctx, member, None)

    ctx.defer.assert_awaited_once()
    member.add_roles.assert_awaited_once_with(role)
    ctx.respond.assert_awaited_once()


@pytest.mark.asyncio
async def test_requiz_refuses_when_member_has_moderator_banish_role(monkeypatch) -> None:
    quiz = _quiz(banish_role_id=20, moderator_banish_role_id=30)
    _set_quizconfig(monkeypatch, quiz)
    requiz_member_mock = AsyncMock()
    monkeypatch.setattr(bot.client, "requiz_member", requiz_member_mock, raising=False)

    moderator_role = MagicMock(id=30)
    ctx = MagicMock()
    ctx.guild = MagicMock(id=111)
    ctx.respond = AsyncMock()
    member = _member_with_roles(moderator_role)
    member.display_name = "BadActor"

    await bot.requiz.callback(ctx, member)

    requiz_member_mock.assert_not_awaited()
    ctx.respond.assert_awaited_once()
    assert "cannot be re-quizzed" in ctx.respond.await_args.args[0]


@pytest.mark.asyncio
async def test_requiz_proceeds_when_member_lacks_moderator_banish_role(monkeypatch) -> None:
    quiz = _quiz(banish_role_id=20, moderator_banish_role_id=30)
    _set_quizconfig(monkeypatch, quiz)
    requiz_member_mock = AsyncMock()
    monkeypatch.setattr(bot.client, "requiz_member", requiz_member_mock, raising=False)

    other_role = MagicMock(id=99)
    ctx = MagicMock()
    ctx.guild = MagicMock(id=111)
    ctx.respond = AsyncMock()
    ctx.defer = AsyncMock()
    member = _member_with_roles(other_role)
    member.display_name = "GoodActor"

    await bot.requiz.callback(ctx, member)

    ctx.defer.assert_awaited_once()
    requiz_member_mock.assert_awaited_once_with(ctx.guild, member)
    ctx.respond.assert_awaited_once()
    assert "Re-quiz started" in ctx.respond.await_args.args[0]


@pytest.mark.asyncio
async def test_requiz_proceeds_when_moderator_banish_role_not_configured(monkeypatch) -> None:
    quiz = _quiz(banish_role_id=20, moderator_banish_role_id=None)
    _set_quizconfig(monkeypatch, quiz)
    requiz_member_mock = AsyncMock()
    monkeypatch.setattr(bot.client, "requiz_member", requiz_member_mock, raising=False)

    ctx = MagicMock()
    ctx.guild = MagicMock(id=111)
    ctx.respond = AsyncMock()
    ctx.defer = AsyncMock()
    member = _member_with_roles()
    member.display_name = "SomeUser"

    await bot.requiz.callback(ctx, member)

    ctx.defer.assert_awaited_once()
    requiz_member_mock.assert_awaited_once_with(ctx.guild, member)
