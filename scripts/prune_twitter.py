import tweepy
from config import settings
import datetime
import logging
import time
import fire

logging.basicConfig(level=logging.INFO)

TODAY = datetime.date.today()


def rate_limit_handler(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            logging.warning(f"Rate limit exceeded")
            logging.info(f"Sleeping for {settings.TWEEPY_SLEEP_TIME}s")
            time.sleep(settings.TWEEPY_SLEEP_TIME)
        except StopIteration:
            break


def authenticate():
    logging.info("Authenticating...")
    auth = tweepy.OAuthHandler(settings.API_KEY, settings.API_SECRET_KEY)
    auth.set_access_token(settings.ACCESS_TOKEN, settings.ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)
    logging.info(f"Authenticated as: {api.me().screen_name}")
    return api


def prune_tweets():
    # set limit
    limit = TODAY - datetime.timedelta(days=settings.TWEET_PRUNE_DAYS)
    logging.info(f"Tweets older than {limit} will be deleted")

    # auth
    api = authenticate()

    # prune
    logging.info(f"{api.me().screen_name} has {api.me().statuses_count} tweets")

    cursor = tweepy.Cursor(
        method=api.user_timeline, screen_name=api.me().screen_name, count=200
    ).items(api.me().statuses_count)

    logging.info("Fetching tweets...")
    for t in rate_limit_handler(cursor):
        if t.created_at.date() < limit:
            logging.info(f"Pruning: {t.id_str} | {t.created_at} | {t.text}")
            try:
                api.destroy_status(t.id_str)
            except tweepy.error.TweepError as e:
                logging.error(e)

    logging.info("Pruning complete")


def prune_friends():
    # set limit
    limit = TODAY - datetime.timedelta(days=settings.FRIEND_PRUNE_DAYS)
    logging.info(f"Friends inactive since {limit} will be unfriended")

    # auth
    api = authenticate()

    # prune
    logging.info(f"{api.me().screen_name} has {api.me().friends_count} friends")

    cursor = tweepy.Cursor(
        method=api.friends, screen_name=api.me().screen_name, count=200
    ).items(api.me().friends_count)

    logging.info("Fetching friends...")
    for f in rate_limit_handler(cursor):
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


if __name__ == "__main__":
    fire.Fire()
