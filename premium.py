import discord
from discord.ext import commands
from discord import app_commands
import datetime
from colors import COLOR, THUMBNAIL_URL

own = 1491790586166902874


class Premium(commands.Cog):
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

    def get_collection(self):
        mongo_db = getattr(self.bot, "mongo_db", None)
        return mongo_db["premium"] if mongo_db is not None else None

    def is_owner(self, interaction):
        return interaction.user.id == own

    @app_commands.command(name="addpremium", description="Add premium to a user (owner only)")
    @app_commands.describe(user_id="User ID to grant premium", days="Duration in days")
    async def addpremium(self, interaction: discord.Interaction, user_id: str, days: int = 30):
        if not self.is_owner(interaction):
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Permission denied.\n```")
        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "```diff\n- ERROR: MongoDB not configured.\n```")
        try:
            uid = int(user_id)
        except ValueError:
            return await self.send(interaction, "❌ [ INVALID ID ]", "```diff\n- ERROR: User ID must be numeric.\n```")
        expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)
        await collection.update_one(
            {"user_id": uid},
            {"$set": {
                "user_id": uid,
                "active": True,
                "expires_at": expires,
                "granted_by": interaction.user.id,
                "granted_at": datetime.datetime.now(datetime.timezone.utc)
            }},
            upsert=True
        )
        await self.send(interaction,
            "⭐ [ PREMIUM GRANTED ]",
            f"```yaml\nUSER ID: {uid}\nDURATION: {days} days\nEXPIRES: {expires.strftime('%Y-%m-%d %H:%M:%S')}\n```")

    @app_commands.command(name="premium", description="Manage premium subscriptions (owner only)")
    @app_commands.describe(action="Action to perform", user_id="User ID (required for check/revoke)")
    @app_commands.choices(action=[
        app_commands.Choice(name="Check", value="check"),
        app_commands.Choice(name="Revoke", value="revoke"),
        app_commands.Choice(name="Stats", value="stats"),
    ])
    async def premium(self, interaction: discord.Interaction, action: str, user_id: str = None):
        if not self.is_owner(interaction):
            return await self.send(interaction, "❌ [ ACCESS RESTRICTED ]",
                "```diff\n- ERROR: Permission denied.\n```")
        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "```diff\n- ERROR: MongoDB not configured.\n```")

        if action == "stats":
            total = await collection.count_documents({})
            active = await collection.count_documents({"active": True})
            await self.send(interaction,
                "📊 [ PREMIUM STATS ]",
                f"```yaml\nTOTAL GRANTS: {total}\nACTIVE: {active}\nEXPIRED: {total - active}\n```")
            return

        if user_id is None:
            return await self.send(interaction, "❌ [ MISSING USER ID ]", "```diff\n- ERROR: user_id required for this action.\n```")
        try:
            uid = int(user_id)
        except ValueError:
            return await self.send(interaction, "❌ [ INVALID ID ]", "```diff\n- ERROR: User ID must be numeric.\n```")

        if action == "check":
            data = await collection.find_one({"user_id": uid})
            if data and data.get("active"):
                exp = data.get("expires_at")
                remaining = (exp - datetime.datetime.now(datetime.timezone.utc)).days if exp else "Unknown"
                await self.send(interaction,
                    "⭐ [ PREMIUM STATUS ]",
                    f"```yaml\nUSER ID: {uid}\nSTATUS: Active\nEXPIRES: {exp.strftime('%Y-%m-%d %H:%M:%S') if exp else 'N/A'}\nDAYS REMAINING: {remaining}\n```")
            else:
                await self.send(interaction,
                    "❌ [ NOT PREMIUM ]",
                    f"```yaml\nUSER ID: {uid}\nSTATUS: No active premium subscription.\n```")

        elif action == "revoke":
            result = await collection.update_one({"user_id": uid}, {"$set": {"active": False}})
            if result.modified_count:
                await self.send(interaction,
                    "🗑️ [ PREMIUM REVOKED ]",
                    f"```yaml\nUSER ID: {uid}\nSTATUS: Premium access revoked.\n```")
            else:
                await self.send(interaction,
                    "❌ [ NOT FOUND ]",
                    f"```yaml\nUSER ID: {uid}\nSTATUS: No premium record found.\n```")


async def setup(bot):
    await bot.add_cog(Premium(bot))
