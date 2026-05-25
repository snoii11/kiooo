import discord
from discord.ext import commands
import json

def save_data(data):
	with open("data.json", "w") as f:
		json.dump(data, f)

def load_data():
	with open("data.json", "r") as f:
		return json.load(f)


own = 1491790586166902874
kio = 0xffec01

class ConfirmView(discord.ui.View):
	def __init__(self, confirm_message):
		super().__init__()
		self.confirm_message = confirm_message


	@discord.ui.button(label="Yes", style=discord.ButtonStyle.red)
	async def confirm(self, interaction, button):
		self.confirmed = True
		embed = discord.Embed(
			title="Confirmed",
			description="Shutdown command has been confirmed, the bot will now shutdown",
			color=discord.Color.yellow()
		)
		await interaction.response.send_message(embed=embed)
		await interaction.client.close()
		self.stop()


	@discord.ui.button(label="No", style=discord.ButtonStyle.green)
	async def cancel(self, interaction, button):
		embed = discord.Embed(
			title="Cancelled",
			description="The shutdown command hass been cancelled!",
			color=discord.Color.yellow()
		)
		await interaction.response.send_message(embed=embed)
		self.stop()

class Owner(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def shutdown(self, ctx):
		print("shutdown command triggered")
		if ctx.author.id == own:
			view = ConfirmView("Shutting down...")
			embed = discord.Embed(
				title="Bot shutdown",
				description="Are you sure you want to shutdown the bot?",
				color=discord.Color.yellow()
			)
			await ctx.send(embed=embed, view=view)
		else:
			embed = discord.Embed(
				title="Owners only command!",
				description="Only owners of this bot can run owners only commands!",
				color=discord.Color.yellow())
			await ctx.send(embed=embed)


	@commands.command(aliases=["noprefix", "Noprefix", "Np", "nprefix", "Nprefix"])
	async def np(self, ctx, action, user_id: int = None):
		action = action.lower()
		if ctx.author.id == own:
			data = load_data()
			if action == "add":
				if user_id is None:
					embed = discord.Embed(
						title=" <:kio_x:1507717440707235950>       |Wrong usage!|",
						description="```diff\n- Usage: np <add/remove> <user_id>```\n ```diff\n+ Example: np add 1234567789```",
						color=kio)
					embed.set_thumbnail(url=ctx.bot.user.avatar.url)
					await ctx.send(embed=embed)
					return
				data["np_list"].append(user_id)
				save_data(data)
				embed = discord.Embed(
					title=" <:kio_grant:1507722880949948447>      |User added to no prefix list",
					description="```diff\n+ User has been added to the no prefix list```\n > Tip: You can remove users with 'np remove <user_id>'",
					color=kio)
				embed.set_thumbnail(url=ctx.bot.user.avatar.url)
				await ctx.send(embed=embed)

			elif action == "remove":
				if user_id is None:
					embed = discord.Embed(
						title=" <:kio_x:1507717440707235950>       |Wrong usage!|",
						description="```diff\n- Usage: np <add/remove> <user_id>```\n ```diff\n+ Example: np remove 1234567789```",
						color=kio)
					embed.set_thumbnail(url=ctx.bot.user.avatar.url)
					await ctx.send(embed=embed)
					return
				data["np_list"].remove(user_id)
				save_data(data)
				embed = discord.Embed(
					title=" <:kio_remove:1507722831595700296>      |User removed from no prefix list",
					description="```diff\n- User has been removed from the no prefix list```\n > Tip: You can add users with 'np add <user_id>'",
					color=kio)
				embed.set_thumbnail(url=ctx.bot.user.avatar.url)
				await ctx.send(embed=embed)

			elif action == "list":
				embed = discord.Embed(
					title=" <:kio_list:1507834436178284665>      |No Prefix List",
					description="```diff\n+ Users in no prefix list:```\n" + "\n".join(f"<@{id}>" for id in data['np_list']),
					color=kio)
				embed.set_thumbnail(url=ctx.bot.user.avatar.url)
				await ctx.send(embed=embed)

		else:
			embed = discord.Embed(
				title=" <:kio_x:1507717440707235950> |Owner only command!",
				description="No prefix command is owners only command!",
				color=discord.Color.yellow())
			embed.set_thumbnail(url=ctx.bot.user.avatar.url)
			await ctx.send(embed=embed)

	@np.error
	async def np_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			embed = discord.Embed(
				title=" <:kio_x:1507717440707235950> |Wrong usage!|",
				description="```diff\n- Usage: np <add/remove> <user_id>```\n ```diff\n+ Example: np add 1234567789```",
				color=discord.Color.yellow())
			embed.set_thumbnail(url=ctx.bot.user.avatar.url)
			await ctx.send(embed=embed)


	@commands.command(aliases=["rlcogs","Rlcogs", "Reloadcogs", "Reload", "reloadcogs"])
	async def reload(self, ctx, cog):
		if ctx.author.id == own:
			try:
				await self.bot.reload_extension(cog)
				embed = discord.Embed(
					title=" <:kio_grant:1507722880949948447>      |Cogs reloaded!",
					description="```diff\n+ Cogs have been reloaded successfully!```",
					color=kio)
				embed.set_thumbnail(url=ctx.bot.user.avatar.url)
				await ctx.send(embed=embed)

			except Exception as e:
				embed = discord.Embed(
					title=" <:kio_x:1507717440707235950>       |Error reloading cogs!|",
					description=f"```diff\n- An error occurred while reloading cogs: {e}``` \n > Tip: You can shutdown the bot with 'k.shutdown'.",
					color=kio)
				embed.set_thumbnail(url=ctx.bot.user.avatar.url)
				await ctx.send(embed=embed)
		else:
			embed = discord.Embed(
				title=" <:kio_x:1507717440707235950> |Owner only command!",
				description="Reload command is owners only command!",
				color=discord.Color.yellow())
			embed.set_thumbnail(url=ctx.bot.user.avatar.url)
			await ctx.send(embed=embed)

	@commands.command(aliases=["Status"])
	async def status(self, ctx, *, message):
		if ctx.author.id == own:
			await self.bot.change_presence(activity=discord.Game(name=message))
			embed = discord.Embed(
				title=" <:kio_grant:1507722880949948447>      |Status updated!",
				description=f"```diff\n+ Bot status has been updated to: {message}```",
				color=kio)
			embed.set_thumbnail(url=ctx.bot.user.avatar.url)
			await ctx.send(embed=embed)

		else:
			embed = discord.Embed(
				title=" <:kio_x:1507717440707235950> |Owner only command!",
				description="Status command is owners only command!",
				color=discord.Color.yellow())
			embed.set_thumbnail(url=ctx.bot.user.avatar.url)
			await ctx.send(embed=embed)

	@commands.command(aliases=["npaddaccess", "Npaddaccess", "Npa"])
	async def npa(self, ctx, action, user_id: int):
		try:
			if ctx.author.id == own:
				data = load_data()
				if action == "add":
					data["np_list"].append(user_id)
					save_data(data)
					embed = discord.Embed(
						title=" <:kio_grant:1507722880949948447>      |User added to no prefix list",
						description="```diff\n+ User has been added to the no prefix list```\n > Tip: You can remove users with 'npa remove <user_id>'",
						color=kio)
					embed.set_thumbnail(url=ctx.bot.user.avatar.url)
					await ctx.send(embed=embed)

				elif action == "remove":
					data["np_list"].remove(user_id)
					save_data(data)
					embed = discord.Embed(
						title=" <:kio_remove:1507722831595700296>      |User removed from no prefix list",
						description="```diff\n- User has been removed from the no prefix list```\n > Tip: You can add users with 'npa add <user_id>'",
						color=kio)
					embed.set_thumbnail(url=ctx.bot.user.avatar.url)
					await ctx.send(embed=embed)
		except Exception as e:
			embed = discord.Embed(
				title=" <:kio_x:1507717440707235950>       |Error!|",
				description=f"```diff\n- An error occurred: {e}```",
				color=kio)
			embed.set_thumbnail(url=ctx.bot.user.avatar.url)
			await ctx.send(embed=embed)



async def setup(bot):
	await bot.add_cog(Owner(bot))