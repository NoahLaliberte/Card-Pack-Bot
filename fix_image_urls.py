# fix_image_urls.py
import sqlite3
import re
import urllib.parse
import urllib.request
import ssl
import sys
from typing import Optional

DB_PATH = "cards.db"

# Matches Bulbapedia page URLs that have a "#/media/File:Something.jpg"
MEDIA_ANCHOR_RE = re.compile(r"#/media/File:(?P<fname>[^?#]+)", re.IGNORECASE)

def is_archives(url: str) -> bool:
    return "archives.bulbagarden.net" in url

def strip_trailing_slash_num(url: str) -> str:
    # Some URLs end like ...xyz.jpg/2 — remove trailing /number
    return re.sub(r"(\.(?:jpg|jpeg|png|webp|gif))(?:/\d+)+$", r"\1", url, flags=re.IGNORECASE)

def to_special_filepath(url: str) -> Optional[str]:
    """
    Convert a Bulbapedia page URL with '#/media/File:...' into a Special:FilePath URL
    that 302-redirects to the real archives CDN file.
    """
    m = MEDIA_ANCHOR_RE.search(url)
    if not m:
        return None
    fname = urllib.parse.unquote(m.group("fname")).strip()
    return f"https://bulbapedia.bulbagarden.net/wiki/Special:FilePath/{urllib.parse.quote(fname)}"

def make_ssl_context() -> ssl.SSLContext:
    """
    Prefer certifi bundle (safe). If not available, fall back to an
    unverified context (acceptable here since we only resolve redirects).
    """
    try:
        import certifi  # type: ignore
        ctx = ssl.create_default_context(cafile=certifi.where())
        return ctx
    except Exception:
        print("WARN: certifi not available; using unverified SSL context.", file=sys.stderr)
        return ssl._create_unverified_context()

SSL_CTX = make_ssl_context()

def resolve_final_url(url: str, timeout: float = 20.0) -> Optional[str]:
    """
    Follow redirects and return the final absolute URL.
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (DiscordCardBot Fixer)",
            "Accept": "image/avif,image/webp,image/apng,image/*;q=0.9,text/html;q=0.8,*/*;q=0.5",
            "Referer": "https://bulbapedia.bulbagarden.net/",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            return resp.geturl()  # final URL after redirects
    except Exception as e:
        print(f"  ! resolve error for {url}: {type(e).__name__}")
        return None

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, image_url FROM cards")
    rows = cur.fetchall()

    total = len(rows)
    changes = 0
    for idx, (cid, url) in enumerate(rows, start=1):
        if idx % 25 == 0:
            print(f"[{idx}/{total}] processed...")

        if not url:
            continue
        original = url
        url = strip_trailing_slash_num(url)

        # Already an archives link? keep (but commit any '/2' cleanup)
        if is_archives(url):
            if url != original:
                cur.execute("UPDATE cards SET image_url=? WHERE id=?", (url, cid))
                changes += 1
            continue

        # Convert Bulbapedia '#/media/File:...' to Special:FilePath and resolve
        special = to_special_filepath(url)
        if special:
            final_url = resolve_final_url(special)
            if final_url and is_archives(final_url):
                final_url = strip_trailing_slash_num(final_url)
                cur.execute("UPDATE cards SET image_url=? WHERE id=?", (final_url, cid))
                changes += 1
            else:
                # Couldn't resolve now; keep original (your runtime code can still follow Special:FilePath)
                # Alternatively, store Special:FilePath even if not resolved:
                # cur.execute("UPDATE cards SET image_url=? WHERE id=?", (special, cid)); changes += 1
                print(f"  ! could not resolve archives for id={cid}")
        else:
            # Not archives and not a media anchor: just keep the cleaned URL if it changed
            if url != original:
                cur.execute("UPDATE cards SET image_url=? WHERE id=?", (url, cid))
                changes += 1

    conn.commit()
    conn.close()
    print(f"Done. Updated {changes} rows out of {total}.")

if __name__ == "__main__":
    main()
