import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import datetime
import json

load_dotenv()
token = os.getenv('TOKEN')

prefix = 'k.'

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=prefix, intents=intents, case_insensitive=True)

def load_data():
	try:
		with open("data.json", "r") as f:
			db = json.load(f)
	except (FileNotFoundError, json.JSONDecodeError):
		db = {}
	
	# Guarantee schema requirements
	if "np_list" not in db:
		db["np_list"] = []
	if "noprefix_access" not in db:
		db["noprefix_access"] = []
	if "warnings" not in db:
		db["warnings"] = {}
	return db

bot.db = load_data()

def save_data():
	with open("data.json", "w") as f:
		json.dump(bot.db, f, indent=4)
bot.save_data = save_data

async def send_embed(ctx, title, description):
	embed = discord.Embed(title=title, description=description, color=0xFFFF00)
	if ctx.bot.user:
		embed.set_footer(text="Kiooo", icon_url=ctx.bot.user.display_avatar.url)
	else:
		embed.set_footer(text="Kiooo")
	embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
	await ctx.send(embed=embed)


@bot.event
async def on_ready():
	print(f"{bot.user} is now online")
	print(f"Loaded Cogs: {bot.cogs}")

@bot.event
async def on_message(message):
	if message.author == bot.user:
		return

	np_users = bot.db.get("np_list", [])

	if message.author.id in np_users:
		if not message.content.startswith(prefix):
			message.content = prefix + message.content

	await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
		return

	if isinstance(error, commands.MissingRequiredArgument):
		command_name = ctx.command.qualified_name if ctx.command else "command"
		await send_embed(ctx, "❌ [ SYNTAX ERROR ]", f"```yaml\nCOMMAND: {command_name}\nERROR: Missing required argument\n```")
		return

	if isinstance(error, commands.BadArgument):
		await send_embed(ctx, "❌ [ SYNTAX ERROR ]", "```yaml\nERROR: One or more arguments were invalid.\n```")
		return

	if isinstance(error, commands.MissingPermissions):
		await send_embed(ctx, "❌ [ ACCESS RESTRICTED ]", "```diff\n- ERROR: Permission denied.\n```")
		return

	if isinstance(error, commands.CheckFailure):
		await send_embed(ctx, "❌ [ ACCESS RESTRICTED ]", "```diff\n- ERROR: You cannot use this command here.\n```")
		return

	if isinstance(error, commands.CommandInvokeError):
		print(f"Command {ctx.command.qualified_name if ctx.command else 'unknown'} failed: {error.original}")
		await send_embed(ctx, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An error occurred while running that command.\n```")
		return

	print(f"Unhandled command error in {ctx.command.qualified_name if ctx.command else 'unknown'}: {error}")
	await send_embed(ctx, "❌ [ OPERATIONAL ERROR ]", "```diff\n- ERROR: An unexpected error occurred while running that command.\n```")


async def setup_hook():
	await bot.load_extension("owner")
	await bot.load_extension("fun")
	await bot.load_extension("utility")
	await bot.load_extension("moderation")
bot.setup_hook = setup_hook



bot.run(token)