#!/usr/bin/env python3
# fix_image_urls.py
# Update/normalize card image URLs in a SQLite DB and write reports listing
# rows that didn't change (archives_kept, unchanged) so you can target them.

import argparse
import sqlite3
import re
import urllib.parse
import urllib.request
import ssl
import sys
from typing import Optional, Tuple, List, Dict
from pathlib import Path

DB_PATH_DEFAULT = "cards.db"

# Matches Bulbapedia page URLs that have a "#/media/File:Something.jpg"
MEDIA_ANCHOR_RE = re.compile(r"#/media/File:(?P<fname>[^?#]+)", re.IGNORECASE)

def is_archives(url: str) -> bool:
    return "archives.bulbagarden.net" in (url or "")

def strip_trailing_slash_num(url: str) -> str:
    # Some URLs end like ...xyz.jpg/2 — remove trailing /number
    return re.sub(r"(\.(?:jpg|jpeg|png|webp|gif))(?:/\d+)+$", r"\1", url or "", flags=re.IGNORECASE)

def to_special_filepath(url: str) -> Optional[str]:
    """
    Convert a Bulbapedia page URL with '#/media/File:...' into a Special:FilePath URL
    that 302-redirects to the real archives CDN file.
    """
    if not url:
        return None
    m = MEDIA_ANCHOR_RE.search(url)
    if not m:
        return None
    fname = urllib.parse.unquote(m.group("fname")).strip()
    if not fname:
        return None
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
    if not url:
        return None
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

def update_image_url(cur, table: str, row_id, new_url, force: bool) -> bool:
    """
    Write image_url. If force is True, always execute an UPDATE (even if same value).
    Returns True if we executed an UPDATE statement.
    """
    if force:
        cur.execute(f"UPDATE {table} SET image_url=? WHERE id=?", (new_url, row_id))
        return True
    else:
        cur.execute(f"SELECT image_url FROM {table} WHERE id=?", (row_id,))
        fetched = cur.fetchone()
        current = fetched[0] if fetched else None
        if (current or "") != (new_url or ""):
            cur.execute(f"UPDATE {table} SET image_url=? WHERE id=?", (new_url, row_id))
            return True
        return False

def write_tsv(path: Path, rows: List[Dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        headers = ["idx", "id", "english_no", "name", "original_url", "final_url", "note"]
        f.write("\t".join(headers) + "\n")
        for r in rows:
            f.write("\t".join(str(r.get(h, "")) for h in headers) + "\n")

def process(db_path: str, table: str, force: bool, report_dir: Path) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Ensure table and columns exist
    cur.execute(f"PRAGMA table_info({table})")
    info = cur.fetchall()
    if not info:
        raise SystemExit(f"Table '{table}' not found in {db_path}.")

    cols = [r[1] for r in info]
    needed = {"id", "image_url"}
    if not needed.issubset(set(cols)):
        raise SystemExit(f"Table '{table}' must have columns: {', '.join(sorted(needed))}.")

    # Build SELECT to include extra columns if present
    select_cols = ["id", "image_url"]
    for extra in ["english_no", "name"]:
        if extra in cols:
            select_cols.append(extra)

    cur.execute(f"SELECT {', '.join(select_cols)} FROM {table}")
    rows = cur.fetchall()
    total = len(rows)

    changes = 0
    stats = {
        "archives_kept": 0,
        "archives_fixed": 0,
        "special_resolved_to_archives": 0,
        "special_fallback_written": 0,
        "other_cleaned": 0,
        "unchanged": 0,
    }

    # Buckets to report
    report_archives_kept: List[Dict[str, str]] = []
    report_unchanged: List[Dict[str, str]] = []

    print(f"Scanning {total} rows in {table}...")
    for idx, row in enumerate(rows, start=1):
        if idx % 25 == 0:
            print(f"[{idx}/{total}] processed...")

        # Unpack by position based on select_cols order
        row_map = dict(zip(select_cols, row))
        cid = row_map["id"]
        original = (row_map.get("image_url") or "").strip()
        name = str(row_map.get("name") or "")
        eng  = str(row_map.get("english_no") or "")

        cleaned = strip_trailing_slash_num(original)

        # Case 1: Already archives
        if is_archives(cleaned):
            wrote = update_image_url(cur, table, cid, cleaned, force)
            if wrote:
                changes += 1
            if cleaned != original:
                stats["archives_fixed"] += 1
            else:
                stats["archives_kept"] += 1
                report_archives_kept.append({
                    "idx": idx, "id": cid, "english_no": eng, "name": name,
                    "original_url": original, "final_url": cleaned, "note": "archives_kept"
                })
            continue

        # Case 2: Bulbapedia anchor -> try resolve to archives; fallback to Special:FilePath
        special = to_special_filepath(cleaned)
        if special:
            final_url = resolve_final_url(special)
            if final_url and is_archives(final_url):
                final_url = strip_trailing_slash_num(final_url)
                wrote = update_image_url(cur, table, cid, final_url, force)
                if wrote:
                    changes += 1
                stats["special_resolved_to_archives"] += 1
            else:
                wrote = update_image_url(cur, table, cid, special, force)
                if wrote:
                    changes += 1
                stats["special_fallback_written"] += 1
            continue

        # Case 3: Other URLs (commit the cleaned version even if identical with --force)
        wrote = update_image_url(cur, table, cid, cleaned, force)
        if wrote:
            changes += 1
            if cleaned != original:
                stats["other_cleaned"] += 1
            else:
                stats["unchanged"] += 1
                report_unchanged.append({
                    "idx": idx, "id": cid, "english_no": eng, "name": name,
                    "original_url": original, "final_url": cleaned, "note": "unchanged"
                })
        else:
            # no UPDATE happened and no textual change = unchanged
            stats["unchanged"] += 1
            report_unchanged.append({
                "idx": idx, "id": cid, "english_no": eng, "name": name,
                "original_url": original, "final_url": cleaned, "note": "unchanged"
            })

    conn.commit()
    conn.close()

    print(f"Done. Updated {changes} rows out of {total}.")
    print("Breakdown:")
    for k, v in stats.items():
        print(f"  - {k}: {v}")

    # Write reports
    report_dir.mkdir(parents=True, exist_ok=True)
    if report_archives_kept:
        path = report_dir / "archives_kept.tsv"
        write_tsv(path, report_archives_kept)
        print(f"📝 Wrote {len(report_archives_kept)} rows → {path}")
    if report_unchanged:
        path = report_dir / "unchanged.tsv"
        write_tsv(path, report_unchanged)
        print(f"📝 Wrote {len(report_unchanged)} rows → {path}")

def main():
    ap = argparse.ArgumentParser(description="Fix/normalize card image URLs and write reports for non-changing rows.")
    ap.add_argument("--db", default=DB_PATH_DEFAULT, help="Path to SQLite database (default: cards.db)")
    ap.add_argument("--table", default="cards", help="Table name (default: cards)")
    ap.add_argument("--force", action="store_true",
                    help="Force UPDATE for every row (even if value unchanged).")
    ap.add_argument("--report-dir", default=".", help="Directory to write TSV reports (default: current folder)")
    args = ap.parse_args()

    process(args.db, args.table, args.force, Path(args.report_dir))

if __name__ == "__main__":
    main()

