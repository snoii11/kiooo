import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
import io
import textwrap
import traceback
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

    def is_owner(self, interaction):
        return interaction.user.id == own

    def get_collection(self, name):
        mongo_db = getattr(self.bot, "mongo_db", None)
        return mongo_db[name] if mongo_db is not None else None

    # ── Shutdown ──

    @app_commands.command(name="shutdown", description="Shut down the bot (owner only)")
    async def shutdown(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
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

    # ── Eval ──

    @app_commands.command(name="eval", description="Evaluate Python code (owner only)")
    @app_commands.describe(code="Python code to evaluate")
    async def eval_code(self, interaction: discord.Interaction, code: str):
        if not self.is_owner(interaction):
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Permission denied.\n```")
        await interaction.response.defer()
        env = {
            "bot": self.bot,
            "interaction": interaction,
            "channel": interaction.channel,
            "guild": interaction.guild,
            "author": interaction.user,
            "db": self.bot.db,
            "mongo_db": self.bot.mongo_db,
        }
        env.update(globals())
        code = code.strip("`").removeprefix("py\n").removeprefix("python\n")
        try:
            result = eval(code, env)
            if asyncio.iscoroutine(result):
                result = await result
            await interaction.followup.send(embed=self.embed(
                "💻 [ EVAL RESULT ]",
                f"```py\n{result}\n```"))
        except Exception as e:
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            await interaction.followup.send(embed=self.embed(
                "❌ [ EVAL ERROR ]",
                f"```py\n{tb[:1900]}\n```"))

    # ── Execute ──

    @app_commands.command(name="execute", description="Execute a shell command (owner only)")
    @app_commands.describe(command="Shell command to execute")
    async def execute(self, interaction: discord.Interaction, command: str):
        if not self.is_owner(interaction):
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Permission denied.\n```")
        await interaction.response.defer()
        import subprocess
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
            if not output:
                output = "[No output]"
            if len(output) > 1900:
                output = output[:1900] + "\n... (truncated)"
            await interaction.followup.send(embed=self.embed(
                "💻 [ EXEC RESULT ]",
                f"```bash\n{output}\n```"))
        except subprocess.TimeoutExpired:
            await interaction.followup.send(embed=self.embed(
                "❌ [ EXEC TIMEOUT ]",
                "```diff\n- ERROR: Command timed out (30s).\n```"))
        except Exception as e:
            await interaction.followup.send(embed=self.embed(
                "❌ [ EXEC ERROR ]",
                f"```diff\n- ERROR: {e}\n```"))

    # ── Global Ban ──

    @app_commands.command(name="globalban", description="Ban a user from all servers the bot is in (owner only)")
    @app_commands.describe(user_id="User ID to globally ban")
    async def globalban(self, interaction: discord.Interaction, user_id: str):
        if not self.is_owner(interaction):
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Permission denied.\n```")
        await interaction.response.defer()
        try:
            uid = int(user_id)
        except ValueError:
            return await self.send(interaction, "❌ [ INVALID ID ]", "```diff\n- ERROR: User ID must be numeric.\n```")
        try:
            user = await self.bot.fetch_user(uid)
        except:
            return await self.send(interaction, "❌ [ USER NOT FOUND ]", "```diff\n- ERROR: Could not fetch user.\n```")
        count = 0
        for guild in self.bot.guilds:
            try:
                await guild.ban(user, reason="Global ban by owner")
                count += 1
            except:
                pass
        await self.send(interaction,
            "🔨 [ GLOBAL BAN EXECUTED ]",
            f"```yaml\nUSER: {user} ({uid})\nSERVERS BANNED FROM: {count}\nTOTAL SERVERS: {len(self.bot.guilds)}\n```")

    # ── Server List ──

    @app_commands.command(name="serverslist", description="List all servers the bot is in (owner only)")
    async def serverslist(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Permission denied.\n```")
        guilds = sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=True)
        if not guilds:
            return await self.send(interaction, "📭 [ NO SERVERS ]", "```yaml\nSTATUS: Bot is not in any servers.\n```")
        lines = [f"✦ {g.name} — {g.member_count} members ({g.id})" for g in guilds[:20]]
        if len(guilds) > 20:
            lines.append(f"\n... and {len(guilds) - 20} more servers.")
        await self.send(interaction,
            "📋 [ SERVERS LIST ]",
            f"```yaml\nTOTAL: {len(guilds)}\n\n" + "\n".join(lines) + "\n```")

    # ── Leave Server ──

    @app_commands.command(name="leaveserver", description="Make the bot leave a server (owner only)")
    @app_commands.describe(guild_id="ID of the server to leave")
    async def leaveserver(self, interaction: discord.Interaction, guild_id: str):
        if not self.is_owner(interaction):
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Permission denied.\n```")
        try:
            gid = int(guild_id)
        except ValueError:
            return await self.send(interaction, "❌ [ INVALID ID ]", "```diff\n- ERROR: Guild ID must be numeric.\n```")
        guild = self.bot.get_guild(gid)
        if guild is None:
            return await self.send(interaction, "❌ [ GUILD NOT FOUND ]", "```diff\n- ERROR: Bot is not in that server.\n```")
        name = guild.name
        try:
            await guild.leave()
            await self.send(interaction,
                "👋 [ LEFT SERVER ]",
                f"```yaml\nGUILD: {name} ({gid})\nSTATUS: Successfully left.\n```")
        except Exception as e:
            await self.send(interaction, "❌ [ ERROR ]", f"```diff\n- ERROR: {e}\n```")

    # ── Blacklist ──

    blacklist_group = app_commands.Group(name="blacklist", description="Manage bot blacklist (owner only)")

    @blacklist_group.command(name="add", description="Add a user to the blacklist")
    @app_commands.describe(user_id="User ID to blacklist")
    async def blacklist_add(self, interaction: discord.Interaction, user_id: str):
        if not self.is_owner(interaction):
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]", "```diff\n- ERROR: Permission denied.\n```")
        try:
            uid = int(user_id)
        except ValueError:
            return await self.send(interaction, "❌ [ INVALID ID ]", "```diff\n- ERROR: User ID must be numeric.\n```")
        collection = self.get_collection("blacklist")
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "```diff\n- ERROR: MongoDB not configured.\n```")
        existing = await collection.find_one({"user_id": uid})
        if existing:
            return await self.send(interaction, "❌ [ ALREADY BLACKLISTED ]", "```diff\n- ERROR: That user is already blacklisted.\n```")
        await collection.insert_one({"user_id": uid, "blacklisted_by": interaction.user.id, "created_at": datetime.datetime.now(datetime.timezone.utc)})
        await self.send(interaction, "✅ [ BLACKLIST ADDED ]", f"```yaml\nUSER ID: {uid}\nSTATUS: Blacklisted from using the bot.\n```")

    @blacklist_group.command(name="remove", description="Remove a user from the blacklist")
    @app_commands.describe(user_id="User ID to unblacklist")
    async def blacklist_remove(self, interaction: discord.Interaction, user_id: str):
        if not self.is_owner(interaction):
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]", "```diff\n- ERROR: Permission denied.\n```")
        try:
            uid = int(user_id)
        except ValueError:
            return await self.send(interaction, "❌ [ INVALID ID ]", "```diff\n- ERROR: User ID must be numeric.\n```")
        collection = self.get_collection("blacklist")
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "```diff\n- ERROR: MongoDB not configured.\n```")
        result = await collection.delete_one({"user_id": uid})
        if result.deleted_count == 0:
            return await self.send(interaction, "❌ [ NOT BLACKLISTED ]", "```diff\n- ERROR: That user is not blacklisted.\n```")
        await self.send(interaction, "✅ [ BLACKLIST REMOVED ]", f"```yaml\nUSER ID: {uid}\nSTATUS: Removed from blacklist.\n```")

    @blacklist_group.command(name="list", description="List all blacklisted users")
    async def blacklist_list(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]", "```diff\n- ERROR: Permission denied.\n```")
        collection = self.get_collection("blacklist")
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "```diff\n- ERROR: MongoDB not configured.\n```")
        bl = await collection.find().to_list(length=100)
        if not bl:
            return await self.send(interaction, "📭 [ BLACKLIST ]", "```yaml\nSTATUS: No blacklisted users.\n```")
        lines = "\n".join(f"✦ <@{e['user_id']}> (`{e['user_id']}`)" for e in bl)
        await self.send(interaction, "📋 [ BLACKLIST ]", f"```yaml\nCOUNT: {len(bl)}\n```\n{lines}")

    # ── NP (No-Prefix) ──

    @app_commands.command(name="np", description="Manage the no-prefix user list (owner only)")
    @app_commands.describe(action="add, remove, or list", user_id="User ID (required for add/remove)")
    @app_commands.choices(action=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove"),
        app_commands.Choice(name="list", value="list"),
    ])
    async def np(self, interaction: discord.Interaction, action: str, user_id: str = None):
        if not self.is_owner(interaction):
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Permission denied.\n```")
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
                f"```ini\n[STATUS] Modification successful.\n[ACTION] Added user <@{uid}> ({uid}) to No-Prefix list.\n```")
        elif action == "remove":
            if uid in self.bot.db["np_list"]:
                self.bot.db["np_list"].remove(uid)
                await self.bot.save_data()
            await self.send(interaction, "🗑️ [ CONFIGURATION UPDATED ]",
                f"```ini\n[STATUS] Modification successful.\n[ACTION] Removed user <@{uid}> ({uid}) from No-Prefix list.\n```")

    # ── NPA ──

    @app_commands.command(name="npa", description="Manage no-prefix admin access (owner only)")
    @app_commands.describe(action="add or remove", user_id="User ID")
    @app_commands.choices(action=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove"),
    ])
    async def npa(self, interaction: discord.Interaction, action: str, user_id: str):
        if not self.is_owner(interaction):
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Permission denied.\n```")
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

    # ── Reload ──

    @app_commands.command(name="reload", description="Reload a cog (owner only)")
    @app_commands.describe(cog="Name of the cog to reload")
    async def reload(self, interaction: discord.Interaction, cog: str):
        if not self.is_owner(interaction):
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Permission denied.\n```")
        try:
            await self.bot.reload_extension(cog)
            await self.send(interaction, "✅ [ SYSTEM HOT-RELOAD SUCCESSFUL ]",
                f"```ini\n[MODULE] {cog}\n[STATUS] Reloaded successfully in active memory.\n```")
        except Exception as e:
            await self.send(interaction, "❌ [ SYSTEM HOT-RELOAD FAILED ]",
                f"```diff\n- MODULE: {cog}\n- STATUS: Fail\n- ERROR: {e}\n```")

    # ── Status ──

    @app_commands.command(name="status", description="Change the bot's playing status (owner only)")
    @app_commands.describe(message="Status message to display")
    async def status(self, interaction: discord.Interaction, message: str):
        if not self.is_owner(interaction):
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Permission denied.\n```")
        await self.bot.change_presence(activity=discord.Game(name=message))
        await self.send(interaction, "✅ [ CLIENT STATUS MODIFIED ]",
            f"```ini\n[PARAMETER] Presence Activity\n[VALUE] Playing {message}\n[STATUS] Applied globally.\n```")


async def setup(bot):
    await bot.add_cog(Owner(bot))
