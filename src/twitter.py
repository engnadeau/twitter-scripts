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


def _fetch_people_from_user(api: tweepy.API, people_type: str, screen_name: str):
    LOGGER.info(f"Fetching {people_type.lower()} from {screen_name}")
    if people_type.lower() == "friends":
        cursor = tweepy.Cursor(
            method=api.get_friends, count=200, screen_name=screen_name
        ).items()
    elif people_type.lower() == "followers":
        cursor = tweepy.Cursor(
            method=api.get_followers, count=200, screen_name=screen_name
        ).items()
    else:
        raise ValueError("People must be FRIENDS or FOLLOWERS")

    # pylint: disable=protected-access
    people = [person._json for person in cursor]
    return people


def dump_users(
    people_type: Optional[str] = None,
    screen_name: Optional[str] = None,
    output: Optional[str] = None,
):
    """Fetch and dump users.

    Args:
        people_type (Optional[str], optional):
            Type of people to fetch; FRIENDS or FOLLOWERS.
            Defaults to None.
        screen_name (Optional[str], optional):
            User to fetch people from.
            Defaults to None.
        input (Optional[str], optional):
            Alternative source of users from list.
            Defaults to None.
        output (Optional[str], optional):
            Output path to dump users.
            Defaults to None.

    Raises:
        ValueError: [description]
        ValueError: [description]
    """
    # authenticate first; needed in many places
    api = _authenticate()

    # if we didn't specify someone else, default to authenticated user
    if not screen_name:
        screen_name = api.verify_credentials().screen_name

    # prepare paths
    if output:
        output_path = Path(output)
    elif people_type:
        output_path = Path().cwd() / f"{screen_name}-{people_type}.json".lower()
    else:
        raise ValueError("Invalid output configuration.")

    # choose where get people from: list or user
    if people_type:
        people = _fetch_people_from_user(
            api=api, people_type=people_type, screen_name=screen_name
        )
    else:
        raise ValueError("Either PEOPLE_TYPE or PATH must not be NONE")
    LOGGER.info(f"Retrieved {len(people)} people")

    # dump to file
    LOGGER.info(f"Dumping results to {output_path.resolve()}")
    with open(output_path, "w") as f:
        json.dump(obj=people, fp=f, indent=4)


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


if __name__ == "__main__":
    fire.Fire()
