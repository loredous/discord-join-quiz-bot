
import os
import discord
import logging
import static_data



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('HnCJoinBot')


embed0 = discord.embeds.Embed()
embed0.description = "Testing"



class JoinBot(discord.Client):

    async def on_member_join(self, member: discord.Member):
        Guild = member.guild
        Member = member
        await self.do_quiz(Guild, Member)

    async def do_quiz(self, guild: discord.Guild, member: discord.Member):
        channel = discord.utils.get(guild.channels, id=static_data.RULES_CHANNEL_ID)
        thread = await channel.create_thread(name=f'Join Quiz for {member.name}', auto_archive_duration=60)
        await thread.send(f'Hello <@{member.id}>!')
        await static_data.send_welcome_message(thread)
        


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

client = JoinBot(intents=intents)
logger.info("Setting up Discord client.")

if __name__ == "__main__":
    token = os.getenv('BOT_TOKEN', None)
    if token:
        logger.info(f'Starting Discord client with token {token[:5]}-***-{token[-5:]}')
        client.run(token)
    else:
        logger.error('Environment variable "BOT_TOKEN" is required before starting the bot.')
