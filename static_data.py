import asyncio
import discord
import time

RULES_CHANNEL_ID = 1073303464655978528
MEMBER_ROLE_ID = 1073303463842295967

### DO YOU AGREE TO THE RULES?

class ReadRulesView(discord.ui.View):
    async def on_timeout(self) -> None:
        await self.message.channel.send("It looks like you took more than 5 minutes to read the rules. Feel free to come back another time when you have time to read the rules!")
        await asyncio.sleep(10)
        self.stop()
        for member in self.message.channel.members:
            if member != self.message.author:
                self.message.guild.kick(member, reason="Took too long to read the rules!")
        if self.message.channel.type == discord.ChannelType.private_thread:
            await self.message.channel.delete()

    @discord.ui.button(label="I agree to the rules", style=discord.ButtonStyle.primary)
    async def success_callback(self, button, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.response.send_message("Great, let's move on!")
        self.stop()
        await send_account_hacking_question(interaction.message.channel)

    
    @discord.ui.button(label="I don't like the rules", style=discord.ButtonStyle.primary)
    async def failure_callback(self, button, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.response.send_message("That is unfortunate. If you decide later that you can deal with the rules, please come back.")
        await asyncio.sleep(10)
        await interaction.guild.kick(interaction.user, reason="Disagreed with the rules.")
        self.stop()
        if interaction.channel.type == discord.ChannelType.private_thread:
            await interaction.channel.delete()

async def send_welcome_message(thread: discord.Thread):
    await thread.send(f"""Welcome to the Hacking and Coding Discord server!
To ensure that new members have a chance to read and understand the rules of the server, we would like to give you a minute to read the rules in the <#{RULES_CHANNEL_ID}> channel.
Once you are done reading the rules, come back to this thread and let me know, and we can proceed.
 """
, view=ReadRulesView(timeout=300))
    

### WHEN IS ACCOUNT HACKING JUSTIFIED?

class AccountHackingAnswers(discord.ui.View):
    failures = 0

    async def on_timeout(self) -> None:
        await self.message.channel.send("It looks like you took more than 5 minutes to answer the question. Feel free to come back another time when you have time to read the rules!")
        await asyncio.sleep(10)
        for member in self.message.channel.members:
            if member != self.message.author:
                self.message.guild.kick(member, reason="Took too long to answer a rules question")
        self.stop()
        if self.message.channel.type == discord.ChannelType.private_thread:
            await self.message.channel.delete()

    @discord.ui.button(label="When it's my account", style=discord.ButtonStyle.primary)
    async def my_account(self, button: discord.Button, interaction: discord.Interaction):
        button.disabled = True
        self.failures += 1
        await interaction.response.send_message("That's incorrect. If you have an account on a service, and the account has been hacked or hijacked, your only option is to work with the support team of that service. Trying to hack an account on a service, even if you own the account, is still considered an attack on the service itself!")
        await self.check_failures(interaction)

    @discord.ui.button(label="When it belongs to a bad person", style=discord.ButtonStyle.primary)
    async def bad_person(self, button: discord.Button, interaction: discord.Interaction):
        button.disabled = True
        self.failures += 1
        await interaction.response.send_message("That's incorrect. Two wrongs don't make a right. Trying to hack an account on a service is considered an attack on the service itself, regardless of the person who owns the account!")
        await self.check_failures(interaction)

    @discord.ui.button(label="Never", style=discord.ButtonStyle.primary)
    async def correct(self, button: discord.Button, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.response.send_message("Correct!")
        self.stop()
        await send_where_should_i_post_question(interaction.channel)

    @discord.ui.button(label="When I'm hacking it back for someone", style=discord.ButtonStyle.primary)
    async def hack_back(self, button: discord.Button, interaction: discord.Interaction):
        button.disabled = True
        self.failures += 1
        await interaction.response.send_message("That's incorrect. If you have an account on a service, and the account has been hacked or hijacked, your only option is to work with the support team of that service. Trying to hack an account on a service, even if you own the account, is still considered an attack on the service itself!")
        await self.check_failures(interaction)

    async def check_failures(self, interaction):
        if self.failures == 2:
            self.disable_all_items()
            await interaction.response.send_message("It looks like you didn't really read the rules. If you decide later that you want to read the rules, come on back!")
            await asyncio.sleep(10)
            await interaction.guild.kick(interaction.user, reason="Didn't read the rules (Failed question 1)")
            self.stop()
            if interaction.channel.type == discord.ChannelType.private_thread:
                await interaction.channel.delete()

async def send_account_hacking_question(thread: discord.Thread):
    await thread.send("""Let's check that you actually read and understood the rules:
     
When are you allowed to ask about account hacking in the server?""", view=AccountHackingAnswers(timeout=300))
    

### WHERE SHOULD I POST MY QUESTIONS?

class SendQuestionAnswers(discord.ui.View):
    failures = 0

    @discord.ui.button(label="In the channel that most closely matches the topic", style=discord.ButtonStyle.primary)
    async def correct(self, button: discord.Button, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.response.send_message("Correct!")
        self.stop()
        if interaction.channel.type == discord.ChannelType.private_thread:
            await interaction.channel.delete()
        try:
            await interaction.user.add_roles(interaction.guild.get_role(MEMBER_ROLE_ID), reason="Passed the rules quiz")
        except Exception:
            print("Fuck")
            

    @discord.ui.button(label="In as many channels as possible so it can get seen", style=discord.ButtonStyle.primary)
    async def many_channels(self, button: discord.Button, interaction: discord.Interaction):
        button.disabled = True
        self.failures += 1
        await interaction.response.send_message("That's incorrect. Please limit posts to a single channel. Posting in multiple channels just makes for chaos when multiple people start answering in multiple places.")
        await self.check_failures(interaction)

    @discord.ui.button(label="In whatever channel I am in", style=discord.ButtonStyle.primary)
    async def where_i_am(self, button: discord.Button, interaction: discord.Interaction):
        button.disabled = True
        self.failures += 1
        await interaction.response.send_message("That's incorrect. Please try to post questions in the most appropriate channel. Some people only monitor the channels that they have knowledege in, and questions they might be able to answer could be missed if they are in the wrong channel.")
        await self.check_failures(interaction)

    @discord.ui.button(label="In a DM to someone who seems like they might know the answer", style=discord.ButtonStyle.primary)
    async def in_a_dm(self, button: discord.Button, interaction: discord.Interaction):
        button.disabled = True
        self.failures += 1
        await interaction.response.send_message("That's incorrect. We try to avoid DMs as much as possible in the server, as they make it so others can't learn from questions that have been asked previously.")
        await self.check_failures(interaction)

    async def check_failures(self, interaction):
        if self.failures == 2:
            self.disable_all_items()
            await interaction.response.send_message("It looks like you didn't really read the rules. If you decide later that you want to read the rules, come on back!")
            await asyncio.sleep(10)
            await interaction.guild.kick(interaction.user, reason="Didn't read the rules (Failed question 2)")
            self.stop()
            if interaction.channel.type == discord.ChannelType.private_thread:
                await interaction.channel.delete()

async def send_where_should_i_post_question(thread: discord.Thread):
    await thread.send("""One last question: 

I have a question. Where should I post it?
    """, view=SendQuestionAnswers(timeout=300))

