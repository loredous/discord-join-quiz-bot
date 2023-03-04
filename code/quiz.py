import asyncio
import logging
from typing import List

import discord
from quiz_config import QuizConfig, Question, Answer, Action, QuizList
from pathlib import Path
from discord import Member, User, Interaction, Guild
import yaml
import random

class QuizAuditLogger():
    channel = None
    
    def __init__(self, config: QuizConfig, guild: Guild) -> None:
        if config.log_channel_id:
            self.channel = guild.get_channel(config.log_channel_id)

    async def send_audit(self, message):
        if self.channel:
            embed = discord.Embed(title="QuizBot Audit")
            embed.add_field(name="Action", value=message)
            await self.channel.send(embed=embed)

class Quiz():
    def __init__(self, quiz_config_path: str) -> None:
        self.logger = logging.getLogger('Quizzer')
        config_path = Path(quiz_config_path)
        if not config_path.is_file():
            self.logger.fatal(f'quiz_config_path value {quiz_config_path} is not a file!')
            raise RuntimeError(f'quiz_config_path value {quiz_config_path} is not a file!')
        self.__load_quiz_configuration(quiz_config_path)
        
    def __load_quiz_configuration(self, config_file_path):
        self.logger.info(f'Attempting to load quiz configuration from file [{config_file_path}]')
        try:
            with open(config_file_path, 'r') as config_file:
                config_dict = yaml.load(config_file, yaml.Loader)
            self.config = QuizList.parse_obj(config_dict)
        except Exception as ex:
            self.logger.exception(f'Exception when attempting to load quiz configuration!')
            raise ex
        
    async def start_quiz(self, member: Member, guild: Guild):
        self.logger.info(f'Starting quiz for user {member.name} in {guild.name}')
        quiz = self.config.get_quiz_by_guild(guild.id)
        if not quiz:
            self.logger.warn(f'No matching quiz found for for guild {guild.name}')
            return
        await QuizRunner(quizconfig=quiz, guild=guild, member=member).run()


class QuizRunner():
    def __init__(self, quizconfig: QuizConfig, guild: Guild, member: Member) -> None:
        self.config = quizconfig
        self.guild = guild
        self.member = member
        
    async def run(self):
        self.failed = False
        self.base_channel = self.guild.get_channel(self.config.quiz_base_channel_id)
        self.quiz_channel = await self.base_channel.create_thread(name=f'Quiz for {self.member.name}', auto_archive_duration=60)
        self.audit = QuizAuditLogger(self.config, self.guild)
        await self.audit.send_audit(f'Starting quiz for user {self.member.name}.')
        await self._send_welcome_message()
        await self.quiz_channel.edit(invitable=False)
        self.questions = self.config.questions.copy()
        self.questions.sort(key=lambda a: a.order) # Sort questions by order value
        await self._send_next_question()


    async def _send_welcome_message(self):
        await self.quiz_channel.send(self.config.welcome_text.format(mention = self.member.mention))

    async def _send_next_question(self):
        self.incorrect_answers = 0
        if len(self.questions) == 0:
            await self._complete_successful()
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
            await self.quiz_channel.send(self.config.success_text)
            await self.audit.send_audit(f"User {self.member.name} completed the rules quiz successfully.")
            role = self.guild.get_role(self.config.success_role_id)
            await self.member.add_roles(role)
        finally:
            await asyncio.sleep(10)
            await self.quiz_channel.delete()

    async def _do_action(self, action: Action):
        match action:
            case Action.KICK:
                await self.guild.kick(self.member)
            case Action.BAN:
                await self.guild.ban(self.member)
            case Action.NOTHING:
                pass

    async def _complete_fail(self):
        try:
            if self.config.fail_text:
                await self.quiz_channel.send(content=self.config.fail_text)
            else:
                await self.quiz_channel.send("Sorry, it looks like you failed the quiz.")
            await self.audit.send_audit(f"User {self.member.name} failed the rules quiz: {self.current_question.fail_audit}. Taking action [{self.config.fail_action.name}]")
            await asyncio.sleep(10)
            await self._do_action(self.config.fail_action)
        finally:
            await self.quiz_channel.delete()

    async def _timeout_callback(self):
        try:
            await self.quiz_channel.send(self.current_question.timeout_text)
            await self.audit.send_audit(f"User {self.member.name} failed the rules quiz: {self.current_question.timeout_audit}. Taking action [{self.config.timeout_action.name}]")
            await asyncio.sleep(10)
            await self._do_action(self.config.timeout_action)
        finally:
            await self.quiz_channel.delete()

    async def _correct_answer_callback(self, interaction: discord.Interaction):
        answer = self.current_question.get_answer_by_id(interaction.custom_id)
        self.current_view.disable_all_items()
        self.current_view.stop()
        if answer.post_text:
            await interaction.response.send_message(answer.post_text)
        else:
            await interaction.response.send_message("That is correct!")
        await self._send_next_question()

    async def _wrong_answer_callback(self, interaction: discord.Interaction):
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

