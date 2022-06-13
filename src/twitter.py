"""Twitter handler."""
import datetime
import json
from pathlib import Path
from typing import Optional

import fire
import tweepy

import utils
from config import settings

TODAY = datetime.date.today()
LOGGER = utils.get_logger("twitter")


def _authenticate(wait_on_rate_limit: bool = True):
    """Create authenticated API object."""
    LOGGER.info("Authenticating...")
    auth = tweepy.OAuthHandler(
        settings.twitter.api_key, settings.twitter.api_secret_key
    )
    auth.set_access_token(
        settings.twitter.access_token, settings.twitter.access_token_secret
    )
    api = tweepy.API(auth, wait_on_rate_limit=wait_on_rate_limit)

    try:
        user = api.verify_credentials()
        LOGGER.info(
            f"Authenticated as {user.screen_name} with {user.statuses_count} tweets"
        )
    except tweepy.Unauthorized as e:
        LOGGER.exception(e)
    return api


def get_followers(screen_name: Optional[str] = None, count: int = 200):
    """Fetch and dump followers of a user.

    Args:
        screen_name (Optional[str], optional):
            User to fetch followers from.
            Defaults to None.
    Raises:
        ValueError: [description]
    """

    # authenticate first; needed in many places
    api = _authenticate()

    # if we didn't specify someone else, default to authenticated user
    if not screen_name:
        screen_name = api.verify_credentials().screen_name

    # fetch friends
    LOGGER.info(f"Fetching followers from {screen_name}")
    cursor = tweepy.Cursor(
        method=api.get_followers, count=count, screen_name=screen_name
    ).items()
    # pylint: disable=protected-access
    followers = [follower._json for follower in cursor]
    LOGGER.info(f"Retrieved {len(followers)} followers")

    # dump to file
    output_path = Path().cwd() / f"{screen_name}-followers.json".lower()
    LOGGER.info(f"Dumping results to {output_path.resolve()}")
    with open(output_path, "w") as f:
        json.dump(obj=followers, fp=f, indent=4)


def get_friends(screen_name: Optional[str] = None, count: int = 200):
    """Fetch and dump friends of a user.

    Args:
        screen_name (Optional[str], optional):
            User to fetch friends from.
            Defaults to None.
    Raises:
        ValueError: [description]
    """

    # authenticate first; needed in many places
    api = _authenticate()

    # if we didn't specify someone else, default to authenticated user
    if not screen_name:
        screen_name = api.verify_credentials().screen_name

    # fetch friends
    LOGGER.info(f"Fetching friends from {screen_name}")
    cursor = tweepy.Cursor(
        method=api.get_friends, count=count, screen_name=screen_name
    ).items()
    # pylint: disable=protected-access
    friends = [friend._json for friend in cursor]
    LOGGER.info(f"Retrieved {len(friends)} friends")

    # dump to file
    output_path = Path().cwd() / f"{screen_name}-friends.json".lower()
    LOGGER.info(f"Dumping results to {output_path.resolve()}")
    with open(output_path, "w") as f:
        json.dump(obj=friends, fp=f, indent=4)


def prune_tweets(
    days: int = settings.twitter.tweet_prune_days,
    delete_liked: bool = settings.twitter.is_delete_liked,
    dry_run: bool = False,
    wait_on_rate_limit: bool = True,
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

    api = _authenticate(wait_on_rate_limit=wait_on_rate_limit)
    LOGGER.info(f"Authenticated as {api.verify_credentials().screen_name}")

    LOGGER.info("Fetching tweets...")
    try:
        for tweet in tweepy.Cursor(method=api.user_timeline, count=100).items():
            # check if outside time limit and if self-liked
            if tweet.created_at.date() < limit and (
                not tweet.favorited or delete_liked
            ):
                LOGGER.info(
                    (
                        "Pruning: "
                        f"{tweet.id_str} |"
                        f"{tweet.created_at.date()} |"
                        f"{tweet.text}"
                    )
                )

                # skip if dry run
                if dry_run:
                    continue

                # delete tweet
                try:
                    api.destroy_status(tweet.id_str)
                except tweepy.TweepyException as e:
                    LOGGER.error(e)
    except tweepy.errors.TooManyRequests as e:
        LOGGER.error(e)

    LOGGER.info("Pruning complete")


def prune_friends(
    days: int = settings.twitter.friend_prune_days,
    dry_run: bool = False,
    wait_on_rate_limit: bool = True,
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
    api = _authenticate(wait_on_rate_limit=wait_on_rate_limit)

    # prune
    screen_name = api.verify_credentials().screen_name
    friends_count = api.verify_credentials().friends_count
    LOGGER.info(f"{screen_name} has {friends_count} friends")

    LOGGER.info("Fetching friends...")
    try:
        for friend in tweepy.Cursor(method=api.get_friends, count=200).items():
            try:
                days_since_last_tweet = (TODAY - friend.status.created_at.date()).days
                is_stale_friend = days_since_last_tweet > days
            except AttributeError:
                LOGGER.info(f"{friend.screen_name} has never tweeted")
                days_since_last_tweet = None
                is_stale_friend = True

            if is_stale_friend:
                LOGGER.info(
                    f"Pruning: {friend.screen_name} | {days_since_last_tweet} days"
                )

                # skip if dry run
                if dry_run:
                    continue

                # unfriend
                try:
                    api.destroy_friendship(screen_name=friend.screen_name)
                except tweepy.TweepyException as e:
                    LOGGER.error(e)
    except tweepy.errors.TooManyRequests as e:
        LOGGER.error(e)

    LOGGER.info("Pruning complete")


def get_people_from_hashtag(hashtag: str, count: int = 200):
    """Get people from a hashtag.

    Args:
        hashtag (str): Hashtag to search for.
        count (int, optional): Number of people to return. Defaults to 100.
    """
    api = _authenticate()
    LOGGER.info(f"Fetching people from {hashtag}")
    people = api.search_users(q=f"#{hashtag}", count=count)
    LOGGER.info(f"Retrieved {len(people)} people")
    return people


if __name__ == "__main__":
    fire.Fire()
