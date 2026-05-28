import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import json
import motor.motor_asyncio

load_dotenv()
token = os.getenv('TOKEN')
mongo_uri = os.getenv('MONGO_URI')
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
    mongo_uri,
    serverSelectionTimeoutMS=5000,
    tlsAllowInvalidCertificates=True
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


def load_data():
    try:
        with open("data.json", "r") as f:
            db = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        db = {}
    if "np_list" not in db:
        db["np_list"] = []
    if "noprefix_access" not in db:
        db["noprefix_access"] = []
    if "warnings" not in db:
        db["warnings"] = {}
    if "balances" not in db:
        db["balances"] = {}
    if "last_work" not in db:
        db["last_work"] = {}
    return db

bot.db = load_data()


def save_data():
    with open("data.json", "w") as f:
        json.dump(bot.db, f, indent=4)
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
                color=0xFFFF00), ephemeral=True)

    if isinstance(error, app_commands.MissingPermissions):
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ [ ACCESS RESTRICTED ]",
                description="```diff\n- ERROR: Permission denied.\n```",
                color=0xFFFF00), ephemeral=True)

    if isinstance(error, app_commands.BotMissingPermissions):
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ [ BOT PERMISSION ERROR ]",
                description=f"```diff\n- ERROR: I need the following permissions: {', '.join(error.missing_permissions)}\n```",
                color=0xFFFF00), ephemeral=True)

    if isinstance(error, app_commands.TransformerError):
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ [ INVALID ARGUMENT ]",
                description=f"```yaml\nERROR: Could not parse argument.\n```",
                color=0xFFFF00), ephemeral=True)

    print(f"Unhandled tree error: {error}")
    try:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ [ OPERATIONAL ERROR ]",
                description="```diff\n- ERROR: An unexpected error occurred.\n```",
                color=0xFFFF00), ephemeral=True)
    except:
        pass


async def setup_hook():
    await bot.load_extension("owner")
    await bot.load_extension("fun")
    await bot.load_extension("utility")
    await bot.load_extension("moderation")
    await bot.load_extension("economy")
    await bot.load_extension("logger")
    bot.mongo_db = mongo_db
bot.setup_hook = setup_hook


bot.run(token)
