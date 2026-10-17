from sklearn.metrics import accuracy_score, log_loss
from sklearn.linear_model import LogisticRegression
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://brunosilva@localhost/pl_predictor")

matches = pd.read_sql(
    """
    SELECT m.id, m.season, m.match_date,
           h.name AS home, a.name AS away,
           m.home_goals, m.away_goals, m.result
    FROM matches m
    JOIN teams h ON h.id = m.home_team_id
    JOIN teams a ON a.id = m.away_team_id
    ORDER BY m.match_date, m.id
    """,
    engine,
)

print(matches.shape)
print(matches.head())
print(matches.tail())

# long format: one row per team per match
home = matches[["id", "match_date", "home", "home_goals", "away_goals"]].copy()
home.columns = ["id", "match_date", "team", "gf", "ga"]
away = matches[["id", "match_date", "away", "away_goals", "home_goals"]].copy()
away.columns = ["id", "match_date", "team", "gf", "ga"]

long = pd.concat([home, away]).sort_values(["team", "match_date", "id"])
long["pts"] = (long["gf"] > long["ga"]) * 3 + (long["gf"] == long["ga"]) * 1

# last 5 games, shifted so the current match is excluded
for col in ["pts", "gf", "ga"]:
    long[f"{col}_l5"] = (
        long.groupby("team")[col]
        .transform(lambda s: s.shift(1).rolling(5, min_periods=5).mean())
    )

feat = long[["id", "team", "pts_l5", "gf_l5", "ga_l5"]]

df = (
    matches
    .merge(feat.add_prefix("h_"), left_on=["id", "home"], right_on=["h_id", "h_team"])
    .merge(feat.add_prefix("a_"), left_on=["id", "away"], right_on=["a_id", "a_team"])
    .dropna(subset=["h_pts_l5", "a_pts_l5"])
)

print(df.shape)
print(df[["home", "away", "h_pts_l5", "a_pts_l5", "result"]].tail())


FEATURES = ["h_pts_l5", "h_gf_l5", "h_ga_l5", "a_pts_l5", "a_gf_l5", "a_ga_l5"]

train = df[df["season"] < "2024-25"]
test = df[df["season"] >= "2024-25"]

X_train, y_train = train[FEATURES], train["result"]
X_test, y_test = test[FEATURES], test["result"]

# baseline: always pick home win
baseline_acc = (y_test == "H").mean()

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

pred = model.predict(X_test)
proba = model.predict_proba(X_test)

print(f"Train rows: {len(train)}, test rows: {len(test)}")
print(f"Baseline (always H): {baseline_acc:.3f}")
print(f"Logistic regression accuracy: {accuracy_score(y_test, pred):.3f}")
print(f"Log loss: {log_loss(y_test, proba, labels=model.classes_):.3f}")
