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

# Group by average VORP by pick
picks_VORP = stats.groupby("Pk", as_index=False).mean()
picks_VORP = picks_VORP[picks_VORP["Pk"] < 61]
picks_VORP = picks_VORP[["Pk", "VORP"]]


# Create dataframe to analyze the difference of Career VORP and player draft pick #
analysis_VORP = stats60.merge(picks_VORP, left_on="Pk", right_on="Pk")
analysis_VORP = analysis_VORP.rename(
    columns={"VORP_x": "Career_VORP", "VORP_y": "Average_VORP"}
)
analysis_VORP = analysis_VORP.assign(
    VORP_Dif=analysis_VORP["Career_VORP"] - analysis_VORP["Average_VORP"]
)

# Best Draft Picks Table
rank_best_VORP = analysis_VORP.sort_values(by=["VORP_Dif"], ascending=False)
rank_best_VORP = rank_best_VORP[["Player", "VORP_Dif"]]
rank_best_VORP = rank_best_VORP.head(10)
rank_best_VORP["Rank"] = range(1, len(rank_best_VORP) + 1)
rank_column = rank_best_VORP.pop("Rank")
rank_best_VORP.insert(0, "Rank", rank_column)

# Vizulations

# Average VORP by Pick Scatter Plot
scatter_picks_vorp = px.scatter(
    picks_VORP,
    x=picks_VORP["Pk"],
    y=picks_VORP["VORP"],
    title="Average VORP by Pick",
    template="plotly_dark",
    labels={"Pk": "Picks"},
)

# All time draft history by VORP

# Scatter plot to plot every draft picks career VORP
scatter_history_vorp = px.scatter(
    stats60,
    x=stats60["Pk"],
    y=stats60["VORP"],
    title="VORP History by Pick",
    hover_data={"Player": True},
    color="Pk",
    labels={"Pk": "Picks"},
    template="plotly_dark",
)
scatter_history_vorp.update_coloraxes(showscale=False)

# Career VORP compared with played draft pick
scatter_diff_vorp = px.scatter(
    analysis_VORP,
    x=analysis_VORP["Career_VORP"],
    y=analysis_VORP["VORP_Dif"],
    color=analysis_VORP["Pk"],
    hover_data={"Player": True},
    template="plotly_dark",
    color_continuous_scale="teal",
    labels={"VORP_Dif": "Vorp Difference", "Pk": "Pick"},
    title="Career VORP Compared to Average VORP for Player Draft Pick",
)
scatter_diff_vorp.update_coloraxes(showscale=False)

# Best Picks Bar Graph
rank_best_sorted = rank_best_VORP.sort_values("VORP_Dif")
bar_best = px.bar(
    rank_best_sorted,
    x="VORP_Dif",
    y="Player",
    orientation="h",
    labels={"VORP_Dif": "VORP Difference"},
    template="plotly_dark",
    title="Best Draft Picks of All Time by VORP",
)
bar_best.update_yaxes(title=None, ticksuffix="  ")
