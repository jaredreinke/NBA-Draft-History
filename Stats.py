# Import neccesary modules
import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
import psycopg2

# Create a list of seasons to scrape
seasons = list(range(1970, 2023))
seasons = [str(year) for year in seasons]

# Get html text for Stats and save
base_url = "https://www.basketball-reference.com/draft/NBA_{}.html#stats"

for season in seasons:
    url = base_url.format(season)
    response = requests.get(url)
    with open("Stats/{}".format(season), "w+", encoding="utf-8") as S:
        S.write(response.text)

# Parse HTML and create a dataframe

dfs = []
for season in seasons:
    with open("Stats/{}".format(season), encoding="utf-8") as S:
        page = S.read()
    soup = BeautifulSoup(page, "html.parser")
    soup.find("tr", class_="over_header").decompose()
    soup.find("tr", class_="thead").decompose()
    table = soup.find(
        id="stats",
    )
    stats = pd.read_html(str(table))[0]
    stats["Season"] = season
    # Reorder Season Column to First
    season_column = stats.pop("Season")
    stats.insert(0, "Season", season_column)
    # Clean the table
    stats = stats[stats["Player"] != "Player"]
    stats.dropna(inplace=True, subset="Pk")
    # Add to list of dfs
    dfs.append(stats)

# Concat list of dfs
stats = pd.concat(dfs)

# Change Data Types
float_cols1 = stats.columns[0:3]
float_cols2 = stats.columns[6:12]
float_cols3 = stats.columns[12:23]
stats[float_cols1] = stats[float_cols1].astype(float)
stats[float_cols2] = stats[float_cols2].astype(float)
stats[float_cols3] = stats[float_cols3].astype(float)

# Upload to SQL Database
conn = psycopg2.connect(
    host="localhost", port=5432, database="NBA", user="postgres", password="postgres"
)

conn.autocommit = True

cur = conn.cursor()
conn.rollback()

engine = create_engine("postgresql://postgres:postgres@localhost:5432/NBA")

stats.to_sql("Draft", engine, if_exists="replace")

conn.commit()

conn.close()
