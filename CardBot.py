# CardBot.py

import os
import io
import re
import time
import json
import random
import sqlite3
import mimetypes
import urllib.parse
from typing import List, Tuple, Dict, Optional

import discord
from discord import app_commands
from discord.ext import commands

import aiohttp
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

try:
    import cairosvg
    HAS_CAIROSVG = True
except Exception:
    HAS_CAIROSVG = False

# ---------- CONFIG ----------
DB_PATH = "cards.db"
SQL_BOOTSTRAP = "black_bolt_types_placeholders.sql"
INTENTS = discord.Intents.default()
INTENTS.message_content = False
INTENTS.members = True  # Enable in Dev Portal for best results
BOT_ACTIVITY = "Opening packs (/packopen)"
GUILD_ID = os.getenv("GUILD_ID")  # optional; we now sync to all joined guilds
PACK_NAME_DEFAULT = "Black Bolt"

EMOJI_CARD = "🖼️"

# Pack groups (only 3 packs total)
TOKEN_PACKS = {"Black Bolt", "Journey Together"}  # token-openable packs
SHOP_ONLY_PACKS = {"Stormfront"}                  # shop-only pack
STORMFRONT_PACK_NAME = "Stormfront"
STORMFRONT_PACK_PRICE = 3000  # essence cost per Stormfront pack in shop

# All known packs (token-openable + shop-only)
PACKS_ALL = sorted(TOKEN_PACKS | SHOP_ONLY_PACKS)

# Dev knob for testing tokens
DEV_FORCE_MAX_TOKENS = True

# ---------- IMAGE LIMITS / SETTINGS ----------
MAX_UPLOAD_BYTES = 7 * 1024 * 1024
MAX_DIM = 1024
FETCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DiscordCardBot/1.0",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}

# ---------- ECONOMY / POINTS ----------
TOKEN_CAP = 75
TOKEN_INITIAL = 15
TOKEN_REFILL_SECS = 2 * 60 * 60  # 2 hours
ESSENCE_PER_TOKEN = 200
TOTAL_CARDS = 172  # legacy value; collection now computes from DB

# Essence gained when pulling a duplicate of a given rarity
ESSENCE_FROM_RARITY: Dict[str, int] = {
    "Common": 100,
    "Uncommon": 250,
    "Rare": 500,

    # Double Rare tier
    "Double Rare": 1000,
    "Rare Holo": 1000,
    "Double Rare or Rare Holo": 1000,

    # Ultra Rare tier
    "Ultra Rare": 1250,
    "Rare Holo LV.X": 1250,
    "Ultra Rare or Rare Holo LV.X": 1250,

    # Illustration / special illustration
    "Illustration Rare": 1500,
    "Illistration Rare": 1500,             # tolerate existing misspelling
    "Special Illustration Rare": 2000,
    "Special Illistration Rare": 2000,     # tolerate existing misspelling

    # Top tier
    "Black White Rare": 5000,
    "Hyper Rare": 5000,
    "Rare Secret": 5000,
    "Black White Rare or Hyper Rare or Rare Secret": 5000,
}

# Scoreboard points per rarity
POINTS_FROM_RARITY: Dict[str, int] = {
    "Common": 1,
    "Uncommon": 2,
    "Rare": 5,

    # Double Rare tier
    "Double Rare": 10,
    "Rare Holo": 10,
    "Double Rare or Rare Holo": 10,

    # Ultra Rare tier
    "Ultra Rare": 15,
    "Rare Holo LV.X": 15,
    "Ultra Rare or Rare Holo LV.X": 15,

    # Illustration / special illustration
    "Illustration Rare": 10,
    "Illistration Rare": 10,
    "Special Illustration Rare": 20,
    "Special Illistration Rare": 20,

    # Top tier
    "Black White Rare": 35,
    "Hyper Rare": 35,
    "Rare Secret": 35,
    "Black White Rare or Hyper Rare or Rare Secret": 35,
}

# Normalize rarity labels used for hit selection; keys are lowercased labels
RARITY_NORMALIZE: Dict[str, str] = {
    "common": "Common",
    "uncommon": "Uncommon",
    "rare": "Rare",

    "double rare": "Double Rare",
    "rare holo": "Rare Holo",
    "double rare or rare holo": "Double Rare or Rare Holo",

    "ultra rare": "Ultra Rare",
    "rare holo lv.x": "Rare Holo LV.X",
    "ultra rare or rare holo lv.x": "Ultra Rare or Rare Holo LV.X",

    "illustration rare": "Illistration Rare",
    "illistration rare": "Illistration Rare",

    "special illustration rare": "Special Illistration Rare",
    "special illistration rare": "Special Illistration Rare",

    "black white rare": "Black White Rare",
    "hyper rare": "Hyper Rare",
    "rare secret": "Rare Secret",
    "black white rare or hyper rare or rare secret": "Black White Rare or Hyper Rare or Rare Secret",
}

COMMON_POOL = {"Common", "Uncommon"}

# Hit tiers: keys are lowercased & looked up via RARITY_NORMALIZE
HIT_TIERS: List[Tuple[str, int]] = [
    # Top tier, very rare
    ("black white rare or hyper rare or rare secret", 20),
    ("hyper rare", 20),
    ("rare secret", 20),
    ("black white rare", 20),

    # High tier
    ("rare holo lv.x", 17),
    ("ultra rare", 17),
    ("special illustration rare", 18),
    ("illustration rare", 15),

    # Mid-tier upgrades
    ("double rare", 10),
    ("rare holo", 10),

    # Fallback rare
    ("rare", 5),
]


# --------- DUELS / SIM / AUCTION / STREAK SETTINGS ---------
DUEL_COOLDOWN_SECS = 60 * 5
DUEL_REWARDS = {"easy": (1, 200), "normal": (2, 350), "hard": (3, 500)}
DUEL_CONSOLATION = (0, 100)
DUEL_ROUNDS = 3
NPCS = {
    "rookie": {"name": "Rookie Ronin", "power_bias": 0.85},
    "veteran": {"name": "Veteran Vale", "power_bias": 1.00},
    "master": {"name": "Master Myra", "power_bias": 1.15},
}
RARITY_POWER = {
    "Common": 1,
    "Uncommon": 2,
    "Rare": 4,

    # Double Rare tier
    "Double Rare": 7,
    "Rare Holo": 7,
    "Double Rare or Rare Holo": 7,

    # Ultra Rare tier
    "Ultra Rare": 10,
    "Rare Holo LV.X": 10,
    "Ultra Rare or Rare Holo LV.X": 10,

    # Illustration / special illustration
    "Illustration Rare": 8,
    "Illistration Rare": 8,
    "Special Illustration Rare": 13,
    "Special Illistration Rare": 13,

    # Top tier
    "Black White Rare": 20,
    "Hyper Rare": 20,
    "Rare Secret": 20,
    "Black White Rare or Hyper Rare or Rare Secret": 20,
}
PVP_ROUNDS = 3
PVP_ESSENCE_WIN = 250
PVP_ESSENCE_LOSS = 100
PVP_RARITY_POWER = dict(RARITY_POWER)

# --------- SHOP SETTINGS ----------
SHOP_COMMON_SLOTS = 4
SHOP_RARE_SLOT = 5
SHOP_SPECIAL_SLOT = 6
SHOP_TOKEN_BUNDLE = 5
SHOP_PRICE_TOKEN_BUNDLE = 2000
SHOP_PRICE_COMMON_CARD = 400
SHOP_PRICE_RARE_CARD = 2000
# ------------------------------------------------------------

# --------- WEEKLY RANDOM EVENTS (PER GUILD) ---------
# Each guild gets exactly one event per week (based on _iso_week_key).
# "effects" is a bag of knobs that various commands read.

WEEKLY_EVENTS: List[Dict] = [
    {
        "id": "double_essence_dupes",
        "name": "Essence Surge",
        "description": "Duplicate card pulls give 2× essence.",
        "effects": {"essence_from_dupes_multiplier": 2.0},
    },
    {
        "id": "triple_essence_dupes",
        "name": "Essence Explosion",
        "description": "Duplicate card pulls give 3× essence.",
        "effects": {"essence_from_dupes_multiplier": 3.0},
    },
    {
        "id": "lucky_tokens",
        "name": "Lucky Tokens Week",
        "description": "Each pack open has a 35% chance to refund the token.",
        "effects": {"pack_token_refund_chance": 0.35},
    },
    {
        "id": "token_smelter",
        "name": "Token Smelter",
        "description": "Selling tokens gives 2× essence.",
        "effects": {"token_sell_essence_factor": 2.0},
    },
    {
        "id": "bargain_shop",
        "name": "Bargain Bazaar",
        "description": "All Essence Shop items are 20% off.",
        "effects": {"shop_price_factor": 0.8},
    },
    {
        "id": "stormfront_frenzy",
        "name": "Stormfront Frenzy",
        "description": "Stormfront packs in the shop are 40% off.",
        "effects": {"shop_stormfront_price_factor": 0.6},
    },
    {
        "id": "duel_jackpot",
        "name": "Duel Jackpot",
        "description": "NPC and PvP duel rewards are doubled.",
        "effects": {"duel_reward_multiplier": 2.0},
    },
    {
        "id": "duel_training",
        "name": "Duel Training Camp",
        "description": "NPC opponents are slightly weaker and rewards are 1.5×.",
        "effects": {
            "npc_bias_factor": 0.9,
            "duel_reward_multiplier": 1.5,
        },
    },
    {
        "id": "essence_fever",
        "name": "Essence Fever",
        "description": "Duplicates give 1.5× essence and duels give 1.25× rewards.",
        "effects": {
            "essence_from_dupes_multiplier": 1.5,
            "duel_reward_multiplier": 1.25,
        },
    },
    {
        "id": "collector_sale",
        "name": "Collector's Sale",
        "description": "Shop is 10% off and selling tokens gives 1.5× essence.",
        "effects": {
            "shop_price_factor": 0.9,
            "token_sell_essence_factor": 1.5,
        },
    },
]


def _weekly_event_key(ts: int) -> str:
    """Key for the current week (aligned with _iso_week_key)."""
    return _iso_week_key(ts)


def _find_event_def(event_id: str) -> Optional[Dict]:
    for ev in WEEKLY_EVENTS:
        if ev["id"] == event_id:
            return ev
    return None


def _get_or_create_weekly_event(conn: sqlite3.Connection, guild_id: str) -> Dict:
    """
    Fetch this guild's event for the current week, or roll a new one if missing
    or out-of-date.
    """
    week = _weekly_event_key(_now_ts())
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    row = cur.execute(
        "SELECT week_key, event_id FROM weekly_events_guild WHERE guild_id=?",
        (guild_id,),
    ).fetchone()

    if row and row["week_key"] == week:
        ev = _find_event_def(row["event_id"])
        if ev:
            return ev

    # Need to select a new event for this week
    ev = random.choice(WEEKLY_EVENTS)
    cur.execute(
        """
        INSERT INTO weekly_events_guild(guild_id, week_key, event_id, created_ts)
        VALUES (?,?,?,?)
        ON CONFLICT(guild_id) DO UPDATE SET
          week_key=excluded.week_key,
          event_id=excluded.event_id,
          created_ts=excluded.created_ts
        """,
        (guild_id, week, ev["id"], _now_ts()),
    )
    conn.commit()
    return ev


def _event_effect(event: Optional[Dict], key: str, default):
    """Safely read an effect knob from a weekly event dict."""
    if not event:
        return default
    effects = event.get("effects") or {}
    return effects.get(key, default)


def _shop_effective_price(base_price: int, item_type: str, event: Optional[Dict]) -> int:
    """
    Apply weekly discounts to shop prices.
    - shop_price_factor applies to all items
    - shop_stormfront_price_factor additionally applies to Stormfront packs
    """
    factor = float(_event_effect(event, "shop_price_factor", 1.0))
    if item_type == "stormfront_pack":
        factor *= float(_event_effect(event, "shop_stormfront_price_factor", 1.0))
    return max(1, int(round(base_price * factor)))


# ------------- DB helpers -------------
def ensure_db():
    """Ensure DB schema exists; extends with name cache, trading, and shop tables."""
    if not os.path.exists(DB_PATH) and os.path.exists(SQL_BOOTSTRAP):
        with open(SQL_BOOTSTRAP, "r", encoding="utf-8") as f:
            sql_text = f.read()
        with sqlite3.connect(DB_PATH) as conn:
            conn.executescript(sql_text)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        c.execute(
            """
        CREATE TABLE IF NOT EXISTS users_guild (
            guild_id       TEXT NOT NULL,
            user_id        TEXT NOT NULL,
            tokens         INTEGER NOT NULL DEFAULT 0,
            essence        INTEGER NOT NULL DEFAULT 0,
            tokens_used    INTEGER NOT NULL DEFAULT 0,
            first_seen_ts  INTEGER NOT NULL DEFAULT 0,
            last_update_ts INTEGER NOT NULL DEFAULT 0,
            profile_card   TEXT NOT NULL DEFAULT 'blank',
            PRIMARY KEY(guild_id, user_id)
        )
        """
        )

        c.execute(
            """
        CREATE TABLE IF NOT EXISTS user_collection_guild (
            guild_id TEXT NOT NULL,
            user_id  TEXT NOT NULL,
            card_id  INTEGER NOT NULL,
            PRIMARY KEY(guild_id, user_id, card_id)
        )
        """
        )

        c.execute(
            """
        CREATE TABLE IF NOT EXISTS users_names_guild (
            guild_id TEXT NOT NULL,
            user_id  TEXT NOT NULL,
            display  TEXT NOT NULL,
            username TEXT NOT NULL,
            updated_ts INTEGER NOT NULL,
            PRIMARY KEY (guild_id, user_id)
        )
        """
        )

        c.execute(
            """
        CREATE TABLE IF NOT EXISTS npc_duel_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id   TEXT NOT NULL,
            user_id    TEXT NOT NULL,
            npc_id     TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            rounds_json TEXT NOT NULL,
            result     TEXT NOT NULL,
            reward_tokens INTEGER NOT NULL DEFAULT 0,
            reward_essence INTEGER NOT NULL DEFAULT 0,
            created_ts INTEGER NOT NULL
        )"""
        )
        c.execute(
            """
        CREATE TABLE IF NOT EXISTS npc_duel_cd (
            guild_id TEXT NOT NULL,
            user_id  TEXT NOT NULL,
            next_ts  INTEGER NOT NULL,
            PRIMARY KEY (guild_id, user_id)
        )"""
        )

        c.execute(
            """
        CREATE TABLE IF NOT EXISTS pvp_duel_challenges (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id       TEXT NOT NULL,
            challenger_id  TEXT NOT NULL,
            target_id      TEXT NOT NULL,
            stake_tokens   INTEGER NOT NULL DEFAULT 0,
            status         TEXT NOT NULL,
            created_ts     INTEGER NOT NULL
        )
        """
        )
        c.execute(
            """
        CREATE TABLE IF NOT EXISTS pvp_duel_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id   TEXT NOT NULL,
            user_a     TEXT NOT NULL,
            user_b     TEXT NOT NULL,
            rounds_json TEXT NOT NULL,
            result      TEXT NOT NULL,
            stake_tokens INTEGER NOT NULL DEFAULT 0,
            reward_tokens_a INTEGER NOT NULL DEFAULT 0,
            reward_tokens_b INTEGER NOT NULL DEFAULT 0,
            reward_essence_a INTEGER NOT NULL DEFAULT 0,
            reward_essence_b INTEGER NOT NULL DEFAULT 0,
            created_ts  INTEGER NOT NULL
        )
        """
        )

        c.execute(
            """
        CREATE TABLE IF NOT EXISTS auction_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id         INTEGER NOT NULL,
            seller_user_id  TEXT NOT NULL,
            seller_guild_id TEXT NOT NULL,
            price_amount    INTEGER NOT NULL,
            price_currency  TEXT NOT NULL,
            status          TEXT NOT NULL,
            created_ts      INTEGER NOT NULL,
            expires_ts      INTEGER NOT NULL,
            buyer_user_id   TEXT,
            buyer_guild_id  TEXT
        )"""
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_auction_active ON auction_listings(status, expires_ts)"
        )

        c.execute(
            """
        CREATE TABLE IF NOT EXISTS streaks_guild (
            guild_id      TEXT NOT NULL,
            user_id       TEXT NOT NULL,
            daily_count   INTEGER NOT NULL DEFAULT 0,
            daily_day     INTEGER NOT NULL DEFAULT 0,
            weekly_count  INTEGER NOT NULL DEFAULT 0,
            weekly_key    TEXT NOT NULL DEFAULT '',
            PRIMARY KEY (guild_id, user_id)
        )
        """
        )

        c.execute(
            """
        CREATE TABLE IF NOT EXISTS trades_guild (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            proposer_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            proposer_card_id INTEGER NOT NULL,
            target_card_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_ts INTEGER NOT NULL
        )
        """
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_trades_open ON trades_guild(guild_id, target_id, status, created_ts)"
        )

        c.execute(
            """
        CREATE TABLE IF NOT EXISTS shop_state_guild (
            guild_id TEXT PRIMARY KEY,
            yyyymmdd INTEGER NOT NULL,
            items_json TEXT NOT NULL
        )
        """
        )
        c.execute(
            """
        CREATE TABLE IF NOT EXISTS shop_purchases_guild (
            guild_id TEXT NOT NULL,
            buyer_id TEXT NOT NULL,
            yyyymmdd INTEGER NOT NULL,
            slot INTEGER NOT NULL,
            UNIQUE (guild_id, yyyymmdd, slot)
        )
        """
        )

        c.execute(
            """
        CREATE TABLE IF NOT EXISTS weekly_events_guild (
            guild_id   TEXT PRIMARY KEY,
            week_key   TEXT NOT NULL,
            event_id   TEXT NOT NULL,
            created_ts INTEGER NOT NULL
        )
        """
        )

        conn.commit()


def _now_ts() -> int:
    return int(time.time())


def _guild_id(interaction: discord.Interaction) -> str:
    return str(interaction.guild.id) if interaction.guild else "DM"


# ----- Name cache helpers -----
def _note_display_name(conn: sqlite3.Connection, guild_id: str, user: discord.abc.User):
    display = (
        getattr(user, "display_name", None)
        or getattr(user, "global_name", None)
        or user.name
        or f"User {user.id}"
    )[:64]
    username = (user.name or str(user.id))[:64]
    conn.execute(
        """
        INSERT INTO users_names_guild(guild_id, user_id, display, username, updated_ts)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id) DO UPDATE SET
          display=excluded.display, username=excluded.username, updated_ts=excluded.updated_ts
    """,
        (guild_id, str(user.id), display, username, _now_ts()),
    )
    conn.commit()


async def _note_name_interaction(interaction: discord.Interaction) -> None:
    """Call this at the TOP of each slash command to cache display names safely."""
    if interaction.guild:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                _note_display_name(conn, _guild_id(interaction), interaction.user)
        except Exception:
            pass


async def _resolve_display_name(interaction: discord.Interaction, uid: int) -> str:
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT display FROM users_names_guild WHERE guild_id=? AND user_id=?",
            (gid, str(uid)),
        ).fetchone()
    if row and row["display"]:
        return row["display"]

    member = None
    if interaction.guild:
        member = interaction.guild.get_member(uid)
        if not member:
            try:
                member = await interaction.guild.fetch_member(uid)
            except Exception:
                member = None
    if member:
        with sqlite3.connect(DB_PATH) as conn:
            _note_display_name(conn, gid, member)
        return member.display_name

    try:
        user = await interaction.client.fetch_user(uid)
        with sqlite3.connect(DB_PATH) as conn:
            _note_display_name(conn, gid, user)
        return getattr(user, "global_name", None) or user.name or f"User {uid}"
    except Exception:
        return f"User {uid}"


# ----- Time helpers -----
def _even_2h_anchor(ts: int) -> int:
    lt = time.localtime(ts)
    even_hour = lt.tm_hour - (lt.tm_hour % 2)
    anchor = time.struct_time(
        (lt.tm_year, lt.tm_mon, lt.tm_mday, even_hour, 0, 0, lt.tm_wday, lt.tm_yday, lt.tm_isdst)
    )
    return int(time.mktime(anchor))


def _next_even_2h(ts: int) -> int:
    a = _even_2h_anchor(ts)
    nxt = a + TOKEN_REFILL_SECS
    if nxt <= ts:
        nxt += TOKEN_REFILL_SECS
    return nxt


def _midnight_anchor_local(ts: int) -> int:
    lt = time.localtime(ts)
    anchor = time.struct_time(
        (lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, lt.tm_wday, lt.tm_yday, lt.tm_isdst)
    )
    return int(time.mktime(anchor))


def _yyyymmdd_local(ts: int) -> int:
    lt = time.localtime(ts)
    # Proper YYYYMMDD integer
    return lt.tm_year * 10000 + lt.tm_mon * 100 + lt.tm_mday


def _iso_week_key(ts: int) -> str:
    return time.strftime("%G-%V", time.localtime(ts))

def _holiday_name(ts: Optional[int] = None) -> Optional[str]:

    if ts is None:
        ts = _now_ts()
    lt = time.localtime(ts)
    m, d = lt.tm_mon, lt.tm_mday

    fixed_holidays = {
        (1, 1): "New Year's Day",
        (2, 14): "Valentine's Day",
        (3, 17): "St. Patrick's Day",
        (7, 4): "Independence Day",
        (10, 31): "Halloween",
        (11, 11): "Veterans Day",
        (12, 24): "Christmas Eve",
        (12, 25): "Christmas Day",
        (12, 31): "New Year's Eve",
        (2, 29): "Leap Day",
    }

    return fixed_holidays.get((m, d))

# ----- Guild-scoped economy -----
def _accrue_tokens(conn: sqlite3.Connection, guild_id: str, user_id: int) -> Dict:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    row = cur.execute(
        "SELECT * FROM users_guild WHERE guild_id=? AND user_id=?",
        (guild_id, str(user_id)),
    ).fetchone()
    now = _now_ts()

    if row is None:
        anchor = _even_2h_anchor(now)
        starting = TOKEN_CAP if DEV_FORCE_MAX_TOKENS else TOKEN_INITIAL
        cur.execute(
            "INSERT INTO users_guild(guild_id, user_id, tokens, essence, tokens_used, first_seen_ts, last_update_ts) "
            "VALUES (?, ?, ?, 0, 0, ?, ?)",
            (guild_id, str(user_id), starting, now, anchor),
        )
        conn.commit()
        return {
            "guild_id": guild_id,
            "user_id": str(user_id),
            "tokens": starting,
            "essence": 0,
            "tokens_used": 0,
            "first_seen_ts": now,
            "last_update_ts": anchor,
        }

    user = dict(row)

    if DEV_FORCE_MAX_TOKENS and user["tokens"] < TOKEN_CAP:
        cur.execute(
            "UPDATE users_guild SET tokens=? WHERE guild_id=? AND user_id=?",
            (TOKEN_CAP, guild_id, str(user_id)),
        )
        conn.commit()
        user["tokens"] = TOKEN_CAP
        return user

    tokens = int(user["tokens"])
    last_up = int(user["last_update_ts"]) if user["last_update_ts"] else _even_2h_anchor(now)
    last_tick = last_up // TOKEN_REFILL_SECS
    this_tick = _even_2h_anchor(now) // TOKEN_REFILL_SECS
    ticks = max(0, this_tick - last_tick)

    if ticks > 0 and tokens < TOKEN_CAP:
        add = min(ticks, TOKEN_CAP - tokens)
        tokens += add
        user["tokens"] = tokens
        new_last = last_up + (add * TOKEN_REFILL_SECS)
        if new_last < _even_2h_anchor(now):
            new_last = _even_2h_anchor(now)
        user["last_update_ts"] = new_last
        cur.execute(
            "UPDATE users_guild SET tokens=?, last_update_ts=? WHERE guild_id=? AND user_id=?",
            (tokens, user["last_update_ts"], guild_id, str(user_id)),
        )
        conn.commit()
    return user


def _spend_tokens(
    conn: sqlite3.Connection, guild_id: str, user_id: int, amount: int
) -> Tuple[bool, Dict, str]:
    user = _accrue_tokens(conn, guild_id, user_id)
    if amount <= 0:
        return False, user, "Amount must be > 0."
    if user["tokens"] < amount:
        nxt = _next_even_2h(_now_ts())
        when = time.strftime("%I:%M %p", time.localtime(nxt)).lstrip("0")
        return False, user, f"You have {user['tokens']} token(s). Next refill at {when}."
    new_t = user["tokens"] - amount
    cur = conn.cursor()
    cur.execute(
        "UPDATE users_guild SET tokens=?, tokens_used=tokens_used+? WHERE guild_id=? AND user_id=?",
        (new_t, amount, guild_id, str(user_id)),
    )
    conn.commit()
    user["tokens"] = new_t
    user["tokens_used"] = user.get("tokens_used", 0) + amount
    return True, user, "ok"


def _add_tokens(conn: sqlite3.Connection, guild_id: str, user_id: int, amount: int) -> Dict:
    user = _accrue_tokens(conn, guild_id, user_id)
    new_t = min(TOKEN_CAP, user["tokens"] + max(0, amount))
    cur = conn.cursor()
    cur.execute(
        "UPDATE users_guild SET tokens=? WHERE guild_id=? AND user_id=?",
        (new_t, guild_id, str(user_id)),
    )
    conn.commit()
    user["tokens"] = new_t
    return user


def _add_essence(conn: sqlite3.Connection, guild_id: str, user_id: int, amount: int) -> Dict:
    user = _accrue_tokens(conn, guild_id, user_id)
    new_e = user["essence"] + max(0, amount)
    cur = conn.cursor()
    cur.execute(
        "UPDATE users_guild SET essence=? WHERE guild_id=? AND user_id=?",
        (new_e, guild_id, str(user_id)),
    )
    conn.commit()
    user["essence"] = new_e
    return user


def _add_essence_delta(
    conn: sqlite3.Connection, guild_id: str, user_id: int, delta: int
) -> Tuple[bool, int]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    row = cur.execute(
        "SELECT essence FROM users_guild WHERE guild_id=? AND user_id=?",
        (guild_id, str(user_id)),
    ).fetchone()
    if not row:
        _accrue_tokens(conn, guild_id, user_id)
        row = cur.execute(
            "SELECT essence FROM users_guild WHERE guild_id=? AND user_id=?",
            (guild_id, str(user_id)),
        ).fetchone()
    current = int(row["essence"])
    if delta < 0 and current < -delta:
        return False, current
    new_e = current + delta
    cur.execute(
        "UPDATE users_guild SET essence=? WHERE guild_id=? AND user_id=?",
        (new_e, guild_id, str(user_id)),
    )
    conn.commit()
    return True, new_e


# ----- Collection helpers -----
def _has_card(conn: sqlite3.Connection, guild_id: str, user_id: int, card_id: int) -> bool:
    cur = conn.cursor()
    r = cur.execute(
        "SELECT 1 FROM user_collection_guild WHERE guild_id=? AND user_id=? AND card_id=?",
        (guild_id, str(user_id), card_id),
    ).fetchone()
    return r is not None


def _give_card(conn: sqlite3.Connection, guild_id: str, user_id: int, card_id: int) -> None:
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO user_collection_guild(guild_id, user_id, card_id) VALUES (?, ?, ?)",
        (guild_id, str(user_id), card_id),
    )
    conn.commit()


def _remove_card(conn: sqlite3.Connection, guild_id: str, user_id: int, card_id: int) -> bool:
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM user_collection_guild WHERE guild_id=? AND user_id=? AND card_id=?",
        (guild_id, str(user_id), card_id),
    )
    conn.commit()
    return cur.rowcount > 0


def _user_owned_card_ids(
    conn: sqlite3.Connection, guild_id: str, user_id: int
) -> List[int]:
    cur = conn.cursor()
    return [
        r[0]
        for r in cur.execute(
            "SELECT card_id FROM user_collection_guild WHERE guild_id=? AND user_id=?",
            (guild_id, str(user_id)),
        )
    ]


# ----- Cards catalog -----
def fetch_pack_cards(pack: str) -> List[Dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, pack, name, english_no, variant_index, type, rarity, image_url "
            "FROM cards WHERE pack = ? ORDER BY id",
            (pack,),
        ).fetchall()
        return [dict(r) for r in rows]


def list_packs() -> List[str]:
    """
    Only allow the three known packs:
    - Black Bolt
    - Journey Together
    - Stormfront
    """
    return PACKS_ALL.copy()


def by_rarity(cards: List[Dict]) -> Dict[str, List[Dict]]:
    groups: Dict[str, List[Dict]] = {}
    for c in cards:
        groups.setdefault(c["rarity"], []).append(c)
    return groups


def choose_from_pool(pool: List[Dict], k: int, avoid_ids: set) -> List[Dict]:
    if not pool:
        return []
    choices = [c for c in pool if c["id"] not in avoid_ids]
    if len(choices) >= k:
        picks = random.sample(choices, k)
    else:
        picks = choices.copy()
        remaining = k - len(picks)
        for _ in range(max(0, remaining)):
            picks.append(random.choice(pool))
    return picks

# Hit tiers that count as "above Rare" and get boosted on holidays
HOLIDAY_BOOST_TIER_KEYS = {key for key, _ in HIT_TIERS if key != "rare"}

def _holiday_name(ts: Optional[int] = None) -> Optional[str]:
    """
    Return the name of a 'major' holiday for the given local date, or None.
    Used to slightly boost rare pulls on special days.
    """
    if ts is None:
        ts = _now_ts()
    lt = time.localtime(ts)
    year, m, d, w = lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_wday  # w: 0 = Monday

    # Fixed-date holidays (month, day) -> name
    fixed_holidays = {
        (1, 1): "New Year's Day",
        # Simple approximation of US presidential inauguration years
        (1, 20): "Inauguration Day" if year % 4 == 1 else None,
        (2, 14): "Valentine's Day",
        (3, 17): "St. Patrick's Day",
        (6, 19): "Juneteenth",
        (7, 4): "Independence Day",
        (10, 31): "Halloween",
        (11, 11): "Veterans Day",
        (12, 24): "Christmas Eve",
        (12, 25): "Christmas Day",
        (12, 31): "New Year's Eve",
        # Leap Day on leap years
        (2, 29): "Leap Day"
        if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))
        else None,
    }

    name = fixed_holidays.get((m, d))
    if name:
        return name

    # Helpers for "nth weekday" style holidays
    def is_nth_weekday_of_month(n: int, weekday: int) -> bool:
        # weekday: 0 = Monday, ..., 6 = Sunday
        return w == weekday and (d - 1) // 7 == n - 1

    def is_last_weekday_of_month(weekday: int) -> bool:
        if w != weekday:
            return False
        # Days in current month
        if m == 2:
            leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
            dim = 29 if leap else 28
        elif m in (1, 3, 5, 7, 8, 10, 12):
            dim = 31
        else:
            dim = 30
        return d + 7 > dim

    # US-style floating holidays
    if m == 1 and is_nth_weekday_of_month(3, 0):
        return "Martin Luther King Jr. Day"
    if m == 2 and is_nth_weekday_of_month(3, 0):
        return "Presidents' Day"
    if m == 5 and is_last_weekday_of_month(0):
        return "Memorial Day"
    if m == 9 and is_nth_weekday_of_month(1, 0):
        return "Labor Day"
    if m == 10 and is_nth_weekday_of_month(2, 0):
        return "Columbus Day"
    if m == 11 and is_nth_weekday_of_month(4, 3):
        return "Thanksgiving"

    # Easter (Western, Gregorian calendar)
    def easter_month_day(y: int) -> Tuple[int, int]:
        a = y % 19
        b = y // 100
        c = y % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m_ = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m_ + 114) // 31
        day = ((h + l - 7 * m_ + 114) % 31) + 1
        return month, day

    easter_m, easter_d = easter_month_day(year)
    if m == easter_m and d == easter_d:
        return "Easter Sunday"

    return None


def roll_hit_tier() -> Optional[str]:
    """
    Roll which rarity tier the hit slot should be.
    On recognized holidays, any tier above 'Rare' gets roughly 2× chance.
    """
    holiday = _holiday_name()
    is_holiday = holiday is not None

    for key, denom in HIT_TIERS:
        d = denom
        if is_holiday and key in HOLIDAY_BOOST_TIER_KEYS:
            d = max(1, denom // 2)
        if random.randint(1, d) == 1:
            return RARITY_NORMALIZE[key]
    return None

def open_one_pack(pack_name: str) -> Tuple[List[Dict], str]:
    all_cards = fetch_pack_cards(pack_name)
    if not all_cards:
        raise ValueError(f"Pack '{pack_name}' not found in DB.")

    groups = by_rarity(all_cards)

    commons_pool: List[Dict] = []
    for r in COMMON_POOL:
        commons_pool += groups.get(r, [])
    if not commons_pool:
        commons_pool = all_cards

    picked: List[Dict] = []
    used_ids = set()

    # first 8 slots
    first_eight = choose_from_pool(commons_pool, 8, used_ids)
    picked.extend(first_eight)
    used_ids.update(c["id"] for c in first_eight)

    # hit slot
    hit_label = roll_hit_tier()
    hit_card = None
    if hit_label:
        priority_order = [RARITY_NORMALIZE[k] for k, _ in HIT_TIERS]
        try:
            start = priority_order.index(hit_label)
        except ValueError:
            start = len(priority_order) - 1
        for idx in range(start, len(priority_order)):
            tier_label = priority_order[idx]
            tier_pool = groups.get(tier_label, [])
            if tier_pool:
                hit_card = choose_from_pool(tier_pool, 1, used_ids)[0]
                break
    if hit_card is None:
        hit_card = choose_from_pool(commons_pool, 1, used_ids)[0]
        hit_label = hit_card["rarity"]

    picked.append(hit_card)
    return picked, hit_label


# --------- Misc helpers ---------
def _emoji_link(url: str) -> str:
    url = (url or "").strip()
    return f"[{EMOJI_CARD}]({url})" if url else EMOJI_CARD


def _rarity_of_card_id(conn: sqlite3.Connection, cid: int) -> str:
    cur = conn.cursor()
    r = cur.execute("SELECT rarity FROM cards WHERE id=?", (cid,)).fetchone()
    return r[0] if r else "Common"


def _name_of_card_id(conn: sqlite3.Connection, cid: int) -> str:
    cur = conn.cursor()
    r = cur.execute("SELECT name FROM cards WHERE id=?", (cid,)).fetchone()
    return r[0] if r else f"Card {cid}"


def _label_of_card_id(conn: sqlite3.Connection, cid: int) -> str:
    cur = conn.cursor()
    r = cur.execute(
        "SELECT name, rarity, english_no FROM cards WHERE id=?", (cid,)
    ).fetchone()
    if r:
        return f"#{cid} | {r[0]} ({r[1]} / {r[2]})"
    return f"#{cid}"


# ------------- Image helpers -------------
def _is_image_content_type(ct: str) -> bool:
    return ct.lower().startswith("image/") if ct else False


def _looks_like_svg(ct: str, url: str, data_head: bytes) -> bool:
    if ct and "svg" in ct.lower():
        return True
    if re.search(r"\.svg($|\?)", url, re.I):
        return True
    head = data_head[:200].lstrip()
    return head.startswith(b"<svg") or head.startswith(b"<?xml")


def _infer_attach_ext_from_bytes(b: bytes) -> str:
    if b[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return ".webp"
    if b[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    return ".bin"


def _scale_and_encode(img_bytes: bytes) -> bytes:
    from PIL import Image as PILImage

    with PILImage.open(io.BytesIO(img_bytes)) as im:
        has_alpha = im.mode in ("RGBA", "LA") or (
            im.mode == "P" and "transparency" in im.info
        )
        im = im.convert("RGBA" if has_alpha else "RGB")
        w, h = im.size
        if max(w, h) > MAX_DIM:
            scale = MAX_DIM / float(max(w, h))
            im = im.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)
        if has_alpha:
            for comp in (6, 7, 9):
                out = io.BytesIO()
                im.save(out, format="PNG", optimize=True, compress_level=comp)
                if out.tell() <= MAX_UPLOAD_BYTES:
                    return out.getvalue()
            im = im.convert("RGB")
        for q in (90, 80, 70, 60, 50, 40, 30, 25, 20):
            out = io.BytesIO()
            im.save(out, format="JPEG", quality=q, optimize=True, progressive=True)
            if out.tell() <= MAX_UPLOAD_BYTES:
                return out.getvalue()
        return out.getvalue()


async def fetch_image_as_file(
    session: aiohttp.ClientSession, url: str, filename_base: str
) -> Tuple[Optional[discord.File], str]:
    if not url:
        return None, "no-url"
    try:
        parsed = urllib.parse.urlparse(url)
        referer = (
            f"{parsed.scheme}://{parsed.netloc}/"
            if parsed.scheme and parsed.netloc
            else None
        )
        headers = dict(FETCH_HEADERS)
        if referer:
            headers["Referer"] = referer
        async with session.get(
            url, timeout=25, headers=headers, allow_redirects=True
        ) as resp:
            status = resp.status
            if status != 200:
                return None, f"http-{status}"
            raw = await resp.read()
            content_type = resp.headers.get("Content-Type", "")
    except Exception as e:
        return None, f"fetch-error:{type(e).__name__}"

    head = raw[:256]
    if _looks_like_svg(content_type, url, head):
        if HAS_CAIROSVG:
            try:
                png_bytes = cairosvg.svg2png(
                    bytestring=raw, output_width=MAX_DIM, output_height=MAX_DIM
                )
                if len(png_bytes) > MAX_UPLOAD_BYTES:
                    png_bytes = _scale_and_encode(png_bytes)
                if len(png_bytes) > MAX_UPLOAD_BYTES:
                    return None, f"svg-too-big:{len(png_bytes)//1024}KB"
                f = discord.File(
                    io.BytesIO(png_bytes), filename=f"{filename_base}.png"
                )
                return f, "ok"
            except Exception:
                pass
        else:
            return None, "svg-requires-cairosvg"

    try:
        processed = _scale_and_encode(raw)
        if len(processed) > MAX_UPLOAD_BYTES:
            return None, f"too-big-after-compress:{len(processed)//1024}KB"
        ext = _infer_attach_ext_from_bytes(processed)
        if ext == ".bin":
            ext = ".jpg"
        file = discord.File(
            io.BytesIO(processed), filename=f"{filename_base}{ext}"
        )
        return file, "ok"
    except Exception:
        if _is_image_content_type(content_type) and len(raw) <= MAX_UPLOAD_BYTES:
            ext = mimetypes.guess_extension(
                content_type.split(";")[0].strip()
            ) or ".img"
            file = discord.File(
                io.BytesIO(raw), filename=f"{filename_base}{ext}"
            )
            return file, "raw-pass-through"
        return None, "encode-error:UnidentifiedImageError"


# ------------- Bot setup -------------
class CardBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=INTENTS)
        self.synced = False

    async def setup_hook(self):
        pass


bot = CardBot()


@bot.event
async def on_ready():
    ensure_db()
    # Fast per-guild sync so slash commands appear instantly in all connected servers
    try:
        synced_guilds = 0
        for g in bot.guilds:
            try:
                await bot.tree.sync(guild=discord.Object(id=g.id))
                print(
                    f"[sync] Slash commands synced to guild {g.id} ({g.name})"
                )
                synced_guilds += 1
            except Exception as e:
                print(f"[sync error] guild {g.id}: {e}")
        # Global sync as a fallback
        try:
            await bot.tree.sync()
            print("[sync] Global slash commands synced")
        except Exception as e:
            print(f"[global sync error] {e}")
        bot.synced = True
    except Exception as e:
        print(f"[sync outer error] {e}")

    await bot.change_presence(activity=discord.Game(name=BOT_ACTIVITY))
    print(f"Logged in as {bot.user} (id {bot.user.id})")


# Sync immediately when the bot joins a new guild
@bot.event
async def on_guild_join(guild: discord.Guild):
    try:
        await bot.tree.sync(guild=discord.Object(id=guild.id))
        print(f"[sync] Joined & synced {guild.id} ({guild.name})")
    except Exception as e:
        print(f"[sync error on join] {guild.id}: {e}")


# Manual resync helper
@bot.tree.command(
    name="resync", description="Force re-sync slash commands to all joined guilds."
)
@app_commands.guild_only()
async def resync_slash(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    ok = 0
    for g in interaction.client.guilds:
        try:
            await interaction.client.tree.sync(guild=discord.Object(id=g.id))
            ok += 1
        except Exception as e:
            print(f"[resync error] {g.id}: {e}")
    await interaction.followup.send(
        f"Resynced to {ok} guild(s).", ephemeral=True
    )


def choices_from(
    query: str, items: List[str], limit: int = 25
) -> List[app_commands.Choice[str]]:
    query_low = (query or "").lower()
    filtered = [p for p in items if query_low in p.lower()] if query_low else items
    return [
        app_commands.Choice(name=p, value=p) for p in filtered[:limit]
    ]


# =============== SLASH COMMANDS ===============

@bot.tree.command(
    name="weekly_event",
    description="Show this server's current weekly event and its effects.",
)
@app_commands.guild_only()
async def weekly_event_slash(interaction: discord.Interaction):
    await _note_name_interaction(interaction)
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        ev = _get_or_create_weekly_event(conn, gid)

    text = (
        f"📅 **This week's event:** {ev['name']}\n"
        f"{ev['description']}"
    )
    await interaction.response.send_message(text, ephemeral=False)

# /token
@bot.tree.command(
    name="token",
    description="Show your token balance and next refill time (per server).",
)
@app_commands.guild_only()
async def token_slash(interaction: discord.Interaction):
    await _note_name_interaction(interaction)
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        user = _accrue_tokens(conn, gid, interaction.user.id)
        nxt = _next_even_2h(_now_ts())
        when = time.strftime("%I:%M %p", time.localtime(nxt)).lstrip("0")
        await interaction.response.send_message(
            f"🪙 You have **{user['tokens']}** token(s) here. Next refill at **{when}**. (Max {TOKEN_CAP})",
            ephemeral=True,
        )


# /essence
@bot.tree.command(
    name="essence", description="Show your total essence in THIS server."
)
@app_commands.guild_only()
async def essence_slash(interaction: discord.Interaction):
    await _note_name_interaction(interaction)
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        user = _accrue_tokens(conn, gid, interaction.user.id)
        await interaction.response.send_message(
            f"💠 You have **{user['essence']}** essence in this server.",
            ephemeral=True,
        )


# /gamble
@bot.tree.command(
    name="gamble", description="Gamble some of your tokens in THIS server."
)
@app_commands.guild_only()
@app_commands.describe(amount="How many tokens to gamble (up to your balance here).")
async def gamble_slash(interaction: discord.Interaction, amount: int):
    await _note_name_interaction(interaction)
    if amount <= 0:
        await interaction.response.send_message(
            "Enter a positive amount.", ephemeral=True
        )
        return
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        user = _accrue_tokens(conn, gid, interaction.user.id)
        if amount > user["tokens"]:
            await interaction.response.send_message(
                f"You only have {user['tokens']} token(s) in this server.",
                ephemeral=True,
            )
            return

        _ok, user, _ = _spend_tokens(conn, gid, interaction.user.id, amount)
        roll = random.randint(1, 3)
        if roll == 1:
            _add_tokens(
                conn, gid, interaction.user.id, min(amount * 2, TOKEN_CAP)
            )
            msg = "✨ **Doubled your bet** and added to your tokens."
        elif roll == 2:
            _add_tokens(conn, gid, interaction.user.id, amount)
            msg = "😊 **Your bet is refunded**."
        else:
            give_back = amount // 2
            if give_back:
                _add_tokens(conn, gid, interaction.user.id, give_back)
            msg = "😴 **You lost half of your bet.**"

        final = _accrue_tokens(conn, gid, interaction.user.id)
        cap_note = (
            f" (Token cap {TOKEN_CAP} — extra vanishes)"
            if final["tokens"] >= TOKEN_CAP
            else ""
        )
        await interaction.response.send_message(
            f"{msg}\nCurrent tokens **here**: **{final['tokens']}**/{TOKEN_CAP}{cap_note}",
            ephemeral=True,
        )


# /sell
@bot.tree.command(
    name="sell",
    description="Sell tokens for essence in THIS server (200 essence per token).",
)
@app_commands.guild_only()
@app_commands.describe(amount="How many tokens you want to sell.")
async def sell_slash(interaction: discord.Interaction, amount: int):
    await _note_name_interaction(interaction)
    if amount <= 0:
        await interaction.response.send_message(
            "Use a number > 0.", ephemeral=True
        )
        return

    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        weekly_event = _get_or_create_weekly_event(conn, gid)
        user = _accrue_tokens(conn, gid, interaction.user.id)

        if amount > user["tokens"]:
            await interaction.response.send_message(
                f"Enter a number ≤ your tokens here (you have {user['tokens']}).",
                ephemeral=True,
            )
            return

        cur = conn.cursor()
        new_t = user["tokens"] - amount
        cur.execute(
            "UPDATE users_guild SET tokens=? WHERE guild_id=? AND user_id=?",
            (new_t, gid, str(interaction.user.id)),
        )

        base_essence = amount * ESSENCE_PER_TOKEN
        factor = float(_event_effect(weekly_event, "token_sell_essence_factor", 1.0))
        gained = int(round(base_essence * factor))
        conn.commit()

        _add_essence(conn, gid, interaction.user.id, gained)
        final = _accrue_tokens(conn, gid, interaction.user.id)

    mult_note = f" (×{factor:g} weekly bonus)" if factor != 1.0 else ""
    await interaction.response.send_message(
        f"💎 Sold **{amount}** token(s) for **{gained} essence**{mult_note}.\n"
        f"Now you have **{final['tokens']}** tokens and **{final['essence']}** essence here.",
        ephemeral=True,
    )

# -------- COLLECTION (PER PACK) --------
def _collection_embeds_for_pack(
    conn: sqlite3.Connection, guild_id: str, user_id: int, pack: str
) -> List[discord.Embed]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Pack completion
    total_cards = cur.execute(
        "SELECT COUNT(*) FROM cards WHERE pack=?", (pack,)
    ).fetchone()[0]

    owned_rows = cur.execute(
        """
        SELECT c.id
        FROM user_collection_guild u
        JOIN cards c ON c.id = u.card_id
        WHERE u.guild_id=? AND u.user_id=? AND c.pack=?
        """,
        (guild_id, str(user_id), pack),
    ).fetchall()

    owned_count = len(owned_rows)
    owned_card_ids = {row[0] for row in owned_rows}
    pct = int(round(owned_count * 100.0 / total_cards)) if total_cards else 0

    rows = cur.execute(
        """
        SELECT id, pack, name, english_no, type, rarity, image_url
        FROM cards
        WHERE pack=?
        ORDER BY 
          CASE WHEN instr(english_no, '/') > 0
               THEN CAST(substr(english_no, 1, instr(english_no, '/')-1) AS INTEGER)
               ELSE 9999 END,
          id
        """,
        (pack,),
    ).fetchall()

    embeds: List[discord.Embed] = []
    header = (
        f"**{pack} collection completion:** {owned_count}/{total_cards} cards ({pct}%)"
    )
    desc_lines: List[str] = [header]
    current_len = len(header)

    def flush_embed():
        nonlocal desc_lines, current_len
        if not desc_lines:
            return
        embed = discord.Embed(
            title=f"📚 Card Collection — {pack}",
            description="\n".join(desc_lines).strip(),
        )
        embeds.append(embed)
        desc_lines = []
        current_len = 0

    for row in rows:
        card_id, _, name, english_no, ctype, rarity, image_url = row

        if card_id in owned_card_ids:
            line = (
                f"\n**{english_no}** — {name} • *{ctype}* • **{rarity}** "
                f"{_emoji_link(image_url or '')}"
            )
        else:
            line = f"\n**{english_no}** — ???? (not yet discovered)"

        if current_len + len(line) > 3800:
            flush_embed()
        desc_lines.append(line)
        current_len += len(line)

    flush_embed()
    if embeds:
        embeds[-1].set_footer(text=f"{total_cards} total cards in pack '{pack}'.")
    return embeds


@bot.tree.command(
    name="collection",
    description="View your card collection for a specific pack in THIS server.",
)
@app_commands.guild_only()
@app_commands.describe(pack="Which pack do you want to view?")
async def collection_slash(interaction: discord.Interaction, pack: str):
    await _note_name_interaction(interaction)
    pack = (pack or "").strip()
    if pack not in list_packs():
        await interaction.response.send_message(
            f"Unknown pack. Valid options: {', '.join(PACKS_ALL)}",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        embeds = _collection_embeds_for_pack(conn, gid, interaction.user.id, pack)
    try:
        if len(embeds) <= 10:
            await interaction.followup.send(embeds=embeds, ephemeral=True)
        else:
            for i in range(0, len(embeds), 10):
                await interaction.followup.send(
                    embeds=embeds[i : i + 10], ephemeral=True
                )
    except discord.HTTPException:
        for emb in embeds:
            await interaction.followup.send(embed=emb, ephemeral=True)


# /scoreboard
@bot.tree.command(
    name="scoreboard",
    description="Server leaderboard by collection points and tokens used.",
)
@app_commands.guild_only()
async def scoreboard_slash(interaction: discord.Interaction):
    await _note_name_interaction(interaction)
    gid = _guild_id(interaction)
    rarity_points = dict(POINTS_FROM_RARITY)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rarities = {
            row["id"]: row["rarity"]
            for row in cur.execute("SELECT id, rarity FROM cards")
        }
        users = list(
            cur.execute(
                "SELECT user_id, tokens_used FROM users_guild WHERE guild_id=?",
                (gid,),
            )
        )
        scores = []
        for u in users:
            uid = u["user_id"]
            owned_ids = [
                r[0]
                for r in cur.execute(
                    "SELECT card_id FROM user_collection_guild WHERE guild_id=? AND user_id=?",
                    (gid, uid),
                )
            ]
            pts = 0
            for cid in owned_ids:
                r = rarities.get(cid, "Common")
                pts += rarity_points.get(r, 0)
            scores.append((int(uid), pts, u["tokens_used"]))

    lines = []
    scores.sort(key=lambda t: (-t[1], -t[2], t[0]))
    for rank, (uid, pts, used) in enumerate(scores[:25], start=1):
        display = await _resolve_display_name(interaction, uid)
        lines.append(
            f"**{rank}. {display}** — {pts} pts • tokens used: {used}"
        )

    if not lines:
        lines = ["No players yet. Open some packs!"]

    await interaction.response.send_message("\n".join(lines), ephemeral=False)


# Help
@bot.tree.command(
    name="help_cardbot", description="Show CardBot commands and what they do."
)
@app_commands.guild_only()
async def help_slash(interaction: discord.Interaction):
    await _note_name_interaction(interaction)
    text = (
        "**Core**\n"
        "**/packopen**, **/packs**, **/packsim**, **/collection**, **/scoreboard**, **/token**, **/sell**, **/essence**, **/gamble**\n"
        "\n**Duels**\n"
        "**/npcduel_start**, **/duel_challenge**, **/duel_accept**, **/duel_decline**\n"
        "\n**Auction House**\n"
        "**/mycards**, **/auction_list**, **/auction_browse**, **/auction_buy**, **/auction_cancel**\n"
        "Note: Use **/mycards** to copy a numeric ID, then pass it to **/auction_list** `card_id`.\n"
        "\n**Trading**\n"
        "**/trade_offer @user pack + card IDs**, **/trade_accept trade_id**, **/trade_decline trade_id**\n"
        "\n**Essence Shop**\n"
        "**/shop_show**, **/shop_buy slot**, **/shop_reset** (admin)\n"
    )
    await interaction.response.send_message(text, ephemeral=True)


# -------- PACK OPEN --------
@bot.tree.command(
    name="packopen",
    description="Open 1 pack (9 cards) in THIS server and display images.",
)
@app_commands.guild_only()
@app_commands.describe(pack="Choose a pack name (token packs only)")
async def packopen_slash(interaction: discord.Interaction, pack: str):
    await _note_name_interaction(interaction)
    gid = _guild_id(interaction)

    pack = (pack or "").strip()
    if pack not in TOKEN_PACKS:
        allowed = ", ".join(sorted(TOKEN_PACKS))
        await interaction.response.send_message(
            f"You can only open these packs with tokens: **{allowed}**.\n"
            f"**{STORMFRONT_PACK_NAME}** is a **shop-only** pack and can only be opened when purchased in `/shop_show` → `/shop_buy`.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(thinking=True, ephemeral=False)

    # Spend token + get weekly event
    with sqlite3.connect(DB_PATH) as conn:
        _note_display_name(conn, gid, interaction.user)
        weekly_event = _get_or_create_weekly_event(conn, gid)

        ok, user, reason = _spend_tokens(conn, gid, interaction.user.id, 1)
        if not ok:
            await interaction.followup.send(f"❌ {reason}")
            return

    dup_mult = float(_event_effect(weekly_event, "essence_from_dupes_multiplier", 1.0))
    refund_chance = float(_event_effect(weekly_event, "pack_token_refund_chance", 0.0))
    refunded_token = False

    try:
        cards, hit_label = open_one_pack(pack)
    except Exception as e:
        # Refund token on error
        with sqlite3.connect(DB_PATH) as conn:
            _add_tokens(conn, gid, interaction.user.id, 1)
        await interaction.followup.send(f"❌ {e}")
        return

    summary = discord.Embed(
        title=f"🎴 {pack} — You opened 1 pack!",
        description="\n".join(
            f"**{i}. {c['name']}** — *{c['rarity']}*  ({c['english_no']}) • {c['type']}"
            for i, c in enumerate(cards, start=1)
        ),
    )
    summary.set_footer(text=f"Hit slot result: {hit_label}")

    card_embeds: List[discord.Embed] = []
    files: List[discord.File] = []

    dup_total_essence = 0
    new_cards = 0

    async with aiohttp.ClientSession() as session:
        with sqlite3.connect(DB_PATH) as conn:
            for i, c in enumerate(cards, start=1):
                e = discord.Embed(
                    title=f"{i}. {c['name']}",
                    description=(
                        f"**Rarity:** {c['rarity']}\n"
                        f"**No.:** {c['english_no']}\n"
                        f"**Type:** {c['type']}"
                    ),
                )

                # New / duplicate handling with weekly essence multiplier
                if _has_card(conn, gid, interaction.user.id, c["id"]):
                    base_bonus = ESSENCE_FROM_RARITY.get(c["rarity"], 0)
                    bonus = int(round(base_bonus * dup_mult))
                    if bonus:
                        _add_essence(conn, gid, interaction.user.id, bonus)
                        dup_total_essence += bonus
                        mult_note = f" (×{dup_mult:g})" if dup_mult != 1.0 else ""
                        e.add_field(
                            name="Duplicate",
                            value=f"Converted to **{bonus} essence**{mult_note}",
                            inline=False,
                        )
                else:
                    _give_card(conn, gid, interaction.user.id, c["id"])
                    new_cards += 1

                # Fetch image
                img_url = (c.get("image_url") or "").strip()
                f, reason = await fetch_image_as_file(session, img_url, f"card_{i}")
                if f:
                    files.append(f)
                    e.set_image(url=f"attachment://{f.filename}")
                    if reason != "ok":
                        e.set_footer(text=f"({reason})")
                else:
                    if img_url:
                        e.set_image(url=img_url)
                        e.set_footer(text=f"(attachment skipped: {reason})")
                    else:
                        e.set_footer(text="(No image_url in DB for this card)")
                card_embeds.append(e)

    # Lucky token refund weekly event
    if refund_chance > 0.0 and random.random() < refund_chance:
        with sqlite3.connect(DB_PATH) as conn:
            _add_tokens(conn, gid, interaction.user.id, 1)
        refunded_token = True

    footer_bits = [f"New cards: {new_cards}"]
    if dup_total_essence:
        footer_bits.append(f"Essence from duplicates: {dup_total_essence}")
    if refunded_token:
        footer_bits.append("Weekly event refunded your token 🎉")

    summary.add_field(name="Results", value=" • ".join(footer_bits), inline=False)

    try:
        await interaction.followup.send(embeds=[summary, *card_embeds], files=files)
    except discord.HTTPException:
        mid = 1 + len(card_embeds) // 2
        files_first = files[: mid - 1]
        files_second = files[mid - 1 :]
        await interaction.followup.send(
            embeds=[summary, *card_embeds[:mid]], files=files_first
        )
        await interaction.followup.send(
            embeds=card_embeds[mid:], files=files_second
        )

@bot.tree.command(name="profile", description="Show specified user profile.")
@app_commands.guild_only()
@app_commands.describe(user="@User")
async def profile_slash(interaction: discord.Interaction, user: discord.User):
    await _note_name_interaction(interaction)
    gid = _guild_id(interaction)
    uid = user.id
    rarity_points = dict(POINTS_FROM_RARITY)

    # Load main data inside a single connection
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # card rarities
        rarities = {
            row["id"]: row["rarity"]
            for row in cur.execute("SELECT id, rarity FROM cards")
        }

        # tokens & profile card
        row = cur.execute(
            "SELECT tokens_used, profile_card FROM users_guild WHERE guild_id=? AND user_id=?",
            (gid, str(uid)),
        ).fetchone()
        token_count = row["tokens_used"] if row else 0
        profile_card = (
            row["profile_card"] if (row and row["profile_card"] != "blank") else None
        )

        # collection score
        owned_ids = [
            r[0]
            for r in cur.execute(
                "SELECT card_id FROM user_collection_guild WHERE guild_id=? AND user_id=?",
                (gid, str(uid)),
            )
        ]
        pts = 0
        for cid in owned_ids:
            r = rarities.get(cid, "Common")
            pts += rarity_points.get(r, 0)

        # if we have a favorite card, grab its image url now
        img_url = None
        if profile_card is not None:
            card_row = cur.execute(
                "SELECT image_url FROM cards WHERE id=?",
                (profile_card,),
            ).fetchone()
            img_url = card_row["image_url"] if card_row else None

    message_lines = [
        f"{user.mention}'s Profile",
        f"Tokens Used: {token_count}",
        f"Collection Score: {pts}",
    ]

    files: List[discord.File] = []
    embed: Optional[discord.Embed] = None

    if profile_card is not None and img_url:
        message_lines.append(f"Favorite Card: {profile_card}")
        async with aiohttp.ClientSession() as session:
            embed = discord.Embed()
            f, reason = await fetch_image_as_file(
                session, img_url, "profile_card"
            )
            if f:
                files.append(f)
                embed.set_image(url=f"attachment://{f.filename}")
                if reason != "ok":
                    embed.set_footer(text=f"({reason})")
            else:
                embed.set_image(url=img_url)
                embed.set_footer(text=f"(attachment skipped: {reason})")

    content = "\n".join(message_lines)

    # IMPORTANT: don't pass files=None to send_message
    if files:
        await interaction.response.send_message(
            content,
            embed=embed,
            files=files,
            ephemeral=False,
        )
    else:
        await interaction.response.send_message(
            content,
            embed=embed,
            ephemeral=False,
        )


# --- Packs list & sim ---
@bot.tree.command(
    name="packs", description="List all packs available (fixed list)."
)
@app_commands.guild_only()
async def packs_slash(interaction: discord.Interaction):
    await _note_name_interaction(interaction)
    packs = list_packs()
    if not packs:
        await interaction.response.send_message(
            "No packs configured.", ephemeral=True
        )
        return

    token_packs = [p for p in packs if p in TOKEN_PACKS]
    shop_packs = [p for p in packs if p in SHOP_ONLY_PACKS]
    other_packs = [
        p for p in packs if p not in TOKEN_PACKS and p not in SHOP_ONLY_PACKS
    ]

    lines: List[str] = ["**Available packs:**"]

    if token_packs:
        lines.append("\n**Token packs** (open with `/packopen`):")
        for p in sorted(token_packs):
            lines.append(f"- {p}")

    if shop_packs:
        lines.append("\n**Shop-only packs** (buy in `/shop_show` and open immediately):")
        for p in sorted(shop_packs):
            lines.append(f"- {p}")

    if other_packs:
        lines.append("\n**Other packs:**")
        for p in sorted(other_packs):
            lines.append(f"- {p}")

    await interaction.response.send_message("\n".join(lines), ephemeral=True)


@bot.tree.command(
    name="packsim", description="Simulate opening packs without spending tokens."
)
@app_commands.guild_only()
@app_commands.describe(
    pack="Pack name to simulate",
    n="How many packs to simulate (max 5000)",
)
async def packsim_slash(
    interaction: discord.Interaction,
    pack: str,
    n: int = 100,
):
    await _note_name_interaction(interaction)
    pack = (pack or "").strip()
    if pack not in list_packs():
        await interaction.response.send_message(
            f"Unknown pack. Valid options: {', '.join(PACKS_ALL)}",
            ephemeral=True,
        )
        return

    n = max(1, min(5000, n))
    await interaction.response.defer(ephemeral=True)
    rarity_counts: Dict[str, int] = {}
    hit_counts: Dict[str, int] = {}
    try:
        for _ in range(n):
            cards, hit_label = open_one_pack(pack)
            hit_counts[hit_label] = hit_counts.get(hit_label, 0) + 1
            for c in cards:
                rarity_counts[c["rarity"]] = (
                    rarity_counts.get(c["rarity"], 0) + 1
                )
    except Exception as e:
        await interaction.followup.send(f"❌ {e}", ephemeral=True)
        return

    exp_essence = 0
    for rar, cnt in rarity_counts.items():
        exp_essence += ESSENCE_FROM_RARITY.get(rar, 0) * cnt

    lines = ["**Pack Simulator**", f"Runs: **{n}** on **{pack}**"]
    lines.append("\n**Per-rarity pulls:**")
    for rar, cnt in sorted(
        rarity_counts.items(), key=lambda x: (-x[1], x[0])
    ):
        lines.append(f"- {rar}: {cnt}")
    lines.append("\n**Hit slot outcomes:**")
    for rar, cnt in sorted(hit_counts.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- {rar}: {cnt}")
    lines.append(
        f"\nUpper-bound essence (if all dupes): **{exp_essence}**"
    )

    await interaction.followup.send("\n".join(lines), ephemeral=True)


# --------- PvP Duels ---------
def _open_challenge_for_target(
    conn: sqlite3.Connection, guild_id: str, target_id: int
) -> Optional[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    return cur.execute(
        "SELECT * FROM pvp_duel_challenges WHERE guild_id=? AND target_id=? AND status='open' "
        "ORDER BY created_ts DESC LIMIT 1",
        (guild_id, str(target_id)),
    ).fetchone()


def _pvp_score_cards(conn: sqlite3.Connection, card_ids: List[int]) -> int:
    total = 0.0
    for cid in card_ids:
        rar = _rarity_of_card_id(conn, cid)
        total += PVP_RARITY_POWER.get(rar, 1)
    total += random.uniform(0, len(card_ids) * 0.75)
    return int(round(total))


def _sample_user_cards_for_duel(
    conn: sqlite3.Connection, guild_id: str, user_id: int, k: int
) -> List[int]:
    owned = _user_owned_card_ids(conn, guild_id, user_id)
    if len(owned) >= k:
        return random.sample(owned, k)

    # Fall back to sampling from the full pack if the user owns fewer than k cards
    try:
        pool = [c["id"] for c in fetch_pack_cards(PACK_NAME_DEFAULT)]
    except Exception:
        pool = []

    extra_needed = max(0, k - len(owned))
    extra = random.sample(pool, min(extra_needed, len(pool))) if pool else []

    # If pool is empty, just return whatever the user owns
    return (owned + extra)[:k]


@bot.tree.command(
    name="duel_challenge",
    description="Challenge another player in THIS server to a 3-round card duel.",
)
@app_commands.guild_only()
@app_commands.describe(
    user="Opponent @user",
    stake_tokens="Optional token stake; both players pay this amount",
)
async def duel_challenge_slash(
    interaction: discord.Interaction,
    user: discord.User,
    stake_tokens: int = 0,
):
    await _note_name_interaction(interaction)
    if not interaction.guild or user.bot or user.id == interaction.user.id:
        await interaction.response.send_message(
            "Pick a real human opponent in this server.",
            ephemeral=True,
        )
        return
    if stake_tokens < 0:
        await interaction.response.send_message(
            "Stake must be >= 0.", ephemeral=True
        )
        return
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        _note_display_name(conn, gid, interaction.user)
        _note_display_name(conn, gid, user)
        you = _accrue_tokens(conn, gid, interaction.user.id)
        if stake_tokens > you["tokens"]:
            await interaction.response.send_message(
                f"You only have {you['tokens']} token(s) here.",
                ephemeral=True,
            )
            return
        cur = conn.cursor()
        cur.execute(
            "UPDATE pvp_duel_challenges SET status='expired' "
            "WHERE guild_id=? AND status='open' AND created_ts<?",
            (gid, _now_ts() - 3600),
        )
        cur.execute(
            "INSERT INTO pvp_duel_challenges(guild_id,challenger_id,target_id,stake_tokens,status,created_ts) "
            "VALUES (?,?,?,?, 'open', ?)",
            (
                gid,
                str(interaction.user.id),
                str(user.id),
                max(0, stake_tokens),
                _now_ts(),
            ),
        )
        conn.commit()
    await interaction.response.send_message(
        f"📣 {user.mention}, **{interaction.user.display_name}** challenged you to a duel! "
        + (
            f"Stake: **{stake_tokens}** token(s) each."
            if stake_tokens
            else "No stake."
        ),
        ephemeral=False,
    )


@bot.tree.command(
    name="duel_accept",
    description="Accept the most recent duel challenge sent to you in THIS server.",
)
@app_commands.guild_only()
async def duel_accept_slash(interaction: discord.Interaction):
    await _note_name_interaction(interaction)
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        ch = _open_challenge_for_target(conn, gid, interaction.user.id)
        if not ch:
            await interaction.response.send_message(
                "No open challenge for you in this server.",
                ephemeral=True,
            )
            return
        stake = int(ch["stake_tokens"])
        if stake:
            ok_b, _, reason_b = _spend_tokens(
                conn, gid, interaction.user.id, stake
            )
            if not ok_b:
                await interaction.response.send_message(
                    f"You cannot cover the stake: {reason_b}",
                    ephemeral=True,
                )
                return
            ok_a, _, reason_a = _spend_tokens(
                conn, gid, int(ch["challenger_id"]), stake
            )
            if not ok_a:
                _add_tokens(conn, gid, interaction.user.id, stake)
                await interaction.response.send_message(
                    "Challenger no longer has the stake; challenge cancelled.",
                    ephemeral=True,
                )
                cur = conn.cursor()
                cur.execute(
                    "UPDATE pvp_duel_challenges SET status='cancelled' WHERE id=?",
                    (ch["id"],),
                )
                conn.commit()
                return

        rounds = []
        a_pts = b_pts = 0
        for _ in range(PVP_ROUNDS):
            a_cards = _sample_user_cards_for_duel(
                conn, gid, int(ch["challenger_id"]), 3
            )
            b_cards = _sample_user_cards_for_duel(
                conn, gid, int(ch["target_id"]), 3
            )
            ascore = _pvp_score_cards(conn, a_cards)
            bscore = _pvp_score_cards(conn, b_cards)
            if ascore > bscore:
                a_pts += 1
            elif bscore > ascore:
                b_pts += 1
            rounds.append(
                {
                    "a": a_cards,
                    "b": b_cards,
                    "ascore": ascore,
                    "bscore": bscore,
                }
            )

        await interaction.response.defer(ephemeral=False)
        a_user = interaction.guild.get_member(int(ch["challenger_id"]))
        b_user = interaction.guild.get_member(int(ch["target_id"]))
        await interaction.followup.send(
            f"⚔️ **{a_user.display_name if a_user else 'Challenger'}** vs "
            f"**{b_user.display_name if b_user else 'Target'}** — **Best of {PVP_ROUNDS}**!"
        )

        a_tally = b_tally = 0
        with sqlite3.connect(DB_PATH) as conn2:
            for i, rnd in enumerate(rounds, start=1):
                ascore, bscore = rnd["ascore"], rnd["bscore"]
                if ascore > bscore:
                    a_tally += 1
                    outcome = "Challenger wins the round!"
                elif bscore > ascore:
                    b_tally += 1
                    outcome = "Target wins the round!"
                else:
                    outcome = "It's a draw!"

                def label_list(ids):
                    return "\n".join(
                        f"- {_label_of_card_id(conn2, cid)}" for cid in ids
                    )

                emb = discord.Embed(
                    title=f"Round {i}",
                    description=(
                        f"**Challenger score:** {ascore}  •  **Target score:** {bscore}\n"
                        f"**Result:** {outcome}\n"
                        f"**Tally:** {a_tally} — {b_tally}"
                    ),
                )
                emb.add_field(
                    name="Challenger cards",
                    value=label_list(rnd["a"]) or "—",
                    inline=True,
                )
                emb.add_field(
                    name="Target cards",
                    value=label_list(rnd["b"]) or "—",
                    inline=True,
                )
                await interaction.followup.send(embed=emb)

        if a_pts > b_pts:
            winner = "a"
            rt_a = stake * 2 if stake else 0
            rt_b = 0
            re_a = PVP_ESSENCE_WIN
            re_b = PVP_ESSENCE_LOSS
        elif b_pts > a_pts:
            winner = "b"
            rt_b = stake * 2 if stake else 0
            rt_a = 0
            re_b = PVP_ESSENCE_WIN
            re_a = PVP_ESSENCE_LOSS
        else:
            winner = "draw"
            rt_a = stake if stake else 0
            rt_b = stake if stake else 0
            re_a = re_b = 150

        with sqlite3.connect(DB_PATH) as conn3:
            if rt_a:
                _add_tokens(
                    conn3, gid, int(ch["challenger_id"]), rt_a
                )
            if rt_b:
                _add_tokens(conn3, gid, int(ch["target_id"]), rt_b)
            if re_a:
                _add_essence(
                    conn3, gid, int(ch["challenger_id"]), re_a
                )
            if re_b:
                _add_essence(conn3, gid, int(ch["target_id"]), re_b)
            cur3 = conn3.cursor()
            cur3.execute(
                "UPDATE pvp_duel_challenges SET status='accepted' WHERE id=?",
                (ch["id"],),
            )
            cur3.execute(
                """
                INSERT INTO pvp_duel_matches(
                    guild_id,user_a,user_b,rounds_json,result,stake_tokens,
                    reward_tokens_a,reward_tokens_b,reward_essence_a,reward_essence_b,created_ts
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """
                ,
                (
                    gid,
                    ch["challenger_id"],
                    ch["target_id"],
                    str(rounds),
                    winner,
                    stake,
                    rt_a,
                    rt_b,
                    re_a,
                    re_b,
                    _now_ts(),
                ),
            )
            conn3.commit()

        result_text = (
            f"Final: **{a_pts} — {b_pts}** "
            f"Winner: **{'Challenger' if winner=='a' else ('Target' if winner=='b' else 'DRAW')}**\n"
            f"Stake: {stake} • Rewards → Challenger: 🪙{rt_a} 💠{re_a} | Target: 🪙{rt_b} 💠{re_b}"
        )
        await interaction.followup.send(
            embed=discord.Embed(title="Duel Result", description=result_text)
        )


@bot.tree.command(
    name="duel_decline",
    description="Decline the most recent duel challenge sent to you.",
)
@app_commands.guild_only()
async def duel_decline_slash(interaction: discord.Interaction):
    await _note_name_interaction(interaction)
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        ch = _open_challenge_for_target(conn, gid, interaction.user.id)
        if not ch:
            await interaction.response.send_message(
                "No open challenge for you.",
                ephemeral=True,
            )
            return
        cur = conn.cursor()
        cur.execute(
            "UPDATE pvp_duel_challenges SET status='declined' WHERE id=?",
            (ch["id"],),
        )
        conn.commit()
    await interaction.response.send_message(
        "❌ Challenge declined.", ephemeral=False
    )


# --------- Auction House ---------
def _owned_cards_with_metadata(
    conn: sqlite3.Connection, guild_id: str, user_id: int
) -> List[Dict]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT c.id, c.name, c.pack, c.english_no, c.variant_index, c.type, c.rarity, c.image_url
        FROM user_collection_guild u
        JOIN cards c ON c.id = u.card_id
        WHERE u.guild_id = ? AND u.user_id = ?
        ORDER BY 
          CASE 
            WHEN instr(c.english_no,'/') > 0 THEN CAST(substr(c.english_no, 1, instr(c.english_no,'/')-1) AS INTEGER)
            ELSE 9999
          END,
          c.id
        """,
        (guild_id, str(user_id)),
    ).fetchall()
    return [dict(r) for r in rows]


def _escrow_card_for_listing(
    conn: sqlite3.Connection, seller_guild_id: str, seller_user_id: int, card_id: int
) -> bool:
    return _remove_card(conn, seller_guild_id, seller_user_id, card_id)


def _deliver_card_to_buyer(
    conn: sqlite3.Connection, buyer_guild_id: str, buyer_user_id: int, card_id: int
):
    _give_card(conn, buyer_guild_id, buyer_user_id, card_id)


def _debit_currency(
    conn: sqlite3.Connection,
    guild_id: str,
    user_id: int,
    amount: int,
    currency: str,
) -> Tuple[bool, str]:
    if currency == "tokens":
        ok, _user, reason = _spend_tokens(conn, guild_id, user_id, amount)
        return ok, reason if not ok else "ok"
    elif currency == "essence":
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        row = cur.execute(
            "SELECT essence FROM users_guild WHERE guild_id=? AND user_id=?",
            (guild_id, str(user_id)),
        ).fetchone()
        bal = int(row["essence"]) if row else 0
        if bal < amount:
            return (
                False,
                f"Need {amount} essence; you have {bal} in this server.",
            )
        ok, _new = _add_essence_delta(conn, guild_id, user_id, -amount)
        return (True, "ok") if ok else (False, "Essence debit failed.")
    return False, "Unknown currency."


@bot.tree.command(
    name="mycards",
    description="List the cards you own from a specific pack in THIS server (by pack card number).",
)
@app_commands.guild_only()
@app_commands.describe(pack="Which pack to list your cards from")
async def mycards_slash(interaction: discord.Interaction, pack: str):
    await _note_name_interaction(interaction)
    pack = (pack or "").strip()
    if pack not in list_packs():
        await interaction.response.send_message(
            f"Unknown pack. Valid options: {', '.join(PACKS_ALL)}",
            ephemeral=True,
        )
        return

    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT c.id, c.name, c.rarity, c.english_no
            FROM user_collection_guild u
            JOIN cards c ON c.id = u.card_id
            WHERE u.guild_id=? AND u.user_id=? AND c.pack=?
            ORDER BY 
              CASE 
                WHEN instr(c.english_no,'/') > 0 THEN CAST(substr(c.english_no, 1, instr(c.english_no,'/')-1) AS INTEGER)
                ELSE 9999
              END,
              c.id
            LIMIT 500
            """,
            (gid, str(interaction.user.id), pack),
        ).fetchall()

        if not rows:
            await interaction.response.send_message(
                f"You don't own any cards from **{pack}** in this server.",
                ephemeral=True,
            )
            return

        lines = []
        for r in rows:
            english_no = r["english_no"] or ""
            display_no = None
            # Try to parse "119/159" -> 119
            if english_no:
                try:
                    num_part = english_no.split("/")[0]
                    display_no = int(num_part)
                except ValueError:
                    display_no = None
            if display_no is None:
                display_no = r["id"]  # fallback to DB id if weird

            # Show pack-local number, but still include DB ID for compatibility
            lines.append(
                f"{display_no:03d} — {r['name']} ({english_no}) [{r['rarity']}] (DB ID #{r['id']})"
            )

    text = f"**Your cards in {pack} (first 500):**\n" + "\n".join(lines)
    await interaction.response.send_message(text, ephemeral=True)



@bot.tree.command(
    name="auction_list",
    description="List one of your cards on the global market (buy-it-now).",
)
@app_commands.guild_only()
@app_commands.describe(
    pack="Pack name, e.g. 'Journey Together'",
    pack_number="Card number within that pack, e.g. 119 for 119/159",
    price_amount="Price",
    price_currency="'tokens' or 'essence'",
    expires_hours="How long the listing is active (default 72 hours)",
)
async def auction_list_slash(
    interaction: discord.Interaction,
    pack: str,
    pack_number: int,
    price_amount: int,
    price_currency: str,
    expires_hours: int = 72,
):
    await _note_name_interaction(interaction)
    gid = _guild_id(interaction)

    pack = (pack or "").strip()
    if pack not in list_packs():
        await interaction.response.send_message(
            f"Unknown pack. Valid options: {', '.join(PACKS_ALL)}",
            ephemeral=True,
        )
        return

    price_currency = (price_currency or "").lower().strip()
    if price_currency not in ("tokens", "essence"):
        await interaction.response.send_message(
            "Currency must be 'tokens' or 'essence'.",
            ephemeral=True,
        )
        return

    if price_amount <= 0:
        await interaction.response.send_message(
            "Price must be > 0.", ephemeral=True
        )
        return

    expires_hours = max(1, min(168, expires_hours))

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            _note_display_name(conn, gid, interaction.user)
            cur = conn.cursor()

            # Resolve (pack, pack_number) -> internal card_id
            cur.execute(
                """
                SELECT id, name, english_no
                FROM cards
                WHERE pack = ?
                  AND (
                        (instr(english_no, '/') > 0 AND
                         CAST(substr(english_no, 1, instr(english_no, '/')-1) AS INTEGER) = ?)
                     OR (instr(english_no, '/') = 0 AND
                         CAST(english_no AS INTEGER) = ?)
                  )
                ORDER BY id
                LIMIT 1
                """,
                (pack, pack_number, pack_number),
            )
            row = cur.fetchone()
            if not row:
                await interaction.response.send_message(
                    f"Could not find card number **{pack_number}** in pack **{pack}**.",
                    ephemeral=True,
                )
                return

            card_id = int(row["id"])

            # Ensure the user actually owns the card in this guild
            if not _has_card(conn, gid, interaction.user.id, card_id):
                await interaction.response.send_message(
                    f"You don't own card **#{pack_number}** in **{pack}** in this server. "
                    f"Use `/mycards {pack}` to check your collection.",
                    ephemeral=True,
                )
                return

            # Move card into escrow so they can't spend/sell it twice
            if not _escrow_card_for_listing(conn, gid, interaction.user.id, card_id):
                await interaction.response.send_message(
                    "Could not escrow card for listing (maybe already listed?).",
                    ephemeral=True,
                )
                return

            now = _now_ts()
            exp = now + expires_hours * 3600

            cur.execute(
                """
                INSERT INTO auction_listings(
                    card_id,
                    seller_user_id,
                    seller_guild_id,
                    price_amount,
                    price_currency,
                    status,
                    created_ts,
                    expires_ts
                )
                VALUES (?,?,?,?,?,'active',?,?)
                """,
                (
                    card_id,
                    str(interaction.user.id),
                    gid,
                    price_amount,
                    price_currency,
                    now,
                    exp,
                ),
            )
            conn.commit()
            listing_id = cur.lastrowid
            label = _label_of_card_id(conn, card_id)

        await interaction.response.send_message(
            f"📣 Listed **{label}** from **{pack}** (card #{pack_number}) "
            f"for **{price_amount} {price_currency}** (Listing **{listing_id}**).",
            ephemeral=False,
        )

    except Exception as e:
        await interaction.response.send_message(
            f"Something went wrong creating the listing: `{e}`",
            ephemeral=True,
        )

@bot.tree.command(
    name="auction_browse", description="Browse active global listings."
)
@app_commands.guild_only()
@app_commands.describe(limit="How many to show (max 20)", page="Page number starting at 1")
async def auction_browse_slash(
    interaction: discord.Interaction,
    limit: int = 10,
    page: int = 1,
):
    await _note_name_interaction(interaction)
    limit = max(1, min(20, limit))
    offset = (max(1, page) - 1) * limit

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT a.id, a.card_id, a.price_amount, a.price_currency, a.created_ts, a.expires_ts,
                   c.name, c.rarity, c.english_no, c.pack
            FROM auction_listings a
            JOIN cards c ON c.id = a.card_id
            WHERE a.status='active' AND a.expires_ts > ?
            ORDER BY a.created_ts DESC
            LIMIT ? OFFSET ?
            """,
            (_now_ts(), limit, offset),
        ).fetchall()

    if not rows:
        await interaction.response.send_message(
            "No active listings on this page.", ephemeral=True
        )
        return

    lines = [f"**Global Auction House** — page {page}"]
    for r in rows:
        english_no = r["english_no"] or ""
        try:
            display_no = (
                int(english_no.split("/")[0]) if english_no else r["card_id"]
            )
        except ValueError:
            display_no = r["card_id"]

        lines.append(
            f"- Listing **{r['id']}** | [{r['pack']}] #{display_no:03d} — {r['name']} ({english_no}) "
            f"— **{r['price_amount']} {r['price_currency']}**"
        )

    await interaction.response.send_message(
        "\n".join(lines), ephemeral=False
    )

@bot.tree.command(
    name="auction_buy", description="Buy a listing from the global market."
)
@app_commands.guild_only()
@app_commands.describe(
    pack="Pack that the listing's card is from",
    listing_id="Listing ID to purchase",
)
async def auction_buy_slash(
    interaction: discord.Interaction,
    pack: str,
    listing_id: int,
):
    await _note_name_interaction(interaction)
    pack = (pack or "").strip()
    if pack not in list_packs():
        await interaction.response.send_message(
            f"Unknown pack. Valid options: {', '.join(PACKS_ALL)}",
            ephemeral=True,
        )
        return

    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        r = cur.execute(
            """
            SELECT a.*
            FROM auction_listings a
            JOIN cards c ON c.id = a.card_id
            WHERE a.id=? AND c.pack=?
            """,
            (listing_id, pack),
        ).fetchone()
        if not r or r["status"] != "active" or r["expires_ts"] <= _now_ts():
            await interaction.response.send_message(
                "Listing not available for that pack.", ephemeral=True
            )
            return
        if str(interaction.user.id) == r["seller_user_id"]:
            await interaction.response.send_message(
                "You can't buy your own listing.", ephemeral=True
            )
            return

        ok, reason = _debit_currency(
            conn,
            gid,
            interaction.user.id,
            r["price_amount"],
            r["price_currency"],
        )
        if not ok:
            await interaction.response.send_message(
                f"❌ {reason}", ephemeral=True
            )
            return

        _deliver_card_to_buyer(
            conn, gid, interaction.user.id, r["card_id"]
        )
        cur.execute(
            """
            UPDATE auction_listings
            SET status='sold', buyer_user_id=?, buyer_guild_id=?
            WHERE id=? AND status='active'
            """,
            (str(interaction.user.id), gid, listing_id),
        )
        conn.commit()

    await interaction.response.send_message(
        f"✅ Purchased listing **{listing_id}** from pack **{pack}**. Card delivered to this server’s collection.",
        ephemeral=False,
    )


@bot.tree.command(
    name="auction_cancel",
    description="Cancel your active listing and return the card.",
)
@app_commands.guild_only()
@app_commands.describe(listing_id="Listing ID to cancel")
async def auction_cancel_slash(
    interaction: discord.Interaction, listing_id: int
):
    await _note_name_interaction(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        r = cur.execute(
            "SELECT * FROM auction_listings WHERE id=?", (listing_id,)
        ).fetchone()
        if not r or r["status"] != "active":
            await interaction.response.send_message(
                "Listing not active.", ephemeral=True
            )
            return
        if r["seller_user_id"] != str(interaction.user.id):
            await interaction.response.send_message(
                "Only the seller can cancel this listing.",
                ephemeral=True,
            )
            return
        _deliver_card_to_buyer(
            conn,
            r["seller_guild_id"],
            int(r["seller_user_id"]),
            r["card_id"],
        )
        cur.execute(
            "UPDATE auction_listings SET status='cancelled' WHERE id=?",
            (listing_id,),
        )
        conn.commit()
    await interaction.response.send_message(
        "🟨 Listing cancelled and card returned.", ephemeral=False
    )


# --------- NPC Duel helpers ---------
NPC_RARITY_WEIGHTS = {
    "rookie": {"Common": 60, "Uncommon": 35, "Rare": 5},
    "veteran": {"Common": 40, "Uncommon": 35, "Rare": 20, "Double Rare": 5},
    "master": {
        "Common": 25,
        "Uncommon": 30,
        "Rare": 25,
        "Double Rare": 10,
        "Ultra Rare": 7,
        "Illistration Rare": 3,
    },
}


def _weighted_choice(items: List[int], weights: List[int], k: int) -> List[int]:
    total = sum(weights)
    out: List[int] = []
    for _ in range(k):
        r = random.uniform(0, total)
        upto = 0
        for it, w in zip(items, weights):
            upto += w
            if upto >= r:
                out.append(it)
                break
    return out


def _npc_cards_for_duel(
    conn: sqlite3.Connection, difficulty: str, k: int
) -> List[int]:
    cards = fetch_pack_cards(PACK_NAME_DEFAULT)
    by_rar: Dict[str, List[int]] = {}
    for c in cards:
        by_rar.setdefault(c["rarity"], []).append(c["id"])
    weights = NPC_RARITY_WEIGHTS.get(difficulty, NPC_RARITY_WEIGHTS["veteran"])
    pop: List[int] = []
    wts: List[int] = []
    for rar, w in weights.items():
        ids = by_rar.get(rar, [])
        if not ids:
            continue
        per = max(1, w // max(1, len(ids)))
        for cid in ids:
            pop.append(cid)
            wts.append(per)
    if not pop:
        pop = [c["id"] for c in cards]
        wts = [1] * len(pop)
    return _weighted_choice(pop, wts, k)


def _score_cards(
    conn: sqlite3.Connection, card_ids: List[int], bias: float = 1.0
) -> int:
    total = 0.0
    for cid in card_ids:
        rar = _rarity_of_card_id(conn, cid)
        base = RARITY_POWER.get(rar, 1)
        total += base
    total *= bias
    total += random.uniform(0, len(card_ids) * 0.75)
    return int(round(total))


def _top_user_cards_for_duel(
    conn: sqlite3.Connection, guild_id: str, user_id: int, k: int
) -> List[int]:
    cur = conn.cursor()
    owned_ids = [
        r[0]
        for r in cur.execute(
            "SELECT card_id FROM user_collection_guild WHERE guild_id=? AND user_id=?",
            (guild_id, str(user_id)),
        )
    ]
    scored = []
    for cid in owned_ids:
        rar = _rarity_of_card_id(conn, cid)
        scored.append((RARITY_POWER.get(rar, 1), cid))
    scored.sort(reverse=True)
    top = [cid for _score, cid in scored[:k]]
    if len(top) < k:
        try:
            pack_ids = [c["id"] for c in fetch_pack_cards(PACK_NAME_DEFAULT)]
            random.shuffle(pack_ids)
            top += pack_ids[: (k - len(top))]
        except Exception:
            pass
    return top[:k]


def _duel_on_cooldown(
    conn: sqlite3.Connection, guild_id: str, user_id: int
) -> int:
    cur = conn.cursor()
    r = cur.execute(
        "SELECT next_ts FROM npc_duel_cd WHERE guild_id=? AND user_id=?",
        (guild_id, str(user_id)),
    ).fetchone()
    now = _now_ts()
    return max(0, (r[0] - now)) if r else 0


def _set_duel_cd(conn: sqlite3.Connection, guild_id: str, user_id: int):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO npc_duel_cd(guild_id, user_id, next_ts) VALUES (?,?,?) "
        "ON CONFLICT(guild_id, user_id) DO UPDATE SET next_ts=excluded.next_ts",
        (guild_id, str(user_id), _now_ts() + DUEL_COOLDOWN_SECS),
    )
    conn.commit()


@bot.tree.command(
    name="npcduel_start",
    description="Fight an NPC in a 3-round rarity-powered duel (with narration).",
)
@app_commands.guild_only()
@app_commands.describe(npc="rookie, veteran, or master", difficulty="easy, normal, hard")
async def npcduel_start_slash(
    interaction: discord.Interaction,
    npc: str,
    difficulty: str,
):
    await _note_name_interaction(interaction)
    npc = (npc or "").lower().strip()
    difficulty = (difficulty or "").lower().strip()
    if npc not in NPCS:
        await interaction.response.send_message(
            "NPC must be one of: rookie, veteran, master.",
            ephemeral=True,
        )
        return
    if difficulty not in DUEL_REWARDS:
        await interaction.response.send_message(
            "Difficulty must be one of: easy, normal, hard.",
            ephemeral=True,
        )
        return

    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        cd = _duel_on_cooldown(conn, gid, interaction.user.id)
        if cd > 0:
            mm = cd // 60
            ss = cd % 60
            await interaction.response.send_message(
                f"⏳ You can duel again in **{mm}m {ss}s**.",
                ephemeral=True,
            )
            return

        conn.row_factory = sqlite3.Row
        weekly_event = _get_or_create_weekly_event(conn, gid)

        rounds = []
        user_points = 0
        npc_points = 0

        base_bias_map = {"easy": 0.90, "normal": 0.98, "hard": 1.00}
        base_bias = base_bias_map.get(difficulty, 0.98)
        event_bias_factor = float(_event_effect(weekly_event, "npc_bias_factor", 1.0))
        bias = base_bias * event_bias_factor

        npc_key = npc

        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(
            f"⚔️ **{interaction.user.display_name}** vs **{NPCS[npc]['name']}** "
            f"({difficulty.title()}) — **Best of {DUEL_ROUNDS}** starts now!"
        )

        for r_i in range(1, DUEL_ROUNDS + 1):
            u_cards = _top_user_cards_for_duel(conn, gid, interaction.user.id, 3)
            n_cards = _npc_cards_for_duel(conn, npc_key, 3)

            us = _score_cards(conn, u_cards, 1.0)
            ns_raw = _score_cards(conn, n_cards, 1.0)
            ns = int(round(ns_raw * bias))

            if us > ns:
                user_points += 1
                round_outcome = "You win the round!"
            elif ns > us:
                npc_points += 1
                round_outcome = f"{NPCS[npc]['name']} wins the round!"
            else:
                round_outcome = "It's a draw!"

            rounds.append({"u": u_cards, "n": n_cards, "uscore": us, "nscore": ns})

            def label_list(ids):
                return "\n".join(f"- {_label_of_card_id(conn, cid)}" for cid in ids)

            emb = discord.Embed(
                title=f"Round {r_i}",
                description=(
                    f"**Your score:** {us}  •  **{NPCS[npc]['name']}'s score:** {ns}\n"
                    f"**Result:** {round_outcome}\n"
                    f"**Tally:** You {user_points} — {npc_points} {NPCS[npc]['name']}"
                ),
            )
            emb.add_field(
                name="Your cards", value=label_list(u_cards) or "—", inline=True
            )
            emb.add_field(
                name=f"{NPCS[npc]['name']}'s cards",
                value=label_list(n_cards) or "—",
                inline=True,
            )
            await interaction.followup.send(embed=emb)

        # Base rewards
        if user_points > npc_points:
            result = "win"
            rt, re = DUEL_REWARDS[difficulty]
        elif npc_points > user_points:
            result = "loss"
            rt, re = DUEL_CONSOLATION
        else:
            result = "draw"
            rt, re = (1, 200)

        # Weekly duel reward multiplier
        reward_mult = float(_event_effect(weekly_event, "duel_reward_multiplier", 1.0))
        rt = int(round(rt * reward_mult))
        re = int(round(re * reward_mult))

        if rt:
            _add_tokens(conn, gid, interaction.user.id, rt)
        if re:
            _add_essence(conn, gid, interaction.user.id, re)

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO npc_duel_matches(
                guild_id,user_id,npc_id,difficulty,rounds_json,result,reward_tokens,reward_essence,created_ts
            )
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                gid,
                str(interaction.user.id),
                npc,
                difficulty,
                str(rounds),
                result,
                rt,
                re,
                _now_ts(),
            ),
        )
        conn.commit()
        _set_duel_cd(conn, gid, interaction.user.id)

    final = discord.Embed(
        title="Duel Complete",
        description=(
            f"Final Score: **You {user_points} — {npc_points} {NPCS[npc]['name']}**\n"
            f"Outcome: **{result.upper()}**\n"
            f"Rewards: 🪙 +{rt}, 💠 +{re}"
        ),
    )
    await interaction.followup.send(embed=final)

# ------------- TRADING -------------
@bot.tree.command(
    name="trade_offer",
    description="Offer a card trade to another user (both cards must be owned here).",
)
@app_commands.guild_only()
@app_commands.describe(
    user="Target user",
    my_pack="Pack your card is from",
    my_card_id="Your card ID",
    their_pack="Pack their card is from",
    their_card_id="Their card ID",
)
async def trade_offer_slash(
    interaction: discord.Interaction,
    user: discord.User,
    my_pack: str,
    my_card_id: int,
    their_pack: str,
    their_card_id: int,
):
    await _note_name_interaction(interaction)
    if not interaction.guild or user.bot or user.id == interaction.user.id:
        await interaction.response.send_message(
            "Pick a real human opponent in this server.",
            ephemeral=True,
        )
        return

    my_pack = (my_pack or "").strip()
    their_pack = (their_pack or "").strip()
    if my_pack not in list_packs() or their_pack not in list_packs():
        await interaction.response.send_message(
            f"Unknown pack name. Valid options: {', '.join(PACKS_ALL)}",
            ephemeral=True,
        )
        return

    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        _note_display_name(conn, gid, interaction.user)
        _note_display_name(conn, gid, user)

        # Verify ownership
        if not _has_card(conn, gid, interaction.user.id, my_card_id):
            await interaction.response.send_message(
                "You do not own that card here.",
                ephemeral=True,
            )
            return
        if not _has_card(conn, gid, user.id, their_card_id):
            await interaction.response.send_message(
                "They do not own that card here.",
                ephemeral=True,
            )
            return

        # Verify pack match for each card
        cur = conn.cursor()
        my_row = cur.execute(
            "SELECT pack FROM cards WHERE id=?", (my_card_id,)
        ).fetchone()
        their_row = cur.execute(
            "SELECT pack FROM cards WHERE id=?", (their_card_id,)
        ).fetchone()

        if not my_row or my_row["pack"] != my_pack:
            await interaction.response.send_message(
                f"Your card **#{my_card_id}** is not from pack **{my_pack}**.",
                ephemeral=True,
            )
            return
        if not their_row or their_row["pack"] != their_pack:
            await interaction.response.send_message(
                f"Their card **#{their_card_id}** is not from pack **{their_pack}**.",
                ephemeral=True,
            )
            return

        cur.execute(
            """
            INSERT INTO trades_guild(
                guild_id,proposer_id,target_id,proposer_card_id,target_card_id,status,created_ts
            )
            VALUES (?,?,?,?,?,'open',?)
            """,
            (
                gid,
                str(interaction.user.id),
                str(user.id),
                my_card_id,
                their_card_id,
                _now_ts(),
            ),
        )
        conn.commit()
        tid = cur.lastrowid
        my_label = _label_of_card_id(conn, my_card_id)
        their_label = _label_of_card_id(conn, their_card_id)
    await interaction.response.send_message(
        f"📦 Trade **#{tid}** offered to {user.mention}:\n"
        f"**You give:** {my_label} (from {my_pack})\n**You get:** {their_label} (from {their_pack})\n"
        f"{user.mention} use `/trade_accept {tid}` or `/trade_decline {tid}`.",
        ephemeral=False,
    )


@bot.tree.command(
    name="trade_accept", description="Accept a pending trade offered to you."
)
@app_commands.guild_only()
@app_commands.describe(trade_id="Trade ID")
async def trade_accept_slash(
    interaction: discord.Interaction, trade_id: int
):
    await _note_name_interaction(interaction)
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        tr = cur.execute(
            "SELECT * FROM trades_guild WHERE id=?", (trade_id,)
        ).fetchone()
        if not tr or tr["guild_id"] != gid or tr["status"] != "open":
            await interaction.response.send_message(
                "Trade not available.", ephemeral=True
            )
            return
        if str(interaction.user.id) != tr["target_id"]:
            await interaction.response.send_message(
                "Only the target user can accept this trade.",
                ephemeral=True,
            )
            return

        proposer = int(tr["proposer_id"])
        target = int(tr["target_id"])
        a_card = int(tr["proposer_card_id"])
        b_card = int(tr["target_card_id"])

        if not _has_card(conn, gid, proposer, a_card):
            await interaction.response.send_message(
                "Proposer no longer owns their card.",
                ephemeral=True,
            )
            return
        if not _has_card(conn, gid, target, b_card):
            await interaction.response.send_message(
                "You no longer own your card.",
                ephemeral=True,
            )
            return

        if not _remove_card(conn, gid, proposer, a_card):
            await interaction.response.send_message(
                "Failed to move proposer card.",
                ephemeral=True,
            )
            return
        if not _remove_card(conn, gid, target, b_card):
            _give_card(conn, gid, proposer, a_card)
            await interaction.response.send_message(
                "Failed to move your card.",
                ephemeral=True,
            )
            return

        _give_card(conn, gid, target, a_card)
        _give_card(conn, gid, proposer, b_card)
        cur.execute(
            "UPDATE trades_guild SET status='accepted' WHERE id=?",
            (trade_id,),
        )
        conn.commit()

        my_label = _label_of_card_id(conn, a_card)
        their_label = _label_of_card_id(conn, b_card)
    proposer_name = await _resolve_display_name(interaction, proposer)
    target_name = await _resolve_display_name(interaction, target)
    await interaction.response.send_message(
        f"✅ Trade **#{trade_id}** completed.\n"
        f"{proposer_name} trades with {target_name}\n"
        f"**Moved:** {my_label} for {their_label}",
        ephemeral=False,
    )


@bot.tree.command(
    name="trade_decline", description="Decline a pending trade offered to you."
)
@app_commands.guild_only()
@app_commands.describe(trade_id="Trade ID")
async def trade_decline_slash(
    interaction: discord.Interaction, trade_id: int
):
    await _note_name_interaction(interaction)
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        tr = cur.execute(
            "SELECT * FROM trades_guild WHERE id=?", (trade_id,)
        ).fetchone()
        if not tr or tr["guild_id"] != gid or tr["status"] != "open":
            await interaction.response.send_message(
                "Trade not available.", ephemeral=True
            )
            return
        if str(interaction.user.id) not in (
            tr["target_id"],
            tr["proposer_id"],
        ):
            await interaction.response.send_message(
                "Only participants can decline this trade.",
                ephemeral=True,
            )
            return
        cur.execute(
            "UPDATE trades_guild SET status='declined' WHERE id=?",
            (trade_id,),
        )
        conn.commit()
    await interaction.response.send_message(
        "❌ Trade declined.", ephemeral=False
    )


# ------------- ESSENCE SHOP -------------
def _shop_today_key() -> int:
    return _yyyymmdd_local(_now_ts())


def _pick_random_card_ids_by_rarity(
    conn: sqlite3.Connection, rarities: List[str], k: int
) -> List[int]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    qs = ",".join("?" for _ in rarities)
    rows = cur.execute(
        f"SELECT id FROM cards WHERE rarity IN ({qs}) AND pack=?",
        (*rarities, PACK_NAME_DEFAULT),
    ).fetchall()
    ids = [r["id"] for r in rows]
    random.shuffle(ids)
    return ids[:k]


def _shop_generate_items(
    conn: sqlite3.Connection, guild_id: str
) -> List[Dict]:
    items = []
    token_slot = random.randint(1, SHOP_COMMON_SLOTS)
    for slot in range(1, SHOP_COMMON_SLOTS + 1):
        if slot == token_slot:
            items.append(
                {
                    "slot": slot,
                    "type": "tokens",
                    "price": SHOP_PRICE_TOKEN_BUNDLE,
                    "data": {"amount": SHOP_TOKEN_BUNDLE},
                    "stock": 1,
                }
            )
        else:
            ids = _pick_random_card_ids_by_rarity(
                conn, ["Common", "Uncommon"], 10
            )
            cid = ids[0] if ids else None
            items.append(
                {
                    "slot": slot,
                    "type": "card_common",
                    "price": SHOP_PRICE_COMMON_CARD,
                    "data": {"card_id": cid},
                    "stock": 1,
                }
            )
    rare_ids = _pick_random_card_ids_by_rarity(
        conn,
        [
            "Double Rare",
            "Rare Holo",
            "Ultra Rare",
            "Rare Holo LV.X",
            "Illistration Rare",
            "Special Illistration Rare",
            "Black White Rare",
            "Hyper Rare",
            "Rare Secret",
        ],
        10,
    )
    rare_cid = rare_ids[0] if rare_ids else None
    items.append(
        {
            "slot": SHOP_RARE_SLOT,
            "type": "card_rare",
            "price": SHOP_PRICE_RARE_CARD,
            "data": {"card_id": rare_cid},
            "stock": 1,
        }
    )
    # Special shop slot: Stormfront pack
    items.append(
        {
            "slot": SHOP_SPECIAL_SLOT,
            "type": "stormfront_pack",
            "price": STORMFRONT_PACK_PRICE,
            "data": {"pack": STORMFRONT_PACK_NAME},
            "stock": 1,
        }
    )
    return items


def _shop_get_or_create_today(
    conn: sqlite3.Connection, guild_id: str
) -> List[Dict]:
    today = _shop_today_key()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    row = cur.execute(
        "SELECT yyyymmdd, items_json FROM shop_state_guild WHERE guild_id=?",
        (guild_id,),
    ).fetchone()
    if row and int(row["yyyymmdd"]) == today:
        return json.loads(row["items_json"])
    items = _shop_generate_items(conn, guild_id)
    cur.execute(
        """
        INSERT INTO shop_state_guild(guild_id, yyyymmdd, items_json)
        VALUES (?,?,?)
        ON CONFLICT(guild_id) DO UPDATE SET yyyymmdd=excluded.yyyymmdd, items_json=excluded.items_json
        """,
        (guild_id, today, json.dumps(items)),
    )
    conn.commit()
    return items


def _shop_save(conn: sqlite3.Connection, guild_id: str, items: List[Dict]):
    today = _shop_today_key()
    conn.execute(
        """
        INSERT INTO shop_state_guild(guild_id, yyyymmdd, items_json)
        VALUES (?,?,?)
        ON CONFLICT(guild_id) DO UPDATE SET yyyymmdd=excluded.yyyymmdd, items_json=excluded.items_json
        """,
        (guild_id, today, json.dumps(items)),
    )
    conn.commit()


def _shop_card_label(conn: sqlite3.Connection, cid: Optional[int]) -> str:
    if not cid:
        return "(unknown card)"
    return _label_of_card_id(conn, cid)


@bot.tree.command(
    name="shop_show", description="Show today's Essence Shop (resets daily)."
)
@app_commands.guild_only()
async def shop_show_slash(interaction: discord.Interaction):
    await _note_name_interaction(interaction)
    await interaction.response.defer(ephemeral=False)
    try:
        gid = _guild_id(interaction)
        with sqlite3.connect(DB_PATH) as conn:
            weekly_event = _get_or_create_weekly_event(conn, gid)
            items = _shop_get_or_create_today(conn, gid)
            lines = [
                f"🛒 **Essence Shop — {time.strftime('%Y-%m-%d', time.localtime())}**"
            ]
            for it in items:
                slot = it["slot"]
                typ = it["type"]
                base_price = int(it["price"])
                price = _shop_effective_price(base_price, typ, weekly_event)
                stock = it["stock"]

                if typ == "tokens":
                    lines.append(
                        f"{slot}) **Token Bundle**: +{it['data']['amount']} tokens — **{price} essence**  (stock {stock})"
                    )
                elif typ == "card_common":
                    lines.append(
                        f"{slot}) **Common Card**: {_shop_card_label(conn, it['data']['card_id'])} — **{price} essence**  (stock {stock})"
                    )
                elif typ == "card_rare":
                    lines.append(
                        f"{slot}) **Rare Card**: {_shop_card_label(conn, it['data']['card_id'])} — **{price} essence**  (stock {stock})"
                    )
                elif typ == "stormfront_pack":
                    lines.append(
                        f"{slot}) **Stormfront Pack** (9 cards) — **{price} essence**  (stock {stock})"
                    )
                else:
                    lines.append(f"{slot}) (unknown item)")
            lines.append("\nBuy with `/shop_buy slot_number`.")
        await interaction.followup.send("\n".join(lines), ephemeral=False)
    except Exception as e:
        await interaction.followup.send(
            f"❌ Shop failed: `{type(e).__name__}: {e}`", ephemeral=True
        )

@bot.tree.command(
    name="shop_buy", description="Buy an item from today's Essence Shop."
)
@app_commands.guild_only()
@app_commands.describe(slot="Slot number (1-6)")
async def shop_buy_slash(interaction: discord.Interaction, slot: int):
    await _note_name_interaction(interaction)
    gid = _guild_id(interaction)
    if slot < 1 or slot > 6:
        await interaction.response.send_message(
            "Slot must be 1-6.", ephemeral=True
        )
        return

    summary_embed: Optional[discord.Embed] = None
    delivered: str = "(unknown)"

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        weekly_event = _get_or_create_weekly_event(conn, gid)
        items = _shop_get_or_create_today(conn, gid)
        item = next((it for it in items if it["slot"] == slot), None)
        if not item:
            await interaction.response.send_message(
                "That slot is not available.", ephemeral=True
            )
            return
        if item["stock"] <= 0:
            await interaction.response.send_message(
                "That item is sold out.", ephemeral=True
            )
            return

        base_price = int(item["price"])
        price = _shop_effective_price(base_price, item["type"], weekly_event)

        ok, _new = _add_essence_delta(conn, gid, interaction.user.id, -price)
        if not ok:
            bal_row = conn.execute(
                "SELECT essence FROM users_guild WHERE guild_id=? AND user_id=?",
                (gid, str(interaction.user.id)),
            ).fetchone()
            bal = int(bal_row["essence"]) if bal_row else 0
            await interaction.response.send_message(
                f"Not enough essence. Need {price}, you have {bal}.",
                ephemeral=True,
            )
            return

        if item["type"] == "tokens":
            _add_tokens(conn, gid, interaction.user.id, int(item["data"]["amount"]))
            delivered = f"+{item['data']['amount']} tokens"
        elif item["type"] in ("card_common", "card_rare"):
            cid = int(item["data"]["card_id"]) if item["data"]["card_id"] else None
            if not cid:
                await interaction.response.send_message(
                    "This card is unavailable.",
                    ephemeral=True,
                )
                return
            _give_card(conn, gid, interaction.user.id, cid)
            delivered = f"{_shop_card_label(conn, cid)}"
        elif item["type"] == "stormfront_pack":
            pack_name = item["data"].get("pack", STORMFRONT_PACK_NAME)
            try:
                cards, hit_label = open_one_pack(pack_name)
            except Exception as e:
                # Refund on failure
                _add_essence_delta(conn, gid, interaction.user.id, price)
                await interaction.response.send_message(
                    f"❌ Could not open pack: {e}", ephemeral=True
                )
                return

            new_cards = 0
            dup_cards = 0
            dup_essence = 0

            for c in cards:
                cid = c["id"]
                rarity = c["rarity"]
                if _has_card(conn, gid, interaction.user.id, cid):
                    dup_cards += 1
                    bonus = ESSENCE_FROM_RARITY.get(rarity, 0)
                    if bonus:
                        _add_essence(conn, gid, interaction.user.id, bonus)
                        dup_essence += bonus
                else:
                    new_cards += 1
                    _give_card(conn, gid, interaction.user.id, cid)

            delivered = (
                f"{pack_name} pack opened "
                f"({new_cards} new, {dup_cards} dupes, {dup_essence} essence)"
            )

            desc_lines = [
                f"- **{c['name']}** • *{c['rarity']}* ({c['english_no']})"
                for c in cards
            ]

            summary_text = (
                f"**Pack:** {pack_name}\n"
                f"**New cards:** {new_cards}\n"
                f"**Duplicates:** {dup_cards}\n"
                f"**Essence from duplicates:** {dup_essence}\n\n"
                + "\n".join(desc_lines)
            )

            summary_embed = discord.Embed(
                title="🌀 Stormfront Pack opened!",
                description=summary_text,
            )
            if hit_label:
                summary_embed.set_footer(text=f"Hit slot upgraded to: {hit_label}")
        else:
            delivered = "(unknown)"

        # Decrement stock for this slot and save
        for it in items:
            if it["slot"] == slot:
                it["stock"] = max(0, it["stock"] - 1)
                break
        _shop_save(conn, gid, items)

    if summary_embed:
        await interaction.response.send_message(
            f"✅ Purchased slot {slot}: **{delivered}**",
            embed=summary_embed,
            ephemeral=False,
        )
    else:
        await interaction.response.send_message(
            f"✅ Purchased slot {slot}: **{delivered}**",
            ephemeral=False,
        )

@bot.tree.command(
    name="shop_reset",
    description="(Admin) Force-refresh today's Essence Shop for this server.",
)
@app_commands.guild_only()
async def shop_reset_slash(interaction: discord.Interaction):
    await _note_name_interaction(interaction)
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "You need Manage Server permission.",
            ephemeral=True,
        )
        return
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        items = _shop_generate_items(conn, gid)
        _shop_save(conn, gid, items)
    await interaction.response.send_message(
        "🧹 Shop refreshed for today.", ephemeral=True
    )


# -------- /setcard pack number (set card for profile) --------
@bot.tree.command(name="setcard", description="Set your profile card")
@app_commands.guild_only()
@app_commands.describe(pack="Choose a pack name", card="Card ID (from /mycards)")
async def setcard_slash(
    interaction: discord.Interaction, pack: str, card: str
):
    ensure_db()
    await _note_name_interaction(interaction)
    pack = (pack or "").strip()
    if pack not in list_packs():
        await interaction.response.send_message(
            f"Unknown pack. Valid options: {', '.join(PACKS_ALL)}",
            ephemeral=True,
        )
        return

    gid = _guild_id(interaction)
    uid = interaction.user.id
    message = "Updated Profile Card"

    try:
        card_id = int(card)
    except ValueError:
        await interaction.response.send_message(
            "Card must be a numeric ID (from /mycards).",
            ephemeral=True,
        )
        return

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # Ensure the user owns the card AND it is from the given pack
        r = cur.execute(
            """
            SELECT 1
            FROM user_collection_guild u
            JOIN cards c ON c.id = u.card_id
            WHERE u.guild_id=? AND u.user_id=? AND u.card_id=? AND c.pack=?
            """,
            (str(gid), str(uid), card_id, pack),
        ).fetchone()
        if r is not None:
            try:
                cur.execute(
                    "UPDATE users_guild SET profile_card=? WHERE guild_id=? AND user_id=?",
                    (card, str(gid), str(uid)),
                )
                conn.commit()
            except Exception:
                cur.execute(
                    "ALTER TABLE users_guild ADD COLUMN profile_card TEXT NOT NULL DEFAULT 'blank'"
                )
                cur.execute(
                    "UPDATE users_guild SET profile_card=? WHERE guild_id=? AND user_id=?",
                    (card, str(gid), str(uid)),
                )
                conn.commit()
        else:
            message = "Failed to update card: you do not own that card in the specified pack."

    await interaction.response.send_message(message, ephemeral=True)

# fax
@bot.tree.command(name="fax", description="Show helpful information about how CardBot works.")
async def fax(interaction: discord.Interaction):
    """A user-friendly FAQ-style explanation of the core CardBot systems."""

    text = (
        "**📌 Tokens**\n"
        "Tokens refill automatically each day. You spend them to open packs.\n\n"

        "**📌 Essence**\n"
        "You earn essence by opening packs or selling tokens. Essence is used in shops.\n\n"

        "**📌 Collection Score**\n"
        "Your score increases based on card rarity. Higher rarity = more points.\n\n"

        "**📌 Favorite Card**\n"
        "Use /setcard to set one of your owned cards as your profile favorite.\n\n"

        "**📌 Shops**\n"
        "/shop_show displays today’s Essence Shop. /shop_buy lets you buy items.\n\n"

        "**📌 Trading**\n"
        "Use /trade_offer to send another user a card trade.\n\n"

        "**📌 Duels**\n"
        "Some servers support duels where card rarity determines power.\n\n"

        "**📌 Packs**\n"
        "Use /packopen to open a pack of 9 cards. Use /packs to view available packs.\n\n"

        "**📌 Weekly Events**\n"
        "Use /weekly_event to view special bonuses active this week.\n\n"

        "If you have more questions, try /help_cardbot for a full command list."
    )

    await interaction.response.send_message(text)

# -------- /cardinfo pack card_id (show a specific card) --------
@bot.tree.command(
    name="cardinfo",
    description="Show information and image for a specific card by pack + card ID."
)
@app_commands.guild_only()
@app_commands.describe(
    pack="Pack name (use /packs to see list)",
    card_id="Card ID number from /mycards or list"
)
async def cardinfo_slash(
    interaction: discord.Interaction,
    pack: str,
    card_id: int,
):
    ensure_db()
    await _note_name_interaction(interaction)

    # Clean and validate the pack input
    pack = (pack or "").strip()
    if pack not in list_packs():
        await interaction.response.send_message(
            f"Unknown pack. Valid options: {', '.join(PACKS_ALL)}",
            ephemeral=True,
        )
        return

    # Look up the card in the cards table
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        row = cur.execute(
            "SELECT * FROM cards WHERE pack=? AND id=?",
            (pack, card_id),
        ).fetchone()

    if row is None:
        await interaction.response.send_message(
            "No card found with that pack and ID.",
            ephemeral=True,
        )
        return

    keys = row.keys()

    # Safely read whatever fields exist in the table
    name = row["name"] if "name" in keys else f"Card #{row['id']}"
    rarity = row["rarity"] if "rarity" in keys else None
    supertype = row["supertype"] if "supertype" in keys else None
    subtype = row["subtype"] if "subtype" in keys else None
    hp = row["hp"] if "hp" in keys else None
    image_url = row["image_url"] if "image_url" in keys else None

    # Build a description using only available fields
    desc_lines = [
        f"**Pack:** {row['pack']}",
        f"**Card ID:** {row['id']}",
    ]
    if rarity:
        desc_lines.append(f"**Rarity:** {rarity}")
    if supertype:
        desc_lines.append(f"**Type:** {supertype}")
    if subtype:
        desc_lines.append(f"**Subtype:** {subtype}")
    if hp:
        desc_lines.append(f"**HP:** {hp}")

    description = "\n".join(desc_lines)

    embed = discord.Embed(
        title=name,
        description=description,
        color=0x00FF00,
    )
    if image_url:
        embed.set_image(url=image_url)

    await interaction.response.send_message(embed=embed)

# --------- Autocomplete for pack arguments ---------
@packopen_slash.autocomplete("pack")
async def packopen_pack_autocomplete(
    interaction: discord.Interaction, current: str
):
    try:
        selectable = [p for p in list_packs() if p in TOKEN_PACKS]
    except Exception:
        return []
    return choices_from(current, selectable)


@setcard_slash.autocomplete("pack")
async def setcard_pack_autocomplete(
    interaction: discord.Interaction, current: str
):
    try:
        packs = list_packs()
    except Exception:
        return []
    return choices_from(current, packs)


@collection_slash.autocomplete("pack")
async def collection_pack_autocomplete(
    interaction: discord.Interaction, current: str
):
    try:
        packs = list_packs()
    except Exception:
        return []
    return choices_from(current, packs)


@mycards_slash.autocomplete("pack")
async def mycards_pack_autocomplete(
    interaction: discord.Interaction, current: str
):
    try:
        packs = list_packs()
    except Exception:
        return []
    return choices_from(current, packs)


@packsim_slash.autocomplete("pack")
async def packsim_pack_autocomplete(
    interaction: discord.Interaction, current: str
):
    try:
        packs = list_packs()
    except Exception:
        return []
    return choices_from(current, packs)


@auction_buy_slash.autocomplete("pack")
async def auction_buy_pack_autocomplete(
    interaction: discord.Interaction, current: str
):
    try:
        packs = list_packs()
    except Exception:
        return []
    return choices_from(current, packs)

@auction_list_slash.autocomplete("pack")
async def auction_list_pack_autocomplete(
    interaction: discord.Interaction, current: str
):
    try:
        packs = list_packs()
    except Exception:
        return []
    return choices_from(current, packs)

@trade_offer_slash.autocomplete("my_pack")
async def trade_my_pack_autocomplete(
    interaction: discord.Interaction, current: str
):
    try:
        packs = list_packs()
    except Exception:
        return []
    return choices_from(current, packs)


@trade_offer_slash.autocomplete("their_pack")
async def trade_their_pack_autocomplete(
    interaction: discord.Interaction, current: str
):
    try:
        packs = list_packs()
    except Exception:
        return []
    return choices_from(current, packs)

@cardinfo_slash.autocomplete("pack")
async def cardinfo_pack_autocomplete(
    interaction: discord.Interaction,
    current: str,
):
    try:
        packs = list_packs()
    except Exception:
        return []
    return choices_from(current, packs)

# ------------- Entry -------------
if __name__ == "__main__":
    ensure_db()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError(
            "Set DISCORD_TOKEN environment variable (your bot token)."
        )
    bot.run(token)
