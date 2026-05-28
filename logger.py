import discord
from discord.ext import commands
from discord import app_commands
import datetime

COLOR_YELLOW = 0xFFFF00


class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description):
        e = discord.Embed(title=title, description=description, color=COLOR_YELLOW)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        return e

    def get_collection(self):
        mongo_db = getattr(self.bot, "mongo_db", None)
        return mongo_db["logger"] if mongo_db is not None else None

    async def get_log_channel(self, guild, category):
        collection = self.get_collection()
        if collection is None:
            return None
        data = await collection.find_one({"guild_id": guild.id})
        if data and data.get(category):
            return guild.get_channel(data[category])
        return None

    async def send_log(self, guild, category, title, description):
        channel = await self.get_log_channel(guild, category)
        if channel:
            await channel.send(embed=self.embed(title, description))

    @app_commands.command(name="setup", description="Configure server settings")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        config_type="What to configure",
        category="Which log category (required for Log type)",
        channel="Target channel (required unless category is All)"
    )
    @app_commands.choices(config_type=[
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
    async def setup(self, interaction: discord.Interaction, config_type: str, category: str = None, channel: discord.TextChannel = None):
        if config_type != "log":
            return await interaction.response.send_message(
                embed=self.embed(
                    "ℹ️ [ COMING SOON ]",
                    f"```yaml\nFEATURE: {config_type.capitalize()}\nSTATUS: Not implemented yet.\n```"), ephemeral=True)

        if category is None:
            return await interaction.response.send_message(
                embed=self.embed(
                    "❌ [ MISSING OPTION ]",
                    "```diff\n- ERROR: Please specify a category or use 'All'.\n```"), ephemeral=True)

        if not channel and category != "all":
            return await interaction.response.send_message(
                embed=self.embed(
                    "❌ [ MISSING OPTION ]",
                    "```diff\n- ERROR: Please specify a channel for this log category.\n```"), ephemeral=True)

        collection = self.get_collection()
        if collection is None:
            return await interaction.response.send_message(
                embed=self.embed(
                    "❌ [ DATABASE OFFLINE ]",
                    "```diff\n- ERROR: MongoDB is not configured.\n```"), ephemeral=True)

        if category == "all":
            await interaction.response.defer()

            existing = await collection.find_one({"guild_id": interaction.guild_id})
            overwrite = discord.PermissionOverwrite()
            overwrite.send_messages = False
            overwrite.add_reactions = False

            category_channel = await interaction.guild.create_category(
                "kio-logs",
                overwrites={interaction.guild.default_role: overwrite}
            )

            channel_map = {
                "message": "messages-logs",
                "member": "member-logs",
                "moderation": "moderation-logs",
                "voice": "voice-logs",
                "channel": "channel-logs",
                "role": "role-logs",
                "command": "command-logs",
                "error": "error-logs",
            }

            data = {"guild_id": interaction.guild_id}
            for key, name in channel_map.items():
                ch = await interaction.guild.create_text_channel(name, category=category_channel)
                data[key] = ch.id

            await collection.update_one(
                {"guild_id": interaction.guild_id},
                {"$set": data},
                upsert=True
            )

            await interaction.followup.send(
                embed=self.embed(
                    "✅ [ LOG SYSTEM DEPLOYED ]",
                    "```yaml\nCATEGORY: kio-logs\nCHANNELS: 8 created\nSTATUS: All events will be logged automatically.\n```"))
        else:
            data = await collection.find_one({"guild_id": interaction.guild_id})
            if data is None:
                data = {"guild_id": interaction.guild_id}
            data[category] = channel.id

            await collection.update_one(
                {"guild_id": interaction.guild_id},
                {"$set": data},
                upsert=True
            )

            await interaction.response.send_message(
                embed=self.embed(
                    "✅ [ LOG CATEGORY SET ]",
                    f"```yaml\nCATEGORY: {category.capitalize()}\nCHANNEL: #{channel.name}\nSTATUS: Logs will be sent here.\n```"))

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild:
            return
        if message.author and message.author.bot:
            return

        author = f"{message.author}" if message.author else "Unknown#0000"
        content = message.content if hasattr(message, 'content') and message.content else "[Content not available]"
        await self.send_log(message.guild, "message",
            "🗑️ [ MESSAGE DELETED ]",
            f"```yaml\nAUTHOR: {author}\nCHANNEL: #{message.channel.name}\nCONTENT: {content[:500]}\n```")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild:
            return
        if before.author and before.author.bot:
            return
        if before.content == after.content:
            return

        old = before.content if hasattr(before, 'content') and before.content else "[Not cached]"
        new = after.content if after.content else "[Empty]"

        await self.send_log(after.guild, "message",
            "✏️ [ MESSAGE EDITED ]",
            f"```yaml\nAUTHOR: {after.author}\nCHANNEL: #{after.channel.name}\nBEFORE: {old[:500]}\nAFTER:  {new[:500]}\n```")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        created = member.created_at.strftime("%Y-%m-%d %H:%M:%S")
        age = (datetime.datetime.now(datetime.timezone.utc) - member.created_at).days
        await self.send_log(member.guild, "member",
            "📥 [ MEMBER JOINED ]",
            f"```yaml\nUSER: {member} ({member.id})\nACCOUNT: {created} ({age} days old)\nMEMBERS: {member.guild.member_count}\n```")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.send_log(member.guild, "member",
            "📤 [ MEMBER LEFT ]",
            f"```yaml\nUSER: {member} ({member.id})\nMEMBERS: {member.guild.member_count}\n```")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.send_log(guild, "moderation",
            "🔨 [ MEMBER BANNED ]",
            f"```yaml\nUSER: {user} ({user.id})\n```")

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.send_log(guild, "moderation",
            "✅ [ MEMBER UNBANNED ]",
            f"```yaml\nUSER: {user} ({user.id})\n```")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        changes = []

        if before.nick != after.nick:
            old_nick = before.nick if before.nick else before.name
            new_nick = after.nick if after.nick else after.name
            changes.append(f"NICK: {old_nick} → {new_nick}")

        if before.roles != after.roles:
            added = [r.mention for r in after.roles if r not in before.roles]
            removed = [r.mention for r in before.roles if r not in after.roles]
            if added:
                changes.append(f"ROLES ADDED: {', '.join(added)}")
            if removed:
                changes.append(f"ROLES REMOVED: {', '.join(removed)}")

        if before.timed_out != after.timed_out:
            status = "Timed out" if after.timed_out else "Timeout removed"
            changes.append(f"TIMEOUT: {status}")

        if not changes:
            return

        await self.send_log(after.guild, "member",
            "👤 [ MEMBER UPDATED ]",
            f"```yaml\nUSER: {after} ({after.id})\nCHANGES:\n" + "\n".join(changes) + "\n```")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        if before.channel == after.channel:
            return

        if before.channel is None:
            await self.send_log(member.guild, "voice",
                "🔊 [ VOICE JOIN ]",
                f"```yaml\nUSER: {member} ({member.id})\nCHANNEL: {after.channel.name}\n```")
        elif after.channel is None:
            await self.send_log(member.guild, "voice",
                "🔇 [ VOICE LEAVE ]",
                f"```yaml\nUSER: {member} ({member.id})\nCHANNEL: {before.channel.name}\n```")
        else:
            await self.send_log(member.guild, "voice",
                "🔀 [ VOICE MOVE ]",
                f"```yaml\nUSER: {member} ({member.id})\nFROM: {before.channel.name}\nTO: {after.channel.name}\n```")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.send_log(channel.guild, "channel",
            "📝 [ CHANNEL CREATED ]",
            f"```yaml\nNAME: #{channel.name}\nTYPE: {str(channel.type)}\nID: {channel.id}\n```")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.send_log(channel.guild, "channel",
            "🗑️ [ CHANNEL DELETED ]",
            f"```yaml\nNAME: #{channel.name}\nTYPE: {str(channel.type)}\nID: {channel.id}\n```")

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        changes = []

        if before.name != after.name:
            changes.append(f"NAME: #{before.name} → #{after.name}")

        if hasattr(before, 'topic') and before.topic != after.topic:
            old = before.topic[:200] if before.topic else "[None]"
            new = after.topic[:200] if after.topic else "[None]"
            changes.append(f"TOPIC: {old} → {new}")

        if not changes:
            return

        await self.send_log(after.guild, "channel",
            "✏️ [ CHANNEL UPDATED ]",
            f"```yaml\nCHANNEL: #{after.name}\nCHANGES:\n" + "\n".join(changes) + "\n```")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self.send_log(role.guild, "role",
            "🆕 [ ROLE CREATED ]",
            f"```yaml\nNAME: {role.name}\nID: {role.id}\nCOLOR: #{role.color.value:06x}\n```")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.send_log(role.guild, "role",
            "🗑️ [ ROLE DELETED ]",
            f"```yaml\nNAME: {role.name}\nID: {role.id}\n```")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        changes = []

        if before.name != after.name:
            changes.append(f"NAME: {before.name} → {after.name}")

        if before.color != after.color:
            old = f"#{before.color.value:06x}" if before.color.value != 0 else "None"
            new = f"#{after.color.value:06x}" if after.color.value != 0 else "None"
            changes.append(f"COLOR: {old} → {new}")

        if before.hoist != after.hoist:
            changes.append(f"DISPLAY SEPARATELY: {before.hoist} → {after.hoist}")

        if before.mentionable != after.mentionable:
            changes.append(f"MENTIONABLE: {before.mentionable} → {after.mentionable}")

        if not changes:
            return

        await self.send_log(after.guild, "role",
            "✏️ [ ROLE UPDATED ]",
            f"```yaml\nROLE: {after.name} ({after.id})\nCHANGES:\n" + "\n".join(changes) + "\n```")

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction, command):
        if not interaction.guild:
            return

        options = []
        if interaction.data and interaction.data.options:
            for opt in interaction.data.options:
                if opt.value is not None:
                    options.append(f"{opt.name}: {opt.value}")

        opt_text = f"\nOPTIONS: {', '.join(options)}" if options else ""

        await self.send_log(interaction.guild, "command",
            "💻 [ COMMAND USED ]",
            f"```yaml\nUSER: {interaction.user} ({interaction.user.id})\nCOMMAND: /{command.name}{opt_text}\nCHANNEL: #{interaction.channel.name}\n```")

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        import traceback
        error = traceback.format_exc()

        guild = None
        for arg in args:
            if hasattr(arg, 'guild'):
                guild = arg.guild
                break

        if guild:
            await self.send_log(guild, "error",
                "⚠️ [ ERROR ]",
                f"```yaml\nEVENT: {event}\n```\n```prolog\n{error[:1500]}\n```")


async def setup(bot):
    await bot.add_cog(Logger(bot))