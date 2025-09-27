# CardBot.py
import os
import io
import re
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
SQL_BOOTSTRAP = "black_bolt_types_placeholders.sql"  # .sql file
INTENTS = discord.Intents.default()
BOT_ACTIVITY = "Opening packs (/packopen)"
# Optional: set a GUILD_ID to sync faster to one server during testing
GUILD_ID = os.getenv("GUILD_ID")  # e.g. "123456789012345678"
# ---------------------------

# ---------- IMAGE LIMITS / SETTINGS ----------
MAX_UPLOAD_BYTES = 7 * 1024 * 1024  
MAX_DIM = 1024                      
FETCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DiscordCardBot/1.0",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}
# --------------------------------------------

RARITY_NORMALIZE = {
    "common": "Common",
    "uncommon": "Uncommon",
    "rare": "Rare",
    "double rare": "Double Rare",
    # DB uses "Illistration Rare" (with that spelling)
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
    """Create and populate the SQLite DB from the .sql file if DB is missing."""
    if os.path.exists(DB_PATH):
        return
    if not os.path.exists(SQL_BOOTSTRAP):
        raise FileNotFoundError(
            f"Missing {SQL_BOOTSTRAP}. Put your SQL file next to this script."
        )
    with open(SQL_BOOTSTRAP, "r", encoding="utf-8") as f:
        sql_text = f.read()
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(sql_text)

def fetch_pack_cards(pack: str) -> List[Dict]:
    """Return all cards for a pack as list of dicts."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, pack, name, english_no, variant_index, type, rarity, image_url "
            "FROM cards WHERE pack = ?", (pack,)
        ).fetchall()
        return [dict(r) for r in rows]

def list_packs() -> List[str]:
    """Return distinct pack names."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT DISTINCT pack FROM cards ORDER BY pack").fetchall()
        return [r[0] for r in rows]

def by_rarity(cards: List[Dict]) -> Dict[str, List[Dict]]:
    groups: Dict[str, List[Dict]] = {}
    for c in cards:
        groups.setdefault(c["rarity"], []).append(c)
    return groups

def choose_from_pool(pool: List[Dict], k: int, avoid_ids: set) -> List[Dict]:
    """Choose up to k unique cards from pool, avoiding duplicates where possible."""
    if not pool:
        return []
    choices = [c for c in pool if c["id"] not in avoid_ids]
    if len(choices) >= k:
        picks = random.sample(choices, k)
    else:
        picks = choices.copy()
        remaining = k - len(picks)
        for _ in range(max(0, remaining)):
            picks.append(random.choice(pool))  # allow dupes if needed
    return picks

def roll_hit_tier() -> Optional[str]:
    """Return the canonical rarity name for the hit slot, or None (no upgrade)."""
    for key, denom in HIT_TIERS:
        if random.randint(1, denom) == 1:
            return RARITY_NORMALIZE[key]
    return None

def open_one_pack(pack_name: str) -> Tuple[List[Dict], str]:
    """
    Returns (cards, hit_tier_label).
    - 8 commons from Common+Uncommon
    - 1 hit slot using tier odds; falls back to commons if tier empty
    """
    all_cards = fetch_pack_cards(pack_name)
    if not all_cards:
        raise ValueError(f"Pack '{pack_name}' not found in DB.")

    groups = by_rarity(all_cards)

    # Build the commons pool (Common + Uncommon)
    commons_pool: List[Dict] = []
    for r in COMMON_POOL:
        commons_pool += groups.get(r, [])
    if not commons_pool:
        # If a pack somehow has no commons/uncommons, treat all cards as the pool
        commons_pool = all_cards

    picked: List[Dict] = []
    used_ids = set()

    # First 8 from commons pool
    first_eight = choose_from_pool(commons_pool, 8, used_ids)
    picked.extend(first_eight)
    used_ids.update(c["id"] for c in first_eight)

    # Hit slot
    hit_label = roll_hit_tier()
    hit_card = None
    if hit_label:
        # If the rolled tier is empty, step down the priority list until we find something
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

    # If no hit or no cards in any rare tier, take from commons pool
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
    """
    Load image via Pillow, scale down if needed, encode as PNG if has alpha else progressive JPEG,
    reduce size until under MAX_UPLOAD_BYTES. Raises UnidentifiedImageError if unreadable.
    """
    with Image.open(io.BytesIO(img_bytes)) as im:
        has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
        im = im.convert("RGBA" if has_alpha else "RGB")

        w, h = im.size
        if max(w, h) > MAX_DIM:
            scale = MAX_DIM / float(max(w, h))
            im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        if has_alpha:
            # PNG path
            for comp in (6, 7, 9):
                out = io.BytesIO()
                im.save(out, format="PNG", optimize=True, compress_level=comp)
                if out.tell() <= MAX_UPLOAD_BYTES:
                    return out.getvalue()
            # flatten to JPEG if still too big
            im = im.convert("RGB")

        # JPEG path
        for q in (90, 80, 70, 60, 50, 40, 30, 25, 20):
            out = io.BytesIO()
            im.save(out, format="JPEG", quality=q, optimize=True, progressive=True)
            if out.tell() <= MAX_UPLOAD_BYTES:
                return out.getvalue()
        return out.getvalue()

async def fetch_image_as_file(session: aiohttp.ClientSession, url: str, filename_base: str) -> Tuple[Optional[discord.File], str]:
    """
    Download image, convert/resize to stay under upload limits.
    Returns (discord.File or None, reason_string).
    """
    if not url:
        return None, "no-url"
    try:
        # Add a referer of the same origin if helpful
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
            except Exception as e:
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
        # If Pillow failed but content-type looks like an image, attach raw bytes as-is.
        if _is_image_content_type(content_type) and len(raw) <= MAX_UPLOAD_BYTES:
            ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".img"
            file = discord.File(io.BytesIO(raw), filename=f"{filename_base}{ext}")
            return file, "raw-pass-through"
        # Otherwise, give up on attachment; caller will try direct URL
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

# --------- Slash command & autocomplete ---------

def choices_from(query: str, items: List[str], limit: int = 25) -> List[app_commands.Choice[str]]:
    query_low = (query or "").lower()
    filtered = [p for p in items if query_low in p.lower()] if query_low else items
    return [app_commands.Choice(name=p, value=p) for p in filtered[:limit]]

@bot.tree.command(name="packopen", description="Open 1 pack (9 cards) and display images for each card.")
@app_commands.describe(pack="Choose a pack name")
async def packopen_slash(interaction: discord.Interaction, pack: str):
    await interaction.response.defer(thinking=True, ephemeral=False)
    try:
        cards, hit_label = open_one_pack(pack)
    except Exception as e:
        await interaction.followup.send(f"❌ {e}")
        return

    # Summary embed
    summary = discord.Embed(
        title=f"🎴 {pack} — You opened 1 pack!",
        description="\n".join(
            f"**{i}. {c['name']}** — *{c['rarity']}*  ({c['english_no']}) • {c['type']}"
            for i, c in enumerate(cards, start=1)
        ),
    )
    summary.set_footer(text=f"Hit slot result: {hit_label}")

    # Build per-card embeds + download images as attachments
    card_embeds: List[discord.Embed] = []
    files: List[discord.File] = []

    async with aiohttp.ClientSession() as session:
        for i, c in enumerate(cards, start=1):
            e = discord.Embed(
                title=f"{i}. {c['name']}",
                description=f"**Rarity:** {c['rarity']}\n**No.:** {c['english_no']}\n**Type:** {c['type']}",
            )
            img_url = (c.get("image_url") or "").strip()
            f, reason = await fetch_image_as_file(session, img_url, f"card_{i}")
            if f:
                files.append(f)
                e.set_image(url=f"attachment://{f.filename}")
                if reason != "ok":
                    e.set_footer(text=f"({reason})")
            else:
                if img_url:
                    # Fallback to direct hotlink (works if host allows Discord to fetch)
                    e.set_image(url=img_url)
                    e.set_footer(text=f"(attachment skipped: {reason})")
                else:
                    e.set_footer(text="(No image_url in DB for this card)")
            card_embeds.append(e)

    # Try one message (10 embeds + up to 9 files). If too large, split into two.
    try:
        await interaction.followup.send(embeds=[summary, *card_embeds], files=files)
    except discord.HTTPException:
        mid = 1 + len(card_embeds) // 2
        files_first = files[:mid-1]
        files_second = files[mid-1:]
        await interaction.followup.send(embeds=[summary, *card_embeds[:mid]], files=files_first)
        await interaction.followup.send(embeds=card_embeds[mid:], files=files_second)

# Autocomplete for the 'pack' argument
@packopen_slash.autocomplete("pack")
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
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("Set DISCORD_TOKEN environment variable (your bot token).")
    bot.run(token)
