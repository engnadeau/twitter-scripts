"""Twitter handler."""
import datetime

import fire
import tweepy

import utils
from config import settings

TODAY = datetime.date.today()
LOGGER = utils._get_logger("twitter")


def _authenticate():
    """Create authenticated API object."""
    LOGGER.info("Authenticating...")
    auth = tweepy.OAuthHandler(
        settings.twitter.api_key, settings.twitter.api_secret_key
    )
    auth.set_access_token(
        settings.twitter.access_token, settings.twitter.access_token_secret
    )
    api = tweepy.API(auth, wait_on_rate_limit=True)

    try:
        user = api.verify_credentials()
        LOGGER.info(
            f"Authenticated as {user.screen_name} with {user.statuses_count} tweets"
        )
    except tweepy.Unauthorized as e:
        LOGGER.exception(e)
    return api


def prune_tweets(
    days: int = settings.twitter.tweet_prune_days,
    delete_liked: bool = settings.twitter.is_delete_liked,
    dry_run: bool = False,
):
    """Delete old tweets.

    Args:
        days (int, optional):
            Limit on number of days old.
            Defaults to settings.twitter.tweet_prune_days.
        delete_liked (bool, optional):
            If self-liked tweets are deleted.
            Defaults to settings.twitter.is_delete_liked.
        dry_run (bool, optional): If deleting should be skipped. Defaults to False.
    """
    if dry_run:
        LOGGER.info("Dry run enabled".upper())

    limit = TODAY - datetime.timedelta(days=days)
    LOGGER.info(f"Tweets older than {days} days ({limit}) will be deleted")

    api = _authenticate()
    LOGGER.info(f"Authenticated as {api.verify_credentials().screen_name}")

    LOGGER.info("Fetching tweets...")
    for t in tweepy.Cursor(method=api.user_timeline, count=100).items():
        # check if outside time limit and if self-liked
        if t.created_at.date() < limit and (not t.favorited or delete_liked):
            LOGGER.info(f"Pruning: {t.id_str} | {t.created_at.date()} | {t.text}")

            # skip if dry run
            if dry_run:
                continue

            # delete tweet
            try:
                api.destroy_status(t.id_str)
            except tweepy.error.TweepError as e:
                LOGGER.error(e)

    LOGGER.info("Pruning complete")


def prune_friends(
    days: int = settings.twitter.friend_prune_days, dry_run: bool = False
):
    """Delete old friends.

    Args:
        days (int, optional):
            Limit of days since last tweet.
            Defaults to settings.twitter.friend_prune_days.
        dry_run (bool, optional):
            If deleting should be skipped.
            Defaults to False.
    """
    if dry_run:
        LOGGER.info("Dry run enabled".upper())

    # set limit
    LOGGER.info(f"Friends inactive since {days} days will be unfriended")

    # auth
    api = _authenticate()

    # prune
    screen_name = api.verify_credentials().screen_name
    friends_count = api.verify_credentials().friends_count
    LOGGER.info(f"{screen_name} has {friends_count} friends")

    LOGGER.info("Fetching friends...")
    for f in tweepy.Cursor(method=api.get_friends, count=200).items():
        try:
            days_since_last_tweet = (TODAY - f.status.created_at.date()).days
            is_stale_friend = days_since_last_tweet > days
        except AttributeError:
            LOGGER.info(f"{f.screen_name} has never tweeted")
            days_since_last_tweet = None
            is_stale_friend = True

        if is_stale_friend:
            LOGGER.info(f"Pruning: {f.screen_name} | {days_since_last_tweet} days")

            # skip if dry run
            if dry_run:
                continue

            # unfriend
            try:
                api.destroy_friendship(screen_name=f.screen_name)
            except tweepy.error.TweepError as e:
                LOGGER.error(e)

    LOGGER.info("Pruning complete")


if __name__ == "__main__":
    fire.Fire()
