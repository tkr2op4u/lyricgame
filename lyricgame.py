import time
import os
import sys
import textwrap

try:
    import lyricsgenius
except ImportError:
    print("Missing dependency. Run: pip install lyricsgenius colorama")
    sys.exit(1)

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    print("Missing dependency. Run: pip install lyricsgenius colorama")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
GENIUS_TOKEN = ""   # paste your token here
DISPLAY_WIDTH = 70   # characters per line when displaying lyrics


# ── Helpers ───────────────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def fetch_lyrics(title: str, artist: str = None) -> tuple[str, str, str]:
    """Return (song_title, artist_name, cleaned_lyrics) or raise."""
    genius = lyricsgenius.Genius(GENIUS_TOKEN, remove_section_headers=True)
    print(f"\n🔍  Searching Genius for '{title}'" + (f" by {artist}" if artist else "") + "…")
    song = genius.search_song(title, artist or "")
    if song is None:
        raise ValueError("Song not found. Try a different title or add the artist name.")
    lyrics = song.lyrics

    # Strip the trailing Genius embed footer (e.g. "123EmbedShare...")
    for marker in ["EmbedShare", "Embed", "You might also like"]:
        idx = lyrics.find(marker)
        if idx != -1:
            lyrics = lyrics[:idx]

    # Remove the first line which Genius adds as "Song Title Lyrics"
    lines = lyrics.strip().splitlines()
    if lines and lines[0].lower().endswith("lyrics"):
        lines = lines[1:]

    return song.title, song.artist, "\n".join(lines).strip()


def chunk_lyrics(lyrics: str, max_words: int = 40) -> list[str]:
    """Split lyrics into manageable chunks of roughly max_words words."""
    words = lyrics.split()
    chunks, current = [], []
    for word in words:
        current.append(word)
        if len(current) >= max_words and word.endswith(("\n", ".", "?", "!", ",")):
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks


def display_target(target: str):
    """Print the target text wrapped and styled."""
    wrapped = textwrap.fill(target, width=DISPLAY_WIDTH)
    print(Fore.CYAN + "\n" + "─" * DISPLAY_WIDTH)
    print(Fore.WHITE + wrapped)
    print(Fore.CYAN + "─" * DISPLAY_WIDTH + "\n")


def score_input(target: str, typed: str) -> dict:
    """Compare typed text to target and return stats."""
    target_words = target.split()
    typed_words = typed.split()

    correct = sum(1 for t, y in zip(target_words, typed_words) if t == y)
    total_typed = len(typed_words)
    total_target = len(target_words)

    return {
        "correct_words": correct,
        "typed_words": total_typed,
        "target_words": total_target,
        "accuracy": (correct / total_typed * 100) if total_typed else 0,
    }


def run_round(target: str) -> dict:
    """Run a single typing round; return stats dict."""
    display_target(target)
    print(Fore.YELLOW + "Start typing and press Enter when done:\n")

    start = time.time()
    try:
        typed = input("> ")
    except KeyboardInterrupt:
        print("\nRound skipped.")
        return None
    elapsed = time.time() - start  # seconds

    stats = score_input(target, typed)
    stats["elapsed_seconds"] = elapsed
    stats["wpm"] = round((stats["correct_words"] / elapsed) * 60, 1) if elapsed > 0 else 0
    return stats


def print_stats(stats: dict, round_num: int):
    """Pretty-print round results."""
    print(Fore.CYAN + f"\n── Round {round_num} Results ──")
    print(f"  Time     : {stats['elapsed_seconds']:.1f}s")
    print(f"  WPM      : {Fore.GREEN}{stats['wpm']}{Style.RESET_ALL}")
    print(f"  Accuracy : {stats['accuracy']:.1f}%  "
          f"({stats['correct_words']}/{stats['typed_words']} words correct)")


def print_final(all_stats: list[dict]):
    """Print aggregate results across all rounds."""
    total_correct = sum(s["correct_words"] for s in all_stats)
    total_elapsed = sum(s["elapsed_seconds"] for s in all_stats)
    avg_wpm = round((total_correct / total_elapsed) * 60, 1) if total_elapsed > 0 else 0
    avg_acc = sum(s["accuracy"] for s in all_stats) / len(all_stats)

    print(Fore.MAGENTA + "\n══════════════════════════════")
    print(Fore.MAGENTA + "       FINAL RESULTS")
    print(Fore.MAGENTA + "══════════════════════════════")
    print(f"  Rounds   : {len(all_stats)}")
    print(f"  Avg WPM  : {Fore.GREEN}{avg_wpm}{Style.RESET_ALL}")
    print(f"  Avg Acc  : {avg_acc:.1f}%")
    print(Fore.MAGENTA + "══════════════════════════════\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    clear()
    print(Fore.MAGENTA + "╔══════════════════════════════╗")
    print(Fore.MAGENTA + "║    🎵  Lyrics Typer  🎵       ║")
    print(Fore.MAGENTA + "╚══════════════════════════════╝\n")

    if GENIUS_TOKEN == "YOUR_GENIUS_API_TOKEN_HERE":
        print(Fore.RED + "⚠  Set your Genius API token in the GENIUS_TOKEN variable at the top of this file.")
        print("   Get one free at: https://genius.com/api-clients\n")
        sys.exit(1)

    title = input("Song title: ").strip()
    artist = input("Artist (optional, press Enter to skip): ").strip() or None

    try:
        song_title, song_artist, lyrics = fetch_lyrics(title, artist)
    except ValueError as e:
        print(Fore.RED + f"\n✗ {e}")
        sys.exit(1)

    print(Fore.GREEN + f"\n✓ Found: {song_title} — {song_artist}")

    chunks = chunk_lyrics(lyrics, max_words=40)
    print(f"  Lyrics split into {len(chunks)} rounds (~40 words each).\n")

    input(Fore.YELLOW + "Press Enter to start…")

    all_stats = []
    for i, chunk in enumerate(chunks, 1):
        clear()
        print(Fore.MAGENTA + f"🎵  {song_title} — {song_artist}   "
              f"[Round {i}/{len(chunks)}]\n")
        stats = run_round(chunk)
        if stats is None:
            continue
        all_stats.append(stats)
        print_stats(stats, i)

        if i < len(chunks):
            cont = input(Fore.YELLOW + "\nNext round? (Enter / q to quit): ").strip().lower()
            if cont == "q":
                break

    if all_stats:
        print_final(all_stats)
    else:
        print("No rounds completed.")


if __name__ == "__main__":
    main()
