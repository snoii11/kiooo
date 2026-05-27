import discord
from discord.ext import commands
from discord import app_commands
import datetime
import random

SHOP_ITEMS = {
    "basic/pickaxe": {"name": "Basic Pickaxe", "price": 500, "durability": 100, "tool_type": "pickaxe"},
    "iron/pickaxe": {"name": "Iron Pickaxe", "price": 2000, "durability": 300, "tool_type": "pickaxe"},
    "gold/pickaxe": {"name": "Golden Pickaxe", "price": 5000, "durability": 500, "tool_type": "pickaxe"},
    "basic/hoe": {"name": "Basic Hoe", "price": 500, "durability": 100, "tool_type": "farming_tool"},
    "iron/hoe": {"name": "Iron Hoe", "price": 2000, "durability": 300, "tool_type": "farming_tool"},
    "gold/hoe": {"name": "Golden Hoe", "price": 5000, "durability": 500, "tool_type": "farming_tool"},
    "basic/fishing rod": {"name": "Basic Fishing Rod", "price": 500, "durability": 100, "tool_type": "fishing_rod"},
    "iron/fishing rod": {"name": "Iron Fishing Rod", "price": 2000, "durability": 300, "tool_type": "fishing_rod"},
    "gold/fishing rod": {"name": "Golden Fishing Rod", "price": 5000, "durability": 500, "tool_type": "fishing_rod"},
    "repair_kit": {"name": "Repair Kit", "price": 1000},
}

TOOL_DURABILITY_COST = {
    "Basic": 2,
    "Iron": 1,
    "Golden": 1,
}

TOOL_EARNINGS = {
    "Basic": (20, 40),
    "Iron": (40, 80),
    "Golden": (80, 150),
}

QUALITY_LABELS = {"Basic": "🟢 Basic", "Iron": "🟠 Iron", "Golden": "🟡 Gold"}

COLOR_YELLOW = 0xFFFF00


class LeaderboardView(discord.ui.View):
    def __init__(self, top_users, bot):
        super().__init__()
        self.page = 0
        self.top_users = top_users
        self.bot = bot

    @discord.ui.button(label="Next Page", style=discord.ButtonStyle.primary, emoji="➡️")
    async def next_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        start = self.page * 10
        end = start + 10
        if start >= len(self.top_users):
            self.page = 0
            start = 0
            end = 10

        e = discord.Embed(
            title="🏆 [ ECONOMY LEADERBOARD ]",
            description="\n".join(
                f"**{idx + 1}.** <@{user['user_id']}> - {user['balance']} KioKreds"
                for idx, user in enumerate(self.top_users[start:end], start=start)
            ),
            color=COLOR_YELLOW)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.response.edit_message(embed=e, view=self)


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description):
        e = discord.Embed(title=title, description=description, color=COLOR_YELLOW)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        return e

    async def send(self, interaction, title, description):
        await interaction.response.send_message(embed=self.embed(title, description))

    def get_collection(self):
        mongo_db = getattr(self.bot, "mongo_db", None)
        return mongo_db["economy"] if mongo_db is not None else None

    async def ensure_profile(self, user):
        collection = self.get_collection()
        profile = None
        if collection is not None:
            profile = await collection.find_one({"user_id": user.id})
        if profile is None:
            profile = {
                "user_id": user.id,
                "balance": 0,
                "work_count": 0,
                "last_work": None,
                "last_daily": None,
                "last_rob": None,
                "inventory": {"farming_tool": None, "pickaxe": None, "fishing_rod": None},
                "repair_kits": 0,
                "created_at": datetime.datetime.now(datetime.timezone.utc)
            }
            if collection is not None:
                await collection.insert_one(profile)
        return profile

    async def update_profile(self, user_id, update_data=None, inc_data=None):
        collection = self.get_collection()
        if collection is None:
            return
        payload = {}
        if update_data:
            payload["$set"] = update_data
        if inc_data:
            payload["$inc"] = inc_data
        if payload:
            await collection.update_one({"user_id": user_id}, payload, upsert=True)

    def parse_dt(self, val):
        if val is None:
            return None
        if isinstance(val, str):
            try:
                val = datetime.datetime.fromisoformat(val)
            except ValueError:
                return None
        if val.tzinfo is None:
            val = val.replace(tzinfo=datetime.timezone.utc)
        return val

    def get_quality(self, name):
        for q in ("Golden", "Iron", "Basic"):
            if q in name:
                return q
        return "Basic"

    def tool_emoji(self, tool_type):
        return {"pickaxe": "⛏️", "farming_tool": "🌾", "fishing_rod": "🎣"}.get(tool_type, "🛠️")

    async def use_tool(self, interaction, tool_type, action_name):
        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")

        profile = await self.ensure_profile(interaction.user)
        inventory = profile.get("inventory", {})
        tool = inventory.get(tool_type)

        if tool is None:
            return await self.send(interaction, "❌ [ NO TOOL ]",
                f"```yaml\nERROR: You don't own a {action_name} tool.\nBuy one with /buy\n```")

        if tool["durability"] <= 0:
            return await self.send(interaction, "❌ [ TOOL BROKEN ]",
                f"```yaml\nERROR: Your {tool['name']} is broken.\nUse /repair to fix it.\n```")

        quality = self.get_quality(tool["name"])
        earned = random.randint(*TOOL_EARNINGS[quality])
        dur_cost = TOOL_DURABILITY_COST[quality]

        new_durability = tool["durability"] - dur_cost
        broken = False

        if new_durability <= 0:
            inventory[tool_type] = None
            broken = True
            dur_display = 0
        else:
            tool["durability"] = new_durability
            dur_display = new_durability

        new_balance = profile.get("balance", 0) + earned

        await self.update_profile(interaction.user.id,
            update_data={"balance": new_balance, "inventory": inventory})

        emoji = self.tool_emoji(tool_type)
        msg = f"```yaml\nEARNED: {earned} KioKreds\nTOOL: {tool['name']} ({dur_display} durability)\nTOTAL BALANCE: {new_balance} KioKreds\n```"
        if broken:
            msg += "\n⚠️ Your tool broke and was removed from inventory!"
        await self.send(interaction, f"{emoji} [ {action_name.upper()} ]", msg)

    @app_commands.command(name="work", description="Work to earn KioKreds")
    async def work(self, interaction: discord.Interaction):
        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")

        profile = await self.ensure_profile(interaction.user)
        now = datetime.datetime.now(datetime.timezone.utc)
        last_work = self.parse_dt(profile.get("last_work"))

        if last_work:
            elapsed = (now - last_work).total_seconds()
            if elapsed < 10:
                remaining = int(10 - elapsed)
                return await self.send(interaction, "⏳ [ WORK COOLDOWN ACTIVE ]",
                    f"```yaml\nNext shift available in {remaining}s.\nTOTAL BALANCE: {profile.get('balance', 0)} KioKreds\n```")

        earned = random.randint(10, 150)
        new_balance = profile.get("balance", 0) + earned
        work_count = profile.get("work_count", 0) + 1

        await self.update_profile(interaction.user.id,
            update_data={"balance": new_balance, "last_work": now, "work_count": work_count})

        await self.send(interaction, "💼 [ WORK SHIFT COMPLETED ]",
            f"```yaml\nEARNED: {earned} KioKreds\nTOTAL BALANCE: {new_balance} KioKreds\nWORK SHIFTS COMPLETED: {work_count}\n```")

    @app_commands.command(name="mine", description="Mine with your pickaxe to earn KioKreds")
    async def mine(self, interaction: discord.Interaction):
        await self.use_tool(interaction, "pickaxe", "Mining")

    @app_commands.command(name="fish", description="Fish with your fishing rod to earn KioKreds")
    async def fish(self, interaction: discord.Interaction):
        await self.use_tool(interaction, "fishing_rod", "Fishing")

    @app_commands.command(name="harvest", description="Harvest with your hoe to earn KioKreds")
    async def harvest(self, interaction: discord.Interaction):
        await self.use_tool(interaction, "farming_tool", "Harvest")

    @app_commands.command(name="balance", description="Check your or someone else's balance")
    @app_commands.describe(member="The member to check (defaults to you)")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")

        if member is None:
            member = interaction.user

        profile = await self.ensure_profile(member)
        balance = profile.get("balance", 0)
        work_count = profile.get("work_count", 0)
        last_work = self.parse_dt(profile.get("last_work"))
        last_work_str = last_work.strftime("%Y-%m-%d %H:%M:%S UTC") if last_work else "Never"

        await self.send(interaction, f"💰 [ BALANCE PROFILE: {member.display_name} ]",
            f"```ini\nBALANCE: {balance} KioKreds\nWORK SHIFTS: {work_count}\nLAST WORK: {last_work_str}\n```")

    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily(self, interaction: discord.Interaction):
        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")

        profile = await self.ensure_profile(interaction.user)
        now = datetime.datetime.now(datetime.timezone.utc)
        last_daily = self.parse_dt(profile.get("last_daily"))

        if last_daily:
            elapsed = (now - last_daily).total_seconds()
            if elapsed < 86400:
                remaining = int(86400 - elapsed)
                h, m = remaining // 3600, (remaining % 3600) // 60
                return await self.send(interaction, "⏳ [ DAILY COOLDOWN ACTIVE ]",
                    f"```yaml\nNext daily available in {h}h {m}m.\n```")

        reward = 500
        new_balance = profile.get("balance", 0) + reward
        await self.update_profile(interaction.user.id,
            update_data={"balance": new_balance, "last_daily": now})

        await self.send(interaction, "🎁 [ DAILY REWARD CLAIMED ]",
            f"```yaml\nDAILY REWARD: {reward} KioKreds\nTOTAL BALANCE: {new_balance} KioKreds\n```")

    @app_commands.command(name="leaderboard", description="View the economy leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")

        top = await collection.find().sort("balance", -1).to_list(length=100)
        if not top:
            return await self.send(interaction, "📭 [ NO DATA ]", "No economy data available yet.")

        e = discord.Embed(
            title="🏆 [ ECONOMY LEADERBOARD ]",
            description="\n".join(
                f"**{idx + 1}.** <@{user['user_id']}> - {user['balance']} KioKreds"
                for idx, user in enumerate(top[:10])
            ),
            color=COLOR_YELLOW)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.response.send_message(embed=e, view=LeaderboardView(top, self.bot))

    @app_commands.command(name="inventory", description="View your tools and repair kits")
    async def inventory(self, interaction: discord.Interaction):
        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")

        profile = await self.ensure_profile(interaction.user)
        inventory = profile.get("inventory", {})
        kits = profile.get("repair_kits", 0)

        lines = []
        for key, label in [("pickaxe", "Pickaxe"), ("farming_tool", "Hoe"), ("fishing_rod", "Fishing Rod")]:
            tool = inventory.get(key)
            if tool:
                quality = self.get_quality(tool["name"])
                tag = QUALITY_LABELS.get(quality, quality)
                lines.append(f"✦ {tag} {label} — {tool['durability']} durability")
            else:
                lines.append(f"✦ Empty slot ({label})")

        desc = "```ini\n[TOOLS]\n```\n" + "\n".join(lines) + f"\n\n```ini\n[CONSUMABLES]\n```\n✦ Repair Kits: **{kits}**"
        await self.send(interaction, f"🎒 [ INVENTORY: {interaction.user.display_name} ]", desc)

    @app_commands.command(name="shop", description="View the Kio shop")
    async def shop(self, interaction: discord.Interaction):
        await self.send(interaction, "🛒 [ KIO SHOP ]",
            "Welcome to the Kio Shop! Here you can spend your KioKreds on various items."
            "\n\n**Available Items: For fishing**\n"
            "1. **Basic Fishing Rod** - 500 KKD (100 durability, +50-100 KKD per catch)\n"
            "2. **Iron Fishing Rod** - 2000 KKD (300 durability, +100-200 KKD per catch)\n"
            "3. **Golden Fishing Rod** - 5000 KKD (500 durability, +200-400 KKD per catch)\n"
            "\n**Available Items: For farming**\n"
            "1. **Basic Hoe** - 500 KKD (100 durability, +50-100 KKD per harvest)\n"
            "2. **Iron Hoe** - 2000 KKD (300 durability, +100-200 KKD per harvest)\n"
            "3. **Golden Hoe** - 5000 KKD (500 durability, +200-400 KKD per harvest)\n"
            "\n**Available Items: For mining**\n"
            "1. **Basic Pickaxe** - 500 KKD (100 durability, +50-100 KKD per mine)\n"
            "2. **Iron Pickaxe** - 2000 KKD (300 durability, +100-200 KKD per mine)\n"
            "3. **Golden Pickaxe** - 5000 KKD (500 durability, +200-400 KKD per mine)\n"
            "\n**Consumables**\n"
            "1. **Repair Kit** — 1,000 KKD (repairs +50 durability to all your tools)\n")

    @app_commands.command(name="buy", description="Buy an item from the shop")
    @app_commands.describe(item="What to buy")
    @app_commands.choices(item=[
        app_commands.Choice(name="⛏️ Basic Pickaxe — 500 KKD", value="basic/pickaxe"),
        app_commands.Choice(name="⛏️ Iron Pickaxe — 2,000 KKD", value="iron/pickaxe"),
        app_commands.Choice(name="⛏️ Gold Pickaxe — 5,000 KKD", value="gold/pickaxe"),
        app_commands.Choice(name="🌾 Basic Hoe — 500 KKD", value="basic/hoe"),
        app_commands.Choice(name="🌾 Iron Hoe — 2,000 KKD", value="iron/hoe"),
        app_commands.Choice(name="🌾 Gold Hoe — 5,000 KKD", value="gold/hoe"),
        app_commands.Choice(name="🎣 Basic Fishing Rod — 500 KKD", value="basic/fishing rod"),
        app_commands.Choice(name="🎣 Iron Fishing Rod — 2,000 KKD", value="iron/fishing rod"),
        app_commands.Choice(name="🎣 Gold Fishing Rod — 5,000 KKD", value="gold/fishing rod"),
        app_commands.Choice(name="🧰 Repair Kit — 1,000 KKD", value="repair_kit"),
    ])
    async def buy(self, interaction: discord.Interaction, item: str):
        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")

        profile = await self.ensure_profile(interaction.user)
        balance = profile.get("balance", 0)

        if item == "repair_kit":
            price = SHOP_ITEMS["repair_kit"]["price"]
            if balance < price:
                return await self.send(interaction, "❌ [ INSUFFICIENT BALANCE ]",
                    f"```yaml\nPrice: {price} KioKreds\nYour Balance: {balance} KioKreds\nShortfall: {price - balance} KioKreds\n```")
            await self.update_profile(interaction.user.id,
                update_data={"balance": balance - price},
                inc_data={"repair_kits": 1})
            return await self.send(interaction, "✅ [ PURCHASE SUCCESSFUL ]",
                f"```yaml\nItem: Repair Kit\nPrice: {price} KioKreds\nNew Balance: {balance - price} KioKreds\n```")

        item_data = SHOP_ITEMS[item]
        price = item_data["price"]
        inventory = profile.get("inventory", {})
        tool_type = item_data["tool_type"]

        if inventory.get(tool_type) is not None:
            existing = inventory[tool_type]
            return await self.send(interaction, "❌ [ ITEM ALREADY OWNED ]",
                f"```yaml\nYou already own: {existing['name']}\nCurrent Durability: {existing['durability']}\n\nTools are not stackable. Use or sell your current item first.\n```")

        if balance < price:
            return await self.send(interaction, "❌ [ INSUFFICIENT BALANCE ]",
                f"```yaml\nPrice: {price} KioKreds\nYour Balance: {balance} KioKreds\nShortfall: {price - balance} KioKreds\n```")

        new_balance = balance - price
        inventory[tool_type] = {"name": item_data["name"], "durability": item_data["durability"]}

        await self.update_profile(interaction.user.id,
            update_data={"balance": new_balance, "inventory": inventory})

        await self.send(interaction, "✅ [ PURCHASE SUCCESSFUL ]",
            f"```yaml\nItem: {item_data['name']}\nPrice: {price} KioKreds\nNew Balance: {new_balance} KioKreds\nDurability: {item_data['durability']}\n```")

    @app_commands.command(name="repair", description="Use a Repair Kit to add +50 durability to all your tools")
    async def repair(self, interaction: discord.Interaction):
        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")

        profile = await self.ensure_profile(interaction.user)
        kits = profile.get("repair_kits", 0)
        if kits < 1:
            return await self.send(interaction, "❌ [ NO REPAIR KITS ]",
                "```yaml\nERROR: You don't have any Repair Kits.\nBuy one with /buy item:repair_kit\n```")

        inventory = profile.get("inventory", {})
        repaired = []
        for key in ("pickaxe", "farming_tool", "fishing_rod"):
            tool = inventory.get(key)
            if tool is not None:
                tool["durability"] += 50
                repaired.append(tool["name"])

        if not repaired:
            return await self.send(interaction, "❌ [ NO TOOLS TO REPAIR ]",
                "```yaml\nERROR: You don't own any tools to repair.\n```")

        await self.update_profile(interaction.user.id,
            update_data={"inventory": inventory},
            inc_data={"repair_kits": -1})

        await self.send(interaction, "🔧 [ REPAIR COMPLETE ]",
            f"```yaml\nKITS USED: 1\nTOOLS REPAIRED (+50 durability):\n" + "\n".join(f"✦ {t}" for t in repaired) + "\n```")

    @app_commands.command(name="gamble", description="Bet on 50/50 — double or nothing")
    @app_commands.describe(amount="Amount of KioKreds to bet")
    async def gamble(self, interaction: discord.Interaction, amount: int):
        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")

        if amount < 10:
            return await self.send(interaction, "❌ [ MINIMUM BET ]", "```yaml\nERROR: Minimum bet is 10 KioKreds.\n```")

        profile = await self.ensure_profile(interaction.user)
        balance = profile.get("balance", 0)

        if amount > balance:
            return await self.send(interaction, "❌ [ INSUFFICIENT BALANCE ]",
                f"```yaml\nYour Balance: {balance} KioKreds\nBet Amount: {amount} KioKreds\n```")

        if random.random() < 0.5:
            new_balance = balance + amount
            await self.update_profile(interaction.user.id,
                update_data={"balance": new_balance})
            await self.send(interaction, "🎲 [ GAMBLE — YOU WIN! ]",
                f"```yaml\nBET: {amount} KioKreds\nRESULT: You doubled your bet!\nNEW BALANCE: {new_balance} KioKreds\n```")
        else:
            new_balance = balance - amount
            await self.update_profile(interaction.user.id,
                update_data={"balance": new_balance})
            await self.send(interaction, "🎲 [ GAMBLE — YOU LOST ]",
                f"```yaml\nBET: {amount} KioKreds\nRESULT: You lost the bet.\nNEW BALANCE: {new_balance} KioKreds\n```")

    @app_commands.command(name="rob", description="Try to rob another user")
    @app_commands.describe(target="The user to rob")
    async def rob(self, interaction: discord.Interaction, target: discord.Member):
        if target == interaction.user:
            return await self.send(interaction, "❌ [ INVALID TARGET ]", "```yaml\nERROR: You cannot rob yourself.\n```")

        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")

        profile = await self.ensure_profile(interaction.user)
        target_profile = await self.ensure_profile(target)

        balance = profile.get("balance", 0)
        target_balance = target_profile.get("balance", 0)

        if balance < 50:
            return await self.send(interaction, "❌ [ POOR ]", "```yaml\nERROR: You need at least 50 KioKreds to attempt a robbery.\n```")

        if target_balance < 50:
            return await self.send(interaction, "❌ [ TARGET TOO POOR ]",
                f"```yaml\nERROR: {target.display_name} has less than 50 KioKreds. Not worth it.\n```")

        now = datetime.datetime.now(datetime.timezone.utc)
        last_rob = self.parse_dt(profile.get("last_rob"))
        if last_rob:
            elapsed = (now - last_rob).total_seconds()
            if elapsed < 3600:
                remaining = int(3600 - elapsed)
                h, m = remaining // 3600, (remaining % 3600) // 60
                return await self.send(interaction, "⏳ [ ROBBERY COOLDOWN ]",
                    f"```yaml\nNext heist available in {h}h {m}m.\n```")

        max_steal = min(int(target_balance * 0.1), 200)
        fine = min(int(balance * 0.05), 100)

        if random.random() < 0.4:
            stolen = random.randint(1, max_steal)
            await self.update_profile(interaction.user.id,
                update_data={"balance": balance + stolen, "last_rob": now})
            await self.update_profile(target.id,
                update_data={"balance": target_balance - stolen})
            await self.send(interaction, "🦹 [ ROBBERY SUCCESSFUL ]",
                f"```yaml\nTARGET: {target.display_name}\nSTOLEN: {stolen} KioKreds\nYOUR BALANCE: {balance + stolen} KioKreds\n```")
        else:
            await self.update_profile(interaction.user.id,
                update_data={"balance": balance - fine, "last_rob": now})
            await self.send(interaction, "🚔 [ ROBBERY FAILED ]",
                f"```yaml\nTARGET: {target.display_name}\nFINE PAID: {fine} KioKreds\nYOUR BALANCE: {balance - fine} KioKreds\n```")

    @app_commands.command(name="gift", description="Give KioKreds to another user")
    @app_commands.describe(target="The user to give KKD to", amount="Amount to give")
    async def gift(self, interaction: discord.Interaction, target: discord.Member, amount: int):
        if target == interaction.user:
            return await self.send(interaction, "❌ [ INVALID TARGET ]", "```yaml\nERROR: You cannot gift yourself.\n```")

        if amount < 1:
            return await self.send(interaction, "❌ [ INVALID AMOUNT ]", "```yaml\nERROR: Amount must be at least 1 KioKred.\n```")

        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")

        profile = await self.ensure_profile(interaction.user)
        balance = profile.get("balance", 0)

        if amount > balance:
            return await self.send(interaction, "❌ [ INSUFFICIENT BALANCE ]",
                f"```yaml\nYour Balance: {balance} KioKreds\nAmount: {amount} KioKreds\nShortfall: {amount - balance} KioKreds\n```")

        await self.update_profile(interaction.user.id,
            update_data={"balance": balance - amount})
        await self.update_profile(target.id,
            inc_data={"balance": amount})

        await self.send(interaction, "🎁 [ GIFT SENT ]",
            f"```yaml\nSENT: {amount} KioKreds\nTO: {target.display_name}\nYOUR BALANCE: {balance - amount} KioKreds\n```")


async def setup(bot):
    await bot.add_cog(Economy(bot))
