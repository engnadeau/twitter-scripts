import datetime
import logging
import time

import fire
import tweepy

from config import settings

logging.basicConfig(level=logging.INFO)

TODAY = datetime.date.today()


def _rate_limit_handler(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            logging.warning(f"Rate limit exceeded")
            logging.info(f"Sleeping for {settings.twitter_tweepy_sleep_time}s")
            time.sleep(settings.twitter_tweepy_sleep_time)
        except StopIteration:
            break


def _authenticate():
    logging.info("Authenticating...")
    auth = tweepy.OAuthHandler(
        settings.twitter_api_key, settings.twitter_api_secret_key
    )
    auth.set_access_token(
        settings.twitter_access_token, settings.twitter_access_token_secret
    )
    api = tweepy.API(auth)
    logging.info(f"Authenticated as: {api.me().screen_name}")
    return api


def _get_tweets_iterator(api: tweepy.API) -> tweepy.Cursor:
    cursor = tweepy.Cursor(
        method=api.user_timeline, screen_name=api.me().screen_name, count=200
    ).items(api.me().statuses_count)
    return cursor


def prune_tweets(days: int = settings.twitter_tweet_prune_days):
    limit = TODAY - datetime.timedelta(days=days)
    logging.info(f"Tweets older than {limit} will be deleted")

    api = _authenticate()
    logging.info(f"{api.me().screen_name} has {api.me().statuses_count} tweets")
    cursor = _get_tweets_iterator(api=api)

    logging.info("Fetching tweets...")
    for t in _rate_limit_handler(cursor):
        # check if outside time limit and not self-liked
        if t.created_at.date() < limit and not t.favorited:
            logging.info(f"Pruning: {t.id_str} | {t.created_at} | {t.text}")
            try:
                api.destroy_status(t.id_str)
            except tweepy.error.TweepError as e:
                logging.error(e)

    logging.info("Pruning complete")


def prune_friends(days: int = settings.twitter_friend_prune_days):
    # set limit
    limit = TODAY - datetime.timedelta(days=days)
    logging.info(f"Friends inactive since {limit} will be unfriended")

    # auth
    api = _authenticate()

    # prune
    logging.info(f"{api.me().screen_name} has {api.me().friends_count} friends")

    cursor = tweepy.Cursor(
        method=api.friends, screen_name=api.me().screen_name, count=200
    ).items(api.me().friends_count)

    logging.info("Fetching friends...")
    for f in _rate_limit_handler(cursor):
        try:
            is_stale_friend = f.status.created_at.date() < limit
        except AttributeError:
            logging.info(f"{f.screen_name} has never tweeted")
            is_stale_friend = True

        if is_stale_friend:
            logging.info(f"Pruning: {f.screen_name}")
            try:
                api.destroy_friendship(f.screen_name)
            except tweepy.error.TweepError as e:
                logging.error(e)

    logging.info("Pruning complete")


def log_viral_tweets(
    likes: int = settings.twitter_viral_likes,
    retweets: int = settings.twitter_viral_retweets,
):
    logging.info(f"Logging personal tweets with {likes} likes or {retweets} retweets")

    api = _authenticate()
    cursor = _get_tweets_iterator(api=api)

    logging.info("Fetching tweets...")
    viral_tweets = []
    for t in _rate_limit_handler(cursor):
        if t.favorite_count >= likes or t.retweet_count >= retweets:
            data = {
                "id": t.id_str,
                "created_at": str(t.created_at),
                "favorite_count": t.favorite_count,
                "retweet_count": t.retweet_count,
                "text": t.text,
                "hashtags": t.entities["hashtags"],
                "mentions": t.entities["user_mentions"],
                "retweeted": t.retweeted,
            }
            logging.info(f"Logging viral tweet: {data}")

    logging.info("Logging complete")
    # TODO: send logs to db


def log_stats():
    api = _authenticate()
    data = {
        "followers": api.me().followers_count,
        "friends": api.me().friends_count,
        "listed_count": api.me().listed_count,
        "verified": api.me().verified,
    }
    logging.info(f"Stats for {api.me().screen_name}: {data}")
    # TODO: get mentions of self >> API.mentions_timeline
    # TODO: send logs to db


if __name__ == "__main__":
    # fire.Fire()
    # log_stats()
    log_viral_tweets(3, 3)
    # TODO: func to autoretweet self tweets with like/viral >> API.retweet(id)
