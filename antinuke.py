import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
from collections import defaultdict
from colors import COLOR, THUMBNAIL_URL

WINDOW = 5


class Antinuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.actions = defaultdict(list)
        self.punish_cooldown = {}
        self.lockdowns = set()

    async def cog_load(self):
        self.bot.loop.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(60)
            now = datetime.datetime.now(datetime.timezone.utc).timestamp()
            cutoff = now - WINDOW
            for key in list(self.actions.keys()):
                self.actions[key] = [t for t in self.actions[key] if t > cutoff]
                if not self.actions[key]:
                    del self.actions[key]
            pc_cutoff = now - 30
            for key in list(self.punish_cooldown.keys()):
                if self.punish_cooldown[key] < pc_cutoff:
                    del self.punish_cooldown[key]

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

    def get_collection(self):
        mongo_db = getattr(self.bot, "mongo_db", None)
        return mongo_db["antinuke"] if mongo_db is not None else None

    async def ensure_config(self, guild_id):
        collection = self.get_collection()
        if collection is not None:
            config = await collection.find_one({"guild_id": guild_id})
            if config:
                config["whitelist"] = config.get("whitelist") or []
                config["trusted_roles"] = config.get("trusted_roles") or []
                config["extra_owners"] = config.get("extra_owners") or []
                config["main_roles"] = config.get("main_roles") or []
                config.setdefault("antinuke_role_id", None)
                config.setdefault("nightmode", False)
                return config
        config = {
            "guild_id": guild_id,
            "enabled": False,
            "punishment": "kick",
            "channel_create": 1,
            "channel_delete": 1,
            "role_create": 1,
            "role_delete": 1,
            "ban": 1,
            "kick": 1,
            "member_role_update": 1,
            "guild_update": 1,
            "webhook_create": 1,
            "webhook_delete": 1,
            "whitelist": [],
            "trusted_roles": [],
            "extra_owners": [],
            "main_roles": [],
            "antinuke_role_id": None,
            "nightmode": False,
            "nightmode_roles": {},
            "punishment_log_channel": None,
        }
        if collection is not None:
            await collection.insert_one(config)
        return config

    async def save_config(self, guild_id, config):
        collection = self.get_collection()
        if collection is not None:
            await collection.update_one({"guild_id": guild_id}, {"$set": config}, upsert=True)

    def is_protected(self, config, guild, user):
        if user.id == guild.owner_id:
            return True
        if user.id == self.bot.user.id:
            return True
        if user.id in (config.get("whitelist") or []):
            return True
        if user.id in (config.get("extra_owners") or []):
            return True
        if isinstance(user, discord.Member):
            trusted = config.get("trusted_roles") or []
            if any(r.id in trusted for r in user.roles):
                return True
        return False

    def is_authorized(self, interaction, config):
        if interaction.user.id == interaction.guild.owner_id:
            return True
        if interaction.user.id in (config.get("extra_owners") or []):
            return True
        return False

    async def on_punish_cooldown(self, guild_id, user_id):
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        key = (guild_id, user_id)
        last = self.punish_cooldown.get(key, 0)
        if now - last < 30:
            return True
        self.punish_cooldown[key] = now
        return False

    async def alert_owner(self, guild, user, action_type, punishment):
        owner = guild.owner
        if not owner:
            return
        try:
            await owner.send(embed=self.embed(
                "🛡️ [ ANTINUKE ALERT ]",
                f"```yaml\nGUILD: {guild.name} ({guild.id})\nUSER: {user} ({user.id})\nACTION: {action_type}\nPUNISHMENT: {punishment}\n```"))
        except:
            pass

    async def check_and_punish(self, guild, user, action_type, config):
        print(f"[ANTINUKE] check_and_punish called — guild={guild.id} user={user.id} action={action_type}")
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        key = (guild.id, user.id, action_type)
        self.actions[key].append(now)
        cutoff = now - WINDOW
        self.actions[key] = [t for t in self.actions[key] if t > cutoff]
        threshold = config.get(action_type, 5)
        count = len(self.actions[key])
        print(f"[ANTINUKE] action count={count}/{threshold} for {action_type}")
        if count < threshold:
            return
        if await self.on_punish_cooldown(guild.id, user.id):
            print(f"[ANTINUKE] punish cooldown active for {user.id}")
            return
        punishments = ["ban", "striproles", "kick"]
        chosen = config.get("punishment", "kick")
        punishments.remove(chosen)
        punishments.insert(0, chosen)
        applied = None
        reason = f"Antinuke: {action_type} threshold exceeded"
        member = guild.get_member(user.id)
        for p in punishments:
            try:
                if p == "ban":
                    await guild.ban(user, reason=reason)
                elif p == "striproles":
                    if member:
                        await member.edit(roles=[], reason=reason)
                    else:
                        continue
                else:
                    if member:
                        await guild.kick(member, reason=reason)
                    else:
                        continue
                applied = p
                print(f"[ANTINUKE] Punishment applied: {p} to {user.id}")
                break
            except Exception as ex:
                print(f"[ANTINUKE] Punishment {p} failed for {user.id}: {ex}")
                continue
        if applied is None:
            await self.lockdown_guild(guild)
            applied = "lockdown (all punishments failed)"
        self.bot.loop.create_task(self.alert_owner(guild, user, action_type, applied))
        log_channel_id = config.get("punishment_log_channel")
        if log_channel_id:
            channel = guild.get_channel(log_channel_id)
            if channel:
                await channel.send(embed=self.embed(
                    "🛡️ [ ANTINUKE ACTION ]",
                    f"```yaml\nUSER: {user} ({user.id})\nACTION: {action_type}\nPUNISHMENT: {applied}\n```"))

    async def lockdown_guild(self, guild):
        self.lockdowns.add(guild.id)
        for channel in guild.channels:
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                try:
                    await channel.set_permissions(guild.default_role, send_messages=False, speak=False, create_instant_invite=False)
                except:
                    pass

    async def unlock_guild(self, guild):
        self.lockdowns.discard(guild.id)
        for channel in guild.channels:
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                try:
                    await channel.set_permissions(guild.default_role, send_messages=None, speak=None, create_instant_invite=None)
                except:
                    pass

    async def setup_role(self, guild, config):
        role_id = config.get("antinuke_role_id")
        role = guild.get_role(role_id) if role_id else None
        if role is None:
            role = await guild.create_role(
                name="Kio Antinuke",
                color=discord.Color(COLOR),
                hoist=False,
                mentionable=False,
                permissions=discord.Permissions(administrator=True),
                reason="Antinuke: creating hierarchy role"
            )
            config["antinuke_role_id"] = role.id
            await self.save_config(guild.id, config)
        else:
            if not role.permissions.administrator:
                await role.edit(permissions=discord.Permissions(administrator=True))
        return role

    async def resolve_user(self, guild, audit_action):
        try:
            async for entry in guild.audit_logs(action=audit_action, limit=1):
                return entry.user
        except:
            pass
        return None

    # ── Event Listeners ──

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild = channel.guild
        if not guild:
            return
        config = await self.ensure_config(guild.id)
        if not config.get("enabled"):
            return
        user = await self.resolve_user(guild, discord.AuditLogAction.channel_create)
        if not user:
            print(f"[ANTINUKE] on_guild_channel_create — could not resolve user from audit log")
            return
        if self.is_protected(config, guild, user):
            print(f"[ANTINUKE] on_guild_channel_create — user {user.id} is protected")
            return
        await self.check_and_punish(guild, user, "channel_create", config)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        if not guild:
            return
        config = await self.ensure_config(guild.id)
        if not config.get("enabled"):
            return
        user = await self.resolve_user(guild, discord.AuditLogAction.channel_delete)
        if not user:
            print(f"[ANTINUKE] on_guild_channel_delete — could not resolve user")
            return
        if self.is_protected(config, guild, user):
            return
        await self.check_and_punish(guild, user, "channel_delete", config)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        guild = role.guild
        if not guild:
            return
        config = await self.ensure_config(guild.id)
        if not config.get("enabled"):
            return
        user = await self.resolve_user(guild, discord.AuditLogAction.role_create)
        if not user:
            print(f"[ANTINUKE] on_guild_role_create — could not resolve user")
            return
        if self.is_protected(config, guild, user):
            return
        await self.check_and_punish(guild, user, "role_create", config)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild = role.guild
        if not guild:
            return
        config = await self.ensure_config(guild.id)
        if not config.get("enabled"):
            return
        user = await self.resolve_user(guild, discord.AuditLogAction.role_delete)
        if not user:
            print(f"[ANTINUKE] on_guild_role_delete — could not resolve user")
            return
        if self.is_protected(config, guild, user):
            return
        await self.check_and_punish(guild, user, "role_delete", config)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if not guild:
            return
        config = await self.ensure_config(guild.id)
        if not config.get("enabled"):
            return
        banner = await self.resolve_user(guild, discord.AuditLogAction.ban)
        if not banner or self.is_protected(config, guild, banner):
            return
        await self.check_and_punish(guild, banner, "ban", config)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        if not guild:
            return
        config = await self.ensure_config(guild.id)
        if not config.get("enabled"):
            return
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
                if not entry.target or entry.target.id != member.id:
                    break
                diff = (datetime.datetime.now(datetime.timezone.utc) - entry.created_at).total_seconds()
                if diff > 3:
                    break
                user = entry.user
                if user and not self.is_protected(config, guild, user):
                    await self.check_and_punish(guild, user, "kick", config)
                break
        except:
            pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles == after.roles:
            return
        guild = after.guild
        if not guild:
            return
        config = await self.ensure_config(guild.id)
        if not config.get("enabled"):
            return
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=1):
                user = entry.user
                if user and not self.is_protected(config, guild, user):
                    await self.check_and_punish(guild, user, "member_role_update", config)
                break
        except:
            pass

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        if before.name == after.name and before.icon == after.icon and before.banner == after.banner:
            return
        guild = after
        config = await self.ensure_config(guild.id)
        if not config.get("enabled"):
            return
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.guild_update, limit=1):
                user = entry.user
                if user and not self.is_protected(config, guild, user):
                    await self.check_and_punish(guild, user, "guild_update", config)
                break
        except:
            pass

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        guild = channel.guild
        if not guild:
            return
        config = await self.ensure_config(guild.id)
        if not config.get("enabled"):
            return
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.webhook_create, limit=1):
                diff = (datetime.datetime.now(datetime.timezone.utc) - entry.created_at).total_seconds()
                if diff > 3:
                    break
                user = entry.user
                if user and not self.is_protected(config, guild, user):
                    await self.check_and_punish(guild, user, "webhook_create", config)
                break
        except:
            pass
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.webhook_delete, limit=1):
                diff = (datetime.datetime.now(datetime.timezone.utc) - entry.created_at).total_seconds()
                if diff > 3:
                    break
                user = entry.user
                if user and not self.is_protected(config, guild, user):
                    await self.check_and_punish(guild, user, "webhook_delete", config)
                break
        except:
            pass

    # ── Slash Commands ──

    antinuke = app_commands.Group(name="antinuke", description="Configure antinuke protection")

    @antinuke.command(name="toggle", description="Enable or disable antinuke protection")
    async def toggle(self, interaction: discord.Interaction, state: bool):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners can toggle antinuke.\n```")
        if state:
            if config.get("enabled"):
                return await self.send(interaction, "❌ [ ALREADY ENABLED ]", "```yaml\nSTATUS: Antinuke is already enabled.\n```")
            await interaction.response.defer()
            await self.setup_role(interaction.guild, config)
            config["pending_setup"] = True
            self.actions = defaultdict(list)
            await self.save_config(interaction.guild_id, config)
            await self.send(interaction, "🛡️ [ ANTINUKE SETUP ]",
                "```yaml\nSTATUS: Role created with ADMIN permissions.\n```\n"
                "➜ Go to **Server Settings → Roles** and drag **Kio Antinuke** above all staff/mods/admin roles.\n"
                "➜ Then run **`/antinuke confirm`** to finish enabling.")
        else:
            config["enabled"] = False
            config["pending_setup"] = False
            self.actions = defaultdict(list)
            await self.save_config(interaction.guild_id, config)
            await self.send(interaction, "🛡️ [ ANTINUKE DISABLED ]", "```yaml\nSTATUS: Disabled\n```")

    @antinuke.command(name="confirm", description="Confirm antinuke setup after manually moving the role")
    async def confirm(self, interaction: discord.Interaction):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners can confirm antinuke.\n```")
        if config.get("enabled"):
            return await self.send(interaction, "❌ [ ALREADY ENABLED ]", "```yaml\nSTATUS: Antinuke is already enabled.\n```")
        if not config.get("pending_setup"):
            return await self.send(interaction, "❌ [ NO PENDING SETUP ]", "```yaml\nSTATUS: Run /antinuke toggle True first.\n```")
        await interaction.response.defer()
        role_id = config.get("antinuke_role_id")
        role = interaction.guild.get_role(role_id) if role_id else None
        if role is None:
            return await self.send(interaction, "❌ [ ROLE NOT FOUND ]", "```diff\n- ERROR: Kio Antinuke role was deleted. Run /antinuke toggle True again.\n```")
        if role not in interaction.guild.me.roles:
            await interaction.guild.me.add_roles(role, reason="Antinuke: assigning hierarchy role")
        config["pending_setup"] = False
        config["enabled"] = True
        self.actions = defaultdict(list)
        await self.save_config(interaction.guild_id, config)
        await self.send(interaction, "🛡️ [ ANTINUKE ENABLED ]",
            "```yaml\nSTATUS: Enabled\nROLE: Kio Antinuke is now active at the top of the hierarchy.\n```")

    @antinuke.command(name="punishment", description="Set the punishment for rule violators")
    @app_commands.choices(punishment=[
        app_commands.Choice(name="Kick", value="kick"),
        app_commands.Choice(name="Ban", value="ban"),
        app_commands.Choice(name="Strip Roles", value="striproles"),
    ])
    async def set_punishment(self, interaction: discord.Interaction, punishment: str):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners.\n```")
        config["punishment"] = punishment
        await self.save_config(interaction.guild_id, config)
        await self.send(interaction, "🛡️ [ PUNISHMENT SET ]", f"```yaml\nPUNISHMENT: {punishment}\n```")

    @antinuke.command(name="threshold", description="Set the action threshold per 5 seconds")
    @app_commands.choices(action=[
        app_commands.Choice(name="Channel Create", value="channel_create"),
        app_commands.Choice(name="Channel Delete", value="channel_delete"),
        app_commands.Choice(name="Role Create", value="role_create"),
        app_commands.Choice(name="Role Delete", value="role_delete"),
        app_commands.Choice(name="Ban", value="ban"),
        app_commands.Choice(name="Kick", value="kick"),
        app_commands.Choice(name="Member Role Update", value="member_role_update"),
        app_commands.Choice(name="Guild Update", value="guild_update"),
        app_commands.Choice(name="Webhook Create", value="webhook_create"),
        app_commands.Choice(name="Webhook Delete", value="webhook_delete"),
    ])
    async def set_threshold(self, interaction: discord.Interaction, action: str, count: int):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners.\n```")
        if count < 1:
            return await self.send(interaction, "❌ [ INVALID COUNT ]", "```diff\n- ERROR: Count must be at least 1.\n```")
        config[action] = count
        await self.save_config(interaction.guild_id, config)
        await self.send(interaction, "🛡️ [ THRESHOLD SET ]", f"```yaml\nACTION: {action}\nTHRESHOLD: {count} per 5s\n```")

    @antinuke.command(name="whitelist", description="Add or remove a user from the whitelist")
    @app_commands.choices(action=[
        app_commands.Choice(name="Add", value="add"),
        app_commands.Choice(name="Remove", value="remove"),
    ])
    async def whitelist(self, interaction: discord.Interaction, action: str, user: discord.User):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners.\n```")
        whitelist = config.get("whitelist") or []
        if action == "add":
            if user.id in whitelist:
                return await self.send(interaction, "❌ [ ALREADY WHITELISTED ]", "```diff\n- ERROR: That user is already whitelisted.\n```")
            whitelist.append(user.id)
            await self.send(interaction, "🛡️ [ WHITELIST UPDATED ]", f"```yaml\nACTION: Added {user} ({user.id})\n```")
        else:
            if user.id not in whitelist:
                return await self.send(interaction, "❌ [ NOT WHITELISTED ]", "```diff\n- ERROR: That user is not in the whitelist.\n```")
            whitelist.remove(user.id)
            await self.send(interaction, "🛡️ [ WHITELIST UPDATED ]", f"```yaml\nACTION: Removed {user} ({user.id})\n```")
        config["whitelist"] = whitelist
        await self.save_config(interaction.guild_id, config)

    @antinuke.command(name="wlisted", description="List all whitelisted users")
    async def wlisted(self, interaction: discord.Interaction):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners.\n```")
        whitelist = config.get("whitelist") or []
        if not whitelist:
            return await self.send(interaction, "📭 [ WHITELIST ]", "```yaml\nSTATUS: No whitelisted users.\n```")
        mentions = "\n".join(f"✦ <@{uid}> (`{uid}`)" for uid in whitelist)
        await self.send(interaction, "📋 [ WHITELISTED USERS ]",
            f"```yaml\nCOUNT: {len(whitelist)}\n```\n{mentions}")

    @antinuke.command(name="unwhitelist", description="Remove a user from the whitelist")
    async def unwhitelist(self, interaction: discord.Interaction, user: discord.User):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners.\n```")
        whitelist = config.get("whitelist") or []
        if user.id not in whitelist:
            return await self.send(interaction, "❌ [ NOT WHITELISTED ]", "```diff\n- ERROR: That user is not whitelisted.\n```")
        whitelist.remove(user.id)
        config["whitelist"] = whitelist
        await self.save_config(interaction.guild_id, config)
        await self.send(interaction, "🗑️ [ UNWHITELISTED ]", f"```yaml\nUSER: {user} ({user.id})\nSTATUS: Removed from whitelist.\n```")

    @antinuke.command(name="whitelistreset", description="Reset the entire whitelist")
    async def whitelistreset(self, interaction: discord.Interaction):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners.\n```")
        config["whitelist"] = []
        await self.save_config(interaction.guild_id, config)
        await self.send(interaction, "🗑️ [ WHITELIST RESET ]", "```yaml\nSTATUS: All whitelisted users have been removed.\n```")

    @antinuke.command(name="trustedrole", description="Add or remove a trusted role that bypasses antinuke")
    @app_commands.choices(action=[
        app_commands.Choice(name="Add", value="add"),
        app_commands.Choice(name="Remove", value="remove"),
    ])
    async def trustedrole(self, interaction: discord.Interaction, action: str, role: discord.Role):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners.\n```")
        trusted = config.get("trusted_roles") or []
        if action == "add":
            if role.id in trusted:
                return await self.send(interaction, "❌ [ ALREADY TRUSTED ]", "```diff\n- ERROR: That role is already trusted.\n```")
            trusted.append(role.id)
            await self.send(interaction, "🛡️ [ TRUSTED ROLE ADDED ]", f"```yaml\nROLE: {role.name} ({role.id})\n```")
        else:
            if role.id not in trusted:
                return await self.send(interaction, "❌ [ NOT TRUSTED ]", "```diff\n- ERROR: That role is not trusted.\n```")
            trusted.remove(role.id)
            await self.send(interaction, "🛡️ [ TRUSTED ROLE REMOVED ]", f"```yaml\nROLE: {role.name} ({role.id})\n```")
        config["trusted_roles"] = trusted
        await self.save_config(interaction.guild_id, config)

    @antinuke.command(name="extraowner", description="Manage extra owners (max 3)")
    @app_commands.choices(action=[
        app_commands.Choice(name="Add", value="add"),
        app_commands.Choice(name="Remove", value="remove"),
    ])
    async def extraowner(self, interaction: discord.Interaction, action: str, user: discord.User):
        if interaction.user.id != interaction.guild.owner_id:
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only the server owner can manage extra owners.\n```")
        config = await self.ensure_config(interaction.guild_id)
        owners = config.get("extra_owners") or []
        if action == "add":
            if user.id in owners:
                return await self.send(interaction, "❌ [ ALREADY EXTRA OWNER ]", "```diff\n- ERROR: That user is already an extra owner.\n```")
            if len(owners) >= 3:
                return await self.send(interaction, "❌ [ LIMIT REACHED ]", "```diff\n- ERROR: Maximum of 3 extra owners allowed.\n```")
            owners.append(user.id)
            await self.send(interaction, "🛡️ [ EXTRA OWNER ADDED ]", f"```yaml\nUSER: {user} ({user.id})\nREMAINING SLOTS: {2 - len(owners)}\n```")
        else:
            if user.id not in owners:
                return await self.send(interaction, "❌ [ NOT EXTRA OWNER ]", "```diff\n- ERROR: That user is not an extra owner.\n```")
            owners.remove(user.id)
            await self.send(interaction, "🛡️ [ EXTRA OWNER REMOVED ]", f"```yaml\nUSER: {user} ({user.id})\n```")
        config["extra_owners"] = owners
        await self.save_config(interaction.guild_id, config)

    # ── Mainrole ──

    mainrole = app_commands.Group(name="mainrole", description="Configure protected main roles (antinuke)")
    mainrole.parent = antinuke

    @mainrole.command(name="add", description="Add a protected main role (max 5)")
    @app_commands.describe(role="The role to protect")
    async def mainrole_add(self, interaction: discord.Interaction, role: discord.Role):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners.\n```")
        main_roles = config.get("main_roles") or []
        if role.id in main_roles:
            return await self.send(interaction, "❌ [ ALREADY PROTECTED ]", "```diff\n- ERROR: That role is already a main role.\n```")
        if len(main_roles) >= 5:
            return await self.send(interaction, "❌ [ LIMIT REACHED ]", "```diff\n- ERROR: Maximum of 5 main roles allowed.\n```")
        main_roles.append(role.id)
        config["main_roles"] = main_roles
        await self.save_config(interaction.guild_id, config)
        await self.send(interaction, "🛡️ [ MAIN ROLE ADDED ]", f"```yaml\nROLE: {role.name} ({role.id})\nPROTECTED: from deletion, permission changes\n```")

    @mainrole.command(name="remove", description="Remove a protected main role")
    @app_commands.describe(role="The role to unprotect")
    async def mainrole_remove(self, interaction: discord.Interaction, role: discord.Role):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners.\n```")
        main_roles = config.get("main_roles") or []
        if role.id not in main_roles:
            return await self.send(interaction, "❌ [ NOT PROTECTED ]", "```diff\n- ERROR: That role is not a main role.\n```")
        main_roles.remove(role.id)
        config["main_roles"] = main_roles
        await self.save_config(interaction.guild_id, config)
        await self.send(interaction, "🛡️ [ MAIN ROLE REMOVED ]", f"```yaml\nROLE: {role.name} ({role.id})\nSTATUS: Protection removed.\n```")

    @mainrole.command(name="list", description="List all protected main roles")
    async def mainrole_list(self, interaction: discord.Interaction):
        config = await self.ensure_config(interaction.guild_id)
        main_roles = config.get("main_roles") or []
        if not main_roles:
            return await self.send(interaction, "📭 [ MAIN ROLES ]", "```yaml\nSTATUS: No protected main roles configured.\n```")
        mentions = "\n".join(f"✦ <@&{rid}> (`{rid}`)" for rid in main_roles)
        await self.send(interaction, "📋 [ PROTECTED MAIN ROLES ]",
            f"```yaml\nCOUNT: {len(main_roles)}/5\n```\n{mentions}")

    @mainrole.command(name="reset", description="Reset all protected main roles")
    async def mainrole_reset(self, interaction: discord.Interaction):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners.\n```")
        config["main_roles"] = []
        await self.save_config(interaction.guild_id, config)
        await self.send(interaction, "🗑️ [ MAIN ROLES RESET ]", "```yaml\nSTATUS: All main roles have been cleared.\n```")

    # ── Nightmode ──

    @antinuke.command(name="nightmode", description="Toggle nightmode — strips ADMIN from all manageable roles")
    async def nightmode(self, interaction: discord.Interaction):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners.\n```")
        await interaction.response.defer()

        if config.get("nightmode"):
            nightmode_roles = config.get("nightmode_roles") or {}
            restored = 0
            for role_id_str, perms_value in nightmode_roles.items():
                role = interaction.guild.get_role(int(role_id_str))
                if role:
                    try:
                        await role.edit(permissions=discord.Permissions(perms_value), reason="Nightmode: restoring permissions")
                        restored += 1
                    except:
                        pass
            config["nightmode"] = False
            config["nightmode_roles"] = {}
            await self.save_config(interaction.guild_id, config)
            await self.send(interaction,
                "🌙 [ NIGHTMODE DISABLED ]",
                f"```yaml\nROLES RESTORED: {restored}\nSTATUS: Administrative permissions restored.\n```")
        else:
            saved = {}
            stripped = 0
            for role in interaction.guild.roles:
                if role.permissions.administrator and role < interaction.guild.me.top_role and not role.is_default() and role != interaction.guild.me.top_role:
                    saved[str(role.id)] = role.permissions.value
                    try:
                        await role.edit(permissions=discord.Permissions.none(), reason="Nightmode: stripping ADMIN permissions")
                        stripped += 1
                    except:
                        pass
            config["nightmode"] = True
            config["nightmode_roles"] = saved
            await self.save_config(interaction.guild_id, config)
            await self.send(interaction,
                "🌙 [ NIGHTMODE ENABLED ]",
                f"```yaml\nROLES STRIPPED: {stripped}\nSTATUS: All ADMIN permissions below the bot's top role have been removed.\nUse /antinuke nightmode again to restore.\n```")

    # ── Config View ──

    @antinuke.command(name="config", description="View the antinuke configuration")
    async def view_config(self, interaction: discord.Interaction):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners.\n```")
        whitelist_mentions = "\n".join(f"✦ <@{uid}>" for uid in (config.get("whitelist") or [])) or "None"
        trusted_mentions = "\n".join(f"✦ <@&{rid}>" for rid in (config.get("trusted_roles") or [])) or "None"
        extra_mentions = "\n".join(f"✦ <@{uid}>" for uid in (config.get("extra_owners") or [])) or "None"
        mainrole_mentions = "\n".join(f"✦ <@&{rid}>" for rid in (config.get("main_roles") or [])) or "None"
        await self.send(interaction, "🛡️ [ ANTINUKE CONFIGURATION ]",
            f"```yaml\nENABLED: {config['enabled']}\nPUNISHMENT: {config['punishment']}\nNIGHTMODE: {config.get('nightmode', False)}\n\nTHRESHOLDS (per 5s):\n  Channel Create: {config['channel_create']}\n  Channel Delete: {config['channel_delete']}\n  Role Create: {config['role_create']}\n  Role Delete: {config['role_delete']}\n  Ban: {config['ban']}\n  Kick: {config['kick']}\n  Member Role Update: {config['member_role_update']}\n  Guild Update: {config['guild_update']}\n  Webhook Create: {config.get('webhook_create', 3)}\n  Webhook Delete: {config.get('webhook_delete', 3)}\n```\n**Extra Owners:**\n{extra_mentions}\n\n**Whitelisted Users:**\n{whitelist_mentions}\n\n**Trusted Roles:**\n{trusted_mentions}\n\n**Protected Main Roles:**\n{mainrole_mentions}")

    @antinuke.command(name="logchannel", description="Set the log channel for antinuke actions")
    async def logchannel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners.\n```")
        config["punishment_log_channel"] = channel.id if channel else None
        await self.save_config(interaction.guild_id, config)
        await self.send(interaction, "🛡️ [ LOG CHANNEL SET ]",
            f"```yaml\nCHANNEL: #{channel.name if channel else 'Disabled'}\n```")

    @antinuke.command(name="lockdown", description="Lock down all channels in an emergency")
    async def lockdown(self, interaction: discord.Interaction):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners.\n```")
        if interaction.guild_id in self.lockdowns:
            return await self.send(interaction, "❌ [ ALREADY LOCKED ]", "```diff\n- ERROR: Server is already in lockdown.\n```")
        await interaction.response.defer()
        await self.lockdown_guild(interaction.guild)
        await self.send(interaction, "🔒 [ LOCKDOWN ENGAGED ]",
            "```yaml\nSTATUS: All channels locked\n@everyone: send_messages, speak denied\n\nUse /antinuke unlock to restore.\n```")

    @antinuke.command(name="unlock", description="Unlock all channels after a lockdown")
    async def unlock(self, interaction: discord.Interaction):
        config = await self.ensure_config(interaction.guild_id)
        if not self.is_authorized(interaction, config):
            return await self.send(interaction, "❌ [ ACCESS DENIED ]", "```diff\n- ERROR: Only server owner and extra owners.\n```")
        if interaction.guild_id not in self.lockdowns:
            return await self.send(interaction, "❌ [ NOT LOCKED ]", "```diff\n- ERROR: Server is not in lockdown.\n```")
        await interaction.response.defer()
        await self.unlock_guild(interaction.guild)
        await self.send(interaction, "🔓 [ LOCKDOWN LIFTED ]",
            "```yaml\nSTATUS: All channels unlocked\nPermissions restored to default.\n```")


async def setup(bot):
    await bot.add_cog(Antinuke(bot))
