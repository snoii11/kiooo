import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import motor.motor_asyncio
import asyncio
import json
from colors import COLOR, THUMBNAIL_URL

load_dotenv()
token = os.getenv('TOKEN')
mongo_uri = os.getenv('MONGO_URI')
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
    mongo_uri,
    serverSelectionTimeoutMS=5000,
) if mongo_uri else None
mongo_db = mongo_client["kio"] if mongo_client is not None else None
test_guild_id = os.getenv('TEST_GUILD_ID')
test_guild = discord.Object(id=int(test_guild_id)) if test_guild_id else None

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix='k.', intents=intents, case_insensitive=True)
bot.db = {}

db_lock = asyncio.Lock()

DEFAULTS = {
    "np_list": [],
    "noprefix_access": [],
    "warnings": {},
    "balances": {},
    "last_work": {},
}


async def load_data():
    global bot
    if mongo_db is None:
        bot.db = DEFAULTS.copy()
        print("[WARN] MONGO_URI not set — config is in-memory only")
        return

    doc = await mongo_db["config"].find_one({"_id": "config"})
    if doc is not None:
        doc.pop("_id", None)
        db = DEFAULTS.copy()
        db.update(doc)
        bot.db = db
        print("[INFO] Config loaded from MongoDB")
        return

    try:
        with open("data.json", "r") as f:
            legacy = json.load(f)
        db = DEFAULTS.copy()
        db.update({k: v for k, v in legacy.items() if k in DEFAULTS})
        await mongo_db["config"].insert_one({"_id": "config", **db})
        bot.db = db
        print("[INFO] Migrated data.json → MongoDB")
        os.remove("data.json")
        print("[INFO] Removed data.json")
    except (FileNotFoundError, json.JSONDecodeError):
        db = DEFAULTS.copy()
        await mongo_db["config"].insert_one({"_id": "config", **db})
        bot.db = db
        print("[INFO] Created fresh config in MongoDB")


async def save_data():
    if mongo_db is None:
        print("[WARN] Cannot save config — MONGO_URI not set")
        return
    async with db_lock:
        await mongo_db["config"].update_one(
            {"_id": "config"},
            {"$set": bot.db}
        )
bot.save_data = save_data


@bot.event
async def on_ready():
    bot.start_time = datetime.datetime.now(datetime.timezone.utc)
    await bot.change_presence(activity=discord.Streaming(name="kiooo", url="https://twitch.tv/bdwoa"))
    print(f"{bot.user} is now online")
    print(f"Loaded Cogs: {bot.cogs}")

    try:
        if test_guild:
            bot.tree.copy_global_to(guild=test_guild)
            await bot.tree.sync(guild=test_guild)
            print(f"Synced commands to test guild {test_guild_id}")
        else:
            await bot.tree.sync()
            print("Synced commands globally")
    except Exception as e:
        print(f"[WARN] Command sync failed (rate-limited?): {e}")


@bot.tree.error
async def on_tree_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="⏳ [ COOLDOWN ACTIVE ]",
                description=f"```yaml\nTry again in {error.retry_after:.1f}s\n```",
                color=COLOR).set_thumbnail(url=THUMBNAIL_URL), ephemeral=True)

    if isinstance(error, app_commands.MissingPermissions):
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ [ ACCESS RESTRICTED ]",
                description="```diff\n- ERROR: Permission denied.\n```",
                color=COLOR).set_thumbnail(url=THUMBNAIL_URL), ephemeral=True)

    if isinstance(error, app_commands.BotMissingPermissions):
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ [ BOT PERMISSION ERROR ]",
                description=f"```diff\n- ERROR: I need the following permissions: {', '.join(error.missing_permissions)}\n```",
                color=COLOR).set_thumbnail(url=THUMBNAIL_URL), ephemeral=True)

    if isinstance(error, app_commands.TransformerError):
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ [ INVALID ARGUMENT ]",
                description=f"```yaml\nERROR: Could not parse argument.\n```",
                color=COLOR).set_thumbnail(url=THUMBNAIL_URL), ephemeral=True)

    print(f"Unhandled tree error: {error}")
    try:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ [ OPERATIONAL ERROR ]",
                description="```diff\n- ERROR: An unexpected error occurred.\n```",
                color=COLOR).set_thumbnail(url=THUMBNAIL_URL), ephemeral=True)
    except:
        pass


# ── AFK Detection ──

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # Check blacklist
    if mongo_db is not None:
        blacklisted = await mongo_db["blacklist"].find_one({"user_id": message.author.id})
        if blacklisted:
            return

    # AFK: remove AFK when user sends a message
    afk_col = mongo_db["afk"] if mongo_db is not None else None
    if afk_col is not None:
        result = await afk_col.delete_one({"guild_id": message.guild.id, "user_id": message.author.id})
        if result.deleted_count:
            try:
                e = discord.Embed(
                    title="🌙 [ WELCOME BACK ]",
                    description="```yaml\nSTATUS: Your AFK status has been automatically removed.\n```",
                    color=COLOR)
                e.set_thumbnail(url=THUMBNAIL_URL)
                await message.channel.send(embed=e, delete_after=5)
            except:
                pass

    # AFK: notify if mentioning an AFK user
    if afk_col is not None and message.mentions:
        for mentioned in message.mentions:
            if mentioned.bot:
                continue
            afk_data = await afk_col.find_one({"guild_id": message.guild.id, "user_id": mentioned.id})
            if afk_data:
                reason = afk_data.get("reason", "AFK")
                try:
                    e = discord.Embed(
                        title="🌙 [ AFK NOTICE ]",
                        description=f"```yaml\nUSER: {mentioned.display_name}\nREASON: {reason}\n```",
                        color=COLOR)
                    e.set_thumbnail(url=THUMBNAIL_URL)
                    await message.channel.send(embed=e, delete_after=5)
                except:
                    pass

    await bot.process_commands(message)


# ── Boost Detection ──

@bot.event
async def on_member_update(before, after):
    if before.premium_since is None and after.premium_since is not None:
        if mongo_db is None:
            return
        boost_data = await mongo_db["boost"].find_one({"guild_id": after.guild.id})
        if boost_data:
            channel_id = boost_data.get("channel_id")
            if channel_id:
                channel = after.guild.get_channel(channel_id)
                if channel:
                    e = discord.Embed(
                        title="⚡ [ BOOST DETECTED ]",
                        description=f"```yaml\nUSER: {after} ({after.id})\nSTATUS: Thank you for boosting!\n```",
                        color=COLOR)
                    e.set_thumbnail(url=THUMBNAIL_URL)
                    e.set_footer(text="Kiooo", icon_url=bot.user.display_avatar.url)
                    e.timestamp = datetime.datetime.now(datetime.timezone.utc)
                    try:
                        await channel.send(embed=e)
                    except:
                        pass


async def setup_hook():
    await load_data()
    bot.mongo_db = mongo_db
    await bot.load_extension("owner")
    await bot.load_extension("fun")
    await bot.load_extension("utility")
    await bot.load_extension("moderation")
    await bot.load_extension("economy")
    await bot.load_extension("logger")
    await bot.load_extension("antinuke")
    await bot.load_extension("premium")
bot.setup_hook = setup_hook

bot.run(token)
