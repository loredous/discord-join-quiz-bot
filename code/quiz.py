import asyncio
import logging
import re
from typing import List

import discord
from quiz_config import QuizConfig, Question, Answer, Action, QuizList
from pathlib import Path
from discord import Forbidden, HTTPException, Member, User, Interaction, Guild
from pyformance import MetricsRegistry
import yaml
import random
import datetime

_METRIC_ORDER = [
    "Quiz Runs",
    "Quiz Successes",
    "Quiz Failures",
    "Timeouts",
    "Correct Answers",
    "Wrong Answers",
    "Actions Taken",
    "Kicks",
    "Bans",
    "Banishes",
]

_QUESTION_METRIC_RE = re.compile(r'^Question (\d+) (Correct|Wrong) Answers$')

def _metric_sort_key(name: str):
    if name in _METRIC_ORDER:
        return (0, _METRIC_ORDER.index(name), name)
    match = _QUESTION_METRIC_RE.match(name)
    if match:
        question_number = int(match.group(1))
        answer_rank = 0 if match.group(2) == "Correct" else 1
        return (1, question_number, answer_rank, name)
    return (2, 0, 0, name)

class QuizLogger():
    channel = None

    def __init__(self, config: QuizConfig, guild: Guild) -> None:
        self.restart_timestamp = datetime.datetime.now(datetime.timezone.utc)
        if config.log_channel_id:
            self.channel = guild.get_channel(config.log_channel_id)

    async def send_audit(self, message):
        if self.channel:
            embed = discord.Embed(title="QuizBot Audit")
            embed.add_field(name="Action", value=message)
            await self.channel.send(embed=embed)

    async def send_metrics(self, metrics: dict):
        if self.channel:
            embed = discord.Embed(title="QuizBot Metrics")
            embed.description = f"Quizbot metrics since last restart"
            if not metrics:
                embed.add_field(name='No Metrics Found', value='No metrics recorded since last restart', inline=True)
            else:
                for key in sorted(metrics, key=_metric_sort_key):
                    embed.add_field(name=key, value=metrics[key]['count'], inline=True)
            await self.channel.send(embed=embed)

class Quiz():
    def __init__(self, quiz_config_path: str, metrics_registry: MetricsRegistry) -> None:
        self._metrics = metrics_registry
        self.logger = logging.getLogger('Quizzer')
        config_path = Path(quiz_config_path)
        if not config_path.is_file():
            self.logger.fatal(f'quiz_config_path value {quiz_config_path} is not a file!')
            raise RuntimeError(f'quiz_config_path value {quiz_config_path} is not a file!')
        self.__load_quiz_configuration(quiz_config_path)
        self.quizees = QuizeeList()
        self.active_quizzes = {}
        
    def __load_quiz_configuration(self, config_file_path):
        self.logger.info(f'Attempting to load quiz configuration from file [{config_file_path}]')
        try:
            with open(config_file_path, 'r') as config_file:
                config_dict = yaml.load(config_file, yaml.Loader)
            self.config = QuizList.parse_obj(config_dict)
        except Exception as ex:
            self.logger.exception(f'Exception when attempting to load quiz configuration!')
            raise ex
        
    async def cancel_active_quiz(self, guild_id: int, member_id: int):
        existing = self.active_quizzes.get((guild_id, member_id))
        if existing:
            self.logger.info(f'Cancelling existing in-progress quiz for user {existing.member.name} (ID: {member_id}) in guild {guild_id}.')
            await existing.cancel()

    async def _run_quiz(self, quiz: QuizConfig, attempt: int, guild: Guild, member: Member):
        await self.cancel_active_quiz(guild.id, member.id)
        runner = QuizRunner(
            quizconfig=quiz, attempt=attempt, guild=guild, member=member,
            metrics_registry=self._metrics, registry=self.active_quizzes, registry_key=(guild.id, member.id)
        )
        self.active_quizzes[(guild.id, member.id)] = runner
        await runner.run()

    async def start_quiz(self, member: Member, guild: Guild):
        self.logger.info(f'Starting quiz for user {member.name} (ID: {member.id}) in {guild.name}')
        quiz = self.config.get_quiz_by_guild(guild.id)
        quizee = self.quizees.get_quizee(guild.id, member)
        if not quiz:
            self.logger.warning(f'No matching quiz found for for guild {guild.name}')
            return
        await self._run_quiz(quiz, quizee['count'], guild, member)

    async def requiz_member(self, member: Member, guild: Guild):
        self.logger.info(f'Redoing quiz for user {member.name} (ID: {member.id}) in {guild.name}')
        quiz = self.config.get_quiz_by_guild(guild.id)
        quizee = self.quizees.get_quizee(guild.id, member)
        if not quiz:
            self.logger.warning(f'No matching quiz found for for guild {guild.name}')
            return
        roles = []
        roles.append(guild.get_role(quiz.success_role_id))
        if quiz.banish_role_id:
            roles.append(guild.get_role(quiz.banish_role_id))
        try:
            await member.remove_roles(*roles)
        except Forbidden as ex:
            self.logger.error(f'Insufficient permissions to remove roles from user {member.name} (ID: {member.id}) during requiz: {ex}')
        except HTTPException as ex:
            self.logger.error(f'Error removing roles from user {member.name} (ID: {member.id}) during requiz: {ex}')

        await self._run_quiz(quiz, quizee['count'], guild, member)


class QuizRunner():
    def __init__(self, quizconfig: QuizConfig, attempt: int, guild: Guild, member: Member, metrics_registry: MetricsRegistry, registry: dict = None, registry_key=None) -> None:
        self._metrics = metrics_registry
        self.config = quizconfig
        self.guild = guild
        self.member = member
        self.attempt_count = attempt
        self.current_view = None
        self.quiz_channel = None
        self.registry = registry
        self.registry_key = registry_key
        self.cancelled = False

    def _unregister(self):
        if self.registry is not None and self.registry.get(self.registry_key) is self:
            del self.registry[self.registry_key]

    async def cancel(self):
        self.cancelled = True
        if self.current_view:
            self.current_view.stop()
        if self.quiz_channel:
            try:
                await self.quiz_channel.delete()
            except (Forbidden, HTTPException):
                pass
        self._unregister()

    async def run(self):
        self._metrics.counter("Quiz Runs").inc()
        self.failed = False
        self.base_channel = self.guild.get_channel(self.config.quiz_base_channel_id)
        self.quiz_channel = await self.base_channel.create_thread(name=f'Quiz for {self.member.name}', auto_archive_duration=60)
        self.audit = QuizLogger(self.config, self.guild)
        await self.audit.send_audit(f'Starting quiz for user {self.member.name} (ID: {self.member.id}).')
        await self._send_welcome_message()
        await self.quiz_channel.edit(invitable=False)
        self.questions = self.config.questions.copy()
        self.questions.sort(key=lambda a: a.order) # Sort questions by order value
        await self._send_next_question()


    async def _send_welcome_message(self):
        await self.quiz_channel.send(f"Welcome to the rules quiz, {self.member.mention}! There are {len(self.config.questions)} questions to answer. Please read each question carefully and select the correct answer. You can only get {self.config.questions[0].fail_count} questions wrong before failing the quiz. This is attempt number {self.attempt_count} for you. The punishment for failing this attempt is {self.config.fail_actions[self.attempt_count-1].name if self.attempt_count < len(self.config.fail_actions) else self.config.fail_actions[-1].name}.")
        await self.quiz_channel.send(self.config.welcome_text.format(mention = self.member.mention))

    async def _send_next_question(self):
        self.incorrect_answers = 0
        if len(self.questions) == 0:
            await self._complete_successful()
            return
        self.current_question = self.questions.pop(0)
        self.current_view = self._view_builder(self.current_question.answers, self.current_question.timeout, self.current_question.randomize_answers)
        await self.quiz_channel.send(content=self.current_question.text, view=self.current_view)

    def _view_builder(self, answers: List[Answer], timeout: int, randomize: bool):
        view = discord.ui.View(timeout=timeout)
        view.disable_on_timeout = True
        view.on_timeout = self._timeout_callback
        if randomize:
            random.shuffle(answers)
        for answer in answers:
            button = discord.ui.Button()
            button.quiz_answer = answer
            button.style = discord.ButtonStyle.primary
            button.label = answer.text
            button.custom_id = answer.id
            button.quiz_runner = self
            if answer.correct:
                button.callback = self. _correct_answer_callback
            else:
                button.callback = self._wrong_answer_callback
            view.add_item(button)
        return view
            
    async def _complete_successful(self):
        try:
            self._metrics.counter("Quiz Successes").inc()
            await self.quiz_channel.send(self.config.success_text)
            await self.audit.send_audit(f"User {self.member.name} (ID: {self.member.id}) completed the rules quiz successfully.")
            role = self.guild.get_role(self.config.success_role_id)
            await self.member.add_roles(role)
        finally:
            self._unregister()
            await asyncio.sleep(10)
            if not self.cancelled:
                await self.quiz_channel.delete()

    async def _do_action(self, action: Action):
        match action:
            case Action.KICK:
                self._metrics.counter(f"Kicks").inc()
                self._metrics.counter(f"Actions Taken").inc()
                await self.guild.kick(self.member)
            case Action.BAN:
                self._metrics.counter(f"Bans").inc()
                self._metrics.counter(f"Actions Taken").inc()
                await self.guild.ban(self.member)
            case Action.BANISH:
                self._metrics.counter(f"Banishes").inc()
                self._metrics.counter(f"Actions Taken").inc()
                role = self.guild.get_role(self.config.banish_role_id)
                if not role:
                    return
                roles_to_remove = [r for r in self.member.roles if r != self.guild.default_role and r.id != self.config.banish_role_id]
                if roles_to_remove:
                    await self.member.remove_roles(*roles_to_remove)
                await self.member.add_roles(role)
            case Action.NOTHING:
                pass

    async def _complete_fail(self):
        try:
            self._metrics.counter("Quiz Failures").inc()
            if self.config.fail_text:
                await self.quiz_channel.send(content=self.config.fail_text)
            else:
                await self.quiz_channel.send("Sorry, it looks like you failed the quiz.")
            await self.audit.send_audit(f"User {self.member.name} (ID: {self.member.id}) failed the rules quiz: {self.current_question.fail_audit}. Taking action [{self.config.fail_actions[self.attempt_count-1].name if self.attempt_count < len(self.config.fail_actions) else self.config.fail_actions[-1].name}]")
            await asyncio.sleep(10)
            if self.cancelled:
                return
            if self.attempt_count < len(self.config.fail_actions):
                await self._do_action(self.config.fail_actions[self.attempt_count-1])
            else:
                await self._do_action(self.config.fail_actions[-1])
        finally:
            self._unregister()
            if not self.cancelled:
                await self.quiz_channel.delete()

    async def _timeout_callback(self):
        try:
            self._metrics.counter(f"Timeouts").inc()
            await self.quiz_channel.send(self.current_question.timeout_text)
            await self.audit.send_audit(f"User {self.member.name} (ID: {self.member.id}) failed the rules quiz: {self.current_question.timeout_audit}. Taking action [{self.config.timeout_action.name}]")
            await asyncio.sleep(10)
            if self.cancelled:
                return
            await self._do_action(self.config.timeout_action)
        finally:
            self._unregister()
            if not self.cancelled:
                await self.quiz_channel.delete()

    async def _correct_answer_callback(self, interaction: discord.Interaction):
        self._metrics.counter("Correct Answers").inc()
        self._metrics.counter(f"Question {self.current_question.order} Correct Answers").inc()
        answer = self.current_question.get_answer_by_id(interaction.custom_id)
        self.current_view.disable_all_items()
        self.current_view.stop()
        if answer.post_text:
            await interaction.response.send_message(answer.post_text)
        else:
            await interaction.response.send_message("That is correct!")
        await self._send_next_question()

    async def _wrong_answer_callback(self, interaction: discord.Interaction):
        self._metrics.counter("Wrong Answers").inc()
        self._metrics.counter(f"Question {self.current_question.order} Wrong Answers").inc()
        answer = self.current_question.get_answer_by_id(interaction.custom_id)
        if answer.post_text:
            await interaction.response.send_message(answer.post_text)
        else:
            await interaction.response.send_message("That is incorrect")
        self.incorrect_answers += 1
        if self.incorrect_answers >= self.current_question.fail_count:
            self.current_view.stop()
            self.current_view.disable_all_items()
            await self._complete_fail()

class QuizeeList():
    def __init__(self) -> None:
        self.quizees = {}
    
    def get_quizee(self, guild_id: int, member: Member) -> dict:
        if guild_id not in self.quizees:
            self.quizees[guild_id] = {}
        if member not in self.quizees[guild_id].keys():
            self.quizees[guild_id][member.id] = {
                'count': 1,
                'last_quiz': datetime.datetime.now(datetime.timezone.utc)
            }
        else:
            self.quizees[guild_id][member.id]['count'] += 1
            self.quizees[guild_id][member.id]['last_quiz'] = datetime.datetime.now(datetime.timezone.utc)
        return self.quizees[guild_id][member.id]

    def purge(self, guild_id: int):
        if guild_id in self.quizees:
            for member in list(self.quizees[guild_id].keys()):
                if (datetime.datetime.now(datetime.timezone.utc) - self.quizees[guild_id][member]['last_quiz']).total_seconds() > 86400:
                    del self.quizees[guild_id][member]