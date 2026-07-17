print("Hey Los it's me")

from nba_api.stats.endpoints import leaguedashptstats
from nba_api.stats.static import players

response = leaguedashptstats.LeagueDashPtStats(
    season="2024-25",
    league_id_nullable="15",
    player_or_team="Team",
    pt_measure_type="SpeedDistance",
    per_mode_simple="Totals",
    timeout=60,
)

df = response.get_dict()
print(df)