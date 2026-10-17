import glob
import os

import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://brunosilva@localhost/pl_predictor")

frames = []
for path in sorted(glob.glob("../data/*.csv")):
    df = pd.read_csv(
        path, usecols=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"])
    df = df.dropna(subset=["Date", "HomeTeam", "AwayTeam"])
    df["season"] = os.path.basename(path).replace(".csv", "")
    frames.append(df)

matches = pd.concat(frames, ignore_index=True)
matches["match_date"] = pd.to_datetime(
    matches["Date"], dayfirst=True, format="mixed")
matches = matches.sort_values("match_date")

team_names = sorted(set(matches["HomeTeam"]) | set(matches["AwayTeam"]))


def val(x):
    return None if pd.isna(x) else x


with engine.begin() as conn:
    if conn.execute(text("SELECT COUNT(*) FROM matches")).scalar() > 0:
        raise SystemExit("Matches already loaded, stopping.")

    for name in team_names:
        conn.execute(text("INSERT INTO teams (name) VALUES (:n)"), {"n": name})

    team_ids = {r.name: r.id for r in conn.execute(
        text("SELECT id, name FROM teams"))}

    rows = [
        {
            "season": r.season,
            "d": r.match_date.date(),
            "h": team_ids[r.HomeTeam],
            "a": team_ids[r.AwayTeam],
            "hg": None if pd.isna(r.FTHG) else int(r.FTHG),
            "ag": None if pd.isna(r.FTAG) else int(r.FTAG),
            "res": val(r.FTR),
        }
        for r in matches.itertuples()
    ]

    conn.execute(
        text(
            "INSERT INTO matches (season, match_date, home_team_id, away_team_id, "
            "home_goals, away_goals, result) "
            "VALUES (:season, :d, :h, :a, :hg, :ag, :res)"
        ),
        rows,
    )

print(f"Loaded {len(team_names)} teams and {len(rows)} matches")
