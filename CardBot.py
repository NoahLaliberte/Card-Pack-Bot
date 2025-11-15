# CardBot.py
# Token: MTQxOTEyMjA3MTE4MjY0MzM4Mg.GeG_dm.LCoJ1iESRp_NlLz-xMHc3jxKiZNg02AUFYRu2k
import os
import io
import re
import time
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
SQL_BOOTSTRAP = "black_bolt_types_placeholders.sql"  # .sql file for the cards table
INTENTS = discord.Intents.default()
INTENTS.members = True  # nicer names in /scoreboard (optional, but enable Members intent in Dev Portal)
BOT_ACTIVITY = "Opening packs (/packopen)"
GUILD_ID = os.getenv("GUILD_ID")  # e.g. "123456789012345678"
PACK_NAME_DEFAULT = "Black Bolt"

EMOJI_CARD = "🖼️"  # emoji used in /collection

# While testing, you can force everybody to be topped up to TOKEN_CAP each time their balance is loaded.
DEV_FORCE_MAX_TOKENS = True   # set False to use normal timed accrual

# ---------------------------

# ---------- IMAGE LIMITS / SETTINGS ----------
MAX_UPLOAD_BYTES = 7 * 1024 * 1024
MAX_DIM = 1024
FETCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DiscordCardBot/1.0",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}
# --------------------------------------------

# ---------- ECONOMY / POINTS ----------
TOKEN_CAP = 50
TOKEN_INITIAL = 10
TOKEN_REFILL_SECS = 2 * 60 * 60  # 2 hours
ESSENCE_PER_TOKEN = 350
TOTAL_CARDS = 172  # whole set (incl. specials)

# Essence from rarity (duplicates → essence)
ESSENCE_FROM_RARITY = {
    "Common": 100,
    "Uncommon": 250,
    "Rare": 500,
    "Double Rare": 1000,
    "Ultra Rare": 1250,
    "Illistration Rare": 1500,            # matches DB spelling
    "Special Illistration Rare": 2000,    # matches DB spelling
    "Black White Rare": 5000,
}

# Points for scoreboard
POINTS_FROM_RARITY = {
    "Common": 1,
    "Uncommon": 2,
    "Rare": 5,
    "Double Rare": 10,
    "Ultra Rare": 15,
    "Illistration Rare": 10,
    "Special Illistration Rare": 20,
    "Black White Rare": 35,
}

RARITY_NORMALIZE = {
    "common": "Common",
    "uncommon": "Uncommon",
    "rare": "Rare",
    "double rare": "Double Rare",
    # DB uses "Illistration Rare"
    "illustration rare": "Illistration Rare",
    "illistration rare": "Illistration Rare",
    "ultra rare": "Ultra Rare",
    # DB uses "Special Illistration Rare"
    "special illustration rare": "Special Illistration Rare",
    "special illistration rare": "Special Illistration Rare",
    # DB uses "Black White Rare"
    "black white rare": "Black White Rare",
    "black ewhite rare": "Black White Rare",
}

COMMON_POOL = {"Common", "Uncommon"}  # both are considered "common cards"

# Priority & odds for the hit slot (rarer first). Tuple: (normalized key, 1/N chance)
HIT_TIERS: List[Tuple[str, int]] = [
    ("black white rare", 20),
    ("special illistration rare", 18),
    ("ultra rare", 17),
    ("illistration rare", 15),
    ("double rare", 10),
    ("rare", 5),
]

# ------------- DB helpers -------------

def ensure_db():
    """Cards table (from SQL) + guild-scoped user tables."""
    if not os.path.exists(DB_PATH) and os.path.exists(SQL_BOOTSTRAP):
        with open(SQL_BOOTSTRAP, "r", encoding="utf-8") as f:
            sql_text = f.read()
        with sqlite3.connect(DB_PATH) as conn:
            conn.executescript(sql_text)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Guild-scoped users
        c.execute("""
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
        """)
        # Guild-scoped collection
        c.execute("""
        CREATE TABLE IF NOT EXISTS user_collection_guild (
            guild_id TEXT NOT NULL,
            user_id  TEXT NOT NULL,
            card_id  INTEGER NOT NULL,
            PRIMARY KEY(guild_id, user_id, card_id)
        )
        """)
        conn.commit()

def _now_ts() -> int:
    return int(time.time())

def _even_2h_anchor(ts: int) -> int:
    """Return the latest even-hour boundary <= ts (00, 02, 04, …) in local time."""
    lt = time.localtime(ts)
    even_hour = lt.tm_hour - (lt.tm_hour % 2)
    anchor = time.struct_time((lt.tm_year, lt.tm_mon, lt.tm_mday, even_hour, 0, 0,
                               lt.tm_wday, lt.tm_yday, lt.tm_isdst))
    return int(time.mktime(anchor))

def _next_even_2h(ts: int) -> int:
    a = _even_2h_anchor(ts)
    nxt = a + TOKEN_REFILL_SECS
    if nxt <= ts:
        nxt += TOKEN_REFILL_SECS
    return nxt

def _guild_id(interaction: discord.Interaction) -> str:
    return str(interaction.guild.id) if interaction.guild else "DM"

# ----- Guild-scoped economy -----

def _accrue_tokens(conn: sqlite3.Connection, guild_id: str, user_id: int) -> Dict:
    """Load or create guild-scoped user row, apply timed accrual OR dev force max."""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM users_guild WHERE guild_id=? AND user_id=?",
                      (guild_id, str(user_id))).fetchone()
    now = _now_ts()

    if row is None:
        anchor = _even_2h_anchor(now)
        starting = TOKEN_CAP if DEV_FORCE_MAX_TOKENS else TOKEN_INITIAL
        cur.execute(
            "INSERT INTO users_guild(guild_id, user_id, tokens, essence, tokens_used, first_seen_ts, last_update_ts) "
            "VALUES (?, ?, ?, 0, 0, ?, ?)",
            (guild_id, str(user_id), starting, now, anchor)
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

    # During testing, keep everyone topped up to the cap.
    if DEV_FORCE_MAX_TOKENS and user["tokens"] < TOKEN_CAP:
        cur.execute("UPDATE users_guild SET tokens=? WHERE guild_id=? AND user_id=?",
                    (TOKEN_CAP, guild_id, str(user_id)))
        conn.commit()
        user["tokens"] = TOKEN_CAP
        return user

    # Normal timed accrual
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
            (tokens, user["last_update_ts"], guild_id, str(user_id))
        )
        conn.commit()
    return user

def _spend_tokens(conn: sqlite3.Connection, guild_id: str, user_id: int, amount: int) -> Tuple[bool, Dict, str]:
    user = _accrue_tokens(conn, guild_id, user_id)
    if amount <= 0:
        return False, user, "Amount must be > 0."
    if user["tokens"] < amount:
        nxt = _next_even_2h(_now_ts())
        # Windows doesn't support %-I, so handle left-trim of 0
        when = time.strftime("%I:%M %p", time.localtime(nxt)).lstrip("0")
        return False, user, f"You have {user['tokens']} token(s). Next refill at {when}."
    new_t = user["tokens"] - amount
    cur = conn.cursor()
    cur.execute("UPDATE users_guild SET tokens=?, tokens_used=tokens_used+? WHERE guild_id=? AND user_id=?",
                (new_t, amount, guild_id, str(user_id)))
    conn.commit()
    user["tokens"] = new_t
    user["tokens_used"] = user.get("tokens_used", 0) + amount
    return True, user, "ok"

def _add_tokens(conn: sqlite3.Connection, guild_id: str, user_id: int, amount: int) -> Dict:
    user = _accrue_tokens(conn, guild_id, user_id)
    new_t = min(TOKEN_CAP, user["tokens"] + max(0, amount))
    cur = conn.cursor()
    cur.execute("UPDATE users_guild SET tokens=? WHERE guild_id=? AND user_id=?",
                (new_t, guild_id, str(user_id)))
    conn.commit()
    user["tokens"] = new_t
    return user

def _add_essence(conn: sqlite3.Connection, guild_id: str, user_id: int, amount: int) -> Dict:
    user = _accrue_tokens(conn, guild_id, user_id)
    new_e = user["essence"] + max(0, amount)
    cur = conn.cursor()
    cur.execute("UPDATE users_guild SET essence=? WHERE guild_id=? AND user_id=?",
                (new_e, guild_id, str(user_id)))
    conn.commit()
    user["essence"] = new_e
    return user

# ----- Guild-scoped collection -----

def _has_card(conn: sqlite3.Connection, guild_id: str, user_id: int, card_id: int) -> bool:
    cur = conn.cursor()
    r = cur.execute(
        "SELECT 1 FROM user_collection_guild WHERE guild_id=? AND user_id=? AND card_id=?",
        (guild_id, str(user_id), card_id)
    ).fetchone()
    return r is not None

def _give_card(conn: sqlite3.Connection, guild_id: str, user_id: int, card_id: int) -> None:
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO user_collection_guild(guild_id, user_id, card_id) VALUES (?, ?, ?)",
                (guild_id, str(user_id), card_id))
    conn.commit()

# ----- Cards -----

def fetch_pack_cards(pack: str) -> List[Dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, pack, name, english_no, variant_index, type, rarity, image_url "
            "FROM cards WHERE pack = ? ORDER BY id", (pack,)
        ).fetchall()
        return [dict(r) for r in rows]

def list_packs() -> List[str]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT DISTINCT pack FROM cards ORDER BY pack").fetchall()
        return [r[0] for r in rows]

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

def roll_hit_tier() -> Optional[str]:
    for key, denom in HIT_TIERS:
        if random.randint(1, denom) == 1:
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

    first_eight = choose_from_pool(commons_pool, 8, used_ids)
    picked.extend(first_eight)
    used_ids.update(c["id"] for c in first_eight)

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
    from PIL import Image
    with Image.open(io.BytesIO(img_bytes)) as im:
        has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
        im = im.convert("RGBA" if has_alpha else "RGB")
        w, h = im.size
        if max(w, h) > MAX_DIM:
            scale = MAX_DIM / float(max(w, h))
            im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
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

async def fetch_image_as_file(session: aiohttp.ClientSession, url: str, filename_base: str) -> Tuple[Optional[discord.File], str]:
    if not url:
        return None, "no-url"
    try:
        parsed = urllib.parse.urlparse(url)
        referer = f"{parsed.scheme}://{parsed.netloc}/" if parsed.scheme and parsed.netloc else None
        headers = dict(FETCH_HEADERS)
        if referer:
            headers["Referer"] = referer
        async with session.get(url, timeout=25, headers=headers, allow_redirects=True) as resp:
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
                png_bytes = cairosvg.svg2png(bytestring=raw, output_width=MAX_DIM, output_height=MAX_DIM)
                if len(png_bytes) > MAX_UPLOAD_BYTES:
                    png_bytes = _scale_and_encode(png_bytes)
                if len(png_bytes) > MAX_UPLOAD_BYTES:
                    return None, f"svg-too-big:{len(png_bytes)//1024}KB"
                f = discord.File(io.BytesIO(png_bytes), filename=f"{filename_base}.png")
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
        file = discord.File(io.BytesIO(processed), filename=f"{filename_base}{ext}")
        return file, "ok"
    except Exception:
        if _is_image_content_type(content_type) and len(raw) <= MAX_UPLOAD_BYTES:
            ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".img"
            file = discord.File(io.BytesIO(raw), filename=f"{filename_base}{ext}")
            return file, "raw-pass-through"
        return None, "encode-error:UnidentifiedImageError"

# ------------- Bot setup -------------

class CardBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=INTENTS)
        self.synced = False
        self.guild = None
        if GUILD_ID:
            try:
                self.guild = discord.Object(id=int(GUILD_ID))
            except ValueError:
                print("WARN: GUILD_ID is set but not an integer; syncing globally.")

    async def setup_hook(self):
        pass

bot = CardBot()

@bot.event
async def on_ready():
    ensure_db()
    if not bot.synced:
        try:
            if bot.guild:
                await bot.tree.sync(guild=bot.guild)
                print(f"[sync] Slash commands synced to guild {bot.guild.id}")
            else:
                await bot.tree.sync()
                print("[sync] Global slash commands synced")
            bot.synced = True
        except Exception as e:
            print(f"[sync error] {e}")
    await bot.change_presence(activity=discord.Game(name=BOT_ACTIVITY))
    print(f"Logged in as {bot.user} (id {bot.user.id})")

# --------- Utility ---------

def choices_from(query: str, items: List[str], limit: int = 25) -> List[app_commands.Choice[str]]:
    query_low = (query or "").lower()
    filtered = [p for p in items if query_low in p.lower()] if query_low else items
    return [app_commands.Choice(name=p, value=p) for p in filtered[:limit]]

def _emoji_link(url: str) -> str:
    """Clickable emoji linking to the image (falls back to plain emoji)."""
    url = (url or "").strip()
    return f"[{EMOJI_CARD}]({url})" if url else EMOJI_CARD

# =============== SLASH COMMANDS ===============

# /token — show current token count and next refill time (guild-scoped)
@bot.tree.command(name="token", description="Show your token balance and next refill time (per server).")
async def token_slash(interaction: discord.Interaction):
    ensure_db()
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        user = _accrue_tokens(conn, gid, interaction.user.id)
        nxt = _next_even_2h(_now_ts())
        when = time.strftime("%I:%M %p", time.localtime(nxt)).lstrip("0")
        await interaction.response.send_message(
            f"🪙 You have **{user['tokens']}** token(s) here. Next refill at **{when}**. (Max {TOKEN_CAP})",
            ephemeral=True
        )

# /gamble amount (guild-scoped)
@bot.tree.command(name="gamble", description="Gamble some of your tokens in THIS server. Outcomes: double / refund / lose half.")
@app_commands.describe(amount="How many tokens to gamble (up to your balance here).")
async def gamble_slash(interaction: discord.Interaction, amount: int):
    ensure_db()
    if amount <= 0:
        await interaction.response.send_message(
            "Enter a positive amount. Reminder: token cap is 50.", ephemeral=True)
        return
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        user = _accrue_tokens(conn, gid, interaction.user.id)
        if amount > user["tokens"]:
            await interaction.response.send_message(
                f"You only have {user['tokens']} token(s) in this server.", ephemeral=True)
            return

        _ok, user, _ = _spend_tokens(conn, gid, interaction.user.id, amount)
        roll = random.randint(1, 3)
        if roll == 1:
            _add_tokens(conn, gid, interaction.user.id, min(amount * 2, TOKEN_CAP))
            msg = "✨ The Pokémon adore you! **Doubled your bet** and added it to your tokens."
        elif roll == 2:
            _add_tokens(conn, gid, interaction.user.id, amount)
            msg = "😊 The Pokémon are generous. **Your bet is refunded**."
        else:
            give_back = amount // 2
            if give_back:
                _add_tokens(conn, gid, interaction.user.id, give_back)
            msg = "😴 The Pokémon felt like Snorlax today. **You lost half of your bet.**"

        final = _accrue_tokens(conn, gid, interaction.user.id)
        cap_note = " (Token cap 50 — extra vanishes)" if final["tokens"] >= TOKEN_CAP else ""
        await interaction.response.send_message(
            f"{msg}\nCurrent tokens **here**: **{final['tokens']}**/{TOKEN_CAP}{cap_note}",
            ephemeral=True
        )

# /sell amount — sell tokens for essence (guild-scoped)
@bot.tree.command(name="sell", description="Sell tokens for Pokémon essence in THIS server (350 essence per token).")
@app_commands.describe(amount="How many tokens you want to sell.")
async def sell_slash(interaction: discord.Interaction, amount: int):
    ensure_db()
    if amount <= 0:
        await interaction.response.send_message(
            "🤨 The Pokémon are confused—you can't sell invisible tokens. Use a number > 0.",
            ephemeral=True
        )
        return
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        user = _accrue_tokens(conn, gid, interaction.user.id)
        if amount > user["tokens"]:
            await interaction.response.send_message(
                f"😡 The Pokémon got angry at your attempt to cheat. "
                f"Enter a number ≤ your tokens here (you have {user['tokens']}).",
                ephemeral=True
            )
            return
        cur = conn.cursor()
        new_t = user["tokens"] - amount
        cur.execute("UPDATE users_guild SET tokens=? WHERE guild_id=? AND user_id=?",
                    (new_t, gid, str(interaction.user.id)))
        conn.commit()
        gained = amount * ESSENCE_PER_TOKEN
        _add_essence(conn, gid, interaction.user.id, gained)
        final = _accrue_tokens(conn, gid, interaction.user.id)
        await interaction.response.send_message(
            f"💎 Sold **{amount}** token(s) for **{gained} essence**.\n"
            f"Now you have **{final['tokens']}** tokens and **{final['essence']}** essence in this server.",
            ephemeral=True
        )

# /essence — show essence (guild-scoped)
@bot.tree.command(name="essence", description="Show your total Pokémon essence in THIS server.")
async def essence_slash(interaction: discord.Interaction):
    ensure_db()
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        user = _accrue_tokens(conn, gid, interaction.user.id)
        await interaction.response.send_message(
            f"💠 You have **{user['essence']}** essence in this server.", ephemeral=True
        )

# -------- FULL COLLECTION VIEW (001–086 + specials under each) --------

def _collection_embeds_full(conn: sqlite3.Connection, guild_id: str, user_id: int) -> List[discord.Embed]:
    """
    Build a full collection view:
      - Base cards 001..086 listed in order
      - Under each base card, a 'Special' line listing special variants for that Pokémon name
      - Owned base/specials show details + clickable emoji to the image; unowned show ????? placeholders
      - Splits across multiple embeds if too long
    """
    cards = fetch_pack_cards(PACK_NAME_DEFAULT)

    # split base vs specials; group specials by name
    base_cards: List[Dict] = []
    specials_by_name: Dict[str, List[Dict]] = {}
    for c in cards:
        try:
            n = int(c["english_no"].split("/")[0])
        except Exception:
            n = 999
        if n <= 86:
            base_cards.append(c)
        else:
            specials_by_name.setdefault(c["name"], []).append(c)

    base_cards.sort(key=lambda x: int(x["english_no"].split("/")[0]))
    for name in specials_by_name:
        specials_by_name[name].sort(key=lambda x: int(x["english_no"].split("/")[0]))

    cur = conn.cursor()
    owned = cur.execute(
        "SELECT COUNT(*) FROM user_collection_guild WHERE guild_id=? AND user_id=?",
        (guild_id, str(user_id))
    ).fetchone()[0]
    pct = min(100, (owned * 100) // TOTAL_CARDS)

    header = f"Total deck completion: **{owned}/{TOTAL_CARDS}** (**{pct}%**)\n"
    embeds: List[discord.Embed] = []
    desc_lines: List[str] = [header]
    current_len = len(header)

    def flush_embed():
        nonlocal desc_lines, current_len
        emb = discord.Embed(
            title=f"{PACK_NAME_DEFAULT} Collection",
            description="\n".join(desc_lines).strip()
        )
        embeds.append(emb)
        desc_lines = []
        current_len = 0

    for c in base_cards:
        base_no = c["english_no"]
        name = c["name"]
        owned_base = _has_card(conn, guild_id, user_id, c["id"])

        if owned_base:
            base_line = f"**{base_no}** — {name} • *{c['type']}* • **{c['rarity']}** {_emoji_link(c.get('image_url',''))}"
        else:
            base_line = (
                f"**{base_no}** — ????\n"
                f"    Type: ???? • Rarity: ????"
            )

        specials = specials_by_name.get(name, [])
        if specials:
            special_parts = []
            for idx, sp in enumerate(specials, start=1):
                owned_sp = _has_card(conn, guild_id, user_id, sp["id"])
                if owned_sp:
                    special_parts.append(
                        f"{idx}) {sp['english_no']} **{sp['rarity']}** {_emoji_link(sp.get('image_url',''))}"
                    )
                else:
                    special_parts.append(f"{idx}) ?????")
            block = base_line + "\n" + f"**{base_no} Special:** " + "  •  ".join(special_parts)
        else:
            block = base_line

        add_len = len(block) + 1
        if current_len + add_len > 3800:
            flush_embed()
        desc_lines.append(block)
        current_len += add_len

    if desc_lines:
        flush_embed()

    if embeds:
        embeds[-1].set_footer(text=f"{len(cards)} cards total")
    return embeds

@bot.tree.command(name="collection", description="View your full Black Bolt collection in THIS server.")
async def collection_slash(interaction: discord.Interaction):
    ensure_db()
    await interaction.response.defer(ephemeral=True)
    gid = _guild_id(interaction)
    with sqlite3.connect(DB_PATH) as conn:
        embeds = _collection_embeds_full(conn, gid, interaction.user.id)

    try:
        if len(embeds) <= 10:
            await interaction.followup.send(embeds=embeds, ephemeral=True)
        else:
            for i in range(0, len(embeds), 10):
                await interaction.followup.send(embeds=embeds[i:i+10], ephemeral=True)
    except discord.HTTPException:
        for emb in embeds:
            await interaction.followup.send(embed=emb, ephemeral=True)

# /scoreboard — leaderboard (guild-scoped)
@bot.tree.command(name="scoreboard", description="Server leaderboard by collection points and tokens used.")
async def scoreboard_slash(interaction: discord.Interaction):
    ensure_db()
    gid = _guild_id(interaction)
    rarity_points = dict(POINTS_FROM_RARITY)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rarities = {row["id"]: row["rarity"] for row in cur.execute("SELECT id, rarity FROM cards")}
        users = list(cur.execute("SELECT user_id, tokens_used FROM users_guild WHERE guild_id=?", (gid,)))
        scores = []
        for u in users:
            uid = u["user_id"]
            owned_ids = [r[0] for r in cur.execute(
                "SELECT card_id FROM user_collection_guild WHERE guild_id=? AND user_id=?",
                (gid, uid)
            )]
            pts = 0
            for cid in owned_ids:
                r = rarities.get(cid, "Common")
                pts += rarity_points.get(r, 0)
            scores.append((int(uid), pts, u["tokens_used"]))

    lines = []
    scores.sort(key=lambda t: (-t[1], -t[2], t[0]))
    for rank, (uid, pts, used) in enumerate(scores[:25], start=1):
        member = interaction.guild.get_member(uid) if interaction.guild else None
        name = member.display_name if member else f"User {uid}"
        lines.append(f"**{rank}. {name}** — {pts} pts • tokens used: {used}")

    if not lines:
        lines = ["No players yet. Open some packs!"]

    await interaction.response.send_message("\n".join(lines), ephemeral=False)

# Help
@bot.tree.command(name="help_cardbot", description="Show CardBot commands and what they do.")
async def help_slash(interaction: discord.Interaction):
    text = (
        "**/packopen pack:** open 1 pack (costs 1 token, per server). Duplicates become essence.\n"
        "**/token:** see your tokens here and next refill (1 every 2 hours, cap 50; first time = 10 unless DEV_FORCE_MAX_TOKENS).\n"
        "**/gamble amount:** gamble tokens here (double / refund / lose half). Cap 50 applies.\n"
        "**/sell amount:** convert tokens → essence here (350 each).\n"
        "**/essence:** show your essence here.\n"
        "**/collection:** full Black Bolt collection (001–086 base plus specials under each; emoji opens image).\n"
        "**/scoreboard:** leaderboard for this server."
    )
    await interaction.response.send_message(text, ephemeral=True)

# -------- /packopen (guild-scoped; charges 1 token & duplicates → essence) --------

@bot.tree.command(name="packopen", description="Open 1 pack (9 cards) in THIS server and display images for each card.")
@app_commands.describe(pack="Choose a pack name")
async def packopen_slash(interaction: discord.Interaction, pack: str):
    ensure_db()
    await interaction.response.defer(thinking=True, ephemeral=False)
    gid = _guild_id(interaction)

    with sqlite3.connect(DB_PATH) as conn:
        ok, user, reason = _spend_tokens(conn, gid, interaction.user.id, 1)
        if not ok:
            await interaction.followup.send(f"❌ {reason}")
            return

    try:
        cards, hit_label = open_one_pack(pack)
    except Exception as e:
        with sqlite3.connect(DB_PATH) as conn:
            _add_tokens(conn, gid, interaction.user.id, 1)  # refund on error
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
        for i, c in enumerate(cards, start=1):
            e = discord.Embed(
                title=f"{i}. {c['name']}",
                description=f"**Rarity:** {c['rarity']}\n**No.:** {c['english_no']}\n**Type:** {c['type']}",
            )
            with sqlite3.connect(DB_PATH) as conn:
                if _has_card(conn, gid, interaction.user.id, c["id"]):
                    bonus = ESSENCE_FROM_RARITY.get(c["rarity"], 0)
                    if bonus:
                        _add_essence(conn, gid, interaction.user.id, bonus)
                        dup_total_essence += bonus
                        e.add_field(name="Duplicate", value=f"Converted to **{bonus} essence**", inline=False)
                else:
                    _give_card(conn, gid, interaction.user.id, c["id"])
                    new_cards += 1

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

    footer_bits = [f"New cards: {new_cards}"]
    if dup_total_essence:
        footer_bits.append(f"Essence from duplicates: {dup_total_essence}")
    summary.add_field(name="Results", value=" • ".join(footer_bits), inline=False)

    try:
        await interaction.followup.send(embeds=[summary, *card_embeds], files=files)
    except discord.HTTPException:
        mid = 1 + len(card_embeds) // 2
        files_first = files[:mid-1]
        files_second = files[mid-1:]
        await interaction.followup.send(embeds=[summary, *card_embeds[:mid]], files=files_first)
        await interaction.followup.send(embeds=card_embeds[mid:], files=files_second)

# -------- /profile @user (show the stats of a specified user) --------

@bot.tree.command(name="profile", description="Show specified user profile.")
@app_commands.describe(user="@User")
async def profile_slash(interaction: discord.Interaction, user: discord.User):
    ensure_db()
    gid = _guild_id(interaction)
    uid = user.id
    rarity_points = dict(POINTS_FROM_RARITY)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rarities = {row["id"]: row["rarity"] for row in cur.execute("SELECT id, rarity FROM cards")}
        token_count = cur.execute("SELECT tokens_used FROM users_guild WHERE guild_id=? AND user_id=?", (gid,uid))
        token_count = cur.fetchone()[0]
        profile_card = None
        try:
            profile_card = cur.execute("SELECT profile_card FROM users_guild WHERE guild_id=? AND user_id=?", (gid,uid))
            profile_card = cur.fetchone()[0]
        except Exception:
            pass
        owned_ids = [r[0] for r in cur.execute(
            "SELECT card_id FROM user_collection_guild WHERE guild_id=? AND user_id=?",
            (gid, uid)
        )]
        pts = 0
        for cid in owned_ids:
            r = rarities.get(cid, "Common")
            pts += rarity_points.get(r, 0)
        
    message = []
    message.append(f'{user.mention}\'s Profile')
    message.append(f'Tokens Used: {token_count}')
    message.append(f'Collection Score: {pts}')
    if (profile_card != None):
        message.append(f'Favorite Card:')
        async with aiohttp.ClientSession() as session:
            e = discord.embed()
            files: List[discord.File] = []
            img_url = cur.execute("SELECT image_url FROM cards WHERE english_no=?", (profile_card))
            img_url = cur.fetchone()
            f, reason = await fetch_image_as_file(session, img_url, f"profile card")
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
            message.append(e)

    await interaction.response.send_message("\n".join(message), ephemeral=False)


# -------- /setcard pack number (set card for profile) --------
@bot.tree.command(name="setcard", description="Set your profile card")
@app_commands.describe(pack="Choose a pack name")
@app_commands.describe(card="Card number (check collection)")
async def setcard_slash(interaction: discord.Interaction, pack: str, card: str):
    ensure_db()
    gid = _guild_id(interaction)
    uid = interaction.user.id
    message = "Updated Profile Card"
    card_id = int(card)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        r = cur.execute(
        "SELECT 1 FROM user_collection_guild WHERE guild_id=? AND user_id=? AND card_id=?",
        (str(gid), str(uid), card_id)
        ).fetchone()
        if r is not None:
            cur.execute("INSERT OR IGNORE INTO users_guild(guild_id, user_id, profile_card) VALUES (?, ?)", (str(gid), str(uid), r))
        else:
            message = "Failed to update card, card was not owner"
        
    await interaction.response.send_message(message, ephemeral=True)

# --------- Autocomplete for the 'pack' argument ---------

@packopen_slash.autocomplete("pack")
async def pack_autocomplete(interaction: discord.Interaction, current: str):
    try:
        ensure_db()
        packs = list_packs()
    except Exception:
        packs = []
    return choices_from(current, packs, limit=25)

@setcard_slash.autocomplete("pack")
async def pack_autocomplete(interaction: discord.Interaction, current: str):
    try:
        ensure_db()
        packs = list_packs()
    except Exception:
        packs = []
    return choices_from(current, packs, limit=25)

# ------------- Entry -------------
if __name__ == "__main__":
    ensure_db()
    # set DISCORD_TOKEN env var before next line
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("Set DISCORD_TOKEN environment variable (your bot token).")
    bot.run(token)

