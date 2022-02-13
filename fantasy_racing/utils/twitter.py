from django.conf import settings
import tweepy


def get_oauth_client():
    callback = settings.TWITTER_CALLBACK
    return tweepy.OAuth1UserHandler(settings.TWITTER_CLIENT_ID, settings.TWITTER_CLIENT_SECRET, callback=callback)


def get_api(access_token, access_token_secret) -> tweepy.Client:
    return tweepy.Client(
        consumer_key=settings.TWITTER_CLIENT_ID, consumer_secret=settings.TWITTER_CLIENT_SECRET,
        access_token=access_token, access_token_secret=access_token_secret
    )
