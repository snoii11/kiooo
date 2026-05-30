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

    # Migrate from data.json if it exists
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
    print(f"{bot.user} is now online")
    print(f"Loaded Cogs: {bot.cogs}")

    if test_guild:
        bot.tree.copy_global_to(guild=test_guild)
        await bot.tree.sync(guild=test_guild)
        print(f"Synced commands to test guild {test_guild_id}")
    else:
        await bot.tree.sync()
        print("Synced commands globally")


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
bot.setup_hook = setup_hook


bot.run(token)
