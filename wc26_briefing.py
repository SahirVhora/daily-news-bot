"""
wc26_briefing.py - FIFA World Cup 2026 morning briefing
Fetches match data from openfootball free JSON source and sends to Telegram.
Designed to run via GitHub Actions at 6am UTC (7am UK BST).
"""

import json
import os
import re
from datetime import date, datetime, timedelta
from urllib.request import urlopen

from digest_common import get_telegram_config, print_dry_run, send_telegram

DATA_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"


def fetch_data():
    with urlopen(DATA_URL, timeout=15) as resp:
        return json.loads(resp.read())


def parse_utc_offset(time_str: str) -> int:
    """Parse '13:00 UTC-6' or '19:00 UTC-4' -> offset_hours (e.g. -6)."""
    m = re.search(r'UTC([+-]\d+)', time_str)
    if m:
        return int(m.group(1))
    return 0


def convert_to_bst(time_str: str) -> str:
    """Convert e.g. '13:00 UTC-6' to BST (UTC+1)."""
    m = re.match(r'(\d{1,2}:\d{2})', time_str)
    if not m:
        return time_str
    time_part = m.group(1)
    hour, minute = map(int, time_part.split(':'))
    offset = parse_utc_offset(time_str)
    # Convert to UTC first, then to BST (UTC+1)
    utc_hour = hour - offset  # offset is negative for UTC-6 etc
    bst_hour = utc_hour + 1   # BST = UTC+1
    # Handle day rollover — just show time for simplicity
    if bst_hour >= 24:
        bst_hour -= 24
    elif bst_hour < 0:
        bst_hour += 24
    return f"{bst_hour:02d}:{minute:02d}"


def compute_standings(matches):
    """Compute group standings from played matches."""
    groups = {}
    teams_in_group = {}

    # Collect all teams and their groups from all matches
    for m in matches:
        g = m.get("group", "")
        if not g:
            continue
        if g not in groups:
            groups[g] = {}
            teams_in_group[g] = set()
        teams_in_group[g].add(m["team1"])
        teams_in_group[g].add(m["team2"])

    # Initialize all teams
    for g, team_set in teams_in_group.items():
        for t in team_set:
            groups[g][t] = {"P": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "Pts": 0}

    # Process played matches
    for m in matches:
        if "score" not in m:
            continue
        g = m.get("group", "")
        if not g:
            continue
        score = m["score"]
        ft = score.get("ft", [])
        if len(ft) != 2:
            continue
        t1, t2 = m["team1"], m["team2"]
        g1, g2 = ft[0], ft[1]

        if t1 not in groups[g] or t2 not in groups[g]:
            continue

        groups[g][t1]["P"] += 1
        groups[g][t2]["P"] += 1
        groups[g][t1]["GF"] += g1
        groups[g][t2]["GF"] += g2
        groups[g][t1]["GA"] += g2
        groups[g][t2]["GA"] += g1

        if g1 > g2:
            groups[g][t1]["W"] += 1
            groups[g][t1]["Pts"] += 3
            groups[g][t2]["L"] += 1
        elif g1 < g2:
            groups[g][t2]["W"] += 1
            groups[g][t2]["Pts"] += 3
            groups[g][t1]["L"] += 1
        else:
            groups[g][t1]["D"] += 1
            groups[g][t2]["D"] += 1
            groups[g][t1]["Pts"] += 1
            groups[g][t2]["Pts"] += 1

        groups[g][t1]["GD"] = groups[g][t1]["GF"] - groups[g][t1]["GA"]
        groups[g][t2]["GD"] = groups[g][t2]["GF"] - groups[g][t2]["GA"]

    # Sort each group by Pts desc, then GD desc, then GF desc
    sorted_groups = {}
    for g, teams in groups.items():
        sorted_teams = sorted(teams.items(), key=lambda x: (-x[1]["Pts"], -x[1]["GD"], -x[1]["GF"]))
        sorted_groups[g] = sorted_teams

    return sorted_groups


def format_standings(sorted_groups):
    """Format group standings as clean text for Telegram."""
    lines = ["\n<b>🏆 Group Standings</b>\n"]
    for g in sorted(sorted_groups.keys()):
        teams = sorted_groups[g]
        if not teams:
            continue
        lines.append(f"\n<b>{g}</b>")
        lines.append("   Team                    P  W  D  L  GF  GA  GD Pts")
        for i, (team, stats) in enumerate(teams, 1):
            team_display = team[:22].ljust(22)
            lines.append(
                f"{i}. {team_display} "
                f"{stats['P']:2d} {stats['W']:2d} {stats['D']:2d} {stats['L']:2d} "
                f"{stats['GF']:2d} {stats['GA']:2d} {stats['GD']:3d} {stats['Pts']:2d}"
            )
    return "\n".join(lines)


def format_yesterdays_results(matches, today):
    """Format yesterday's completed matches."""
    yesterday = today - timedelta(days=1)
    yday_str = yesterday.strftime("%Y-%m-%d")

    yday_matches = [m for m in matches
                    if m.get("date") == yday_str and "score" in m]

    if not yday_matches:
        return "\n\n<b>📅 Yesterday's Results</b>\nNo matches played yesterday."

    lines = ["\n<b>📅 Yesterday's Results</b>\n"]
    for m in yday_matches:
        score = m["score"]["ft"]
        g = m.get("group", "")
        lines.append(f"<b>{m['team1']} {score[0]}-{score[1]} {m['team2']}</b>  ({g})")

    return "\n".join(lines)


def format_todays_fixtures(matches, today):
    """Format today's upcoming matches in BST."""
    today_str = today.strftime("%Y-%m-%d")

    today_matches = [m for m in matches
                     if m.get("date") == today_str and "score" not in m]

    if not today_matches:
        return "\n\n<b>⚽ Today's Fixtures</b>\nNo matches scheduled today."

    lines = ["\n<b>⚽ Today's Fixtures (UK times)</b>\n"]
    for m in today_matches:
        time_str = m.get("time", "")
        bst_time = convert_to_bst(time_str) if time_str else ""
        g = m.get("group", "")
        ground = m.get("ground", "")
        time_display = f"{bst_time} BST" if bst_time else "TBC"
        lines.append(f"<b>{m['team1']} vs {m['team2']}</b>")
        lines.append(f"   {time_display}  |  {g}  |  {ground}")

    return "\n".join(lines)


def main(dry_run=False):
    if dry_run:
        print("[DRY RUN] Would fetch WC26 data and send to Telegram\n")

    token, chat_id = get_telegram_config()
    today = date.today()
    today_display = today.strftime("%A, %d %B %Y")

    data = fetch_data()
    matches = data.get("matches", [])

    # Compute standings
    sorted_groups = compute_standings(matches)

    # Build message
    header = f"<b>🌍 World Cup 2026 Briefing - {today_display}</b>"
    results = format_yesterdays_results(matches, today)
    standings = format_standings(sorted_groups)
    fixtures = format_todays_fixtures(matches, today)

    message = header + results + standings + fixtures

    # Footer
    message += "\n\n<i>Data: openfootball • Times in BST (UTC+1)</i>"

    if dry_run:
        print_dry_run(message, f"Would send WC26 briefing to Telegram")
        return

    send_telegram(message, token, chat_id)
    print("Sent WC26 morning briefing to Telegram.")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="FIFA World Cup 2026 morning briefing")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout instead of sending")
    args = p.parse_args()
    main(dry_run=args.dry_run)
