import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
from colors import COLOR, THUMBNAIL_URL


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
        guild = self.guild

        if select.values[0] == "admins":
            admins = [m for m in guild.members if m.guild_permissions.administrator]
            text = "\n".join(f"✦ {m.name}" for m in admins[:80])
            if len(admins) > 80:
                text += f"\n\n... and {len(admins) - 80} more administrators."
            e = discord.Embed(
                title="🛡️ [ CORE ADMINISTRATORS ]",
                description=f"```ini\n[SECTOR] {guild.name}\n[COUNT] {len(admins)} admin nodes\n```\n{text or 'None found.'}",
                color=COLOR)

        elif select.values[0] == "boosters":
            boosters = [m for m in guild.members if m.premium_since]
            text = "\n".join(f"✦ {m.name}" for m in boosters[:80])
            if len(boosters) > 80:
                text += f"\n\n... and {len(boosters) - 80} more boosters."
            e = discord.Embed(
                title="⚡ [ SERVER SYSTEM AMPLIFIERS ]",
                description=f"```ini\n[SECTOR] {guild.name}\n[COUNT] {len(boosters)} boosters\n```\n{text or 'None found.'}",
                color=COLOR)

        elif select.values[0] == "emojis":
            emojis = guild.emojis
            text = "\n".join(f"✦ :{emoji.name}:" for emoji in emojis[:80])
            if len(emojis) > 80:
                text += f"\n\n... and {len(emojis) - 80} more emojis."
            e = discord.Embed(
                title="🔮 [ GUILD EMOJI MANIFEST ]",
                description=f"```ini\n[SECTOR] {guild.name}\n[COUNT] {len(emojis)} custom emojis\n```\n{text or 'None found.'}",
                color=COLOR)

        elif select.values[0] == "roles":
            roles = guild.roles
            text = "\n".join(f"✦ {role.name}" for role in roles[:80])
            if len(roles) > 80:
                text += f"\n\n... and {len(roles) - 80} more roles."
            e = discord.Embed(
                title="🧬 [ SECURITY ROLE DIRECTORY ]",
                description=f"```ini\n[SECTOR] {guild.name}\n[COUNT] {len(roles)} registered roles\n```\n{text or 'None found.'}",
                color=COLOR)

        e.set_thumbnail(url=THUMBNAIL_URL)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.followup.send(embed=e, ephemeral=True)


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
            perms = [p.replace('_', ' ').upper() for p, v in self.member.guild_permissions if v]
            fmt = "\n".join(f"✦ {p}" for p in perms) if perms else "No permissions detected."
            e = discord.Embed(
                title=f"🛡️ [ PERMISSIONS MATRIX: {self.member.name} ]",
                description=f"```prolog\n[NODENAME] {self.member}\n[MATRIX OVERVIEW]\n```\n{fmt}",
                color=COLOR)

        elif select.values[0] == "badges":
            e = discord.Embed(
                title="🎖️ [ SECTOR BADGES ]",
                description="```diff\n- ERROR: Badging sub-routine offline.\n> Tip: Badge records system coming soon!\n```",
                color=COLOR)

        e.set_thumbnail(url=THUMBNAIL_URL)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.followup.send(embed=e, ephemeral=True)


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description):
        e = discord.Embed(title=title, description=description, color=COLOR)
        e.set_thumbnail(url=THUMBNAIL_URL)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        return e

    @app_commands.command(name="userinfo", description="View information about a user")
    @app_commands.describe(member="The member to look up (defaults to you)")
    async def ui(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user

        joined = member.joined_at.strftime("%Y-%m-%d %H:%M:%S") if member.joined_at else "UNKNOWN"
        created = member.created_at.strftime("%Y-%m-%d %H:%M:%S") if member.created_at else "UNKNOWN"

        e = discord.Embed(title=f"❖ [ USER DIAGNOSTICS: {member.name} ] ❖", color=COLOR)
        e.set_thumbnail(url=THUMBNAIL_URL)
        e.add_field(name="🧬 USER IDENTIFIER", value=f"`{member.name}`", inline=True)
        e.add_field(name="🆔 SYSTEM ID", value=f"`{member.id}`", inline=True)
        e.add_field(name="📅 SERVER OVERLINK ESTABLISHED", value=f"`{joined}`", inline=False)
        e.add_field(name="⏳ ACCOUNT ORIGIN TIME", value=f"`{created}`", inline=False)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.response.send_message(embed=e, view=UserInfoView(member, self.bot))

    @app_commands.command(name="avatar", description="View a user's avatar")
    @app_commands.describe(member="The member whose avatar to view (defaults to you)")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user
        e = discord.Embed(title=f"🖼️ [ VISUAL AVATAR DATA: {member.name} ]", color=COLOR)
        e.set_thumbnail(url=THUMBNAIL_URL)
        e.set_image(url=member.display_avatar.url)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.response.send_message(embed=e, view=UserAvatarView(member))

    @app_commands.command(name="serverinfo", description="View information about this server")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        owner = guild.owner.name if guild.owner else "UnknownOwner"
        e = discord.Embed(title=f"🪐 [ GUILD SYSTEM MANIFEST: {guild.name} ]", color=COLOR)
        e.set_thumbnail(url=THUMBNAIL_URL)
        e.add_field(name="🌌 GUILD CODENAME", value=f"`{guild.name}`", inline=True)
        e.add_field(name="🆔 REGISTRY ID", value=f"`{guild.id}`", inline=True)
        e.add_field(name="👑 SECTOR FOUNDER", value=f"`{owner}`", inline=False)
        e.add_field(name="👥 POPULATION METRIC", value=f"`{guild.member_count} active nodes`", inline=False)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.response.send_message(embed=e, view=ServerInfoView(guild, self.bot))

    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self.embed(
            "🏓 [ NETWORK PING TRACE ]",
            f"```yaml\nCONNECTION: Active\nLATENCY: {round(self.bot.latency * 1000)} ms\nDIAGNOSTICS: Nominal\n```"))

    @app_commands.command(name="poll", description="Create a poll for members to vote on")
    @app_commands.describe(question="The poll question", option1="First option", option2="Second option", option3="Third option (optional)", option4="Fourth option (optional)")
    async def poll(self, interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)

        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        desc = "\n\n".join(f"{emojis[i]} {opt}" for i, opt in enumerate(options))
        e = discord.Embed(title=f"📊 [ POLL: {question} ]", description=desc, color=COLOR)
        e.set_thumbnail(url=THUMBNAIL_URL)
        e.set_footer(text="Kiooo • React to vote", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        msg = await interaction.response.send_message(embed=e)
        msg = await interaction.original_response()
        for i in range(len(options)):
            await msg.add_reaction(emojis[i])

    @app_commands.command(name="remind", description="Set a reminder")
    @app_commands.describe(minutes="Minutes from now", text="What to remind you about")
    async def remind(self, interaction: discord.Interaction, minutes: int, text: str):
        if minutes < 1:
            return await interaction.response.send_message(embed=self.embed(
                "❌ [ VALIDATION ERROR ]",
                "```diff\n- ERROR: Minutes must be at least 1.\n```"))

        await interaction.response.send_message(embed=self.embed(
            "⏰ [ REMINDER SET ]",
            f"```yaml\nTIME: {minutes} minute(s) from now\nMESSAGE: {text}\nSTATUS: Confirmed\n```"))

        await asyncio.sleep(minutes * 60)
        try:
            await interaction.user.send(embed=self.embed(
                "⏰ [ REMINDER ]",
                f"```yaml\nMESSAGE: {text}\nSTATUS: Delivered\n```"))
        except:
            pass

    @app_commands.command(name="roleinfo", description="View information about a role")
    @app_commands.describe(role="The role to look up")
    async def roleinfo(self, interaction: discord.Interaction, role: discord.Role):
        perms = [p.replace('_', ' ').upper() for p, v in role.permissions if v]
        perm_text = "\n".join(f"✦ {p}" for p in perms[:15]) if perms else "None"
        if len(perms) > 15:
            perm_text += f"\n\n... and {len(perms) - 15} more permissions."

        e = discord.Embed(title=f"🧬 [ ROLE ANALYSIS: {role.name} ]", color=role.color if role.color.value != 0 else COLOR)
        e.set_thumbnail(url=THUMBNAIL_URL)
        e.add_field(name="🆔 ROLE ID", value=f"`{role.id}`", inline=True)
        e.add_field(name="🎨 COLOR", value=f"`#{role.color.value:06x}`" if role.color.value != 0 else "`None`", inline=True)
        e.add_field(name="👥 MEMBERS", value=f"`{len(role.members)}`", inline=True)
        e.add_field(name="📶 POSITION", value=f"`{role.position}`", inline=True)
        e.add_field(name="🔒 MENTIONABLE", value=f"`{role.mentionable}`", inline=True)
        e.add_field(name="📌 DISPLAYED SEPARATELY", value=f"`{role.hoist}`", inline=True)
        e.add_field(name="🛡️ PERMISSIONS", value=perm_text, inline=False)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="botinfo", description="View information about the bot")
    async def botinfo(self, interaction: discord.Interaction):
        bot = self.bot
        guilds = len(bot.guilds)
        users = sum(g.member_count for g in bot.guilds)
        uptime = datetime.datetime.now(datetime.timezone.utc) - bot.start_time if hasattr(bot, 'start_time') else datetime.timedelta(0)
        uptime_str = str(uptime).split('.')[0]

        e = discord.Embed(title="🤖 [ BOT SYSTEM INFO ]", color=COLOR)
        e.set_thumbnail(url=THUMBNAIL_URL)
        e.add_field(name="🆔 BOT ID", value=f"`{bot.user.id}`", inline=True)
        e.add_field(name="📦 SERVERS", value=f"`{guilds}`", inline=True)
        e.add_field(name="👥 USERS", value=f"`{users}`", inline=True)
        e.add_field(name="⏱️ UPTIME", value=f"`{uptime_str}`", inline=False)
        e.add_field(name="📡 LATENCY", value=f"`{round(bot.latency * 1000)} ms`", inline=True)
        e.add_field(name="🐍 LIBRARY", value="`discord.py`", inline=True)
        e.set_footer(text="Kiooo", icon_url=bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.response.send_message(embed=e)


async def setup(bot):
    await bot.add_cog(Utility(bot))
