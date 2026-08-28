#!/usr/bin/env python3
"""
Download and convert Lenny's Podcast transcripts from the ChatPRD repository.
Source: https://github.com/ChatPRD/lennys-podcast-transcripts

Converts markdown transcripts with YAML frontmatter into the JSON format
expected by the ingestion pipeline.

Usage:
    python scripts/download_transcripts.py
    python scripts/download_transcripts.py --limit 20
    python scripts/download_transcripts.py --skip-download  # if repo already cloned
"""
import os
import sys
import json
import subprocess
import argparse
import re
from pathlib import Path

# Project root
ROOT = Path(__file__).parent.parent
TRANSCRIPTS_DIR = ROOT / "data" / "transcripts"
CLONE_DIR = ROOT / "data" / "_raw_transcripts_repo"
REPO_URL = "https://github.com/ChatPRD/lennys-podcast-transcripts.git"


def clone_repo():
    """Clone or update the transcripts repository."""
    if CLONE_DIR.exists():
        print(f"Repository already exists at {CLONE_DIR}, pulling latest...")
        subprocess.run(["git", "pull"], cwd=str(CLONE_DIR), check=True)
    else:
        print(f"Cloning {REPO_URL}...")
        CLONE_DIR.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", REPO_URL, str(CLONE_DIR)],
            check=True,
        )
    print("Repository ready.")


def parse_transcript_md(filepath: Path) -> dict:
    """Parse a markdown transcript file with YAML frontmatter into JSON format."""
    content = filepath.read_text(encoding="utf-8", errors="replace")

    # Split frontmatter from content
    parts = content.split("---")
    if len(parts) < 3:
        return None

    frontmatter_text = parts[1]
    transcript_text = "---".join(parts[2:]).strip()

    # Parse YAML frontmatter manually (avoid requiring pyyaml)
    metadata = {}
    for line in frontmatter_text.strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value:
                metadata[key] = value

    if not metadata.get("guest") and not metadata.get("title"):
        return None

    # Build episode JSON
    guest = metadata.get("guest", "Unknown")
    title = metadata.get("title", f"Episode with {guest}")
    date = metadata.get("publish_date", "")
    url = metadata.get("youtube_url", "")

    # Clean transcript text (remove excessive whitespace)
    transcript_text = re.sub(r'\n{3,}', '\n\n', transcript_text).strip()

    if len(transcript_text) < 100:
        return None  # Skip very short/empty transcripts

    return {
        "title": title,
        "url": url,
        "date": date,
        "speaker": guest,
        "content": transcript_text,
    }


def convert_transcripts(limit: int = None):
    """Convert all markdown transcripts to JSON format."""
    episodes_dir = CLONE_DIR / "episodes"
    if not episodes_dir.exists():
        print(f"ERROR: Episodes directory not found at {episodes_dir}")
        sys.exit(1)

    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    # Find all transcript.md files
    transcript_files = sorted(episodes_dir.glob("*/transcript.md"))
    print(f"Found {len(transcript_files)} transcript files")

    if limit:
        transcript_files = transcript_files[:limit]
        print(f"Processing first {limit} transcripts (use --limit to change)")

    converted = 0
    skipped = 0

    for filepath in transcript_files:
        guest_folder = filepath.parent.name
        output_name = f"{guest_folder}.json"
        output_path = TRANSCRIPTS_DIR / output_name

        # Skip if already converted
        if output_path.exists():
            skipped += 1
            continue

        parsed = parse_transcript_md(filepath)
        if parsed is None:
            skipped += 1
            continue

        # Write JSON
        output_path.write_text(
            json.dumps(parsed, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        converted += 1
        print(f"  ✓ {output_name} ({parsed['speaker']})")

    print(f"\nDone! Converted: {converted}, Skipped: {skipped}")
    print(f"Transcripts saved to: {TRANSCRIPTS_DIR}")
    print(f"\nTotal JSON files in data/transcripts/: {len(list(TRANSCRIPTS_DIR.glob('*.json')))}")


def main():
    parser = argparse.ArgumentParser(
        description="Download and convert Lenny's Podcast transcripts"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Max number of transcripts to convert (default: all 269)"
    )
    parser.add_argument(
        "--skip-download", action="store_true",
        help="Skip git clone/pull (use if repo already downloaded)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Lenny's Podcast Transcript Downloader")
    print("Source: github.com/ChatPRD/lennys-podcast-transcripts")
    print("=" * 60)
    print()

    if not args.skip_download:
        clone_repo()
        print()

    convert_transcripts(limit=args.limit)

    print()
    print("Next steps:")
    print("  1. Start the backend: docker-compose up --build")
    print("  2. Transcripts will be auto-ingested on first startup")
    print("  3. Or manually: cd backend && python scripts/ingest_transcripts.py")


if __name__ == "__main__":
    main()
