from demoparser2 import DemoParser
import json
import traceback

def analyze_demo(demo_path):
    print("Loading demo...")
    parser = DemoParser(demo_path)

    print("Parsing events...")
    kills = parser.parse_event("player_death")
    hurts = parser.parse_event("player_hurt")
    shots = parser.parse_event("weapon_fire")

    if kills is None or kills.empty:
        print("No kill data found.")
        return

    players = {}

    def init_player(name):
        if name not in players:
            players[name] = {
                "kills": 0,
                "deaths": 0,
                "headshots": 0,
                "weapons": {},
                "damage": 0,
                "shots": 0,
                "hits": 0,
                "engagements": 0,
                "kill_positions": []
            }

    # ------------------
    # Weapon fire (shots)
    # ------------------
    if shots is not None:
        for _, row in shots.iterrows():
            shooter = row.get("user_name")
            if shooter:
                init_player(shooter)
                players[shooter]["shots"] += 1

    # ------------------
    # Player hurt (hits + damage)
    # ------------------
    if hurts is not None:
        for _, row in hurts.iterrows():
            attacker = row.get("attacker_name")
            if attacker:
                init_player(attacker)
                players[attacker]["hits"] += 1
                dmg = row.get("dmg_health", 0)
                if dmg:
                    players[attacker]["damage"] += dmg

    # ------------------
    # Player deaths (kills / deaths)
    # ------------------
    for _, row in kills.iterrows():
        killer = row.get("attacker_name")
        victim = row.get("user_name")

        if killer:
            init_player(killer)
            players[killer]["kills"] += 1
            players[killer]["engagements"] += 1

            weapon = row.get("weapon", "unknown")
            players[killer]["weapons"][weapon] = players[killer]["weapons"].get(weapon, 0) + 1

            if row.get("headshot"):
                players[killer]["headshots"] += 1

            x = row.get("attacker_x")
            y = row.get("attacker_y")
            if x is not None and y is not None:
                players[killer]["kill_positions"].append({"x": x, "y": y})

        if victim:
            init_player(victim)
            players[victim]["deaths"] += 1
            players[victim]["engagements"] += 1

    # ------------------
    # Player selection
    # ------------------
    indexed_players = {i + 1: name for i, name in enumerate(players.keys())}

    print("\n=== Players Found ===")
    for idx, name in indexed_players.items():
        print(f"[{idx}] {name}")

    choice = input("\nEnter player number OR exact name: ").strip()

    if choice.isdigit() and int(choice) in indexed_players:
        player_name = indexed_players[int(choice)]
    elif choice in players:
        player_name = choice
    else:
        print("Invalid selection.")
        return

    p = players[player_name]

    # ------------------
    # Calculations
    # ------------------
    kd = round(p["kills"] / p["deaths"], 2) if p["deaths"] > 0 else p["kills"]
    hs_pct = round((p["headshots"] / p["kills"]) * 100, 1) if p["kills"] > 0 else 0
    acc = round((p["hits"] / p["shots"]) * 100, 1) if p["shots"] > 0 else 0
    kpe = round(p["kills"] / p["engagements"], 2) if p["engagements"] > 0 else 0

    # ------------------
    # Output
    # ------------------
    print(f"\n=== Stats for {player_name} ===")
    print(f"Kills: {p['kills']}")
    print(f"Deaths: {p['deaths']}")
    print(f"K/D: {kd}")
    print(f"Headshots: {p['headshots']} ({hs_pct}%)")
    print(f"Damage dealt: {p['damage']}")
    print(f"Accuracy: {acc}%")
    print(f"Engagements: {p['engagements']}")
    print(f"Kills per engagement: {kpe}")

    print("\n--- Kills by Weapon ---")
    for weapon, count in sorted(p["weapons"].items(), key=lambda x: x[1], reverse=True):
        print(f"{weapon:15} {count}")

    print(f"\nHeatmap points recorded: {len(p['kill_positions'])}")

    # ------------------
    # JSON Export
    # ------------------
    export = input("\nExport this player's stats to JSON? (y/n): ").lower()
    if export == "y":
        export_data = {
            "player": player_name,
            "kills": p["kills"],
            "deaths": p["deaths"],
            "kd": kd,
            "headshots": p["headshots"],
            "headshot_pct": hs_pct,
            "damage": p["damage"],
            "accuracy_pct": acc,
            "engagements": p["engagements"],
            "kills_per_engagement": kpe,
            "weapons": p["weapons"],
            "kill_positions": p["kill_positions"]
        }

        filename = f"{player_name}_demo_stats.json".replace(" ", "_")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=4)

        print(f"Stats exported to {filename}")

# ------------------
# Safe entry point
# ------------------
if __name__ == "__main__":
    try:
        demo_file = input("Enter path to .dem file: ").strip()
        analyze_demo(demo_file)
    except Exception:
        print("\n!!! ERROR OCCURRED !!!")
        traceback.print_exc()
    finally:
        input("\nPress Enter to close...")
