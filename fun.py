import discord
from discord.ext import commands
from discord import app_commands
import pyjokes
import random
import datetime
import aiohttp
from deep_translator import GoogleTranslator
import asyncio
from concurrent.futures import ThreadPoolExecutor

url = f"https://insult.mattbas.org/api/insult&rand={random.randint(1, 1000000)}"

answers = [
    "Yes!", "No!", "Maybe...", "Definitely!",
    "I don't think so...", "Ask again later!",
    "Without a doubt!", "Very doubtful!"
]

COLOR_YELLOW = 0xFFFF00
COLOR_CYAN = 0x00F0FF


class TriviaView(discord.ui.View):
    def __init__(self, all_answers, correct_answer):
        super().__init__()
        self.correct_answer = correct_answer
        self.add_item(TriviaSelect(all_answers, correct_answer))

class TriviaSelect(discord.ui.Select):
    def __init__(self, all_answers, correct_answer):
        self.correct_answer = correct_answer
        options = [
            discord.SelectOption(label=answer[:100], value=str(idx))
            for idx, answer in enumerate(all_answers, start=1)
        ]
        super().__init__(placeholder="Choose your answer...", options=options)

    async def callback(self, interaction):
        correct_idx = str(
            next(i for i, o in enumerate(self.options, start=1) if o.label == self.correct_answer[:100])
        )
        if self.values[0] == correct_idx:
            await interaction.response.send_message("✅ Correct! 🎉", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Wrong! The correct answer was: **{self.correct_answer}**", ephemeral=True)
        self.view.stop()


class MemeView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Next Meme", style=discord.ButtonStyle.primary, emoji="😂")
    async def next_meme(self, interaction, button):
        async with aiohttp.ClientSession(headers={"Accept-Encoding": "gzip, deflate"}) as session:
            async with session.get("https://meme-api.com/gimme") as r:
                data = await r.json()
                e = discord.Embed(title=data["title"], color=COLOR_YELLOW)
                e.set_image(url=data["url"])
                e.set_footer(text=f"👍 {data['ups']} | r/{data['subreddit']}")
                await interaction.response.edit_message(embed=e)


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description, color=COLOR_YELLOW):
        e = discord.Embed(title=title, description=description, color=color)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        return e

    @app_commands.command(name="joke", description="Get a random joke")
    async def joke(self, interaction: discord.Interaction):
        joke = pyjokes.get_joke()
        await interaction.response.send_message(embed=self.embed(
            "🤣 [ INCOMING TRANSMISSION: JOKE ]",
            f"```prolog\n\"{joke}\"\n```"))

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    @app_commands.describe(question="Your question for the 8-ball")
    async def eightball(self, interaction: discord.Interaction, question: str):
        answer = random.choice(answers)
        await interaction.response.send_message(embed=self.embed(
            "🎱 [ QUANTUM PREDICTIVE ENGINE ]",
            f"```yaml\nQUESTION: \"{question}\"\nRESPONSE: \"{answer}\"\n```\n> Tip: Wanna hear a joke? Use `/joke` command!"))

    @app_commands.command(name="meme", description="Get a random meme")
    async def meme(self, interaction: discord.Interaction):
        await interaction.response.defer()
        async with aiohttp.ClientSession(headers={"Accept-Encoding": "gzip, deflate"}) as session:
            async with session.get("https://meme-api.com/gimme") as r:
                data = await r.json()
                e = discord.Embed(title=data["title"], color=COLOR_YELLOW)
                e.set_image(url=data["url"])
                e.set_footer(text=f"👍 {data['ups']} | r/{data['subreddit']}")
                await interaction.followup.send(embed=e, view=MemeView())

    @app_commands.command(name="trivia", description="Answer a random trivia question")
    async def trivia(self, interaction: discord.Interaction):
        await interaction.response.defer()
        async with aiohttp.ClientSession(headers={"Accept-Encoding": "gzip, deflate"}) as session:
            async with session.get("https://opentdb.com/api.php?amount=1&type=multiple") as r:
                data = await r.json()
                if data["response_code"] != 0:
                    return await interaction.followup.send("❌ Failed to fetch trivia question. Please try again later.")

                q = data["results"][0]
                question = q["question"]
                correct = q["correct_answer"]
                incorrect = q["incorrect_answers"]
                all_answers = incorrect + [correct]
                random.shuffle(all_answers)

                e = self.embed(
                    "❓ [ TRIVIA CHALLENGE ]",
                    f"```markdown\n{question}\n```\n> Tip: Wanna hear a joke? Use `/joke` command!",
                    color=COLOR_CYAN)
                for idx, ans in enumerate(all_answers, start=1):
                    e.add_field(name=f"Option {idx}", value=ans, inline=False)
                await interaction.followup.send(embed=e, view=TriviaView(all_answers, correct))

    @app_commands.command(name="roast", description="Roast someone (or yourself)")
    @app_commands.describe(target="The person to roast (defaults to you)")
    async def roast(self, interaction: discord.Interaction, target: discord.Member = None):
        if target is None:
            target = interaction.user
        await interaction.response.defer()
        async with aiohttp.ClientSession(headers={"Accept-Encoding": "gzip, deflate"}) as session:
            async with session.get(url) as r:
                insult = await r.text()
                await interaction.followup.send(embed=self.embed(
                    "🔥 [ ROAST ]",
                    f"```prolog\n{target.display_name}, {insult}\n```"))

    @app_commands.command(name="translate", description="Translate text to another language")
    @app_commands.describe(target_language="Target language code (e.g. es, fr, de)", text="The text to translate")
    async def translate(self, interaction: discord.Interaction, target_language: str, text: str):
        await interaction.response.defer()
        try:
            translator = GoogleTranslator(source='auto', target=target_language)
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(pool, lambda: translator.translate(text))
            await interaction.followup.send(embed=self.embed(
                "🌐 [ TRANSLATION ]",
                f"```yaml\nOriginal: \"{text}\"\nTranslated: \"{result}\"\n```",
                color=COLOR_CYAN))
        except Exception as e:
            await interaction.followup.send(f"❌ Translation failed: {str(e)}")


async def setup(bot):
    await bot.add_cog(Fun(bot))
