from django.conf import settings
import tweepy


def get_oauth_client():
    callback = settings.TWITTER_CALLBACK
    return tweepy.OAuth1UserHandler(
        consumer_key=settings.TWITTER_KEY, consumer_secret=settings.TWITTER_SECRET,
        callback=callback
    )


def get_client(access_token: str, access_token_secret: str) -> tweepy.Client:
    return tweepy.Client(
        consumer_key=settings.TWITTER_KEY, consumer_secret=settings.TWITTER_SECRET,
        access_token=access_token, access_token_secret=access_token_secret
    )
