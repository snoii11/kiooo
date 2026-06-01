import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
from colors import COLOR, THUMBNAIL_URL


class NukeView(discord.ui.View):
    def __init__(self, channel):
        super().__init__()
        self.channel = channel
        self.confirmed = False

    @discord.ui.button(label="CONFIRM NUKE", style=discord.ButtonStyle.danger, emoji="💥")
    async def confirm(self, interaction, button):
        self.confirmed = True
        await interaction.response.defer()
        for child in self.children:
            child.disabled = True
        await interaction.edit_original_response(view=self)
        new_channel = await self.channel.clone(reason="Nuke: channel cloned")
        await self.channel.delete(reason="Nuke: original deleted")
        e = discord.Embed(
            title="💥 [ CHANNEL NUKED ]",
            description=f"```yaml\nCHANNEL: #{new_channel.name}\nSTATUS: Channel has been obliterated.\n```",
            color=COLOR)
        e.set_thumbnail(url=THUMBNAIL_URL)
        e.set_footer(text="Kiooo")
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await new_channel.send(embed=e)
        self.stop()

    @discord.ui.button(label="CANCEL", style=discord.ButtonStyle.green)
    async def cancel(self, interaction, button):
        self.confirmed = False
        await interaction.response.edit_message(content="Nuke cancelled.", embed=None, view=None)
        self.stop()


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description):
        e = discord.Embed(title=title, description=description, color=COLOR)
        e.set_thumbnail(url=THUMBNAIL_URL)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        return e

    async def send(self, interaction, title, description):
        e = self.embed(title, description)
        if interaction.response.is_done():
            await interaction.followup.send(embed=e)
        else:
            await interaction.response.send_message(embed=e)

    def check_hierarchy(self, interaction, member):
        if member == interaction.user:
            return "You cannot moderate yourself!"
        if member == interaction.guild.owner:
            return "You cannot moderate the server owner!"
        if interaction.user.id != interaction.guild.owner_id and interaction.user.top_role <= member.top_role:
            return "You cannot moderate someone with an equal or higher role than yours!"
        if interaction.guild.me.top_role <= member.top_role:
            return "I cannot moderate this member because their role is higher than or equal to mine!"
        return None

    def check_role_hierarchy(self, interaction, member, role):
        if interaction.user.id != interaction.guild.owner_id and interaction.user.top_role <= role:
            return "You cannot manage a role that is equal to or higher than your highest role!"
        if interaction.guild.me.top_role <= role:
            return "I cannot manage this role because it is higher than or equal to my highest role!"
        if interaction.user.id != interaction.guild.owner_id and interaction.user.top_role <= member.top_role:
            return "You cannot manage roles for someone with an equal or higher role than yours!"
        return None

    # ── Kick ──

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.describe(member="The member to kick", reason="Reason for the kick")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        err = self.check_hierarchy(interaction, member)
        if err:
            return await self.send(interaction, "❌ [ MODERATION DENIED ]", f"```diff\n- ERROR: {err}\n```")
        try:
            await member.kick(reason=reason)
            await self.send(interaction,
                "👢 [ ACTION LOG: MEMBER KICKED ]",
                f"```yaml\nTARGET: {member}\nREASON: {reason if reason else 'No reason provided.'}\n```")
        except Exception as e:
            print(f"Error kicking member: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while trying to kick the member.\n```")

    # ── Ban ──

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(member="The member to ban", reason="Reason for the ban")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        err = self.check_hierarchy(interaction, member)
        if err:
            return await self.send(interaction, "❌ [ MODERATION DENIED ]", f"```diff\n- ERROR: {err}\n```")
        try:
            await member.ban(reason=reason)
            await self.send(interaction,
                "🔨 [ ACTION LOG: MEMBER BANNED ]",
                f"```yaml\nTARGET: {member}\nREASON: {reason if reason else 'No reason provided.'}\n```")
        except Exception as e:
            print(f"Error banning member: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while trying to ban the member.\n```")

    # ── Unban ──

    @app_commands.command(name="unban", description="Unban a user by their ID")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(user_id="The ID of the user to unban")
    async def unban(self, interaction: discord.Interaction, user_id: str):
        try:
            uid = int(user_id)
        except ValueError:
            return await self.send(interaction, "❌ [ INVALID ID ]", "```diff\n- ERROR: User ID must be a numeric value.\n```")
        try:
            user = await self.bot.fetch_user(uid)
            await interaction.guild.unban(user)
            await self.send(interaction,
                "✅ [ ACTION LOG: MEMBER UNBANNED ]",
                f"```yaml\nTARGET: {user}\nSTATUS: Ban revoked. Registry cleared.\n```")
        except discord.NotFound:
            await self.send(interaction, "❌ [ NOT FOUND ]", "```diff\n- ERROR: User or ban not found.\n```")
        except Exception as e:
            print(f"Error unbanning user: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while trying to unban the user.\n```")

    # ── Unban All ──

    @app_commands.command(name="unbanall", description="Unban all users in the server")
    @app_commands.default_permissions(ban_members=True)
    async def unbanall(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            bans = [entry async for entry in interaction.guild.bans()]
            if not bans:
                return await self.send(interaction, "✅ [ UNBAN ALL ]", "```yaml\nSTATUS: No banned users found.\n```")
            count = 0
            for entry in bans:
                try:
                    await interaction.guild.unban(entry.user, reason="Unban all")
                    count += 1
                except:
                    pass
            await self.send(interaction,
                "✅ [ UNBAN ALL COMPLETE ]",
                f"```yaml\nTOTAL UNBANNED: {count}\nSTATUS: All bans cleared.\n```")
        except Exception as e:
            print(f"Error unbanning all: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while unbanning all users.\n```")

    # ── Clear ──

    @app_commands.command(name="clear", description="Clear a number of messages from the channel")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(amount="Number of messages to clear (1-100)")
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 1:
            return await self.send(interaction, "❌ [ OPERATIONAL FAILURE ]", "```diff\n- ERROR: Clear amount must be strictly greater than 0.\n```")
        if amount > 100:
            amount = 100
        await interaction.response.defer()
        try:
            deleted = await interaction.channel.purge(limit=amount + 1)
            e = self.embed(
                "🧹 [ ACTION LOG: CHANNEL PURGED ]",
                f"```yaml\nCHANNEL: #{interaction.channel.name}\nACTION: Message stack deleted\nCOUNT: {len(deleted) - 1} messages cleared\n```")
            await interaction.followup.send(embed=e, delete_after=5)
        except Exception as e:
            print(f"Error clearing messages: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while trying to clear messages.\n```")

    # ── Purge Bots ──

    @app_commands.command(name="purgebots", description="Purge bot messages from the channel")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(amount="Number of messages to scan (max 100)")
    async def purgebots(self, interaction: discord.Interaction, amount: int = 100):
        if amount < 1:
            return await self.send(interaction, "❌ [ INVALID AMOUNT ]", "```diff\n- ERROR: Amount must be at least 1.\n```")
        amount = min(amount, 100)
        await interaction.response.defer()
        try:
            def is_bot(msg):
                return msg.author.bot
            deleted = await interaction.channel.purge(limit=amount, check=is_bot)
            await self.send(interaction,
                "🤖 [ BOT MESSAGES PURGED ]",
                f"```yaml\nCHANNEL: #{interaction.channel.name}\nCOUNT: {len(deleted)} bot messages removed\n```")
        except Exception as e:
            print(f"Error purging bots: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred.\n```")

    # ── Timeout ──

    @app_commands.command(name="timeout", description="Timeout a member for a duration")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="The member to timeout", duration="Duration in minutes (1-40320)", reason="Reason for the timeout")
    async def timeout_member(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = None):
        err = self.check_hierarchy(interaction, member)
        if err:
            return await self.send(interaction, "❌ [ MODERATION DENIED ]", f"```diff\n- ERROR: {err}\n```")
        if duration <= 0 or duration > 40320:
            return await self.send(interaction, "❌ [ VALIDATION ERROR ]", "```diff\n- ERROR: Duration must be between 1 and 40320 minutes (28 days)!\n```")
        try:
            until = datetime.timedelta(minutes=duration)
            await member.timeout(until, reason=reason)
            await self.send(interaction,
                "🔇 [ ACTION LOG: MEMBER TIMED OUT ]",
                f"```yaml\nTARGET: {member}\nDURATION: {duration} minutes\nREASON: {reason if reason else 'No reason provided.'}\n```")
        except Exception as e:
            print(f"Error timing out member: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while trying to time out the member.\n```")

    # ── Untimeout ──

    @app_commands.command(name="untimeout", description="Remove a timeout from a member")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="The member to remove timeout from")
    async def untimeout_member(self, interaction: discord.Interaction, member: discord.Member):
        err = self.check_hierarchy(interaction, member)
        if err:
            return await self.send(interaction, "❌ [ MODERATION DENIED ]", f"```diff\n- ERROR: {err}\n```")
        try:
            await member.timeout(None)
            await self.send(interaction,
                "✅ [ ACTION LOG: TIMEOUT REMOVED ]",
                f"```yaml\nTARGET: {member}\nSTATUS: Active connection restored.\n```")
        except Exception as e:
            print(f"Error removing timeout: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while trying to remove the timeout.\n```")

    # ── Warn ──

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(member="The member to warn", reason="Reason for the warning")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        err = self.check_hierarchy(interaction, member)
        if err:
            return await self.send(interaction, "❌ [ MODERATION DENIED ]", f"```diff\n- ERROR: {err}\n```")
        try:
            user_id = str(member.id)
            if user_id not in self.bot.db["warnings"]:
                self.bot.db["warnings"][user_id] = []
            self.bot.db["warnings"][user_id].append(reason if reason else "No reason provided.")
            await self.bot.save_data()
            await self.send(interaction,
                "⚠️ [ ACTION LOG: MEMBER WARNED ]",
                f"```yaml\nTARGET: {member}\nREASON: {reason if reason else 'No reason provided.'}\nTOTAL WARNINGS: {len(self.bot.db['warnings'][user_id])}\n```")
        except Exception as e:
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", f"```diff\n- Failed to register warn incident.\n- ERROR: {e}\n```")

    # ── Warnings ──

    @app_commands.command(name="warnings", description="View warnings for a member")
    @app_commands.describe(member="The member to check warnings for (defaults to you)")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user
        if member != interaction.user and not interaction.channel.permissions_for(interaction.user).manage_messages:
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]", "```diff\n- ERROR: You do not have permission to view other members' warnings!\n```")
        user_id = str(member.id)
        warning_list = self.bot.db["warnings"].get(user_id, [])
        if not warning_list:
            e = self.embed("✅ [ SECURE STANDING: NO WARNINGS ]",
                f"```ini\n[USER] {member}\n[STANDING] Nominal. Zero active incident logs.\n```")
        else:
            formatted = "\n".join(f"✦ {idx+1}. {w}" for idx, w in enumerate(warning_list))
            e = self.embed(f"⚠️ [ INCIDENT LOG HISTORY: {member.name} ]",
                f"**Active Warnings Registry:**\n{formatted}")
        await interaction.response.send_message(embed=e)

    # ── Lock ──

    @app_commands.command(name="lock", description="Lock the current channel")
    @app_commands.default_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await self.send(interaction,
            "🔒 [ CHANNEL LOCKED ]",
            f"```ini\n[CHANNEL] #{interaction.channel.name}\n[STATUS] Locked.\n```")

    # ── Unlock ──

    @app_commands.command(name="unlock", description="Unlock the current channel")
    @app_commands.default_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await self.send(interaction,
            "🔓 [ CHANNEL UNLOCKED ]",
            f"```ini\n[CHANNEL] #{interaction.channel.name}\n[STATUS] Unlocked.\n```")

    # ── Lock All ──

    @app_commands.command(name="lockall", description="Lock all channels in the server")
    @app_commands.default_permissions(manage_channels=True)
    async def lockall(self, interaction: discord.Interaction):
        await interaction.response.defer()
        count = 0
        for channel in interaction.guild.channels:
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                try:
                    await channel.set_permissions(interaction.guild.default_role, send_messages=False, speak=False)
                    count += 1
                    await asyncio.sleep(0.5)
                except:
                    pass
        await self.send(interaction,
            "🔒 [ ALL CHANNELS LOCKED ]",
            f"```ini\n[SERVER] {interaction.guild.name}\n[CHANNELS LOCKED] {count}\n[STATUS] Server-wide lockdown.\n```")

    # ── Unlock All ──

    @app_commands.command(name="unlockall", description="Unlock all channels in the server")
    @app_commands.default_permissions(manage_channels=True)
    async def unlockall(self, interaction: discord.Interaction):
        await interaction.response.defer()
        count = 0
        for channel in interaction.guild.channels:
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                try:
                    await channel.set_permissions(interaction.guild.default_role, send_messages=None, speak=None)
                    count += 1
                    await asyncio.sleep(0.5)
                except:
                    pass
        await self.send(interaction,
            "🔓 [ ALL CHANNELS UNLOCKED ]",
            f"```ini\n[SERVER] {interaction.guild.name}\n[CHANNELS UNLOCKED] {count}\n[STATUS] Server-wide unlock.\n```")

    # ── Hide ──

    @app_commands.command(name="hide", description="Hide the current channel from @everyone")
    @app_commands.default_permissions(manage_channels=True)
    async def hide(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await self.send(interaction,
            "👁️ [ CHANNEL HIDDEN ]",
            f"```ini\n[CHANNEL] #{interaction.channel.name}\n[STATUS] Hidden from @everyone.\n```")

    # ── Unhide ──

    @app_commands.command(name="unhide", description="Unhide the current channel from @everyone")
    @app_commands.default_permissions(manage_channels=True)
    async def unhide(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=True)
        await self.send(interaction,
            "👁️ [ CHANNEL UNHIDDEN ]",
            f"```ini\n[CHANNEL] #{interaction.channel.name}\n[STATUS] Visible to @everyone.\n```")

    # ── Hide All ──

    @app_commands.command(name="hideall", description="Hide all channels from @everyone")
    @app_commands.default_permissions(manage_channels=True)
    async def hideall(self, interaction: discord.Interaction):
        await interaction.response.defer()
        count = 0
        for channel in interaction.guild.channels:
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                try:
                    await channel.set_permissions(interaction.guild.default_role, view_channel=False)
                    count += 1
                    await asyncio.sleep(0.5)
                except:
                    pass
        await self.send(interaction,
            "👁️ [ ALL CHANNELS HIDDEN ]",
            f"```ini\n[SERVER] {interaction.guild.name}\n[CHANNELS HIDDEN] {count}\n[STATUS] All channels hidden.\n```")

    # ── Unhide All ──

    @app_commands.command(name="unhideall", description="Unhide all channels from @everyone")
    @app_commands.default_permissions(manage_channels=True)
    async def unhideall(self, interaction: discord.Interaction):
        await interaction.response.defer()
        count = 0
        for channel in interaction.guild.channels:
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                try:
                    await channel.set_permissions(interaction.guild.default_role, view_channel=True)
                    count += 1
                    await asyncio.sleep(0.5)
                except:
                    pass
        await self.send(interaction,
            "👁️ [ ALL CHANNELS UNHIDDEN ]",
            f"```ini\n[SERVER] {interaction.guild.name}\n[CHANNELS UNHIDDEN] {count}\n[STATUS] All channels visible.\n```")

    # ── Slowmode ──

    @app_commands.command(name="slowmode", description="Set slowmode delay on the current channel")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.describe(seconds="Slowmode delay in seconds")
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        await interaction.channel.edit(slowmode_delay=seconds)
        await self.send(interaction,
            "🐢 [ RATE LIMIT APPLIED ]",
            f"```ini\n[CHANNEL] #{interaction.channel.name}\n[RATE LIMIT] {seconds}s\n[STATUS] Applied.\n```")

    # ── Nuke ──

    @app_commands.command(name="nuke", description="Clone and delete the current channel")
    @app_commands.default_permissions(manage_channels=True)
    async def nuke(self, interaction: discord.Interaction):
        e = discord.Embed(
            title="💥 [ CHANNEL NUKE CONFIRMATION ]",
            description="```yaml\nWARNING: This will delete and recreate this channel.\nAre you sure you want to proceed?\n```",
            color=COLOR)
        e.set_thumbnail(url=THUMBNAIL_URL)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.response.send_message(embed=e, view=NukeView(interaction.channel))

    # ── List ──

    @app_commands.command(name="list", description="List members by type")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(category="What to list", role="Role (required for 'inrole')")
    @app_commands.choices(category=[
        app_commands.Choice(name="Administrators", value="admins"),
        app_commands.Choice(name="Bots", value="bots"),
        app_commands.Choice(name="In Role", value="inrole"),
        app_commands.Choice(name="Banned Users", value="bans"),
    ])
    async def list_members(self, interaction: discord.Interaction, category: str, role: discord.Role = None):
        await interaction.response.defer()
        if category == "admins":
            members = [m for m in interaction.guild.members if m.guild_permissions.administrator]
            text = "\n".join(f"✦ {m} ({m.id})" for m in members[:30])
            if len(members) > 30:
                text += f"\n\n... and {len(members) - 30} more."
            await self.send(interaction,
                "🛡️ [ ADMINISTRATORS ]",
                f"```yaml\nCOUNT: {len(members)}\n\n{text or 'None'}\n```")
        elif category == "bots":
            members = [m for m in interaction.guild.members if m.bot]
            text = "\n".join(f"✦ {m} ({m.id})" for m in members[:30])
            if len(members) > 30:
                text += f"\n\n... and {len(members) - 30} more."
            await self.send(interaction,
                "🤖 [ BOTS ]",
                f"```yaml\nCOUNT: {len(members)}\n\n{text or 'None'}\n```")
        elif category == "inrole":
            if role is None:
                return await self.send(interaction, "❌ [ MISSING ROLE ]", "```diff\n- ERROR: Please specify a role.\n```")
            members = [m for m in interaction.guild.members if role in m.roles]
            text = "\n".join(f"✦ {m} ({m.id})" for m in members[:30])
            if len(members) > 30:
                text += f"\n\n... and {len(members) - 30} more."
            await self.send(interaction,
                f"📋 [ MEMBERS WITH {role.name} ]",
                f"```yaml\nROLE: {role.name}\nCOUNT: {len(members)}\n\n{text or 'None'}\n```")
        elif category == "bans":
            try:
                bans = [entry async for entry in interaction.guild.bans()]
                text = "\n".join(f"✦ {b.user} ({b.user.id})" for b in bans[:30])
                if len(bans) > 30:
                    text += f"\n\n... and {len(bans) - 30} more."
                await self.send(interaction,
                    "🔨 [ BANNED USERS ]",
                    f"```yaml\nCOUNT: {len(bans)}\n\n{text or 'None'}\n```")
            except Exception as e:
                await self.send(interaction, "❌ [ ERROR ]", f"```diff\n- {e}\n```")

    # ── Addrole ──

    @app_commands.command(name="addrole", description="Add a role to a member")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.describe(member="The member to give the role to", role="The role to add")
    async def addrole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        err = self.check_role_hierarchy(interaction, member, role)
        if err:
            return await self.send(interaction, "❌ [ ROLE ACCESS RESTRICTED ]", f"```diff\n- ERROR: {err}\n```")
        await member.add_roles(role, reason=f"Moderator: {interaction.user} ({interaction.user.id})")
        await self.send(interaction,
            "✅ [ ROLE ADDED ]",
            f"```yaml\nTARGET: {member}\nROLE ADDED: {role.name}\nSTATUS: Assigned successfully.\n```")

    # ── Removerole ──

    @app_commands.command(name="removerole", description="Remove a role from a member")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.describe(member="The member to remove the role from", role="The role to remove")
    async def removerole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        err = self.check_role_hierarchy(interaction, member, role)
        if err:
            return await self.send(interaction, "❌ [ ROLE ACCESS RESTRICTED ]", f"```diff\n- ERROR: {err}\n```")
        await member.remove_roles(role, reason=f"Moderator: {interaction.user} ({interaction.user.id})")
        await self.send(interaction,
            "✅ [ ROLE REMOVED ]",
            f"```yaml\nTARGET: {member}\nROLE REMOVED: {role.name}\nSTATUS: De-assigned successfully.\n```")

    # ── Nick ──

    @app_commands.command(name="nick", description="Change a member's nickname")
    @app_commands.default_permissions(manage_nicknames=True)
    @app_commands.describe(member="The member to rename", nickname="The new nickname (leave blank to reset)")
    async def nick(self, interaction: discord.Interaction, member: discord.Member, nickname: str = None):
        err = self.check_hierarchy(interaction, member)
        if err:
            return await self.send(interaction, "❌ [ MODERATION DENIED ]", f"```diff\n- ERROR: {err}\n```")
        try:
            old = member.display_name
            await member.edit(nick=nickname)
            if nickname:
                await self.send(interaction,
                    "✏️ [ MEMBER RENAMED ]",
                    f"```yaml\nTARGET: {member}\nOLD: {old}\nNEW: {nickname}\nSTATUS: Identity overwritten.\n```")
            else:
                await self.send(interaction,
                    "✏️ [ NICKNAME RESET ]",
                    f"```yaml\nTARGET: {member}\nOLD: {old}\nNEW: {member.name}\nSTATUS: Identity restored.\n```")
        except Exception as e:
            print(f"Error changing nickname: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred.\n```")

    # ── Move ──

    @app_commands.command(name="move", description="Move a member to another voice channel")
    @app_commands.default_permissions(move_members=True)
    @app_commands.describe(member="The member to move", channel="Target voice channel")
    async def move(self, interaction: discord.Interaction, member: discord.Member, channel: discord.VoiceChannel):
        if not member.voice or not member.voice.channel:
            return await self.send(interaction, "❌ [ NOT IN VOICE ]", "```diff\n- ERROR: That member is not in a voice channel.\n```")
        try:
            await member.move_to(channel)
            await self.send(interaction,
                "🚀 [ MEMBER MOVED ]",
                f"```yaml\nTARGET: {member}\nTO: {channel.name}\nSTATUS: Relocated.\n```")
        except Exception as e:
            print(f"Error moving member: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred.\n```")

    # ── Voicekick ──

    @app_commands.command(name="voicekick", description="Disconnect a member from voice channel")
    @app_commands.default_permissions(mute_members=True)
    @app_commands.describe(member="The member to disconnect", reason="Reason")
    async def voicekick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        err = self.check_hierarchy(interaction, member)
        if err:
            return await self.send(interaction, "❌ [ MODERATION DENIED ]", f"```diff\n- ERROR: {err}\n```")
        if not member.voice or not member.voice.channel:
            return await self.send(interaction, "❌ [ NOT IN VOICE ]", "```diff\n- ERROR: That member is not in a voice channel.\n```")
        try:
            await member.move_to(None)
            await self.send(interaction,
                "🔊 [ VOICE DISCONNECT ]",
                f"```yaml\nTARGET: {member}\nREASON: {reason if reason else 'No reason provided.'}\nSTATUS: Disconnected.\n```")
        except Exception as e:
            print(f"Error disconnecting member: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred.\n```")

    # ── Banlist ──

    @app_commands.command(name="banlist", description="View the list of banned users")
    @app_commands.default_permissions(ban_members=True)
    async def banlist(self, interaction: discord.Interaction):
        try:
            bans = [entry async for entry in interaction.guild.bans()]
            if not bans:
                return await self.send(interaction, "✅ [ BAN LIST ]", "```yaml\nSTATUS: No banned users found.\n```")
            lines = [f"✦ {b.user.name} ({b.user.id})" for b in bans[:50]]
            if len(bans) > 50:
                lines.append(f"\n... and {len(bans) - 50} more.")
            await self.send(interaction,
                "📋 [ BAN LIST ]",
                f"```yaml\nTOTAL BANS: {len(bans)}\n\n" + "\n".join(lines) + "\n```")
        except Exception as e:
            print(f"Error fetching ban list: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred.\n```")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
