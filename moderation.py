import discord
from discord.ext import commands
import datetime
import json

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f)

def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"warnings": {}}

kio = 0xffec01

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["Kick", "fuckoff", "Fuckoff"])
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title=" <:kio_kick:1508053936144125962> Member Kicked",
                description=f"{member} has been kicked from the server.\nReason: {reason if reason else 'No reason provided.'} \n```diff\n- Note: Kicked members can rejoin the server if they have an invite link! To prevent this, consider banning the member with 'k.ban' instead! ```",
                color=0xffec01
            )
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error occurred while kicking member: {e}")
            await ctx.send("An error occurred while trying to kick the member.")

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="<:kio_x:1507717440707235950> Wrong usage!",
                description="```diff\n- Usage: kick <member> <reason>```\n```diff\n+ Example: kick @user spamming``` \n > Tip: If the user is being disruptive, consider banning them with 'k.ban' command!",
                color=kio)
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="<:kio_x:1507717440707235950> Missing Permissions!",
                description="```diff\n- You don't have permission to kick members!```",
                color=kio)
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
            await ctx.send(embed=embed)

    @commands.command(aliases=["Ban"])
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title=" <:kio_ban:1508055240455229610> Member Banned",
                description=f"{member} has been banned from the server.\nReason: {reason if reason else 'No reason provided.'} \n > Tip: You can kick members with 'k.kick' command.",
                color=0xffec01
            )
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error occurred while banning member: {e}")
            await ctx.send("An error occurred while trying to ban the member.")

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="<:kio_x:1507717440707235950> Wrong usage!",
                description="```diff\n- Usage: ban <member> <reason>```\n```diff\n+ Example: ban @user spamming``` \n > Tip: You can unban members with 'k.unban' command if you change your mind!",
                color=kio)
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="<:kio_x:1507717440707235950> Missing Permissions!",
                description="```diff\n- You don't have permission to ban members!```",
                color=kio)
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
            await ctx.send(embed=embed)

    @commands.command(aliases=["Unban"])
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            embed = discord.Embed(
                title=" <:kio_unban:1508055930864414218> Member Unbanned",
                description=f"{user} has been unbanned from the server.",
                color=0xffec01
            )
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error occurred while unbanning member: {e}")
            await ctx.send("An error occurred while trying to unban the member.")


    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="<:kio_x:1507717440707235950> Wrong usage!",
                description="```diff\n- Usage: unban <user_id>```\n```diff\n+ Example: unban 123456789012345678``` \n > Tip: You can ban members with 'k.ban' command if you want to prevent them from rejoining the server!",
                color=kio)
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="<:kio_x:1507717440707235950> Missing Permissions!",
                description="```diff\n- You don't have permission to unban members!```",
                color=kio)
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
            await ctx.send(embed=embed)


    @commands.command(aliases=["purge", "Purge", "Clear"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        if amount < 1:
            embed = discord.Embed(
                title="<:kio_x:1507717440707235950> Invalid amount!",
                description="```diff\n- Amount must be greater than 0!```",
                color=kio)
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
            await ctx.send(embed=embed)
            return

        try:
            deleted = await ctx.channel.purge(limit=amount + 1)
            embed = discord.Embed(
                title=" <:kio_purge:1508064294443683981> Messages Cleared",
                description=f"{len(deleted)-1} messages have been cleared from the channel.",
                color=kio
            )
            await ctx.send(embed=embed, delete_after=5)
        except Exception as e:
            print(f"Error occurred while clearing messages: {e}")
            await ctx.send("An error occurred while trying to clear messages.")


    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="<:kio_x:1507717440707235950> Wrong usage!",
                description="```diff\n- Usage: clear <amount>```\n```diff\n+ Example: clear 10``` \n > Tip: You can also use 'k.purge' as an alias for this command!",
                color=kio)
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="<:kio_x:1507717440707235950> Missing Permissions!",
                description="```diff\n- You don't have permission to manage messages!```",
                color=kio)
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
            await ctx.send(embed=embed)

    @commands.command(name="timeout", aliases=["Timeout", "Mute", "mute"])
    @commands.has_permissions(moderate_members=True)
    async def timeout_member(self, ctx, member: discord.Member, duration: int, *, reason=None):
        print(f"Attempting to timeout {member} for {duration} minutes. Reason: {reason}")
        try:
            await member.timeout(datetime.timedelta(minutes=duration), reason=reason)
            embed = discord.Embed(
                title=" <:kio_timeout:1508104735780245574> Member Timed Out",
                description=f"{member} has been timed out for {duration} minutes.\nReason: {reason if reason else 'No reason provided.'}",
                color=0xffec01
            )
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error occurred while timing out member: {e}")
            await ctx.send("An error occurred while trying to time out the member.")

    @timeout_member.error
    async def timeout_member_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="<:kio_x:1507717440707235950> Wrong usage!",
                description="```diff\n- Usage: timeout <member> <duration_in_minutes> <reason>```\n```diff\n+ Example: timeout @user 10 spamming``` \n > Tip: You can also use 'k.mute' as an alias for this command!",
                color=kio)
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="<:kio_x:1507717440707235950> Missing Permissions!",
                description="```diff\n- You don't have permission to moderate members!```",
                color=kio)
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))