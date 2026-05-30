import discord
from discord.ext import commands
from discord import app_commands
import datetime
from colors import COLOR, THUMBNAIL_URL

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
        await interaction.response.send_message(embed=self.embed(title, description))

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
                "<:kio_fuckoff:1508532380544012430> [ ACTION LOG: MEMBER KICKED ]",
                f"```yaml\nTARGET: {member}\nREASON: {reason if reason else 'No reason provided.'}\n```\n*Note: Kicked members can rejoin if they have a valid invite link.*")
        except Exception as e:
            print(f"Error kicking member: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while trying to kick the member.\n```")

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
                "<:kio_ban:1508533367287845115> [ ACTION LOG: MEMBER BANNED ]",
                f"```yaml\nTARGET: {member}\nREASON: {reason if reason else 'No reason provided.'}\n```")
        except Exception as e:
            print(f"Error banning member: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while trying to ban the member.\n```")

    @app_commands.command(name="unban", description="Unban a user by their ID")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(user_id="The ID of the user to unban")
    async def unban(self, interaction: discord.Interaction, user_id: int):
        try:
            user = await self.bot.fetch_user(user_id)
            await interaction.guild.unban(user)
            await self.send(interaction,
                "✅ [ ACTION LOG: MEMBER UNBANNED ]",
                f"```yaml\nTARGET: {user}\nSTATUS: Ban revoked. Registry cleared.\n```")
        except Exception as e:
            print(f"Error unbanning user: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while trying to unban the user.\n```")

    @app_commands.command(name="clear", description="Clear a number of messages from the channel")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(amount="Number of messages to clear (1-100)")
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 1:
            return await self.send(interaction, "❌ [ OPERATIONAL FAILURE ]", "```diff\n- ERROR: Clear amount must be strictly greater than 0.\n```")
        if amount > 100:
            amount = 100

        try:
            deleted = await interaction.channel.purge(limit=amount + 1)
            e = self.embed(
                "<:kio_clear:1508532264928153881> [ ACTION LOG: CHANNEL PURGED ]",
                f"```yaml\nCHANNEL: #{interaction.channel.name}\nACTION: Message stack deleted\nCOUNT: {len(deleted) - 1} messages cleared\n```")
            await interaction.response.send_message(embed=e, delete_after=5)
        except Exception as e:
            print(f"Error clearing messages: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while trying to clear messages.\n```")

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
            await member.timeout(datetime.timedelta(minutes=duration), reason=reason)
            await self.send(interaction,
                "<:kio_timeout:1508532589617479752> [ ACTION LOG: MEMBER TIMED OUT ]",
                f"```yaml\nTARGET: {member}\nDURATION: {duration} minutes\nREASON: {reason if reason else 'No reason provided.'}\n```")
        except Exception as e:
            print(f"Error timing out member: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while trying to time out the member.\n```")

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
            e = self.embed(
                "✅ [ SECURE STANDING: NO WARNINGS ]",
                f"```ini\n[USER] {member}\n[STANDING] Nominal. Zero active incident logs.\n```")
        else:
            formatted = "\n".join(f"✦ {idx+1}. {w}" for idx, w in enumerate(warning_list))
            e = self.embed(
                f"⚠️ [ INCIDENT LOG HISTORY: {member.name} ]",
                f"**Active Warnings Registry:**\n{formatted}")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="lock", description="Lock the current channel")
    @app_commands.default_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await self.send(interaction,
            "🔒 [ SECURE PERIMETER DEFENSE LOCKED ]",
            f"```ini\n[CHANNEL] #{interaction.channel.name}\n[PERMISSIONS] send_messages: Denied (@everyone)\n[STATUS] Locked.\n```")

    @app_commands.command(name="unlock", description="Unlock the current channel")
    @app_commands.default_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await self.send(interaction,
            "🔓 [ SECURE PERIMETER DEFENSE UNLOCKED ]",
            f"```ini\n[CHANNEL] #{interaction.channel.name}\n[PERMISSIONS] send_messages: Allowed (@everyone)\n[STATUS] Unlocked.\n```")

    @app_commands.command(name="slowmode", description="Set slowmode delay on the current channel")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.describe(seconds="Slowmode delay in seconds")
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        await interaction.channel.edit(slowmode_delay=seconds)
        await self.send(interaction,
            "🐢 [ NETWORK RATE-LIMIT SET ]",
            f"```ini\n[CHANNEL] #{interaction.channel.name}\n[RATE LIMIT] {seconds} seconds delay\n[STATUS] Applied successfully.\n```")

    @app_commands.command(name="addrole", description="Add a role to a member")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.describe(member="The member to give the role to", role="The role to add")
    async def addrole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        err = self.check_role_hierarchy(interaction, member, role)
        if err:
            return await self.send(interaction, "❌ [ ROLE ACCESS RESTRICTED ]", f"```diff\n- ERROR: {err}\n```")

        await member.add_roles(role, reason=f"Moderator: {interaction.user} ({interaction.user.id})")
        await self.send(interaction,
            "✅ [ SECURE REGISTRY MODIFIED ]",
            f"```yaml\nTARGET: {member}\nROLE ADDED: {role.name}\nSTATUS: Assigned successfully.\n```")

    @app_commands.command(name="removerole", description="Remove a role from a member")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.describe(member="The member to remove the role from", role="The role to remove")
    async def removerole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        err = self.check_role_hierarchy(interaction, member, role)
        if err:
            return await self.send(interaction, "❌ [ ROLE ACCESS RESTRICTED ]", f"```diff\n- ERROR: {err}\n```")

        await member.remove_roles(role, reason=f"Moderator: {interaction.user} ({interaction.user.id})")
        await self.send(interaction,
            "✅ [ SECURE REGISTRY MODIFIED ]",
            f"```yaml\nTARGET: {member}\nROLE REMOVED: {role.name}\nSTATUS: De-assigned successfully.\n```")

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
                    "✏️ [ ACTION LOG: MEMBER RENAMED ]",
                    f"```yaml\nTARGET: {member}\nOLD: {old}\nNEW: {nickname}\nSTATUS: Identity overwritten.\n```")
            else:
                await self.send(interaction,
                    "✏️ [ ACTION LOG: NICKNAME RESET ]",
                    f"```yaml\nTARGET: {member}\nOLD: {old}\nNEW: {member.name}\nSTATUS: Identity restored to default.\n```")
        except Exception as e:
            print(f"Error changing nickname: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while trying to change the nickname.\n```")

    @app_commands.command(name="move", description="Move a member to another voice channel")
    @app_commands.default_permissions(move_members=True)
    @app_commands.describe(member="The member to move", channel="The voice channel to move them to")
    async def move(self, interaction: discord.Interaction, member: discord.Member, channel: discord.VoiceChannel):
        if not member.voice or not member.voice.channel:
            return await self.send(interaction, "❌ [ OPERATIONAL FAILURE ]", "```diff\n- ERROR: That member is not currently in a voice channel.\n```")

        try:
            await member.move_to(channel)
            await self.send(interaction,
                "🚀 [ ACTION LOG: MEMBER MOVED ]",
                f"```yaml\nTARGET: {member}\nFROM: {member.voice.channel.name if member.voice and member.voice.channel else 'None'}\nTO: {channel.name}\nSTATUS: Relocated.\n```")
        except Exception as e:
            print(f"Error moving member: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while trying to move the member.\n```")

    @app_commands.command(name="voicekick", description="Disconnect a member from voice channel")
    @app_commands.default_permissions(mute_members=True)
    @app_commands.describe(member="The member to disconnect", reason="Reason for disconnecting")
    async def voicekick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        err = self.check_hierarchy(interaction, member)
        if err:
            return await self.send(interaction, "❌ [ MODERATION DENIED ]", f"```diff\n- ERROR: {err}\n```")

        if not member.voice or not member.voice.channel:
            return await self.send(interaction, "❌ [ OPERATIONAL FAILURE ]", "```diff\n- ERROR: That member is not currently in a voice channel.\n```")

        try:
            await member.move_to(None)
            await self.send(interaction,
                "🔊 [ ACTION LOG: VOICE DISCONNECT ]",
                f"```yaml\nTARGET: {member}\nCHANNEL: {member.voice.channel.name if member.voice and member.voice.channel else 'N/A'}\nREASON: {reason if reason else 'No reason provided.'}\nSTATUS: Disconnected.\n```")
        except Exception as e:
            print(f"Error disconnecting member: {e}")
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while trying to disconnect the member.\n```")

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
            await self.send(interaction, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while fetching the ban list.\n```")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
