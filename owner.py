import discord
from discord.ext import commands
import datetime

own = 1491790586166902874

# Advanced Futuristic Color Tokens
COLOR_YELLOW = 0xFFFF00
COLOR_CYAN = 0x00F0FF
COLOR_PINK = 0xFF007F
COLOR_GREEN = 0x39FF14

class ConfirmView(discord.ui.View):
	def __init__(self, confirm_message, bot):
		super().__init__()
		self.confirm_message = confirm_message
		self.bot = bot

	@discord.ui.button(label="AUTHORIZED TERMINATION (YES)", style=discord.ButtonStyle.red)
	async def confirm(self, interaction, button):
		self.confirmed = True
		embed = discord.Embed(
			title="❖ [ SYSTEM SHUTDOWN CONFIRMED ] ❖",
			description="```ini\n[STATUS] Terminal shutdown command authorized.\n[ACTION] Terminating active processes and closing connection.\n```",
			color=COLOR_YELLOW
		)
		embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
		embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
		await interaction.response.send_message(embed=embed)
		await interaction.client.close()
		self.stop()

	@discord.ui.button(label="ABORT COMMAND (NO)", style=discord.ButtonStyle.green)
	async def cancel(self, interaction, button):
		embed = discord.Embed(
			title="❖ [ SHUTDOWN CANCELLED ] ❖",
			description="```ini\n[STATUS] Terminal shutdown aborted.\n[ACTION] Resuming normal operations.\n```",
			color=COLOR_YELLOW
		)
		embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
		embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
		await interaction.response.send_message(embed=embed)
		self.stop()

class Owner(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def send_embed(self, ctx, title, description):
		embed = discord.Embed(title=title, description=description, color=COLOR_YELLOW)
		embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
		embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
		await ctx.send(embed=embed)

	@commands.command()
	async def shutdown(self, ctx):
		print("shutdown command triggered")
		if ctx.author.id == own:
			view = ConfirmView("Shutting down...", self.bot)
			embed = discord.Embed(
				title="❖ [ SYSTEM SHUTDOWN PROMPT ] ❖",
				description="```yaml\nWARNING: You are about to initiate a terminal shutdown. This will disconnect the bot completely.\n```\n**Are you sure you want to proceed?**",
				color=COLOR_YELLOW
			)
			embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
			embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
			await ctx.send(embed=embed, view=view)
		else:
			embed = discord.Embed(
				title="❌ [ ACCESS RESTRICTED ]",
				description="```diff\n- ERROR: Unauthorized access attempt detected.\n- LEVEL: Required credentials: Core Owner\n```",
				color=COLOR_YELLOW
			)
			embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
			embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
			await ctx.send(embed=embed)


	@commands.command(aliases=["noprefix", "nprefix"])
	async def np(self, ctx, action, user_id: int = None):
		action = action.lower()
		allowed_users = self.bot.db.get("noprefix_access", [])
		
		if ctx.author.id == own or ctx.author.id in allowed_users:
			if action == "add":
				if user_id is None:
					embed = discord.Embed(
						title="❌ [ SYNTAX ERROR ]",
						description="```yaml\nCOMMAND: np\nERROR: Missing or invalid arguments\nUSAGE: np add <user_id>\nEXAMPLE: np add 1234567789\n```",
						color=COLOR_YELLOW)
					embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
					embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
					await ctx.send(embed=embed)
					return
				
				if user_id not in self.bot.db["np_list"]:
					self.bot.db["np_list"].append(user_id)
					self.bot.save_data()
					
				embed = discord.Embed(
					title="✅ [ CONFIGURATION UPDATED ]",
					description=f"```ini\n[STATUS] Modification successful.\n[ACTION] Added user <@{user_id}> ({user_id}) to No-Prefix list.\n```\n> Tip: You can remove users with `np remove <user_id>`",
					color=COLOR_YELLOW)
				embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
				embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
				await ctx.send(embed=embed)

			elif action == "remove":
				if user_id is None:
					embed = discord.Embed(
						title="❌ [ SYNTAX ERROR ]",
						description="```yaml\nCOMMAND: np\nERROR: Missing or invalid arguments\nUSAGE: np remove <user_id>\nEXAMPLE: np remove 1234567789\n```",
						color=COLOR_YELLOW)
					embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
					embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
					await ctx.send(embed=embed)
					return
				
				if user_id in self.bot.db["np_list"]:
					self.bot.db["np_list"].remove(user_id)
					self.bot.save_data()
					
				embed = discord.Embed(
					title="🗑️ [ CONFIGURATION UPDATED ]",
					description=f"```ini\n[STATUS] Modification successful.\n[ACTION] Removed user <@{user_id}> ({user_id}) from No-Prefix list.\n```\n> Tip: You can add users with `np add <user_id>`",
					color=COLOR_YELLOW)
				embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
				embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
				await ctx.send(embed=embed)

			elif action == "list":
				user_mentions = "\n".join(f"✦ <@{uid}> (`{uid}`)" for uid in self.bot.db['np_list']) if self.bot.db['np_list'] else "No users in override list."
				embed = discord.Embed(
					title="📋 [ NO-PREFIX CONFIGURATION LOG ]",
					description=f"```ini\n[MODULE] Override Caching System\n[STATUS] Online & Active\n```\n**Authorized Override Users:**\n{user_mentions}",
					color=COLOR_YELLOW)
				embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
				embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
				await ctx.send(embed=embed)

		else:
			embed = discord.Embed(
				title="❌ [ ACCESS RESTRICTED ]",
				description="```diff\n- ERROR: Permission denied.\n- COMMAND: No-Prefix settings modification is restricted to Core Administration.\n```",
				color=COLOR_YELLOW)
			embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
			embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
			await ctx.send(embed=embed)

	@np.error
	async def np_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			embed = discord.Embed(
				title="❌ [ SYNTAX ERROR ]",
				description="```yaml\nCOMMAND: np\nERROR: Missing required arguments\nUSAGE: np <add/remove/list> [user_id]\nEXAMPLE: np add 1234567789\n```",
				color=COLOR_YELLOW)
			embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
			embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
			await ctx.send(embed=embed)


	@commands.command(aliases=["rlcogs", "reloadcogs"])
	async def reload(self, ctx, cog):
		if ctx.author.id == own:
			try:
				await self.bot.reload_extension(cog)
				embed = discord.Embed(
					title="✅ [ SYSTEM HOT-RELOAD SUCCESSFUL ]",
					description=f"```ini\n[MODULE] {cog}\n[STATUS] Reloaded successfully in active memory.\n```",
					color=COLOR_YELLOW)
				embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
				embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
				await ctx.send(embed=embed)

			except Exception as e:
				embed = discord.Embed(
					title="❌ [ SYSTEM HOT-RELOAD FAILED ]",
					description=f"```diff\n- MODULE: {cog}\n- STATUS: Fail\n- ERROR: {e}\n```\n> Tip: You can shutdown the bot completely with `k.shutdown` if necessary.",
					color=COLOR_YELLOW)
				embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
				embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
				await ctx.send(embed=embed)
		else:
			embed = discord.Embed(
				title="❌ [ ACCESS RESTRICTED ]",
				description="```diff\n- ERROR: Permission denied.\n- COMMAND: Cog hot-reloading is restricted to Core Developers.\n```",
				color=COLOR_YELLOW)
			embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
			embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
			await ctx.send(embed=embed)

	@commands.command()
	async def status(self, ctx, *, message):
		if ctx.author.id == own:
			await self.bot.change_presence(activity=discord.Game(name=message))
			embed = discord.Embed(
				title="✅ [ CLIENT STATUS MODIFIED ]",
				description=f"```ini\n[PARAMETER] Presence Activity\n[VALUE] Playing {message}\n[STATUS] Applied globally.\n```",
				color=COLOR_YELLOW)
			embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
			embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
			await ctx.send(embed=embed)

		else:
			embed = discord.Embed(
				title="❌ [ ACCESS RESTRICTED ]",
				description="```diff\n- ERROR: Permission denied.\n- COMMAND: Presence status override is restricted to Developer account.\n```",
				color=COLOR_YELLOW)
			embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
			embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
			await ctx.send(embed=embed)

	@commands.command(aliases=["npaddaccess"])
	async def npa(self, ctx, action, user_id: int):
		action = action.lower()
		try:
			if ctx.author.id == own:
				if action == "add":
					if user_id not in self.bot.db["noprefix_access"]:
						self.bot.db["noprefix_access"].append(user_id)
						self.bot.save_data()
					embed = discord.Embed(
						title="✅ [ PRIVILEGES GRANTED ]",
						description=f"```ini\n[PRIVILEGE] No-Prefix Admin Access\n[GRANTEE] User ID {user_id}\n[STATUS] Added successfully.\n```\n> Tip: You can remove users with `npa remove <user_id>`",
						color=COLOR_YELLOW)
					embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
					embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
					await ctx.send(embed=embed)

				elif action == "remove":
					if user_id in self.bot.db["noprefix_access"]:
						self.bot.db["noprefix_access"].remove(user_id)
						self.bot.save_data()
					embed = discord.Embed(
						title="🗑️ [ PRIVILEGES REVOKED ]",
						description=f"```ini\n[PRIVILEGE] No-Prefix Admin Access\n[REVOKEE] User ID {user_id}\n[STATUS] Removed successfully.\n```\n> Tip: You can add users with `npa add <user_id>`",
						color=COLOR_YELLOW)
					embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
					embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
					await ctx.send(embed=embed)
				else:
					await self.send_embed(ctx, "❌ [ SYNTAX ERROR ]", "```yaml\nERROR: Invalid action. Use 'add' or 'remove'.\n```")
		except Exception as e:
			embed = discord.Embed(
				title="❌ [ EXCEPTION RAISED ]",
				description=f"```diff\n- STATUS: Operational Fail\n- ERROR DETAILS: {e}\n```",
				color=COLOR_YELLOW)
			embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
			embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
			await ctx.send(embed=embed)



async def setup(bot):
	await bot.add_cog(Owner(bot))