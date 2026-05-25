import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import json

load_dotenv()
token = os.getenv('TOKEN')

prefix = 'k.'

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=prefix, intents=intents)

with open("data.json", "r") as f:
	data = json.load(f)


def load_data():
	with open("data.json", "r") as f:
		return json.load(f)

np_users = data["np_list"]

@bot.event
async def on_ready():
	print(f"{bot.user} is now online")
	print(f"Loaded Cogs: {bot.cogs}")

@bot.event
async def on_message(message):
	if message.author == bot.user:
		return

	data = load_data()
	np_users = data["np_list"]

	if message.author.id in np_users:
		if not message.content.startswith(prefix):
			message.content = prefix + message.content

	await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
		pass


async def setup_hook():
	await bot.load_extension("owner")
	await bot.load_extension("fun")
	await bot.load_extension("utility")
	await bot.load_extension("moderation")
bot.setup_hook = setup_hook



bot.run(token)