import discord
from discord.ext import commands

kio = 0xffec01


class ServerInfoView(discord.ui.View):
    def __init__(self, guild):
        super().__init__()
        self.guild = guild

    @discord.ui.select(
        placeholder="Select an option",
        options=[
            discord.SelectOption(label="Admin's list", value="admins"),
            discord.SelectOption(label="Boosters list", value="boosters"),
            discord.SelectOption(label="emoji list", value="emojis"),
            discord.SelectOption(label="Role list", value="roles")
        ]
    )
    async def select_callback(self, interaction, select):
        await interaction.response.defer()
        if select.values[0] == "admins":
            admins = [member for member in self.guild.members if member.guild_permissions.administrator]
            admins_list = "\n".join([admin.name for admin in admins]) if admins else "No administrators found."
            embed = discord.Embed(
                title=f"{self.guild.name}'s Administrators",
                description=admins_list,
                color=kio
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

        elif select.values[0] == "boosters":
            boosters = [member for member in self.guild.members if member.premium_since]
            boosters_list = "\n".join([booster.name for booster in boosters]) if boosters else "No boosters found."
            embed = discord.Embed(
                title=f"{self.guild.name}'s Boosters",
                description=boosters_list,
                color=kio
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

        elif select.values[0] == "emojis":
            emojis_list = "\n".join([emoji.name for emoji in self.guild.emojis]) if self.guild.emojis else "No emojis found."
            embed = discord.Embed(
                title=f"{self.guild.name}'s Emojis",
                description=emojis_list,
                color=kio
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

        elif select.values[0] == "roles":
            roles_list = "\n".join([role.name for role in self.guild.roles]) if self.guild.roles else "No roles found."
            embed = discord.Embed(
                title=f"{self.guild.name}'s Roles",
                description=roles_list,
                color=kio
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


class UserAvatarView(discord.ui.View):
    def __init__(self, member):
        super().__init__()
        self.member = member

    @discord.ui.button(label="Download Avatar", style=discord.ButtonStyle.green)
    async def download_avatar(self, interaction, button):
        await interaction.response.send_message(f"[Click here to download]({self.member.avatar.url})", ephemeral=True)

class UserInfoView(discord.ui.View):
    def __init__(self, member):
        super().__init__()
        self.member = member

    @discord.ui.select(
        placeholder="Select an option",
        options=[
            discord.SelectOption(label="User's Permissions", value="permissions"),
            discord.SelectOption(label="Badges", value="badges"),
        ]
    )
    async def select_callback(self, interaction, select):
        await interaction.response.defer()
        if select.values[0] == "permissions":
            permissions = self.member.guild_permissions
            permissions_list = [perm for perm, value in permissions if value]
            embed = discord.Embed(
                title=f"{self.member}'s Permissions",
                description="\n".join(permissions_list) if permissions_list else "No permissions",
                color=0xffec01
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


        elif select.values[0] == "badges":
            embed = discord.Embed(
            title="Badges",
            description="```diff\n- No badges yet!```\n > Tip: Badges system coming soon!",
            color=kio
    )
            await interaction.followup.send(embed=embed, ephemeral=True)

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(aliases=["userinfo", "Userinfo", "Ui"])
    async def ui(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        view = UserInfoView(member)

        embed = discord.Embed(
            title=f"{member}'s Information",
            color=0xffec01
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="Username", value=member.name, inline=True)
        embed.add_field(name="Discriminator", value=member.discriminator, inline=True)
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(name="Joined Server At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        embed.add_field(name="Account Created At", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed, view=view)



    @commands.command(aliases=["av", "Avatar", "AV", "Av"])
    async def avatar(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        view = UserAvatarView(member)
        embed = discord.Embed(
            title=f"{member}'s Avatar",
            color=0xffec01
        )
        embed.set_image(url=member.avatar.url)
        await ctx.send(embed=embed, view=view)

    @commands.command(aliases=["si", "Serverinfo", "Si"])
    async def serverinfo(self, ctx):
        try:
            view = ServerInfoView(ctx.guild)
            guild = ctx.guild
            guild_icon = guild.icon.url if guild.icon else self.bot.user.avatar.url
            embed = discord.Embed(
                title=f"{guild.name}'s Information",
                color=0xffec01
            )
            embed.set_thumbnail(url=guild_icon)
            embed.add_field(name="Server Name", value=guild.name, inline=True)
            embed.add_field(name="Server ID", value=guild.id, inline=True)
            embed.add_field(name="Owner", value=guild.owner.name if guild.owner else "Unknown", inline=False)
            embed.add_field(name="Member Count", value=guild.member_count, inline=False)
            embed.set_thumbnail(url=guild_icon)
            await ctx.send(embed=embed, view=view)
        except Exception as e:
            print(f"Error in serverinfo command: {e}")
            embed = discord.Embed(
                title="Error",
                description="An error occurred while fetching server information.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)


    @commands.command(aliases=["Ping"])
    async def ping(self, ctx):
        embed = discord.Embed(
            title=" 🏓 Pong!",
            description=f" <:kio_ping:1508049489376710696> Latency: {round(self.bot.latency * 1000)}ms",
            color=kio
        )
        embed.set_thumbnail(url=ctx.bot.user.avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))