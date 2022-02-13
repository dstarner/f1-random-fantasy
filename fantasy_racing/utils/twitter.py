from django.conf import settings
import tweepy


def get_oauth_client():
    callback = settings.TWITTER_CALLBACK
    return tweepy.OAuth2UserHandler(
        client_id=settings.TWITTER_CLIENT_ID, client_secret=settings.TWITTER_CLIENT_SECRET,
        redirect_uri=callback, scope=['users.read', 'tweet.write']
    )


def get_client(token_data: dict) -> tweepy.Client:
    return tweepy.Client(
        token_data['access_token'], consumer_key=settings.TWITTER_KEY, consumer_secret=settings.TWITTER_SECRET
    )
