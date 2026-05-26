import discord
from discord.ext import commands
import datetime

# Advanced Futuristic Color Tokens
COLOR_YELLOW = 0xFFFF00
COLOR_CYAN = 0x00F0FF
COLOR_PINK = 0xFF007F
COLOR_GREEN = 0x39FF14
COLOR_RED = 0xFF3131

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_embed(self, ctx, title, description):
        embed = discord.Embed(title=title, description=description, color=COLOR_YELLOW)
        embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed)

    async def send_error(self, ctx, description, title="❌ [ OPERATIONAL ERROR ]"):
        await self.send_embed(ctx, title, description)

    def check_hierarchy(self, ctx, member: discord.Member):
        if member == ctx.author:
            return "You cannot moderate yourself!"
        if member == ctx.guild.owner:
            return "You cannot moderate the server owner!"
        if ctx.author.id != ctx.guild.owner_id and ctx.author.top_role <= member.top_role:
            return "You cannot moderate someone with an equal or higher role than yours!"
        if ctx.guild.me.top_role <= member.top_role:
            return "I cannot moderate this member because their role is higher than or equal to mine!"
        return None

    def check_role_hierarchy(self, ctx, member: discord.Member, role: discord.Role):
        if ctx.author.id != ctx.guild.owner_id and ctx.author.top_role <= role:
            return "You cannot manage a role that is equal to or higher than your highest role!"
        if ctx.guild.me.top_role <= role:
            return "I cannot manage this role because it is higher than or equal to my highest role!"
        if ctx.author.id != ctx.guild.owner_id and ctx.author.top_role <= member.top_role:
            return "You cannot manage roles for someone with an equal or higher role than yours!"
        return None

    @commands.command(aliases=["fuckoff"])
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        err = self.check_hierarchy(ctx, member)
        if err:
            return await self.send_error(ctx, f"```diff\n- ERROR: {err}\n```", title='❌ [ MODERATION DENIED ]')

        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="<:kio_fuckoff:1508532380544012430> [ ACTION LOG: MEMBER KICKED ]",
                description=f"```yaml\nTARGET: {member}\nREASON: {reason if reason else 'No reason provided.'}\n```\n*Note: Kicked members can rejoin if they have a valid invite link.*",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error occurred while kicking member: {e}")
            await self.send_error(ctx, "```diff\n- ERROR: An error occurred while trying to kick the member.\n```")

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ [ SYNTAX ERROR ]",
                description="```yaml\nCOMMAND: kick\nERROR: Missing required target member\nUSAGE: kick <member> [reason]\nEXAMPLE: kick @user disruptive behavior\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ [ ACCESS RESTRICTED ]",
                description="```diff\n- ERROR: Permission denied.\n- REQUIRED PERMISSION: Kick Members\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        err = self.check_hierarchy(ctx, member)
        if err:
            return await self.send_error(ctx, f"```diff\n- ERROR: {err}\n```", title='❌ [ MODERATION DENIED ]')

        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="<:kio_ban:1508533367287845115> [ ACTION LOG: MEMBER BANNED ]",
                description=f"```yaml\nTARGET: {member}\nREASON: {reason if reason else 'No reason provided.'}\n```",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error occurred while banning member: {e}")
            await self.send_error(ctx, "```diff\n- ERROR: An error occurred while trying to ban the member.\n```")

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ [ SYNTAX ERROR ]",
                description="```yaml\nCOMMAND: ban\nERROR: Missing required target member\nUSAGE: ban <member> [reason]\nEXAMPLE: ban @user malicious activity\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ [ ACCESS RESTRICTED ]",
                description="```diff\n- ERROR: Permission denied.\n- REQUIRED PERMISSION: Ban Members\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            embed = discord.Embed(
                title="✅ [ ACTION LOG: MEMBER UNBANNED ]",
                description=f"```yaml\nTARGET: {user}\nSTATUS: Ban revoked. Registry cleared.\n```",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error occurred while unbanning member: {e}")
            await self.send_error(ctx, "```diff\n- ERROR: An error occurred while trying to unban the member.\n```")

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ [ SYNTAX ERROR ]",
                description="```yaml\nCOMMAND: unban\nERROR: Missing required User ID\nUSAGE: unban <user_id>\nEXAMPLE: unban 1234567890\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ [ ACCESS RESTRICTED ]",
                description="```diff\n- ERROR: Permission denied.\n- REQUIRED PERMISSION: Ban Members\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)

    @commands.command(aliases=["purge"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        if amount < 1:
            await self.send_error(ctx, "```diff\n- ERROR: Clear amount must be strictly greater than 0.\n```", title="❌ [ OPERATIONAL FAILURE ]")
            return
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)
            embed = discord.Embed(
                title="<:kio_clear:1508532264928153881> [ ACTION LOG: CHANNEL PURGED ]",
                description=f"```yaml\nCHANNEL: #{ctx.channel.name}\nACTION: Message stack deleted\nCOUNT: {len(deleted)-1} messages cleared\n```",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed, delete_after=5)
        except Exception as e:
            print(f"Error occurred while clearing messages: {e}")
            await self.send_error(ctx, "```diff\n- ERROR: An error occurred while trying to clear messages.\n```")

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ [ SYNTAX ERROR ]",
                description="```yaml\nCOMMAND: clear\nERROR: Missing message limit count\nUSAGE: clear <amount>\nEXAMPLE: clear 50\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ [ ACCESS RESTRICTED ]",
                description="```diff\n- ERROR: Permission denied.\n- REQUIRED PERMISSION: Manage Messages\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)

    @commands.command(name="timeout", aliases=["mute"])
    @commands.has_permissions(moderate_members=True)
    async def timeout_member(self, ctx, member: discord.Member, duration: int, *, reason=None):
        err = self.check_hierarchy(ctx, member)
        if err:
            return await self.send_error(ctx, f"```diff\n- ERROR: {err}\n```", title='❌ [ MODERATION DENIED ]')

        if duration <= 0 or duration > 40320:
            await self.send_error(ctx, "```diff\n- ERROR: Duration must be between 1 and 40320 minutes (28 days)!\n```", title='❌ [ VALIDATION ERROR ]')
            return

        try:
            await member.timeout(datetime.timedelta(minutes=duration), reason=reason)
            embed = discord.Embed(
                title="<:kio_timeout:1508532589617479752> [ ACTION LOG: MEMBER TIMED OUT ]",
                description=f"```yaml\nTARGET: {member}\nDURATION: {duration} minutes\nREASON: {reason if reason else 'No reason provided.'}\n```",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error occurred while timing out member: {e}")
            await self.send_error(ctx, "```diff\n- ERROR: An error occurred while trying to time out the member.\n```")

    @timeout_member.error
    async def timeout_member_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ [ SYNTAX ERROR ]",
                description="```yaml\nCOMMAND: timeout\nERROR: Missing required duration or target\nUSAGE: timeout <member> <duration_minutes> [reason]\nEXAMPLE: timeout @user 60 spamming\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ [ ACCESS RESTRICTED ]",
                description="```diff\n- ERROR: Permission denied.\n- REQUIRED PERMISSION: Moderate Members\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)

    @commands.command(aliases=["untimeout", "unmute"])
    @commands.has_permissions(moderate_members=True)
    async def untimeout_member(self, ctx, member: discord.Member):
        err = self.check_hierarchy(ctx, member)
        if err:
            return await self.send_error(ctx, f"```diff\n- ERROR: {err}\n```", title='❌ [ MODERATION DENIED ]')

        try:
            await member.timeout(None)
            embed = discord.Embed(
                title="✅ [ ACTION LOG: TIMEOUT REMOVED ]",
                description=f"```yaml\nTARGET: {member}\nSTATUS: Active connection restored.\n```",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error occurred while removing timeout: {e}")
            await self.send_error(ctx, "```diff\n- ERROR: An error occurred while trying to remove the timeout.\n```")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        err = self.check_hierarchy(ctx, member)
        if err:
            return await self.send_error(ctx, f"```diff\n- ERROR: {err}\n```", title='❌ [ MODERATION DENIED ]')

        try:
            user_id = str(member.id)
            if user_id not in self.bot.db["warnings"]:
                self.bot.db["warnings"][user_id] = []
            self.bot.db["warnings"][user_id].append(reason if reason else "No reason provided.")
            self.bot.save_data()
            embed = discord.Embed(
                title="⚠️ [ ACTION LOG: MEMBER WARNED ]",
                description=f"```yaml\nTARGET: {member}\nREASON: {reason if reason else 'No reason provided.'}\nTOTAL WARNINGS: {len(self.bot.db['warnings'][user_id])}\n```",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ [ OPERATIONAL ERROR ]",
                description=f"```diff\n- Failed to register warn incident.\n- ERROR: {e}\n```",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)

    @warn.error
    async def warn_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ [ SYNTAX ERROR ]",
                description="```yaml\nCOMMAND: warn\nERROR: Missing target member\nUSAGE: warn <member> [reason]\nEXAMPLE: warn @user inappropriate behavior\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ [ ACCESS RESTRICTED ]",
                description="```diff\n- ERROR: Permission denied.\n- REQUIRED PERMISSION: Manage Messages\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)

    @commands.command()
    async def warnings(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        if member != ctx.author and not ctx.channel.permissions_for(ctx.author).manage_messages:
            await self.send_error(ctx, "```diff\n- ERROR: You do not have permission to view other members' warnings!\n```", title="❌ [ ACCESS RESTRICTED ]")
            return

        user_id = str(member.id)
        warnings = self.bot.db["warnings"].get(user_id, [])
        if not warnings:
            embed = discord.Embed(
                title="✅ [ SECURE STANDING: NO WARNINGS ]",
                description=f"```ini\n[USER] {member}\n[STANDING] Nominal. Zero active incident logs.\n```",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        else:
            warnings_formatted = "\n".join(f"✦ {idx+1}. {warn}" for idx, warn in enumerate(warnings))
            embed = discord.Embed(
                title=f"⚠️ [ INCIDENT LOG HISTORY: {member.name} ]",
                description=f"**Active Warnings Registry:**\n{warnings_formatted}",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        embed = discord.Embed(
            title="🔒 [ SECURE PERIMETER DEFENSE LOCKED ]",
            description=f"```ini\n[CHANNEL] #{ctx.channel.name}\n[PERMISSIONS] send_messages: Denied (@everyone)\n[STATUS] Locked.\n```",
            color=COLOR_YELLOW
        )
        embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed)

    @lock.error
    async def lock_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ [ ACCESS RESTRICTED ]",
                description="```diff\n- ERROR: Permission denied.\n- REQUIRED PERMISSION: Manage Channels\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        elif isinstance(error, Exception):
            embed = discord.Embed(
                title="❌ [ EXCEPTION RAISED ]",
                description=f"```diff\n- Failure locking channel perimeter.\n- DETAILS: {error}\n```",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        embed = discord.Embed(
            title="🔓 [ SECURE PERIMETER DEFENSE UNLOCKED ]",
            description=f"```ini\n[CHANNEL] #{ctx.channel.name}\n[PERMISSIONS] send_messages: Allowed (@everyone)\n[STATUS] Unlocked.\n```",
            color=COLOR_YELLOW
        )
        embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed)

    @unlock.error
    async def unlock_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ [ ACCESS RESTRICTED ]",
                description="```diff\n- ERROR: Permission denied.\n- REQUIRED PERMISSION: Manage Channels\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        elif isinstance(error, Exception):
            embed = discord.Embed(
                title="❌ [ EXCEPTION RAISED ]",
                description=f"```diff\n- Failure unlocking channel perimeter.\n- DETAILS: {error}\n```",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        await ctx.channel.edit(slowmode_delay=seconds)
        embed = discord.Embed(
            title="🐢 [ NETWORK RATE-LIMIT SET ]",
            description=f"```ini\n[CHANNEL] #{ctx.channel.name}\n[RATE LIMIT] {seconds} seconds delay\n[STATUS] Applied successfully.\n```",
            color=COLOR_YELLOW
        )
        embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed)

    @slowmode.error
    async def slowmode_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ [ ACCESS RESTRICTED ]",
                description="```diff\n- ERROR: Permission denied.\n- REQUIRED PERMISSION: Manage Channels\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        elif isinstance(error, Exception):
            embed = discord.Embed(
                title="❌ [ EXCEPTION RAISED ]",
                description=f"```diff\n- Failure configuring channel slowmode delay.\n- DETAILS: {error}\n```",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)

    @commands.command(aliases=["ar"])
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx, member: discord.Member, role: discord.Role):
        err = self.check_role_hierarchy(ctx, member, role)
        if err:
            return await self.send_error(ctx, f"```diff\n- ERROR: {err}\n```", title='❌ [ ROLE ACCESS RESTRICTED ]')

        await member.add_roles(role)
        embed = discord.Embed(
            title="✅ [ SECURE REGISTRY MODIFIED ]",
            description=f"```yaml\nTARGET: {member}\nROLE ADDED: {role.name}\nSTATUS: Assigned successfully.\n```",
            color=COLOR_YELLOW
        )
        embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed)

    @addrole.error
    async def addrole_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ [ ACCESS RESTRICTED ]",
                description="```diff\n- ERROR: Permission denied.\n- REQUIRED PERMISSION: Manage Roles\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        elif isinstance(error, Exception):
            embed = discord.Embed(
                title="❌ [ EXCEPTION RAISED ]",
                description=f"```diff\n- Failure updating member role list.\n- DETAILS: {error}\n```",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)

    @commands.command(aliases=["rr"])
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, member: discord.Member, role: discord.Role):
        err = self.check_role_hierarchy(ctx, member, role)
        if err:
            return await self.send_error(ctx, f"```diff\n- ERROR: {err}\n```", title='❌ [ ROLE ACCESS RESTRICTED ]')

        await member.remove_roles(role)
        embed = discord.Embed(
            title="✅ [ SECURE REGISTRY MODIFIED ]",
            description=f"```yaml\nTARGET: {member}\nROLE REMOVED: {role.name}\nSTATUS: De-assigned successfully.\n```",
            color=COLOR_YELLOW
        )
        embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed)

    @removerole.error
    async def removerole_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ [ ACCESS RESTRICTED ]",
                description="```diff\n- ERROR: Permission denied.\n- REQUIRED PERMISSION: Manage Roles\n```",
                color=COLOR_YELLOW)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
        elif isinstance(error, Exception):
            embed = discord.Embed(
                title="❌ [ EXCEPTION RAISED ]",
                description=f"```diff\n- Failure updating member role list.\n- DETAILS: {error}\n```",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))