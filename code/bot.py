
import asyncio
import os
from typing import Any
import discord
import logging
import pyformance
import re
from quiz import Quiz, QuizLogger
from quiz_config import Action

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DiscordJoinQuizBot')

class JoinBot(discord.Bot):
    def __init__(self, *, loop: asyncio.AbstractEventLoop | None = None, **options: Any):
        self._metrics = pyformance.MetricsRegistry()
        super().__init__(loop=loop, **options)

    @property
    def quizconfig(self):
        return self._quizconfig
    
    @quizconfig.setter
    def quizconfig(self, config: Quiz):
        self._quizconfig = config

    async def on_ready(self):
        self.loop.call_later(86400,self.daily_metrics)

    def daily_metrics(self):
        for guild in self.guilds:
            asyncio.create_task(self.send_metrics(guild))
        self.loop.call_later(86400,self.daily_metrics)
        
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        quiz = self.quizconfig.config.get_quiz_by_guild(guild.id)
        if quiz and quiz.name_regex_actions:
            for action_cfg in quiz.name_regex_actions:
                pattern = re.compile(action_cfg.pattern, re.IGNORECASE)
                if pattern.search(member.name) or pattern.search(member.display_name):
                    logger.info(f'User {member.name} matched join regex {action_cfg.pattern}. Action {action_cfg.action.name}')
                    await QuizLogger(quiz, guild).send_audit(
                        f'User {member.name} matched join regex {action_cfg.pattern}. Taking action {action_cfg.action.name}'
                    )
                    if action_cfg.action == Action.KICK:
                        await guild.kick(member)
                    elif action_cfg.action == Action.BAN:
                        await guild.ban(member)
                    return
        await self._quizconfig.start_quiz(member, guild)

    async def send_metrics(self, guild):
        metrics = self._metrics.dump_metrics()
        sender = QuizLogger(self.quizconfig.config.get_quiz_by_guild(guild.id), guild)
        await sender.send_metrics(metrics)

    async def requiz_member(self, guild, member):
        await self._quizconfig.requiz_member(member, guild)
        

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

client = JoinBot(intents=intents)
logger.info("Setting up Discord client.")

@client.slash_command(name="metrics", description="Display the quizbot's metrics in the bot logging channel")
async def send_metrics(ctx):
    await client.send_metrics(ctx.guild)
    await ctx.respond('Metrics sent to logging channel')

@client.slash_command(description="Force a user to go back through the join quiz")
async def requiz(ctx, member: discord.Member):
    await client.requiz_member(ctx.guild, member)
    await ctx.respond(f'Re-quiz started for user {member.display_name}')

if __name__ == "__main__":
    token = os.getenv('BOT_TOKEN', None)
    config = os.getenv('QUIZ_CONFIG', "/quiz_config.yaml")
    if token:
        logger.info(f'Loading quiz configuration from [{config}]')
        quiz = Quiz(config, client._metrics)
        client.quizconfig = quiz
        logger.info(f'Starting Discord client with token {token[:5]}-***-{token[-5:]}')
        client.run(token)
    else:
        logger.error('Environment variable "BOT_TOKEN" is required before starting the bot.')