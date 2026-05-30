import discord
from discord.ext import commands
from discord import app_commands
import datetime
import random
from colors import COLOR

# ── Shop (tools + consumables) ──
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

TOOL_DURABILITY_COST = {"Basic": 2, "Iron": 1, "Golden": 1}
QUALITY_LABELS = {"Basic": "🟢 Basic", "Iron": "🟠 Iron", "Golden": "🟡 Gold"}

# ── Collectible Items ──
ITEMS = {
    "stone": {"name": "Stone", "sell": 5, "tier": "basic", "type": "mining"},
    "coal": {"name": "Coal", "sell": 10, "tier": "basic", "type": "mining"},
    "copper": {"name": "Copper Ore", "sell": 15, "tier": "basic", "type": "mining"},
    "iron_ore": {"name": "Iron Ore", "sell": 25, "tier": "iron", "type": "mining"},
    "gold_ore": {"name": "Gold Ore", "sell": 40, "tier": "iron", "type": "mining"},
    "silver_ore": {"name": "Silver Ore", "sell": 35, "tier": "iron", "type": "mining"},
    "diamond": {"name": "Diamond", "sell": 100, "tier": "gold", "type": "mining"},
    "emerald": {"name": "Emerald", "sell": 80, "tier": "gold", "type": "mining"},
    "ruby": {"name": "Ruby", "sell": 90, "tier": "gold", "type": "mining"},
    "wheat": {"name": "Wheat", "sell": 5, "tier": "basic", "type": "farming"},
    "carrot": {"name": "Carrot", "sell": 8, "tier": "basic", "type": "farming"},
    "potato": {"name": "Potato", "sell": 7, "tier": "basic", "type": "farming"},
    "tomato": {"name": "Tomato", "sell": 15, "tier": "iron", "type": "farming"},
    "pumpkin": {"name": "Pumpkin", "sell": 20, "tier": "iron", "type": "farming"},
    "melon": {"name": "Melon", "sell": 18, "tier": "iron", "type": "farming"},
    "golden_wheat": {"name": "Golden Wheat", "sell": 50, "tier": "gold", "type": "farming"},
    "magic_berry": {"name": "Magic Berry", "sell": 65, "tier": "gold", "type": "farming"},
    "star_fruit": {"name": "Star Fruit", "sell": 75, "tier": "gold", "type": "farming"},
    "salmon": {"name": "Salmon", "sell": 8, "tier": "basic", "type": "fishing"},
    "cod": {"name": "Cod", "sell": 6, "tier": "basic", "type": "fishing"},
    "trout": {"name": "Trout", "sell": 10, "tier": "basic", "type": "fishing"},
    "tuna": {"name": "Tuna", "sell": 20, "tier": "iron", "type": "fishing"},
    "bass": {"name": "Bass", "sell": 25, "tier": "iron", "type": "fishing"},
    "mackerel": {"name": "Mackerel", "sell": 22, "tier": "iron", "type": "fishing"},
    "legendary_fish": {"name": "Legendary Fish", "sell": 80, "tier": "gold", "type": "fishing"},
    "pearl": {"name": "Pearl", "sell": 70, "tier": "gold", "type": "fishing"},
    "treasure_map": {"name": "Treasure Map", "sell": 95, "tier": "gold", "type": "fishing"},
}

ITEM_POOLS = {
    "pickaxe": {"basic": ["stone", "coal", "copper"], "iron": ["iron_ore", "gold_ore", "silver_ore"], "gold": ["diamond", "emerald", "ruby"]},
    "farming_tool": {"basic": ["wheat", "carrot", "potato"], "iron": ["tomato", "pumpkin", "melon"], "gold": ["golden_wheat", "magic_berry", "star_fruit"]},
    "fishing_rod": {"basic": ["salmon", "cod", "trout"], "iron": ["tuna", "bass", "mackerel"], "gold": ["legendary_fish", "pearl", "treasure_map"]},
}


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
            color=COLOR)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.response.edit_message(embed=e, view=self)


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description):
        e = discord.Embed(title=title, description=description, color=COLOR)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        return e

    async def send(self, interaction, title, description):
        e = self.embed(title, description)
        if interaction.response.is_done():
            await interaction.followup.send(embed=e)
        else:
            await interaction.response.send_message(embed=e)

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
                "items": {},
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

    async def use_tool(self, interaction, tool_type, action_name, emoji):
        await interaction.response.defer()
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

        # Drop a collectible item
        pool = ITEM_POOLS.get(tool_type, {}).get(quality.lower(), ["stone"])
        item_key = random.choice(pool)
        item_data = ITEMS[item_key]
        quantity = random.randint(1, 3)

        items = profile.get("items", {})
        items[item_key] = items.get(item_key, 0) + quantity

        kkd = random.randint(5, 20)

        if broken:
            await self.update_profile(interaction.user.id,
                inc_data={"balance": kkd, f"items.{item_key}": quantity},
                update_data={f"inventory.{tool_type}": None})
        else:
            await self.update_profile(interaction.user.id,
                inc_data={"balance": kkd, f"items.{item_key}": quantity, f"inventory.{tool_type}.durability": -dur_cost})

        lines = [
            f"EARNED: {kkd} KioKreds",
            f"FOUND: {quantity}x {item_data['name']}",
            f"TOOL: {tool['name']} ({dur_display} durability)",
        ]
        msg = "```yaml\n" + "\n".join(lines) + "\n```"
        if broken:
            msg += "\n⚠️ Your tool broke and was removed from inventory!"

        await self.send(interaction, f"{emoji} [ {action_name.upper()} RESULT ]", msg)

    # ── Work ──

    @app_commands.command(name="work", description="Work to earn KioKreds")
    async def work(self, interaction: discord.Interaction):
        await interaction.response.defer()
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
        work_count = profile.get('work_count', 0) + 1
        new_balance = profile.get('balance', 0) + earned

        await self.update_profile(interaction.user.id,
            inc_data={"balance": earned, "work_count": 1},
            update_data={"last_work": now})

        await self.send(interaction, "💼 [ WORK SHIFT COMPLETED ]",
            f"```yaml\nEARNED: {earned} KioKreds\nTOTAL BALANCE: {new_balance} KioKreds\nWORK SHIFTS COMPLETED: {work_count}\n```")

    # ── Gathering Commands ──

    @app_commands.command(name="mine", description="Mine with your pickaxe to find ores and gems")
    @app_commands.checks.cooldown(1, 3, key=lambda i: i.user.id)
    async def mine(self, interaction: discord.Interaction):
        await self.use_tool(interaction, "pickaxe", "Mining", "⛏️")

    @app_commands.command(name="fish", description="Fish with your rod to catch fish and treasures")
    @app_commands.checks.cooldown(1, 3, key=lambda i: i.user.id)
    async def fish(self, interaction: discord.Interaction):
        await self.use_tool(interaction, "fishing_rod", "Fishing", "🎣")

    @app_commands.command(name="harvest", description="Harvest with your hoe to gather crops")
    @app_commands.checks.cooldown(1, 3, key=lambda i: i.user.id)
    async def harvest(self, interaction: discord.Interaction):
        await self.use_tool(interaction, "farming_tool", "Harvest", "🌾")

    # ── Balance ──

    @app_commands.command(name="balance", description="Check your or someone else's balance")
    @app_commands.describe(member="The member to check (defaults to you)")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()
        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")
        if member is None:
            member = interaction.user

        profile = await self.ensure_profile(member)
        await self.send(interaction, f"💰 [ BALANCE PROFILE: {member.display_name} ]",
            f"```ini\nBALANCE: {profile.get('balance', 0)} KioKreds\nWORK SHIFTS: {profile.get('work_count', 0)}\nLAST WORK: {(self.parse_dt(profile.get('last_work')) or 'Never')}\n```")

    # ── Daily ──

    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily(self, interaction: discord.Interaction):
        await interaction.response.defer()
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

        await self.update_profile(interaction.user.id,
            inc_data={"balance": reward},
            update_data={"last_daily": now})
        await self.send(interaction, "🎁 [ DAILY REWARD CLAIMED ]",
            f"```yaml\nDAILY REWARD: {reward} KioKreds\nTOTAL BALANCE: {new_balance} KioKreds\n```")

    # ── Leaderboard ──

    @app_commands.command(name="leaderboard", description="View the economy leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
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
            color=COLOR)
        e.set_footer(text="Kiooo", icon_url=self.bot.user.display_avatar.url)
        e.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.response.send_message(embed=e, view=LeaderboardView(top, self.bot))

    # ── Inventory ──

    @app_commands.command(name="inventory", description="View your tools and collected items")
    @app_commands.describe(category="Filter by category (all, mining, farming, fishing)")
    @app_commands.choices(category=[
        app_commands.Choice(name="All", value="all"),
        app_commands.Choice(name="⛏️ Mining", value="mining"),
        app_commands.Choice(name="🌾 Farming", value="farming"),
        app_commands.Choice(name="🎣 Fishing", value="fishing"),
    ])
    async def inventory(self, interaction: discord.Interaction, category: str = "all"):
        await interaction.response.defer()
        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")

        profile = await self.ensure_profile(interaction.user)
        inventory = profile.get("inventory", {})
        items = profile.get("items", {})
        kits = profile.get("repair_kits", 0)

        # Tools
        tool_lines = []
        for key, label in [("pickaxe", "Pickaxe"), ("farming_tool", "Hoe"), ("fishing_rod", "Fishing Rod")]:
            t = inventory.get(key)
            if t:
                q = self.get_quality(t["name"])
                tag = QUALITY_LABELS.get(q, q)
                tool_lines.append(f"✦ {tag} {label} — {t['durability']} durability")
            else:
                tool_lines.append(f"✦ Empty ({label})")

        # Items
        item_lines = []
        total_value = 0
        for ik, qty in sorted(items.items()):
            if qty < 1:
                continue
            data = ITEMS.get(ik)
            if not data:
                continue
            if category != "all" and data["type"] != category:
                continue
            value = data["sell"] * qty
            total_value += value
            item_lines.append(f"✦ {qty}x {data['name']} — {data['sell']} KKD each (total: {value} KKD)")

        if category == "all":
            total_all = sum(ITEMS[ik]["sell"] * qty for ik, qty in items.items() if ik in ITEMS)
            desc = f"```ini\n[TOOLS]\n```\n" + "\n".join(tool_lines)
            desc += f"\n\n```ini\n[CONSUMABLES]\n```\n✦ Repair Kits: **{kits}**"
            if item_lines:
                desc += f"\n\n```ini\n[COLLECTED ITEMS — Total Value: {total_all} KKD]\n```\n" + "\n".join(item_lines)
            else:
                desc += "\n\nNo items collected yet. Use /mine, /fish, or /harvest!"
        else:
            if item_lines:
                desc = f"**Collected Items ({category}) — Total Value: {total_value} KKD**\n\n" + "\n".join(item_lines)
            else:
                desc = f"No {category} items yet."

        await self.send(interaction, f"🎒 [ INVENTORY: {interaction.user.display_name} ]", desc)

    # ── Shop & Buy ──

    @app_commands.command(name="shop", description="View the Kio shop")
    async def shop(self, interaction: discord.Interaction):
        await self.send(interaction, "🛒 [ KIO SHOP ]",
            "Welcome to the Kio Shop! Here you can spend your KioKreds on various items."
            "\n\n**🎣 Fishing Rods**\n"
            "1. **Basic Fishing Rod** - 500 KKD (100 durability)\n"
            "2. **Iron Fishing Rod** - 2000 KKD (300 durability)\n"
            "3. **Golden Fishing Rod** - 5000 KKD (500 durability)\n"
            "\n**🌾 Hoes**\n"
            "1. **Basic Hoe** - 500 KKD (100 durability)\n"
            "2. **Iron Hoe** - 2000 KKD (300 durability)\n"
            "3. **Golden Hoe** - 5000 KKD (500 durability)\n"
            "\n**⛏️ Pickaxes**\n"
            "1. **Basic Pickaxe** - 500 KKD (100 durability)\n"
            "2. **Iron Pickaxe** - 2000 KKD (300 durability)\n"
            "3. **Golden Pickaxe** - 5000 KKD (500 durability)\n"
            "\n**🧰 Consumables**\n"
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
        await interaction.response.defer()
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
                inc_data={"balance": -price, "repair_kits": 1})
            return await self.send(interaction, "✅ [ PURCHASE SUCCESSFUL ]",
                f"```yaml\nItem: Repair Kit\nPrice: {price} KioKreds\nNew Balance: {balance - price} KioKreds\n```")

        item_data = SHOP_ITEMS[item]
        price = item_data["price"]
        inv = profile.get("inventory", {})
        tt = item_data["tool_type"]

        if inv.get(tt) is not None:
            existing = inv[tt]
            return await self.send(interaction, "❌ [ ITEM ALREADY OWNED ]",
                f"```yaml\nYou already own: {existing['name']}\nCurrent Durability: {existing['durability']}\n```")
        if balance < price:
            return await self.send(interaction, "❌ [ INSUFFICIENT BALANCE ]",
                f"```yaml\nPrice: {price} KioKreds\nYour Balance: {balance} KioKreds\nShortfall: {price - balance} KioKreds\n```")

        inv[tt] = {"name": item_data["name"], "durability": item_data["durability"]}
        await self.update_profile(interaction.user.id,
            inc_data={"balance": -price},
            update_data={"inventory": inv})
        await self.send(interaction, "✅ [ PURCHASE SUCCESSFUL ]",
            f"```yaml\nItem: {item_data['name']}\nPrice: {price} KioKreds\nNew Balance: {balance - price} KioKreds\nDurability: {item_data['durability']}\n```")

    # ── Repair ──

    @app_commands.command(name="repair", description="Use a Repair Kit to add +50 durability to all your tools")
    async def repair(self, interaction: discord.Interaction):
        await interaction.response.defer()
        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")

        profile = await self.ensure_profile(interaction.user)
        if profile.get("repair_kits", 0) < 1:
            return await self.send(interaction, "❌ [ NO REPAIR KITS ]",
                "```yaml\nERROR: You don't have any Repair Kits.\nBuy one with /buy\n```")

        inv = profile.get("inventory", {})
        repaired = []
        for key in ("pickaxe", "farming_tool", "fishing_rod"):
            t = inv.get(key)
            if t is not None:
                t["durability"] += 50
                repaired.append(t["name"])

        if not repaired:
            return await self.send(interaction, "❌ [ NO TOOLS TO REPAIR ]",
                "```yaml\nERROR: You don't own any tools to repair.\n```")

        await self.update_profile(interaction.user.id,
            update_data={"inventory": inv},
            inc_data={"repair_kits": -1})

        await self.send(interaction, "🔧 [ REPAIR COMPLETE ]",
            f"```yaml\nKITS USED: 1\nTOOLS REPAIRED (+50 durability):\n" + "\n".join(f"✦ {t}" for t in repaired) + "\n```")

    # ── Sell ──

    @app_commands.command(name="sell", description="Sell collected items from your inventory")
    @app_commands.describe(item="Item to sell (or 'all' to sell everything)")
    async def sell(self, interaction: discord.Interaction, item: str = "all"):
        await interaction.response.defer()
        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")

        profile = await self.ensure_profile(interaction.user)
        items = profile.get("items", {})

        if not items or all(q < 1 for q in items.values()):
            return await self.send(interaction, "📭 [ EMPTY INVENTORY ]", "```yaml\nERROR: You have no items to sell.\n```")

        item = item.strip().lower()
        balance = profile.get("balance", 0)

        if item == "all":
            total = 0
            sold = []
            for ik, qty in list(items.items()):
                if qty < 1:
                    continue
                data = ITEMS.get(ik)
                if not data:
                    continue
                value = data["sell"] * qty
                total += value
                sold.append(f"✦ {qty}x {data['name']} — {value} KKD")
                items[ik] = 0

            if total == 0:
                return await self.send(interaction, "📭 [ NOTHING TO SELL ]", "```yaml\nERROR: No sellable items found.\n```")

            await self.update_profile(interaction.user.id,
                inc_data={"balance": total, **{f"items.{ik}": -qty for ik, qty in items.items() if qty > 0}})
            await self.send(interaction, "💰 [ BULK SALE COMPLETE ]",
                f"```yaml\nTOTAL EARNED: {total} KioKreds\nNEW BALANCE: {balance + total} KioKreds\n```\n" + "\n".join(sold))

        else:
            # Try to find the item
            matched = None
            for ik, data in ITEMS.items():
                if ik == item or data["name"].lower() == item:
                    matched = ik
                    break

            if matched is None:
                return await self.send(interaction, "❌ [ ITEM NOT FOUND ]",
                    f"```yaml\nERROR: No item named '{item}'.\nCheck /inventory for your items.\n```")

            qty = items.get(matched, 0)
            if qty < 1:
                return await self.send(interaction, "❌ [ NOT OWNED ]",
                    f"```yaml\nERROR: You don't have any {ITEMS[matched]['name']} to sell.\n```")

            data = ITEMS[matched]
            value = data["sell"] * qty

            await self.update_profile(interaction.user.id,
                inc_data={"balance": value, f"items.{matched}": -qty})
            await self.send(interaction, "💰 [ ITEM SOLD ]",
                f"```yaml\nITEM: {qty}x {data['name']}\nEARNED: {value} KioKreds\nNEW BALANCE: {balance + value} KioKreds\n```")

    # ── Gamble ──

    @app_commands.command(name="gamble", description="Bet on 50/50 — double or nothing")
    @app_commands.describe(amount="Amount of KioKreds to bet")
    async def gamble(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer()
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
            await self.update_profile(interaction.user.id, inc_data={"balance": amount})
            await self.send(interaction, "🎲 [ GAMBLE — YOU WIN! ]",
                f"```yaml\nBET: {amount} KioKreds\nRESULT: You doubled your bet!\nNEW BALANCE: {balance + amount} KioKreds\n```")
        else:
            await self.update_profile(interaction.user.id, inc_data={"balance": -amount})
            await self.send(interaction, "🎲 [ GAMBLE — YOU LOST ]",
                f"```yaml\nBET: {amount} KioKreds\nRESULT: You lost the bet.\nNEW BALANCE: {balance - amount} KioKreds\n```")

    # ── Rob ──

    @app_commands.command(name="rob", description="Try to rob another user")
    @app_commands.describe(target="The user to rob")
    async def rob(self, interaction: discord.Interaction, target: discord.Member):
        await interaction.response.defer()
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
                f"```yaml\nERROR: {target.display_name} has less than 50 KioKreds.\n```")

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
            await self.update_profile(interaction.user.id, inc_data={"balance": stolen}, update_data={"last_rob": now})
            await self.update_profile(target.id, inc_data={"balance": -stolen})
            await self.send(interaction, "🦹 [ ROBBERY SUCCESSFUL ]",
                f"```yaml\nTARGET: {target.display_name}\nSTOLEN: {stolen} KioKreds\nYOUR BALANCE: {balance + stolen} KioKreds\n```")
        else:
            await self.update_profile(interaction.user.id, inc_data={"balance": -fine}, update_data={"last_rob": now})
            await self.send(interaction, "🚔 [ ROBBERY FAILED ]",
                f"```yaml\nTARGET: {target.display_name}\nFINE PAID: {fine} KioKreds\nYOUR BALANCE: {balance - fine} KioKreds\n```")

    # ── Gift ──

    @app_commands.command(name="gift", description="Give KioKreds to another user")
    @app_commands.describe(target="The user to give KKD to", amount="Amount to give")
    async def gift(self, interaction: discord.Interaction, target: discord.Member, amount: int):
        await interaction.response.defer()
        if target == interaction.user:
            return await self.send(interaction, "❌ [ INVALID TARGET ]", "```yaml\nERROR: You cannot gift yourself.\n```")
        if amount < 1:
            return await self.send(interaction, "❌ [ INVALID AMOUNT ]", "```yaml\nERROR: Amount must be at least 1.\n```")

        collection = self.get_collection()
        if collection is None:
            return await self.send(interaction, "❌ [ DATABASE OFFLINE ]", "Economy database is not configured.")

        profile = await self.ensure_profile(interaction.user)
        balance = profile.get("balance", 0)
        if amount > balance:
            return await self.send(interaction, "❌ [ INSUFFICIENT BALANCE ]",
                f"```yaml\nYour Balance: {balance} KioKreds\nAmount: {amount} KioKreds\n```")

        await self.update_profile(interaction.user.id, inc_data={"balance": -amount})
        await self.update_profile(target.id, inc_data={"balance": amount})
        await self.send(interaction, "🎁 [ GIFT SENT ]",
            f"```yaml\nSENT: {amount} KioKreds\nTO: {target.display_name}\nYOUR BALANCE: {balance - amount} KioKreds\n```")


async def setup(bot):
    await bot.add_cog(Economy(bot))
