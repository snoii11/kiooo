import discord
from discord.ext import commands
import datetime

# Advanced Futuristic Color Tokens
COLOR_YELLOW = 0xFFFF00

class ServerInfoView(discord.ui.View):
    def __init__(self, guild, bot):
        super().__init__()
        self.guild = guild
        self.bot = bot

    @discord.ui.select(
        placeholder="SELECT NETWORK METRIC...",
        options=[
            discord.SelectOption(label="ADMINISTRATORS", value="admins", emoji="🛡️"),
            discord.SelectOption(label="BOOSTERS", value="boosters", emoji="⚡"),
            discord.SelectOption(label="EMOJI MANIFEST", value="emojis", emoji="🔮"),
            discord.SelectOption(label="ROLE DIRECTORY", value="roles", emoji="🧬")
        ]
    )
    async def select_callback(self, interaction, select):
        await interaction.response.defer()
        if select.values[0] == "admins":
            admins = [member for member in self.guild.members if member.guild_permissions.administrator]
            if len(admins) > 80:
                admins_list = "\n".join([f"✦ {admin.name}" for admin in admins[:80]]) + f"\n\n... and {len(admins) - 80} more administrators."
            else:
                admins_list = "\n".join([f"✦ {admin.name}" for admin in admins]) if admins else "No administrators found."
            embed = discord.Embed(
                title=f"🛡️ [ CORE ADMINISTRATORS ]",
                description=f"```ini\n[SECTOR] {self.guild.name}\n[COUNT] {len(admins)} admin nodes\n```\n{admins_list}",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await interaction.followup.send(embed=embed, ephemeral=True)

        elif select.values[0] == "boosters":
            boosters = [member for member in self.guild.members if member.premium_since]
            if len(boosters) > 80:
                boosters_list = "\n".join([f"✦ {booster.name}" for booster in boosters[:80]]) + f"\n\n... and {len(boosters) - 80} more boosters."
            else:
                boosters_list = "\n".join([f"✦ {booster.name}" for booster in boosters]) if boosters else "No boosters found."
            embed = discord.Embed(
                title=f"⚡ [ SERVER SYSTEM AMPLIFIERS ]",
                description=f"```ini\n[SECTOR] {self.guild.name}\n[COUNT] {len(boosters)} boosters\n```\n{boosters_list}",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await interaction.followup.send(embed=embed, ephemeral=True)

        elif select.values[0] == "emojis":
            emojis = self.guild.emojis
            if len(emojis) > 80:
                emojis_list = "\n".join([f"✦ :{emoji.name}:" for emoji in emojis[:80]]) + f"\n\n... and {len(emojis) - 80} more emojis."
            else:
                emojis_list = "\n".join([f"✦ :{emoji.name}:" for emoji in emojis]) if emojis else "No emojis found."
            embed = discord.Embed(
                title=f"🔮 [ GUILD EMOJI MANIFEST ]",
                description=f"```ini\n[SECTOR] {self.guild.name}\n[COUNT] {len(emojis)} custom emojis\n```\n{emojis_list}",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await interaction.followup.send(embed=embed, ephemeral=True)

        elif select.values[0] == "roles":
            roles = self.guild.roles
            if len(roles) > 80:
                roles_list = "\n".join([f"✦ {role.name}" for role in roles[:80]]) + f"\n\n... and {len(roles) - 80} more roles."
            else:
                roles_list = "\n".join([f"✦ {role.name}" for role in roles]) if roles else "No roles found."
            embed = discord.Embed(
                title=f"🧬 [ SECURITY ROLE DIRECTORY ]",
                description=f"```ini\n[SECTOR] {self.guild.name}\n[COUNT] {len(roles)} registered roles\n```\n{roles_list}",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await interaction.followup.send(embed=embed, ephemeral=True)


class UserAvatarView(discord.ui.View):
    def __init__(self, member):
        super().__init__()
        self.member = member

    @discord.ui.button(label="DOWNLOAD VECTOR DATA", style=discord.ButtonStyle.green, emoji="💾")
    async def download_avatar(self, interaction, button):
        await interaction.response.send_message(f"[Click here to download]({self.member.display_avatar.url})", ephemeral=True)

class UserInfoView(discord.ui.View):
    def __init__(self, member, bot):
        super().__init__()
        self.member = member
        self.bot = bot

    @discord.ui.select(
        placeholder="CHOOSE USER READOUT...",
        options=[
            discord.SelectOption(label="PERMISSIONS MATRIX", value="permissions", emoji="🛡️"),
            discord.SelectOption(label="SECTOR BADGES", value="badges", emoji="🎖️"),
        ]
    )
    async def select_callback(self, interaction, select):
        await interaction.response.defer()
        if select.values[0] == "permissions":
            permissions = self.member.guild_permissions
            permissions_list = [perm.replace('_', ' ').upper() for perm, value in permissions if value]
            permissions_formatted = "\n".join(f"✦ {perm}" for perm in permissions_list) if permissions_list else "No permissions detected."
            embed = discord.Embed(
                title=f"🛡️ [ PERMISSIONS MATRIX: {self.member.name} ]",
                description=f"```prolog\n[NODENAME] {self.member}\n[MATRIX OVERVIEW]\n```\n{permissions_formatted}",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await interaction.followup.send(embed=embed, ephemeral=True)

        elif select.values[0] == "badges":
            embed = discord.Embed(
                title="🎖️ [ SECTOR BADGES ]",
                description="```diff\n- ERROR: Badging sub-routine offline.\n> Tip: Badge records system coming soon!\n```",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await interaction.followup.send(embed=embed, ephemeral=True)

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(aliases=["userinfo"])
    async def ui(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        view = UserInfoView(member, self.bot)

        embed = discord.Embed(
            title=f"❖ [ USER DIAGNOSTICS: {member.name} ] ❖",
            color=COLOR_YELLOW
        )
        embed.add_field(name="🧬 USER IDENTIFIER", value=f"`{member.name}`", inline=True)
        embed.add_field(name="🆔 SYSTEM ID", value=f"`{member.id}`", inline=True)
        
        joined_str = member.joined_at.strftime("%Y-%m-%d %H:%M:%S") if member.joined_at else "UNKNOWN"
        created_str = member.created_at.strftime("%Y-%m-%d %H:%M:%S") if member.created_at else "UNKNOWN"
        
        embed.add_field(name="📅 SERVER OVERLINK ESTABLISHED", value=f"`{joined_str}`", inline=False)
        embed.add_field(name="⏳ ACCOUNT ORIGIN TIME", value=f"`{created_str}`", inline=False)
        embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed, view=view)


    @commands.command(aliases=["av"])
    async def avatar(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        view = UserAvatarView(member)
        embed = discord.Embed(
            title=f"🖼️ [ VISUAL AVATAR DATA: {member.name} ]",
            color=COLOR_YELLOW
        )
        embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed, view=view)

    @commands.command(aliases=["si"])
    async def serverinfo(self, ctx):
        try:
            view = ServerInfoView(ctx.guild, self.bot)
            guild = ctx.guild
            guild_icon = guild.icon.url if guild.icon else self.bot.user.display_avatar.url
            embed = discord.Embed(
                title=f"🪐 [ GUILD SYSTEM MANIFEST: {guild.name} ]",
                color=COLOR_YELLOW
            )
            embed.add_field(name="🌌 GUILD CODENAME", value=f"`{guild.name}`", inline=True)
            embed.add_field(name="🆔 REGISTRY ID", value=f"`{guild.id}`", inline=True)
            embed.add_field(name="👑 SECTOR FOUNDER", value=f"`{guild.owner.name if guild.owner else 'UnknownOwner'}`", inline=False)
            embed.add_field(name="👥 POPULATION METRIC", value=f"`{guild.member_count} active nodes`", inline=False)
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed, view=view)
        except Exception as e:
            print(f"Error in serverinfo command: {e}")
            embed = discord.Embed(
                title="❌ [ OPERATIONAL ERROR ]",
                description=f"```diff\n- ERROR: Failed to compile sector metrics.\n- DETAILS: {e}\n```",
                color=COLOR_YELLOW
            )
            embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)


    @commands.command()
    async def ping(self, ctx):
        embed = discord.Embed(
            title="🏓 [ NETWORK PING TRACE ]",
            description=f"```yaml\nCONNECTION: Active\nLATENCY: {round(self.bot.latency * 1000)} ms\nDIAGNOSTICS: Nominal\n```",
            color=COLOR_YELLOW
        )
        embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))