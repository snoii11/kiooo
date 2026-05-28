import discord
from discord.ext import commands 
from discord import app_commands

class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Configure server settings")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        type="What to configure",
        category="Which log category",
        channel="Taregt channel (required unless category is All)"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="Log", value="log"),
        app_commands.Choice(name="Ticket", value="ticket"),
        app_commands.Choice(name="Customrole", value="customrole"),
    ])
    @app_commands.choices(category=[
        app_commands.Choice(name="All (auto-create channels)", value="all"),
        app_commands.Choice(name="Message", value="message"),
        app_commands.Choice(name="Member", value="member"),
        app_commands.Choice(name="Moderation", value="moderation"),
        app_commands.Choice(name="Voice", value="voice"),
        app_commands.Choice(name="Channel", value="channel"),
        app_commands.Choice(name="Role", value="role"),
        app_commands.Choice(name="Command", value="command"),
        app_commands.Choice(name="Error", value="error"),
    ])
    async def setup(self, interaction: discord.Interaction, type: str, category: str, channel: discord.TextChannel = None):
        pass
def setup(bot):
    bot.add_cog(Logger(bot))