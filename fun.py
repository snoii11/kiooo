import discord
from discord.ext import commands
import pyjokes
import random


answers = [
    "Yes!", "No!", "Maybe...", "Definitely!", 
    "I don't think so...", "Ask again later!", 
    "Without a doubt!", "Very doubtful!"
]

kio = 0xffec01

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command("Joke")
    async def joke(self, ctx):
        joke = pyjokes.get_joke()
        embed = discord.Embed(
            title="  <:kio:1508019650456322078>     |    Here's a joke for you!",
            description= f"> {joke}",
            color=kio
        )
        embed.set_thumbnail(url=ctx.bot.user.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["8ball"])
    async def eightball(self, ctx, *, question):
        answer = random.choice(answers)
        embed = discord.Embed(
            title="  <:eightball:1508028601495326782>     |    8-Ball",
            description= f" -8ball says...`{answer}`\n ```diff\n- Note: The Magic 8-Ball's answers are random and for fun, don't take them seriously!``` \n > Tip: Wanna hear a joke? Use `k.joke` command!",
            color=kio
        )
        embed.set_thumbnail(url=ctx.bot.user.avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))