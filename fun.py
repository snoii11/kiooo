import discord
from discord.ext import commands
import pyjokes
import random
import datetime

answers = [
    "Yes!", "No!", "Maybe...", "Definitely!", 
    "I don't think so...", "Ask again later!", 
    "Without a doubt!", "Very doubtful!"
]

# Advanced Futuristic Color Tokens
COLOR_YELLOW = 0xFFFF00
COLOR_CYAN = 0x00F0FF

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command("joke")
    async def joke(self, ctx):
        joke = pyjokes.get_joke()
        embed = discord.Embed(
            title="🤣 [ INCOMING TRANSMISSION: JOKE ]",
            description=f"```prolog\n\"{joke}\"\n```",
            color=COLOR_YELLOW
        )
        embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed)

    @commands.command(aliases=["8ball"])
    async def eightball(self, ctx, *, question):
        answer = random.choice(answers)
        embed = discord.Embed(
            title="🎱 [ QUANTUM PREDICTIVE ENGINE ]",
            description=f"```yaml\nQUESTION: \"{question}\"\nRESPONSE: \"{answer}\"\n```\n> Tip: Wanna hear a joke? Use `k.joke` command!",
            color=COLOR_YELLOW
        )
        embed.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))