import logging
import random

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, HttpResponseRedirect
import tweepy

from fantasy_racing.utils import twitter

from .models import Race, Schedule


logger = logging.getLogger(__name__)


def index(request):
    race = Race.objects.current()
    return render(request, 'index.html', {
        'race': race,
        'headline': random.choice([
            'The fantasy racing game where you don\'t get to pick who wins.',
            'Why spend money on fantasy racing?',
            'Spinning a prize wheel meets fantasy Formula 1 racing.',
            'Fantasy racing that\'s not considered gambling.',
            'Fantasy racing crossed with a random number generator.',
        ])
    })


def about(request):
    return render(request, 'about.html', {
        'faqs': [
            {'question': 'How does it work?', 'answer': 'Each week you play F1 Random Fantasy Racing, you\'re randomly assigned a car number that corresponds to a car racing in the next Formula 1 race. After the race, you earn the number of points that car scored in the real race. The player with the highest number of points at the end of the season wins.'}
        ]
    })


def schedule(request, year=None):
    schedule = Schedule.objects.last() if year is None else get_object_or_404(Schedule, year=year)
    years = Schedule.objects.values_list('year', flat=True)
    return render(request, 'schedule.html', {'schedule': schedule, 'years': years})


def picks(request, id=None):
    race = Race.objects.current() if id is None else get_object_or_404(Race, id=id)
    if not race:
        raise Http404
    return render(request, 'picks.html', {'race': race, 'title': race.track})


def standings(request, year=None):
    schedule = Schedule.objects.last() if year is None else get_object_or_404(Schedule, year=year)
    return render(request, 'standings.html', {'schedule': schedule, 'title': f'{schedule.year} Standings'})


def play(request):
    oauth = twitter.get_oauth_client()
    auth_url = oauth.get_authorization_url(signin_with_twitter=True)
    response = HttpResponseRedirect(auth_url)
    request.session['request_token'] = oauth.request_token
    logger.debug('%s', oauth.request_token)
    return response


def pick(request):
    verifier = request.GET.get('oauth_verifier')
    oauth = twitter.get_oauth_client()
    token = request.session.get('request_token')
	# remove the request token now we don't need it
    request.session.delete('request_token')
    oauth.request_token = token

    logger.debug('%s -- %s', verifier, token)
    try:
        access_token, access_token_secret = oauth.get_access_token(verifier)
    except (tweepy.TweepyException, tweepy.TwitterServerError):
        logger.exception('Could not get access token for user')
        return HttpResponse(status=500)

    twitter_api = twitter.get_api(access_token, access_token_secret)
    try:
        user = twitter_api.get_me()
    except (tweepy.TweepyException, tweepy.TwitterServerError):
        logger.exception('Could not get user information')
        return HttpResponse(status=500)
    logger.info('%s', user)
    return render(request, 'pick.html')