import pandas as pd
import numpy as np
import psycopg2
from sqlalchemy import create_engine
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

# Query SQL Database
conn = psycopg2.connect(
    host="localhost", port=5432, database="NBA", user="postgres", password="postgres"
)
engine = create_engine("postgresql://postgres:postgres@localhost:5432/NBA")
stats = pd.read_sql_query('''SELECT * FROM "Draft"''', engine)

# Rename Columns
stats = stats.rename(
    columns={"MP.1": "MPG", "PTS.1": "PPG", "TRB.1": "RPG", "AST.1": "APG"}
)

# Filter out one off drafts with more than 60 picks
stats60 = stats[stats["Pk"] < 61]

# Average WS/48 by pick
stats_na = stats.copy()
stats_na["WS/48"].fillna(
    0, inplace=True
)  # Replace null values to 0 to account for players who never played
picks_WS = stats_na.groupby("Pk", as_index=False).mean()
picks_WS = picks_WS[picks_WS["Pk"] < 61]
picks_WS = picks_WS[["Pk", "WS/48"]]

# Create dataframe to analyze the difference of Career WS/48 and player draft pick #
analysis_WS = stats60.merge(picks_WS, left_on="Pk", right_on="Pk")
analysis_WS = analysis_WS.rename(
    columns={"WS/48_x": "Career_WS/48", "WS/48_y": "Average_WS/48"}
)
analysis_WS = analysis_WS.assign(
    WS_Dif=analysis_WS["Career_WS/48"] - analysis_WS["Average_WS/48"]
)

# Filter dataframe for players who played more than specified minutes
analysis_WS_filtered = analysis_WS[analysis_WS["MP"] > 10000]
analysis_WS_filtered = analysis_WS_filtered.assign(
    WS_Dif=analysis_WS_filtered["Career_WS/48"] - analysis_WS_filtered["Average_WS/48"]
)

# Best Draft Picks Dataframe
rank_best_ws = analysis_WS_filtered.sort_values(by=["WS_Dif"], ascending=False)
rank_best_ws = rank_best_ws[["Player", "Pk", "WS_Dif"]]
rank_best_ws = rank_best_ws.head(10)
rank_best_ws["Rank"] = range(1, len(rank_best_ws) + 1)
rank_column = rank_best_ws.pop("Rank")
rank_best_ws.insert(0, "Rank", rank_column)

# Worst Draft Picks Dataframe
rank_worst_ws = analysis_WS.sort_values(by=["WS_Dif"], ascending=False)
rank_worst_ws = rank_worst_ws[["Player", "Pk", "WS_Dif"]]
rank_worst_ws = rank_worst_ws.tail(10)
rank_worst_ws = rank_worst_ws.sort_values(by=["WS_Dif"])
rank_worst_ws["Rank"] = range(1, len(rank_worst_ws) + 1)
rank_column = rank_worst_ws.pop("Rank")
rank_worst_ws.insert(0, "Rank", rank_column)

# Vizualizations

# Average WS/48 by pick
scatter_picks_ws = px.scatter(
    picks_WS,
    x=picks_WS["Pk"],
    y=picks_WS["WS/48"],
    title="Average WS/48 by Pick",
    template="plotly_dark",
    labels={"Pk": "Picks"},
)

# All time draft history by WS/48
stats60_mp = stats60[stats60["MP"] > 10000]
scatter_history_ws = px.scatter(
    stats60_mp,
    x=stats60_mp["Pk"],
    y=stats60_mp["WS/48"],
    title="Draft History WS/48 by Pick MP > 10,000",
    template="plotly_dark",
    color="Pk",
    hover_data={"Player": True},
    labels={"Pk": "Picks"},
)
scatter_history_ws.update_coloraxes(showscale=False)


# Career WS/48 compared with player draft pick
scatter_diff_ws = px.scatter(
    analysis_WS_filtered,
    x=analysis_WS_filtered["Pk"],
    y=analysis_WS_filtered["WS_Dif"],
    color=analysis_WS_filtered["Career_WS/48"],
    hover_data={"Player": True},
    color_continuous_scale="teal",
    labels={
        "WS_Dif": "Win Shares Difference",
        "Pk": "Pick",
        "Career_WS/48": "Career Win Shares/48",
    },
    template="plotly_dark",
    title="Career WS/48 Difference for Respective Draft Pick MP > 10,000",
)
scatter_diff_ws.update_coloraxes(showscale=False)
rank_best_sorted = rank_best_ws.sort_values("WS_Dif")
bar_best = px.bar(
    rank_best_sorted,
    x="WS_Dif",
    y="Player",
    orientation="h",
    labels={"WS_Dif": "WS Difference"},
    template="plotly_dark",
    title="Best Draft Picks of All Time by Win Share/48",
)
bar_best.update_yaxes(title=None, ticksuffix="  ")

scatter_picks_ws.show()
scatter_history_ws.show()
scatter_diff_ws.show()
bar_best.show()
