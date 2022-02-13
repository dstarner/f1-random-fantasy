import logging
import random

from django.conf import settings
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404, render, HttpResponseRedirect
import requests
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


def play(request: HttpRequest):
    oauth = twitter.get_oauth_client()
    auth_url = oauth.get_authorization_url()
    response = HttpResponseRedirect(auth_url)
    request.session['code_verifier'] = oauth.code_verifier
    return response


def pick(request: HttpRequest):
    oauth = twitter.get_oauth_client()
    oauth.code_verifier = request.session['code_verifier']
    request.session.delete('code_verifier')
    
    bearer_token_info = oauth.fetch_token(authorization_response=request.build_absolute_uri())
    client = twitter.get_client(bearer_token_info)
    try:
        user = client.get_user(username='dan_starner')
    except tweepy.Forbidden as e:
        logger.exception('unable to get user info: %s', e.response.json())
    return render(request, 'pick.html')