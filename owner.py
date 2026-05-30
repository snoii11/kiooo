import discord
from discord.ext import commands
from discord import app_commands
import datetime
from colors import COLOR, THUMBNAIL_URL

own = 1491790586166902874


class ConfirmView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.button(label="AUTHORIZED TERMINATION (YES)", style=discord.ButtonStyle.red)
    async def confirm(self, interaction, button):
        e = discord.Embed(
            title="❖ [ SYSTEM SHUTDOWN CONFIRMED ] ❖",
            description="```ini\n[STATUS] Terminal shutdown command authorized.\n[ACTION] Terminating active processes and closing connection.\n```",
            color=COLOR)
        e.set_thumbnail(url=THUMBNAIL_URL)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.response.send_message(embed=e)
        await interaction.client.close()
        self.stop()

    @discord.ui.button(label="ABORT COMMAND (NO)", style=discord.ButtonStyle.green)
    async def cancel(self, interaction, button):
        e = discord.Embed(
            title="❖ [ SHUTDOWN CANCELLED ] ❖",
            description="```ini\n[STATUS] Terminal shutdown aborted.\n[ACTION] Resuming normal operations.\n```",
            color=COLOR)
        e.set_thumbnail(url=THUMBNAIL_URL)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.response.send_message(embed=e)
        self.stop()


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description):
        e = discord.Embed(title=title, description=description, color=COLOR)
        e.set_thumbnail(url=THUMBNAIL_URL)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        return e

    async def send(self, interaction, title, description):
        await interaction.response.send_message(embed=self.embed(title, description))

    @app_commands.command(name="shutdown", description="Shut down the bot (owner only)")
    async def shutdown(self, interaction: discord.Interaction):
        if interaction.user.id != own:
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Unauthorized access attempt detected.\n- LEVEL: Required credentials: Core Owner\n```")

        view = ConfirmView(self.bot)
        e = discord.Embed(
            title="❖ [ SYSTEM SHUTDOWN PROMPT ] ❖",
            description="```yaml\nWARNING: You are about to initiate a terminal shutdown. This will disconnect the bot completely.\n```\n**Are you sure you want to proceed?**",
            color=COLOR)
        e.set_thumbnail(url=THUMBNAIL_URL)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.response.send_message(embed=e, view=view)

    @app_commands.command(name="np", description="Manage the no-prefix user list (owner only)")
    @app_commands.describe(action="add, remove, or list", user_id="User ID (required for add/remove)")
    @app_commands.choices(action=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove"),
        app_commands.Choice(name="list", value="list"),
    ])
    async def np(self, interaction: discord.Interaction, action: str, user_id: str = None):
        if interaction.user.id != own:
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Permission denied.\n- COMMAND: No-Prefix settings modification is restricted to Core Administration.\n```")

        if action == "list":
            mentions = "\n".join(f"✦ <@{uid}> (`{uid}`)" for uid in self.bot.db['np_list']) if self.bot.db['np_list'] else "No users in override list."
            return await self.send(interaction, "📋 [ NO-PREFIX CONFIGURATION LOG ]",
                f"```ini\n[MODULE] Override Caching System\n[STATUS] Online & Active\n```\n**Authorized Override Users:**\n{mentions}")

        if user_id is None:
            return await self.send(interaction, "❌ [ SYNTAX ERROR ]",
                f"```yaml\nCOMMAND: np\nERROR: Missing user_id for '{action}'\nUSAGE: /np action:{action} user_id:123456789\n```")

        try:
            uid = int(user_id)
        except ValueError:
            return await self.send(interaction, "❌ [ INVALID USER ID ]",
                "```yaml\nERROR: User ID must be a numeric value.\n```")

        if action == "add":
            if uid not in self.bot.db["np_list"]:
                self.bot.db["np_list"].append(uid)
                await self.bot.save_data()
            await self.send(interaction, "✅ [ CONFIGURATION UPDATED ]",
                f"```ini\n[STATUS] Modification successful.\n[ACTION] Added user <@{uid}> ({uid}) to No-Prefix list.\n```\n> Tip: You can remove users with `/np action:remove`")

        elif action == "remove":
            if uid in self.bot.db["np_list"]:
                self.bot.db["np_list"].remove(uid)
                await self.bot.save_data()
            await self.send(interaction, "🗑️ [ CONFIGURATION UPDATED ]",
                f"```ini\n[STATUS] Modification successful.\n[ACTION] Removed user <@{uid}> ({uid}) from No-Prefix list.\n```\n> Tip: You can add users with `/np action:add`")

    @app_commands.command(name="reload", description="Reload a cog (owner only)")
    @app_commands.describe(cog="Name of the cog to reload (e.g. moderation, fun, economy, utility, owner)")
    async def reload(self, interaction: discord.Interaction, cog: str):
        if interaction.user.id != own:
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Permission denied.\n- COMMAND: Cog hot-reloading is restricted to Core Developers.\n```")

        try:
            await self.bot.reload_extension(cog)
            await self.send(interaction, "✅ [ SYSTEM HOT-RELOAD SUCCESSFUL ]",
                f"```ini\n[MODULE] {cog}\n[STATUS] Reloaded successfully in active memory.\n```")
        except Exception as e:
            await self.send(interaction, "❌ [ SYSTEM HOT-RELOAD FAILED ]",
                f"```diff\n- MODULE: {cog}\n- STATUS: Fail\n- ERROR: {e}\n```\n> Tip: You can shutdown the bot completely with `/shutdown` if necessary.")

    @app_commands.command(name="status", description="Change the bot's playing status (owner only)")
    @app_commands.describe(message="The status message to display")
    async def status(self, interaction: discord.Interaction, message: str):
        if interaction.user.id != own:
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Permission denied.\n- COMMAND: Presence status override is restricted to Developer account.\n```")

        await self.bot.change_presence(activity=discord.Game(name=message))
        await self.send(interaction, "✅ [ CLIENT STATUS MODIFIED ]",
            f"```ini\n[PARAMETER] Presence Activity\n[VALUE] Playing {message}\n[STATUS] Applied globally.\n```")

    @app_commands.command(name="npa", description="Manage no-prefix admin access (owner only)")
    @app_commands.describe(action="add or remove", user_id="User ID")
    @app_commands.choices(action=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove"),
    ])
    async def npa(self, interaction: discord.Interaction, action: str, user_id: str):
        if interaction.user.id != own:
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Permission denied.\n- COMMAND: This command is restricted to Core Owner.\n```")

        try:
            uid = int(user_id)
        except ValueError:
            return await self.send(interaction, "❌ [ INVALID USER ID ]",
                "```yaml\nERROR: User ID must be a numeric value.\n```")

        if action == "add":
            if uid not in self.bot.db["noprefix_access"]:
                self.bot.db["noprefix_access"].append(uid)
                await self.bot.save_data()
            await self.send(interaction, "✅ [ PRIVILEGES GRANTED ]",
                f"```ini\n[PRIVILEGE] No-Prefix Admin Access\n[GRANTEE] User ID {uid}\n[STATUS] Added successfully.\n```")

        elif action == "remove":
            if uid in self.bot.db["noprefix_access"]:
                self.bot.db["noprefix_access"].remove(uid)
                await self.bot.save_data()
            await self.send(interaction, "🗑️ [ PRIVILEGES REVOKED ]",
                f"```ini\n[PRIVILEGE] No-Prefix Admin Access\n[REVOKEE] User ID {uid}\n[STATUS] Removed successfully.\n```")


async def setup(bot):
    await bot.add_cog(Owner(bot))
