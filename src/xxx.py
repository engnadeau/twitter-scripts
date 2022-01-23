import matplotlib.pyplot as plt
from datetime import datetime
import json
from pathlib import Path
import pandas as pd
import seaborn as sns


p = "/home/nicholas/git/social-media-cron/engnadeau-followers.json"
path = Path(p)

with open(p) as f:
    users = json.load(f)

fmt = "%a %b %d %H:%M:%S +0000 %Y"
times = []
for user in users:
    try:
        time = user["status"]["created_at"]
        # time = datetime.strptime(time, fmt)
        times.append(time)
    except KeyError:
        pass

times = pd.to_datetime(times).to_series()
df = pd.DataFrame()
df["day"] = times.dt.day_name()
df["hour"] = times.dt.hour
df = df.groupby("day").hour.value_counts().unstack()
df.fillna(0, inplace=True)
df = (df - df.values.mean()) / df.values.std()
df = df.transpose()

plot = sns.heatmap(df, cbar=False)
plot.get_figure().savefig("output.png")
