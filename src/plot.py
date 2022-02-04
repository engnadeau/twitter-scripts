"""Plotting tools for social media."""
import json
from calendar import day_abbr
from datetime import datetime
from pathlib import Path

import fire
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

import utils
from config import settings

LOGGER = utils.get_logger("plot")


def twitter_heatmap(*users: str, output: str = "twitter_heatmap.png"):
    """Plot heatmap of Twitter users' last status."""

    # extract, load, and merge given user data
    LOGGER.info(f"Loaded {len(users)} user data files")
    user_data = []
    for user in users:
        path = Path(user)
        LOGGER.info(f"Processing {path}...")
        with open(path) as f:
            user_data.extend(json.load(f))

    # extract last status times
    LOGGER.info(f"Loaded {len(user_data)} users")
    times = []
    for user in user_data:
        try:
            time = user["status"]["created_at"]
            times.append(time)
        except KeyError:
            # not all users have tweeted; skip if missing
            pass
    LOGGER.info(f"Extracted {len(times)} status updates")

    # transform and prepare data
    df = (
        # convert times to datetime with correct timezone
        pd.DataFrame(index=pd.to_datetime(times).tz_convert(tz=settings.timezone))
        # create columns for heatmap
        .assign(weekday=lambda x: x.index.weekday)
        .assign(hour=lambda x: x.index.hour)
        # create 2D heatmap data
        .groupby("weekday")["hour"]
        .value_counts()
        .unstack()
        # no data = no tweets
        .fillna(0)
        .transpose()
        # scale each day by weekday (column)
        # https://en.wikipedia.org/wiki/Feature_scaling#Standardization_(Z-score_Normalization)
        .apply(lambda x: (x - x.mean()) / x.std())
    )

    # give weekday columns a nice label
    df.columns = [day_abbr[i] for i in df.columns]

    LOGGER.info("Most active hour of the day:")
    for i, idxmax in df.idxmax().items():
        LOGGER.info(f"\t{i}: {df.index[idxmax]}")

    # plot and save data
    ax = plt.axes()
    plot = sns.heatmap(df, cbar=False, cmap="icefire", ax=ax)
    fig = plot.get_figure()

    plt.suptitle("Twitter Heatmap")
    ax.set_title(f"{datetime.now()}")

    path = Path(output)
    LOGGER.info(f"Saving heatmap to {path}")
    fig.savefig(output)


if __name__ == "__main__":
    fire.Fire()
