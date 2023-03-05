
import os
import discord
import logging
from quiz import Quiz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DiscordJoinQuizBot')

class JoinBot(discord.Client):

    @property
    def quizconfig(self):
        return self._quizconfig
    
    @quizconfig.setter
    def quizconfig(self, config: Quiz):
        self._quizconfig = config
        
    async def on_member_join(self, member: discord.Member):
        Guild = member.guild
        Member = member
        await self._quizconfig.start_quiz(Member, Guild)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

client = JoinBot(intents=intents)
logger.info("Setting up Discord client.")

if __name__ == "__main__":
    token = os.getenv('BOT_TOKEN', None)
    config = os.getenv('QUIZ_CONFIG', "/quiz_config.yaml")
    if token:
        logger.info(f'Loading quiz configuration from [{config}]')
        quiz = Quiz(config)
        client.quizconfig = quiz
        logger.info(f'Starting Discord client with token {token[:5]}-***-{token[-5:]}')
        client.run(token)
    else:
        logger.error('Environment variable "BOT_TOKEN" is required before starting the bot.')
